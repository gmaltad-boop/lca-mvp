import hashlib
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from discord_bridge import contains_secret, list_requests
from memory import Store
import mcp_server


class IntegrationTests(unittest.TestCase):
    def test_webhook_not_accepted_as_task_text(self):
        self.assertTrue(contains_secret("!lca pedir T-003 https://discord.com/api/webhooks/123456789012345678/example-test-only"))

    def test_memory_candidate_retrieved_with_provenance_and_matching_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            store = Store(Path(temp) / "memory.db")
            h = hashlib.sha256(b"synthetic source").hexdigest()
            store.add({"id": "candidate", "claim": "Modelo por metadados, com supervisão", "scope": "T-002", "source_ref": "synthetic://fixture", "source_hash": h, "artifact_hash": h, "kind": "observacao", "source_group": "one", "supervised": True, "feedback_used": True, "checks": {"format": True, "fidelity": None, "utility": None}})
            store.close()
            with patch.dict(os.environ, {"LCA_COORDINATION_HOME": temp}):
                args = {"query": "metadados", "scope": "T-002"}
                self.assertEqual(mcp_server.call_tool("lca_memory_search", args), [])
                records = mcp_server.call_tool("lca_memory_search", dict(args, include_candidates=True))
                self.assertEqual(records[0]["source_ref"], "synthetic://fixture")
                self.assertEqual(records[0]["status"], "candidato")
                self.assertEqual(mcp_server.call_tool("lca_memory_search", dict(args, scope="T-003", include_candidates=True)), [])
                with self.assertRaises(ValueError):
                    mcp_server.call_tool("lca_memory_history", {"id": "candidate", "scope": "T-003"})

    def test_empty_inbox_is_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "absent" / "discord.db"
            self.assertEqual(list_requests(target), [])
            self.assertFalse(target.parent.exists())


if __name__ == "__main__":
    unittest.main()
