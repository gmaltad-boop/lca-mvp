import copy
from contextlib import closing
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest import mock
import urllib.error

MODULE = Path(__file__).resolve().parents[1] / "server" / "discord_bridge.py"
SPEC = importlib.util.spec_from_file_location("discord_bridge", MODULE)
bridge_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge_module)
Bridge = bridge_module.Bridge
UTC = timezone.utc
NOW = datetime(2026, 11, 3, 14, 0, tzinfo=UTC)
CONFIG = {"guild_id": "759916034731278358", "channel_id": "1566593781430616247", "authorized_user_ids": ["123456789012345678"], "enabled": False}


def message(content="!lca pedir T-003 Revisar uma fonte pública", mid="1566593781430616248"):
    return {"id": mid, "guild_id": CONFIG["guild_id"], "channel_id": CONFIG["channel_id"], "author": {"id": CONFIG["authorized_user_ids"][0], "bot": False}, "timestamp": NOW.isoformat(), "content": content}


class FakeClient:
    def __init__(self):
        self.posts = []
        self.messages = []
        self.fail_post = False
        self.calls = []

    def get_channel(self, cid):
        self.calls.append("channel")
        return {"id": cid, "guild_id": CONFIG["guild_id"]}

    def get_messages(self, cid, *, after, limit):
        self.calls.append((after, limit))
        return self.messages

    def post_message(self, cid, body):
        self.posts.append((cid, body))
        if self.fail_post:
            raise bridge_module.TransportFailure("timeout")
        return {"id": "1666593781430616248"}


class Response:
    def __init__(self, data):
        self.data = json.dumps(data).encode()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, limit): return self.data[:limit]


class DiscordBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "bridge.sqlite"
        self.bridge = Bridge(CONFIG, self.db)

    def tearDown(self): self.tmp.cleanup()

    def count(self, table):
        with closing(sqlite3.connect(self.db)) as db:
            return db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]

    def live(self):
        config = dict(CONFIG, enabled=True, ids_confirmed=True, credential_rotation_confirmed=True)
        return Bridge(config, self.db)

    def test_offline_request_is_only_awaiting_review(self):
        result = self.bridge.handle(message(), now=NOW)
        self.assertEqual(result["decision"], "request_queued")
        self.assertFalse(result["network_used"])
        self.assertEqual(self.bridge.list_requests()[0]["status"], "awaiting_review")
        self.assertEqual(self.count("discord_outbox"), 1)

    def test_empty_allowlist_and_nonnumeric_ids_rejected(self):
        for change in ({"authorized_user_ids": []}, {"authorized_user_ids": ["not-user"]}, {"guild_id": True}, {"channel_id": "../123"}, {"enabled": "true"}):
            with self.subTest(change=change), self.assertRaises(bridge_module.ConfigError):
                Bridge(dict(CONFIG, **change), self.db)

    def test_bot_webhook_wrong_author_guild_channel_rejected(self):
        cases = []
        for field, value in (("guild_id", "99"), ("channel_id", "98"), ("webhook_id", "123")):
            item = message(); item[field] = value; cases.append(item)
        item = message(); item["author"]["bot"] = True; cases.append(item)
        item = message(); item["author"]["id"] = "97"; cases.append(item)
        for item in cases:
            self.assertEqual(self.bridge.handle(item, now=NOW)["decision"], "ignored")
        self.assertEqual(self.count("discord_requests"), 0)

    def test_stale_future_naive_and_missing_timestamp_rejected(self):
        for stamp in ((NOW-timedelta(seconds=301)).isoformat(), (NOW+timedelta(seconds=31)).isoformat(), "2026-11-03T14:00:00", ""):
            item = message(); item["timestamp"] = stamp
            self.assertEqual(self.bridge.handle(item, now=NOW)["decision"], "ignored")

    def test_length_prefix_and_other_task_id(self):
        self.assertEqual(self.bridge.handle(message("!lca pedir T-003 "+"x"*500), now=NOW)["reason"], "content_too_long")
        self.assertEqual(self.bridge.handle(message("!lcaevil status"), now=NOW)["decision"], "ignored")
        self.assertEqual(self.bridge.handle(message("!lca pedir T-999 teste"), now=NOW)["decision"], "unknown_command")
        self.assertEqual(self.count("discord_requests"), 0)

    def test_secret_never_saved_in_any_table(self):
        synthetic = "sk-proj-" + "x"*32
        result = self.bridge.handle(message("!lca pedir T-003 "+synthetic), now=NOW)
        self.assertEqual(result["decision"], "secret_rejected")
        self.assertEqual(self.bridge.list_requests(), [])
        with closing(sqlite3.connect(self.db)) as db:
            dump = "\n".join(db.iterdump())
        self.assertNotIn(synthetic, dump)
        self.assertNotIn(synthetic, result["reply"])

    def test_replay_atomic_deduplication(self):
        first = self.bridge.handle(message(), now=NOW)
        second = Bridge(CONFIG, self.db).handle(message(), now=NOW)
        self.assertEqual(second["decision"], "duplicate")
        self.assertEqual(self.count("discord_requests"), 1)
        self.assertEqual(self.count("discord_outbox"), 1)
        self.assertTrue(first["outbox_id"])

    def test_concurrent_duplicate_has_one_inbox_and_outbox(self):
        results = []
        threads = [threading.Thread(target=lambda: results.append(Bridge(CONFIG, self.db).handle(message(), now=NOW))) for _ in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(sorted(r["decision"] for r in results), ["duplicate", "request_queued"])
        self.assertEqual(self.count("discord_requests"), 1)
        self.assertEqual(self.count("discord_outbox"), 1)

    def test_status_pending_help_do_not_execute(self):
        for index, command in enumerate(("status", "pendencias", "ajuda")):
            result = self.bridge.handle(message("!lca "+command, str(1566593781430616250+index)), now=NOW)
            self.assertIn(result["decision"], ("status", "pending", "help"))
        self.assertEqual(self.bridge.list_requests(), [])

    def test_monday_window_exact_boundaries(self):
        monday = datetime(2026, 11, 2, 11, 45, tzinfo=UTC)
        for stamp in (monday, monday+timedelta(minutes=29,seconds=59)):
            self.assertTrue(bridge_module.protected_window(stamp))
            self.assertEqual(self.bridge.handle(message(), now=stamp)["reason"], "protected_window")
        self.assertFalse(bridge_module.protected_window(monday-timedelta(seconds=1)))
        self.assertFalse(bridge_module.protected_window(monday+timedelta(minutes=30)))
        self.assertEqual(self.count("discord_processed"), 0)

    def test_live_gates_default_disabled_and_rotation_required(self):
        with self.assertRaises(bridge_module.BridgeStop):
            self.bridge.poll_once(FakeClient(), now=NOW)
        enabled = Bridge(dict(CONFIG, enabled=True, ids_confirmed=True), self.db)
        with self.assertRaises(bridge_module.BridgeStop):
            enabled.poll_once(FakeClient(), now=NOW)

    def test_bootstrap_cursor_no_history_replay_and_persistence(self):
        client = FakeClient(); client.messages = [message()]
        bridge = self.live()
        self.assertEqual(bridge.poll_once(client, now=NOW)["state"], "bootstrapped_without_replay")
        self.assertEqual(self.count("discord_requests"), 0)
        self.assertEqual(Bridge(CONFIG, self.db).cursor(), message()["id"])

    def test_first_live_contact_never_publishes_offline_preview(self):
        self.bridge.handle(message(),now=NOW)
        client=FakeClient(); bridge=self.live()
        bridge.poll_once(client,now=NOW)
        bridge.poll_once(client,now=NOW)
        self.assertEqual(client.posts,[])
        self.assertEqual(len(bridge.list_requests()),1)

    def test_poll_enriches_guild_only_after_verified_channel(self):
        client = FakeClient(); bridge = self.live()
        bridge.poll_once(client, now=NOW)
        item = message(); del item["guild_id"]; client.messages = [item]
        result = bridge.poll_once(client, now=NOW)
        self.assertEqual(result["decisions"], ["request_queued"])
        self.assertEqual(len(client.posts), 1)
        self.assertEqual(client.posts[0][1]["allowed_mentions"]["parse"], [])

    def test_timeout_marks_uncertain_and_replay_never_posts_again(self):
        client = FakeClient(); client.fail_post = True; bridge = self.live()
        bridge.handle(message(), now=NOW)
        self.assertEqual(bridge.dispatch_pending(client, now=NOW)[0]["status"], "send_uncertain")
        self.assertEqual(bridge.handle(message(), now=NOW)["decision"], "duplicate")
        self.assertEqual(bridge.dispatch_pending(client, now=NOW), [])
        self.assertEqual(len(client.posts), 1)

    def test_dispatch_claims_before_network_and_no_double_send(self):
        bridge = self.live(); bridge.handle(message(), now=NOW)
        outer = self
        class Inspect(FakeClient):
            def post_message(self, cid, body):
                with closing(sqlite3.connect(outer.db)) as db:
                    outer.assertEqual(db.execute("SELECT status FROM discord_outbox").fetchone()[0], "sending")
                return super().post_message(cid, body)
        client = Inspect()
        bridge.dispatch_pending(client, now=NOW)
        bridge.dispatch_pending(client, now=NOW)
        self.assertEqual(len(client.posts), 1)

    def test_protected_poll_does_not_touch_network_or_cursor(self):
        client = FakeClient()
        result = self.live().poll_once(client, now=datetime(2026,11,2,12,0,tzinfo=UTC))
        self.assertEqual(result["state"], "protected_window")
        self.assertEqual(client.calls, [])
        self.assertIsNone(self.bridge.cursor())

    def test_429_has_only_two_attempts_and_respects_delay(self):
        calls, waits = [], []
        def opener(request, timeout):
            calls.append(request)
            if len(calls)==1:
                raise urllib.error.HTTPError(request.full_url,429,"limited",{},io.BytesIO(b'{"retry_after":0.25}'))
            return Response([])
        client = bridge_module.RESTClient("synthetic-offline",opener=opener,sleeper=waits.append,clock=lambda:NOW)
        self.assertEqual(client.get_messages(CONFIG["channel_id"],after="123",limit=1), [])
        self.assertEqual(waits, [0.25]); self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0].headers["User-agent"], bridge_module.USER_AGENT)

    def test_429_exhaustion_and_401_403_stop_without_loop(self):
        for code in (401,403,429):
            calls=[]
            def opener(request, timeout):
                calls.append(request)
                raise urllib.error.HTTPError(request.full_url,code,"stop",{},io.BytesIO(b'{"retry_after":0}'))
            client=bridge_module.RESTClient("synthetic-offline",opener=opener,sleeper=lambda n:None,clock=lambda:NOW)
            with self.assertRaises(bridge_module.BridgeStop):
                client.get_channel(CONFIG["channel_id"])
            self.assertEqual(len(calls), 2 if code==429 else 1)

    def test_rest_protected_window_rejects_before_opener(self):
        calls=[]
        client=bridge_module.RESTClient("synthetic-offline",opener=lambda *a,**k:calls.append(a),clock=lambda:datetime(2026,11,2,12,0,tzinfo=UTC))
        with self.assertRaises(bridge_module.ProtectedWindow):
            client.get_channel(CONFIG["channel_id"])
        self.assertEqual(calls, [])

    def test_list_requests_validation(self):
        self.assertEqual(bridge_module.list_requests(self.db), [])
        with self.assertRaises(ValueError):
            bridge_module.list_requests(self.db, 0)

    def test_cursor_never_moves_backwards(self):
        self.bridge._cursor("1566593781430616249")
        self.bridge._cursor("1566593781430616248")
        self.assertEqual(self.bridge.cursor(), "1566593781430616249")

    def test_cli_without_run_has_no_files_or_environment_read(self):
        missing = Path(self.tmp.name)/"not-read.json"
        not_created = Path(self.tmp.name)/"not-created.db"
        original_get=bridge_module.os.environ.get
        def no_credential_read(name,*args):
            if name=="LCA_DISCORD_BOT_TOKEN": raise AssertionError("credential must not be read")
            return original_get(name,*args)
        with redirect_stdout(io.StringIO()), mock.patch.object(bridge_module.os.environ,"get",side_effect=no_credential_read):
            code=bridge_module.main(["--config",str(missing),"--db",str(not_created)])
        self.assertEqual(code,0)
        self.assertFalse(not_created.exists())

    def test_cli_once_with_fake_transport_only(self):
        path=Path(self.tmp.name)/"config.json"
        path.write_text(json.dumps(dict(CONFIG,enabled=True,ids_confirmed=True,credential_rotation_confirmed=True)),encoding="utf-8")
        client=FakeClient()
        with redirect_stdout(io.StringIO()), mock.patch.object(bridge_module,"RESTClient",return_value=client), mock.patch.dict(bridge_module.os.environ,{"LCA_DISCORD_BOT_TOKEN":"synthetic-offline-only"}), mock.patch.object(bridge_module,"protected_window",return_value=False):
            code=bridge_module.main(["--config",str(path),"--db",str(self.db),"--run","--once"])
        self.assertEqual(code,0)
        self.assertIsNotNone(self.bridge.cursor())

    def test_post_5xx_is_uncertain_and_not_retried(self):
        calls=[]
        def opener(request,timeout):
            calls.append(request)
            raise urllib.error.HTTPError(request.full_url,500,"unknown",{},io.BytesIO(b'{}'))
        client=bridge_module.RESTClient("synthetic-offline",opener=opener,clock=lambda:NOW)
        with self.assertRaises(bridge_module.TransportFailure):
            client.post_message(CONFIG["channel_id"],{"content":"test"})
        self.assertEqual(len(calls),1)


if __name__ == "__main__":
    unittest.main()
