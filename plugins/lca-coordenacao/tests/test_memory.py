import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest import mock


spec = importlib.util.spec_from_file_location("lca_memory", Path(__file__).resolve().parents[1] / "server" / "memory.py")
memory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory)
Store = memory.Store
sha = lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()
CHECKS = {"format": True, "fidelity": True, "utility": True}


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "memory.sqlite3"
        self.store = Store(self.path)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def data(self, identifier, **overrides):
        value = dict(id=identifier, claim="Conferir citações e hipóteses", scope="pesquisa",
                     source_ref="fixture:" + identifier, source_hash=sha("source:" + identifier),
                     artifact_hash=sha("artifact:" + identifier), kind="observacao",
                     source_group="group:" + identifier, supervised=False, feedback_used=False,
                     checks=dict(CHECKS), reviewer=None)
        value.update(overrides)
        return value

    def review(self, identifier="a", **overrides):
        value = dict(reviewer="reviewer:test", evidence_ref="review:receipt", checks=dict(CHECKS),
                     source_hash=sha("source:"+identifier), artifact_hash=sha("artifact:"+identifier))
        value.update(overrides)
        return value

    def active(self, identifier, **overrides):
        record = self.store.add(self.data(identifier, **overrides))
        return self.store.promote(identifier, self.review(identifier, source_hash=record["source_hash"], artifact_hash=record["artifact_hash"]))

    def test_candidates_are_not_rules_even_with_all_checks(self):
        item = self.store.add(self.data("a"))
        self.assertEqual(item["status"], "candidato")
        self.assertEqual(self.store.search("citações", "pesquisa"), [])
        result = self.store.search("citac\u0327o\u0303es", "pesquisa", include_candidates=True)
        self.assertEqual(result[0]["id"], "a")
        self.assertEqual(result[0]["source_hash"], sha("source:a"))

    def test_formal_success_without_utility_is_not_approval(self):
        self.store.add(self.data("a"))
        with self.assertRaises(ValueError):
            self.store.promote("a", self.review(checks={"format": True, "fidelity": True, "utility": False}))
        self.assertEqual(len(self.store.history("a")), 1)

    def test_review_receipt_and_three_distinct_checks_are_required(self):
        self.store.add(self.data("a"))
        for invalid in ({"reviewer": "r", "checks": CHECKS},
                        self.review(evidence_ref=" "), self.review(checks={"format": True}),
                        self.review(checks={"format": 1, "fidelity": True, "utility": True}),
                        self.review(N=True), self.review(independent_source_count=20)):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.store.promote("a", invalid)

    def test_one_group_cannot_promote_a_lesson(self):
        self.active("a")
        self.store.add(self.data("lesson", kind="licao"))
        with self.assertRaises(ValueError):
            self.store.promote("lesson", self.review("lesson", evidence_ids=["a", "a"]))

    def test_same_source_copies_do_not_count_as_independent(self):
        self.active("a")
        self.active("b", source_hash=sha("source:a"))
        self.store.add(self.data("lesson", kind="licao"))
        with self.assertRaises(ValueError):
            self.store.promote("lesson", self.review("lesson", evidence_ids=["a", "b"]))

    def test_same_group_or_artifact_does_not_count_twice(self):
        for field in ("source_group", "artifact_hash"):
            with self.subTest(field=field):
                left, right, lesson = "a:"+field, "b:"+field, "l:"+field
                first = self.active(left)
                self.active(right, **{field: first[field]})
                self.store.add(self.data(lesson, kind="licao"))
                with self.assertRaises(ValueError):
                    self.store.promote(lesson, self.review(lesson, evidence_ids=[left, right]))

    def test_two_independent_unassisted_observations_allow_lesson(self):
        self.active("a")
        self.active("b")
        self.store.add(self.data("lesson", kind="licao"))
        item = self.store.promote("lesson", self.review("lesson", evidence_ids=["a", "b"]))
        self.assertEqual(item["status"], "ativo")
        self.assertEqual(item["review"]["independent_source_count"], 2)
        self.assertEqual(set(item["review"]["independent_source_groups"]), {"group:a", "group:b"})

    def test_feedback_or_candidate_evidence_cannot_prove_generalization(self):
        self.active("a")
        for identifier, kwargs, approve in (("guided", {"supervised": True}, True),
                                            ("feedback", {"feedback_used": True}, True),
                                            ("pending", {}, False)):
            if approve:
                self.active(identifier, **kwargs)
            else:
                self.store.add(self.data(identifier, **kwargs))
            lesson = "lesson:"+identifier
            self.store.add(self.data(lesson, kind="licao"))
            with self.assertRaises(ValueError):
                self.store.promote(lesson, self.review(lesson, evidence_ids=["a", identifier]))

    def test_scope_and_unicode_search_do_not_leak_other_projects(self):
        self.active("a", scope="PESQUISA", claim="Avaliação de hipóteses")
        self.active("private", scope="outro-projeto", claim="Avaliação de hipóteses")
        self.assertEqual([x["id"] for x in self.store.search("avaliac\u0327a\u0303o", "pesquisa")], ["a"])
        self.assertEqual(self.store.search("inexistente", "pesquisa"), [])
        for limit in (True, 0, 51, 1.5):
            with self.assertRaises(ValueError):
                self.store.search("", "pesquisa", limit=limit)

    def test_evidence_from_other_scope_is_rejected(self):
        self.active("a")
        self.active("b", scope="outro-projeto")
        self.store.add(self.data("lesson", kind="licao"))
        with self.assertRaises(ValueError):
            self.store.promote("lesson", self.review("lesson", evidence_ids=["a", "b"]))

    def test_withdrawal_and_history_persist_and_cascade_to_lesson(self):
        self.active("a")
        self.active("b")
        self.store.add(self.data("lesson", kind="licao"))
        self.store.promote("lesson", self.review("lesson", evidence_ids=["a", "b"]))
        self.store.withdraw("a", "fonte contestada")
        self.assertEqual([x["action"] for x in self.store.history("a")], ["created", "promoted", "withdrawn"])
        self.assertEqual(self.store.history("lesson")[-1]["detail"]["reason"], "support_withdrawn:a")
        self.store.close()
        self.store = Store(self.path)
        self.assertEqual([x["id"] for x in self.store.search("", "pesquisa", include_candidates=True)], ["b"])
        with self.assertRaises(ValueError):
            self.store.promote("a", self.review())

    def test_promotion_reserves_writer_before_validated_evidence_can_be_withdrawn(self):
        self.active("a")
        self.active("b")
        self.store.add(self.data("lesson", kind="licao"))
        other = Store(self.path)
        other.db.execute("PRAGMA busy_timeout=50")
        original_append = self.store._append
        attempted = []

        def interleave(identifier, action, detail):
            if identifier == "lesson" and action == "promoted":
                # This is the former race: supporting rows have been validated,
                # but the promotion event has not been inserted yet.
                attempted.append(True)
                with self.assertRaises(ValueError) as error:
                    other.withdraw("a", "retirada concorrente")
                self.assertIsInstance(error.exception.__cause__, sqlite3.OperationalError)
                self.assertIn("locked", str(error.exception.__cause__))
            return original_append(identifier, action, detail)

        try:
            with mock.patch.object(self.store, "_append", side_effect=interleave):
                promoted = self.store.promote("lesson", self.review("lesson", evidence_ids=["a", "b"]))
            self.assertEqual(attempted, [True])
            self.assertEqual(promoted["status"], "ativo")
            self.assertEqual(other.history("a")[-1]["action"], "promoted")
            # Once the promotion commits, the retry sees and withdraws its lesson.
            other.withdraw("a", "retirada após revisão")
            self.assertEqual(self.store.history("lesson")[-1]["detail"]["reason"], "support_withdrawn:a")
            self.assertNotIn("lesson", [x["id"] for x in self.store.search("", "pesquisa")])
        finally:
            other.close()

    def test_withdrawal_reserves_writer_before_its_first_state_read(self):
        self.active("a")
        self.active("b")
        self.store.add(self.data("lesson", kind="licao"))
        other = Store(self.path)
        other.db.execute("PRAGMA busy_timeout=50")
        original_view = self.store._view
        attempted = []

        def interleave(identifier):
            record = original_view(identifier)
            if identifier == "a" and not attempted:
                attempted.append(True)
                with self.assertRaises(ValueError) as error:
                    other.promote("lesson", self.review("lesson", evidence_ids=["a", "b"]))
                self.assertIsInstance(error.exception.__cause__, sqlite3.OperationalError)
            return record

        try:
            with mock.patch.object(self.store, "_view", side_effect=interleave):
                self.store.withdraw("a", "fonte contestada")
            self.assertEqual(attempted, [True])
            with self.assertRaises(ValueError):
                other.promote("lesson", self.review("lesson", evidence_ids=["a", "b"]))
            self.assertEqual([event["action"] for event in other.history("lesson")], ["created"])
        finally:
            other.close()

    def test_cascade_failure_rolls_back_support_and_lesson_together(self):
        self.active("a")
        self.active("b")
        self.store.add(self.data("lesson", kind="licao"))
        self.store.promote("lesson", self.review("lesson", evidence_ids=["a", "b"]))
        original_append = self.store._append

        def fail_cascade(identifier, action, detail):
            if identifier == "lesson" and action == "withdrawn":
                raise ValueError("injected cascade failure")
            return original_append(identifier, action, detail)

        with mock.patch.object(self.store, "_append", side_effect=fail_cascade):
            with self.assertRaisesRegex(ValueError, "injected cascade failure"):
                self.store.withdraw("a", "fonte contestada")
        self.assertEqual(self.store.history("a")[-1]["action"], "promoted")
        self.assertEqual(self.store.history("lesson")[-1]["action"], "promoted")

    def test_history_requires_the_requested_scope_and_normalizes_unicode(self):
        self.active("a", scope="Équipe")
        self.assertEqual(self.store.history("a", scope=" E\u0301QUIPE "), self.store.history("a"))
        for scope in ("outro-projeto", "", True):
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                self.store.history("a", scope=scope)

    def test_read_only_store_reads_without_schema_writes_and_rejects_mutations(self):
        self.active("a")
        self.store.add(self.data("candidate"))
        self.store.close()
        traced = []
        connect = sqlite3.connect

        def traced_connect(*args, **kwargs):
            connection = connect(*args, **kwargs)
            connection.set_trace_callback(traced.append)
            return connection

        with mock.patch.object(memory.sqlite3, "connect", side_effect=traced_connect):
            reader = Store(self.path, read_only=True)
        self.assertEqual(traced, [])  # Opening read-only never attempts CREATE/DDL.
        try:
            self.assertEqual([x["id"] for x in reader.search("", "pesquisa")], ["a"])
            self.assertEqual(reader.history("a", "pesquisa")[-1]["action"], "promoted")
            for action in (lambda: reader.add(self.data("new")),
                           lambda: reader.promote("candidate", self.review("candidate")),
                           lambda: reader.withdraw("a", "não permitido")):
                with self.assertRaisesRegex(ValueError, "read-only"):
                    action()
            with self.assertRaises(sqlite3.OperationalError):
                reader.db.execute("CREATE TABLE forbidden(id TEXT)")
        finally:
            reader.close()
            self.store = Store(self.path)
        self.assertEqual(self.store.history("a")[-1]["action"], "promoted")

    def test_read_only_missing_path_does_not_create_database_or_directory(self):
        missing = Path(self.temp.name) / "absent" / "never-created.sqlite3"
        with self.assertRaises(ValueError):
            Store(missing, read_only=True)
        self.assertFalse(missing.parent.exists())
        with self.assertRaises(ValueError):
            Store(":memory:", read_only=True)
        with self.assertRaises(ValueError):
            Store(self.path, read_only=1)

    def test_hash_format_and_payload_corruption_are_rejected(self):
        for field in ("source_hash", "artifact_hash"):
            with self.assertRaises(ValueError):
                self.store.add(self.data("bad", **{field: "not-a-hash"}))
        self.store.add(self.data("a"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.db.execute("UPDATE experiences SET digest='bad' WHERE id='a'")
        self.store.db.execute("DROP TRIGGER experience_no_update")
        self.store.db.execute("UPDATE experiences SET payload=? WHERE id='a'", (json.dumps(self.data("a", artifact_hash=sha("changed"))),))
        self.store.db.commit()
        with self.assertRaises(ValueError):
            self.store.promote("a", self.review())

    def test_review_cannot_approve_another_artifact_version(self):
        self.store.add(self.data("a"))
        for field in ("source_hash", "artifact_hash"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.store.promote("a", self.review(**{field:sha("other-version")}))
        self.assertEqual(len(self.store.history("a")), 1)

    def test_event_history_corruption_is_detected(self):
        self.active("a")
        self.store.db.execute("DROP TRIGGER event_no_update")
        self.store.db.execute("UPDATE events SET digest='bad' WHERE experience_id='a' AND seq=2")
        self.store.db.commit()
        with self.assertRaises(ValueError):
            self.store.history("a")


if __name__ == "__main__":
    unittest.main()
