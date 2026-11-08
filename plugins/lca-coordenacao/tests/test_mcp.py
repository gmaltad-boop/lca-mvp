import io
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import mcp_server as mcp


class MCPTests(unittest.TestCase):
    def exchange(self, requests):
        output = io.StringIO()
        mcp.serve(io.StringIO("\n".join(json.dumps(r) for r in requests) + "\n"), output)
        return [json.loads(line) for line in output.getvalue().splitlines()]

    def test_real_stdio_discovery_and_harmless_call(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "offline-test", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "lca_status", "arguments": {}}}
        ]
        with tempfile.TemporaryDirectory() as temp:
            env = dict(os.environ, LCA_COORDINATION_HOME=temp)
            env.pop("OPENAI_API_KEY", None)
            env.pop("LCA_DISCORD_BOT_TOKEN", None)
            proc = subprocess.run([sys.executable, str(mcp.PACKAGE / "server/mcp_server.py")], input="\n".join(json.dumps(r) for r in requests) + "\n", text=True, encoding="utf-8", capture_output=True, timeout=10, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0]["result"]["protocolVersion"], "2025-11-25")
        self.assertEqual(len(lines[1]["result"]["tools"]), 4)
        self.assertTrue(all(t["annotations"]["readOnlyHint"] for t in lines[1]["result"]["tools"]))
        self.assertFalse(lines[2]["result"]["isError"])
        self.assertIn("verified_at", json.loads(lines[2]["result"]["content"][0]["text"]))

    def test_tools_before_init_refused(self):
        self.assertIn("error", self.exchange([{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}])[0])

    def test_arbitrary_path_or_shell_tool_refused(self):
        with self.assertRaises(ValueError):
            mcp.call_tool("shell", {"command": "echo test"})
        with self.assertRaises(ValueError):
            mcp.call_tool("lca_status", {"path": "../state/secret"})

    def test_search_limit_boolean_rejected(self):
        with self.assertRaises(ValueError):
            mcp.validate_args("lca_memory_search", {"query": "modelo", "scope": "T-002", "limit": True})

    def test_unknown_fields_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            mcp.validate_args("lca_memory_search", {"query": "modelo", "scope": "T-002", "approve": True})

    def test_packaged_node_launcher_real_stdio(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "lca_pending", "arguments": {}}}
        ]
        with tempfile.TemporaryDirectory() as temp:
            env = dict(os.environ, LCA_COORDINATION_HOME=temp, LCA_PYTHON_EXE=sys.executable)
            proc = subprocess.run(["node", str(mcp.PACKAGE / "server/launch-mcp.mjs")], input="\n".join(json.dumps(r) for r in requests) + "\n", text=True, encoding="utf-8", capture_output=True, timeout=15, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertFalse(lines[-1]["result"]["isError"])
        self.assertIn("local_requests", json.loads(lines[-1]["result"]["content"][0]["text"]))

    def test_read_tools_do_not_create_state(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp) / "missing"
            with patch.dict(os.environ, {"LCA_COORDINATION_HOME": str(home)}):
                self.assertEqual(mcp.call_tool("lca_pending", {})["local_requests"], [])
                self.assertEqual(mcp.call_tool("lca_memory_search", {"query": "", "scope": "T-002"}), [])
            self.assertFalse(home.exists())

    def test_history_requires_scope(self):
        with self.assertRaises(ValueError):
            mcp.validate_args("lca_memory_history", {"id": "b"})


if __name__ == "__main__":
    unittest.main()
