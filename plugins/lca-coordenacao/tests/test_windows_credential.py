"""Only synthetic credentials in temporary files; no GUI or real network calls."""
import contextlib
from datetime import datetime, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


MODULE = Path(__file__).resolve().parents[1] / "server" / "windows_credential.py"
SPEC = importlib.util.spec_from_file_location("windows_credential", MODULE)
credential = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(credential)
SYNTHETIC = "U1lOVEhFVElDX09OTFlfTk9UX1JFQUw.TEST00." + "SYNTHETIC_ONLY_" * 3


class CredentialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root / "config.json"
        self.secret = self.root / "local" / "bot.dpapi"
        self.write_config(enabled=False, ids_confirmed=False, credential_rotation_confirmed=False,
                          guild_id="123456789012345678", channel_id="223456789012345678",
                          authorized_user_ids=["323456789012345678"])

    def tearDown(self):
        self.temp.cleanup()

    def write_config(self, **config):
        self.config.write_text(json.dumps(config), encoding="utf-8")

    def read_config(self):
        return json.loads(self.config.read_text(encoding="utf-8"))

    @unittest.skipUnless(sys.platform == "win32", "DPAPI round-trip requires Windows")
    def test_synthetic_roundtrip_encrypted_file_receipt_and_no_plaintext_or_output(self):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            receipt = credential.save_new_credential(SYNTHETIC, self.config, self.secret, confirmed=True)
            restored = credential.load_credential(self.secret)
        self.assertEqual(restored, SYNTHETIC)
        self.assertTrue(self.secret.read_bytes().startswith(credential.MAGIC))
        self.assertEqual(output.getvalue() + errors.getvalue(), "")
        self.assertFalse(list(self.root.rglob("*.tmp")))
        for path in self.root.rglob("*"):
            if path.is_file():
                self.assertNotIn(SYNTHETIC.encode(), path.read_bytes(), str(path))
        self.assertEqual(set(receipt), {"saved_at", "config_path"})
        self.assertEqual(json.loads(credential.metadata_path(self.secret).read_text()), receipt)
        config = self.read_config()
        self.assertIs(config["enabled"], False)
        self.assertIs(config["ids_confirmed"], False)
        self.assertIs(config["credential_rotation_confirmed"], True)
        self.assertEqual(config["credential_rotated_at"], receipt["saved_at"])
        self.assertEqual(datetime.fromisoformat(receipt["saved_at"]).utcoffset(), timezone.utc.utcoffset(None))

    @unittest.skipUnless(sys.platform == "win32", "DPAPI requires Windows")
    def test_setup_preserves_existing_enabled_and_other_fields(self):
        for enabled in (False, True):
            with self.subTest(enabled=enabled):
                self.write_config(enabled=enabled, ids_confirmed=False, extra="synthetic-preserved")
                credential.save_new_credential(SYNTHETIC, self.config, self.secret, True)
                config = self.read_config()
                self.assertIs(config["enabled"], enabled)
                self.assertIs(config["ids_confirmed"], False)
                self.assertEqual(config["extra"], "synthetic-preserved")
        self.write_config(extra="default-disabled")
        credential.save_new_credential(SYNTHETIC, self.config, self.secret, True)
        self.assertIs(self.read_config()["enabled"], False)

    def test_invalid_token_or_unchecked_confirmation_never_writes(self):
        before = self.config.read_bytes()
        for token, confirmed in ((SYNTHETIC, False), (SYNTHETIC, 1), ("", True),
                                 ("Bot " + SYNTHETIC, True), (SYNTHETIC + "\n", True),
                                 ("mfa." + "A" * 60, True), ("A" * 300, True)):
            with self.subTest(confirmed=confirmed):
                with mock.patch.object(credential, "_windows_only"), mock.patch.object(credential, "_crypt") as crypt:
                    with self.assertRaises(ValueError):
                        credential.save_new_credential(token, self.config, self.secret, confirmed)
                    crypt.assert_not_called()
                self.assertEqual(self.config.read_bytes(), before)
                self.assertFalse(self.secret.parent.exists())

    def test_non_windows_has_no_plaintext_fallback(self):
        with mock.patch.object(credential.sys, "platform", "linux"):
            for action in (lambda: credential.save_new_credential(SYNTHETIC, self.config, self.secret, True),
                           lambda: credential.load_credential(self.secret),
                           lambda: credential.start_bridge(self.config, self.secret, self.root / "db")):
                with self.assertRaisesRegex(ValueError, "Windows"):
                    action()
        self.assertFalse(self.secret.exists())

    def test_defaults_and_non_boolean_flags_never_decrypt_or_start(self):
        configurations = [{}, {"enabled": False},
                          {"enabled": True, "ids_confirmed": True, "credential_rotation_confirmed": False},
                          {"enabled": 1, "ids_confirmed": True, "credential_rotation_confirmed": True},
                          {"enabled": True, "ids_confirmed": 1, "credential_rotation_confirmed": True}]
        for config in configurations:
            self.write_config(**config)
            with self.subTest(config=config), mock.patch.object(credential, "_windows_only"), \
                    mock.patch.object(credential, "load_credential") as load, \
                    mock.patch.object(credential.subprocess, "run") as run:
                with self.assertRaises(ValueError):
                    credential.start_bridge(self.config, self.secret, self.root / "db", once=True)
                load.assert_not_called()
                run.assert_not_called()

    def test_explicit_start_passes_token_only_in_child_environment_and_once(self):
        self.write_config(enabled=True, ids_confirmed=True, credential_rotation_confirmed=True)
        captured = {}

        def fake_run(command, **kwargs):
            captured.update(command=list(command), env=dict(kwargs["env"]),
                            shell=kwargs["shell"], check=kwargs["check"])
            return subprocess.CompletedProcess(command, 0)

        with mock.patch.dict(os.environ, {credential.TOKEN_ENV: "SYNTHETIC_PARENT_ONLY"}, clear=True), \
                mock.patch.object(credential, "_windows_only"), \
                mock.patch.object(credential, "load_credential", return_value=SYNTHETIC), \
                mock.patch.object(credential.subprocess, "run", side_effect=fake_run):
            result = credential.start_bridge(self.config, self.secret, self.root / "db", once=True)
            self.assertEqual(os.environ[credential.TOKEN_ENV], "SYNTHETIC_PARENT_ONLY")
        self.assertEqual(result, 0)
        self.assertEqual(captured["env"][credential.TOKEN_ENV], SYNTHETIC)
        self.assertEqual(captured["command"][0], sys.executable)
        self.assertTrue(captured["command"][1].endswith("discord_bridge.py"))
        self.assertIn("--run", captured["command"])
        self.assertIn("--once", captured["command"])
        self.assertNotIn(SYNTHETIC, " ".join(captured["command"]))
        self.assertIs(captured["shell"], False)
        self.assertIs(captured["check"], False)

    @unittest.skipUnless(sys.platform == "win32", "DPAPI requires Windows")
    def test_corrupted_encrypted_file_is_rejected_without_revealing_plaintext(self):
        credential.save_new_credential(SYNTHETIC, self.config, self.secret, True)
        self.secret.write_bytes(credential.MAGIC + b"synthetic-invalid-ciphertext")
        with self.assertRaises(ValueError) as error:
            credential.load_credential(self.secret)
        self.assertNotIn(SYNTHETIC, str(error.exception))

    def test_no_setup_window_opens_on_import_and_cli_requires_explicit_mode(self):
        with mock.patch.object(credential, "setup_window") as setup, \
                mock.patch.object(credential, "start_bridge") as start, \
                contextlib.redirect_stderr(io.StringIO()) as errors:
            with self.assertRaises(SystemExit):
                credential.main(["--config", str(self.config), "--secret-file", str(self.secret), SYNTHETIC])
            setup.assert_not_called()
            start.assert_not_called()
        self.assertNotIn(SYNTHETIC, errors.getvalue())


if __name__ == "__main__":
    unittest.main()
