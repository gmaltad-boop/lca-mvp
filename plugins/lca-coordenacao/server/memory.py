"""Local, reviewed experience memory. No model calls or automatic rule learning."""
import hashlib
import itertools
import json
import re
import sqlite3
import unicodedata
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


CHECKS = {"format", "fidelity", "utility"}
FIELDS = {"id", "claim", "scope", "source_ref", "source_hash", "artifact_hash",
          "kind", "source_group", "supervised", "feedback_used", "checks", "reviewer"}


def _text(value, field, maximum=4000):
    if not isinstance(value, str):
        raise ValueError(field + " must be text")
    value = unicodedata.normalize("NFC", value).strip()
    if not value or len(value) > maximum:
        raise ValueError(field + " is empty or too long")
    return value


def _fold(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold())
                   if unicodedata.category(c) != "Mn")


def _hash(value, field):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value):
        raise ValueError(field + " must be a SHA-256 hex digest")
    return value.lower()


def _checks(value, approved=False):
    if not isinstance(value, dict) or set(value) != CHECKS:
        raise ValueError("format, fidelity and utility checks are all required")
    if any(v is not None and type(v) is not bool for v in value.values()):
        raise ValueError("checks must be booleans or null")
    if approved and any(v is not True for v in value.values()):
        raise ValueError("all three checks must be explicitly approved")
    return dict(value)


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _record(data):
    if not isinstance(data, dict) or set(data) - FIELDS:
        raise ValueError("unknown experience field")
    required = FIELDS - {"id", "reviewer"}
    if not required <= set(data):
        raise ValueError("missing experience fields")
    result = {key: _text(data[key], key) for key in ("claim", "source_ref")}
    result.update({key: _text(data[key], key, 200).casefold()
                   for key in ("scope", "source_group")})
    result["id"] = _text(data.get("id", str(uuid.uuid4())), "id", 200)
    for key in ("source_hash", "artifact_hash"):
        result[key] = _hash(data[key], key)
    if not isinstance(data["kind"], str) or data["kind"] not in {"observacao", "hipotese", "licao"}:
        raise ValueError("invalid kind")
    result["kind"] = data["kind"]
    for key in ("supervised", "feedback_used"):
        if type(data[key]) is not bool:
            raise ValueError(key + " must be a boolean")
        result[key] = data[key]
    result["checks"] = _checks(data["checks"])
    result["reviewer"] = None if data.get("reviewer") is None else _text(data["reviewer"], "reviewer", 200)
    return result


class Store:
    """Append-only API and SQLite guards, not protection from a database administrator.

    add/promote/withdraw return a record; search returns records; history returns events.
    Promotion receipts are caller-supplied: this class checks their presence and integrity,
    not whether a named reviewer is a real person or has authority to approve.
    """
    def __init__(self, path, read_only=False):
        if type(read_only) is not bool:
            raise ValueError("read_only must be a boolean")
        self.read_only = read_only
        if read_only:
            if str(path) == ":memory:":
                raise ValueError("read-only memory requires an existing database")
            try:
                self.db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
            except sqlite3.Error as exc:
                raise ValueError("cannot open existing read-only memory") from exc
            self.db.row_factory = sqlite3.Row
            return
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS experiences (
                id TEXT PRIMARY KEY, payload TEXT NOT NULL, digest TEXT NOT NULL,
                scope_key TEXT NOT NULL, search_text TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                experience_id TEXT NOT NULL REFERENCES experiences(id),
                payload TEXT NOT NULL, prev_digest TEXT NOT NULL, digest TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS memory_scope ON experiences(scope_key);
            CREATE INDEX IF NOT EXISTS memory_events ON events(experience_id,seq);
            CREATE TRIGGER IF NOT EXISTS experience_no_update BEFORE UPDATE ON experiences
              BEGIN SELECT RAISE(ABORT,'append-only'); END;
            CREATE TRIGGER IF NOT EXISTS experience_no_delete BEFORE DELETE ON experiences
              BEGIN SELECT RAISE(ABORT,'append-only'); END;
            CREATE TRIGGER IF NOT EXISTS event_no_update BEFORE UPDATE ON events
              BEGIN SELECT RAISE(ABORT,'append-only'); END;
            CREATE TRIGGER IF NOT EXISTS event_no_delete BEFORE DELETE ON events
              BEGIN SELECT RAISE(ABORT,'append-only'); END;
        """)

    def close(self):
        self.db.close()

    @contextmanager
    def _write(self):
        if self.read_only:
            raise ValueError("memory is read-only")
        if self.db.in_transaction:
            raise ValueError("a memory transaction is already open")
        try:
            # Reserve the writer before validating state. Another connection must
            # not withdraw evidence between a promotion's reads and its insert.
            self.db.execute("BEGIN IMMEDIATE")
            yield
            self.db.commit()
        except sqlite3.Error as exc:
            self.db.rollback()
            raise ValueError("memory write failed") from exc
        except BaseException:
            self.db.rollback()
            raise

    def _load(self, identifier):
        identifier = _text(identifier, "id", 200)
        row = self.db.execute("SELECT * FROM experiences WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ValueError("unknown experience")
        if _digest(row["payload"]) != row["digest"]:
            raise ValueError("experience integrity failure")
        try:
            record = _record(json.loads(row["payload"]))
        except (TypeError, KeyError, json.JSONDecodeError) as exc:
            raise ValueError("invalid stored experience") from exc
        if record["id"] != identifier or record["scope"] != row["scope_key"]:
            raise ValueError("experience identity mismatch")
        return record

    def _events(self, identifier):
        previous = ""
        result = []
        for row in self.db.execute("SELECT * FROM events WHERE experience_id=? ORDER BY seq", (identifier,)):
            if row["prev_digest"] != previous or _digest(previous + "\n" + row["payload"]) != row["digest"]:
                raise ValueError("event integrity failure")
            try:
                event = json.loads(row["payload"])
            except json.JSONDecodeError as exc:
                raise ValueError("invalid stored event") from exc
            if event.get("id") != identifier or event.get("action") not in {"created", "promoted", "withdrawn"}:
                raise ValueError("invalid stored event")
            event["seq"] = row["seq"]
            result.append(event)
            previous = row["digest"]
        if not result or result[0]["action"] != "created":
            raise ValueError("missing creation event")
        return result

    def _append(self, identifier, action, detail):
        previous = self.db.execute("SELECT digest FROM events WHERE experience_id=? ORDER BY seq DESC LIMIT 1", (identifier,)).fetchone()
        previous = previous[0] if previous else ""
        event = {"id": identifier, "action": action,
                 "at": datetime.now(timezone.utc).isoformat(), "detail": detail}
        payload = _json(event)
        self.db.execute("INSERT INTO events(experience_id,payload,prev_digest,digest) VALUES(?,?,?,?)",
                        (identifier, payload, previous, _digest(previous + "\n" + payload)))

    def _view(self, identifier):
        record = self._load(identifier)
        events = self._events(identifier)
        record["status"] = {"created": "candidato", "promoted": "ativo", "withdrawn": "retirado"}[events[-1]["action"]]
        reviews = [event["detail"] for event in events if event["action"] == "promoted"]
        if reviews:
            record["review"] = reviews[-1]
            record["checks"] = reviews[-1]["checks"]
            record["reviewer"] = reviews[-1]["reviewer"]
        return record

    def add(self, data):
        record = _record(data)
        payload = _json(record)
        with self._write():
            self.db.execute("INSERT INTO experiences VALUES(?,?,?,?,?)", (record["id"], payload, _digest(payload), record["scope"], _fold(record["claim"])))
            self._append(record["id"], "created", {})
        return self._view(record["id"])

    def search(self, query, scope, limit=5, include_candidates=False):
        if not isinstance(query, str) or len(query) > 4000:
            raise ValueError("invalid query")
        scope = _text(scope, "scope", 200).casefold()
        if type(limit) is not int or not 1 <= limit <= 50 or type(include_candidates) is not bool:
            raise ValueError("invalid search limit or candidate flag")
        terms = re.findall(r"\w+", _fold(query))
        result = []
        for row in self.db.execute("SELECT id FROM experiences WHERE scope_key=? ORDER BY rowid DESC", (scope,)):
            record = self._view(row["id"])
            if record["status"] == "retirado" or (record["status"] == "candidato" and not include_candidates):
                continue
            if all(term in _fold(record["claim"]) for term in terms):
                result.append(record)
                if len(result) == limit:
                    break
        return result

    def promote(self, identifier, reviewdict):
        allowed = {"reviewer", "evidence_ref", "checks", "source_hash", "artifact_hash", "evidence_ids"}
        if not isinstance(reviewdict, dict) or set(reviewdict) - allowed:
            raise ValueError("unknown review field; counts cannot be self-declared")
        try:
            review = {"reviewer": _text(reviewdict["reviewer"], "reviewer", 200),
                      "evidence_ref": _text(reviewdict["evidence_ref"], "evidence_ref", 2000),
                      "source_hash": _hash(reviewdict["source_hash"], "source_hash"),
                      "artifact_hash": _hash(reviewdict["artifact_hash"], "artifact_hash"),
                      "checks": _checks(reviewdict["checks"], approved=True)}
        except KeyError as exc:
            raise ValueError("reviewer, evidence_ref, matching hashes and separate checks are required") from exc
        ids = reviewdict.get("evidence_ids", [])
        if not isinstance(ids, list) or len(ids) > 20:
            raise ValueError("evidence_ids must be a list of up to 20 ids")
        ids = list(dict.fromkeys(_text(item, "evidence id", 200) for item in ids))
        with self._write():
            record = self._view(identifier)
            if record["status"] != "candidato":
                raise ValueError("only candidates can be promoted")
            if any(record[key] != review[key] for key in ("source_hash", "artifact_hash")):
                raise ValueError("review does not match the source and artifact version")
            evidence = [self._view(item) for item in ids]
            qualified = [item for item in evidence if item["id"] != identifier
                         and item["status"] == "ativo" and item["kind"] == "observacao"
                         and item["scope"] == record["scope"]
                         and not item["supervised"] and not item["feedback_used"]
                         and all(item["checks"][check] is True for check in CHECKS)]
            # Two genuinely distinct stored groups, sources AND artifacts are necessary.
            pair = next((list(items) for items in itertools.combinations(qualified, 2)
                         if all(len({x[field] for x in items}) == 2
                                for field in ("source_group", "source_hash", "artifact_hash"))), [])
            if record["kind"] == "licao" and not pair:
                raise ValueError("a lesson needs two reviewed, unassisted independent source groups")
            review["evidence_ids"] = ids
            review["independent_source_groups"] = [item["source_group"] for item in pair]
            review["independent_source_count"] = len(pair)  # Minimal supporting witness, never a caller's N.
            self._append(identifier, "promoted", review)
        return self._view(identifier)

    def withdraw(self, identifier, reason):
        reason = _text(reason, "reason", 2000)
        with self._write():
            record = self._view(identifier)
            if record["status"] == "retirado":
                raise ValueError("experience is already withdrawn")
            self._append(identifier, "withdrawn", {"reason": reason})
            # Dependent lessons require fresh review if a supporting experience is withdrawn.
            for row in self.db.execute("SELECT id FROM experiences WHERE id!=?", (identifier,)).fetchall():
                other = self._view(row["id"])
                if other["status"] == "ativo" and other["kind"] == "licao" and identifier in other.get("review", {}).get("evidence_ids", []):
                    self._append(other["id"], "withdrawn", {"reason": "support_withdrawn:" + identifier})
        return self._view(identifier)

    def history(self, identifier, scope=None):
        record = self._load(identifier)
        if scope is not None and _text(scope, "scope", 200).casefold() != record["scope"]:
            raise ValueError("experience does not belong to this scope")
        return self._events(identifier)
