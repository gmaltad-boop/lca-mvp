"""Explicit local Discord credential setup; standard library, Windows user DPAPI.

No import reads a credential, opens a window or starts the bridge. --setup asks
the operator to paste a newly rotated bot credential into a masked local field.
The checkbox is an owner's declaration, not independent proof of revocation.
--start is foreground only and still requires the bridge's activation flags.
DPAPI protects the file for the current Windows user; it is not a defence from
code running as that user. Python cannot guarantee erasure of immutable strings
from process memory. Neither command prints or writes a plaintext credential.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


MAGIC = b"LCA-DPAPI\x00\x01"
ENTROPY = b"LCA Discord bot local credential v1"
UI_FORBIDDEN = 1  # No CRYPTPROTECT_LOCAL_MACHINE: default scope is current user.
TOKEN_ENV = "LCA_DISCORD_BOT_TOKEN"


def _windows_only():
    if sys.platform != "win32":
        raise ValueError("Esta operação exige Windows e não possui alternativa em texto aberto.")


def _token(value):
    if (not isinstance(value, str) or len(value) > 256
            or not re.fullmatch(r"[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", value)):
        raise ValueError("Formato de credencial inválido.")
    return value


def _crypt(data: bytes, decrypt=False) -> bytes:
    _windows_only()

    class Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    function = crypt32.CryptUnprotectData if decrypt else crypt32.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob),
                         ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    raw = ctypes.create_string_buffer(data, len(data))
    entropy = ctypes.create_string_buffer(ENTROPY, len(ENTROPY))
    source = Blob(len(data), ctypes.cast(raw, ctypes.POINTER(ctypes.c_ubyte)))
    extra = Blob(len(ENTROPY), ctypes.cast(entropy, ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    try:
        if not function(ctypes.byref(source), None, ctypes.byref(extra), None, None,
                        UI_FORBIDDEN, ctypes.byref(output)):
            raise ValueError("A proteção local da credencial não pôde ser concluída.")
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        ctypes.memset(raw, 0, len(data))
        if output.pbData:
            ctypes.memset(output.pbData, 0, output.cbData)
            kernel32.LocalFree(ctypes.cast(output.pbData, ctypes.c_void_p))


def metadata_path(secret_path):
    return Path(str(secret_path) + ".saved.json")


def _paths(config_path, secret_path):
    for value in (config_path, secret_path):
        if str(value).startswith(("\\\\", "//")):
            raise ValueError("Escolha arquivos locais neste PC.")
    config, secret = Path(config_path).resolve(), Path(secret_path).resolve()
    if secret.suffix.lower() != ".dpapi" or config == secret or config == metadata_path(secret):
        raise ValueError("Destinos locais inválidos.")
    return config, secret


def _read_config(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise ValueError("A configuração local não pôde ser lida.") from None
    if not isinstance(value, dict) or type(value.get("enabled", False)) is not bool:
        raise ValueError("A configuração local é inválida.")
    return value


def _atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def save_new_credential(token, config_path, secret_path, confirmed):
    """Save only after explicit owner confirmation; never enables a disabled bridge.

    Each replacement is atomic. The three files are not a single transaction;
    the receipt is written last and only exists after all save steps succeed.
    """
    _windows_only()
    if confirmed is not True:
        raise ValueError("A confirmação do proprietário é necessária.")
    token = _token(token)
    config_path, secret_path = _paths(config_path, secret_path)
    config = _read_config(config_path)
    config.setdefault("enabled", False)
    stamp = datetime.now(timezone.utc).isoformat()
    config.update(credential_rotation_confirmed=True, credential_rotated_at=stamp)
    encrypted = MAGIC + _crypt(token.encode("ascii"))
    receipt = {"saved_at": stamp, "config_path": str(config_path)}
    _atomic_write(secret_path, encrypted)
    _atomic_write(config_path, _json_bytes(config))
    _atomic_write(metadata_path(secret_path), _json_bytes(receipt))
    return receipt


def load_credential(secret_path):
    """Decrypt an explicitly selected file for its Windows user; no fallback."""
    _windows_only()
    path = Path(secret_path)
    if path.suffix.lower() != ".dpapi" or str(path).startswith(("\\\\", "//")):
        raise ValueError("Destino local inválido.")
    try:
        with path.open("rb") as handle:
            encrypted = handle.read(16385)
        if not encrypted.startswith(MAGIC) or not len(MAGIC) < len(encrypted) <= 16384:
            raise ValueError("Arquivo protegido inválido.")
        return _token(_crypt(encrypted[len(MAGIC):], decrypt=True).decode("ascii"))
    except (OSError, UnicodeError):
        raise ValueError("A credencial local não pôde ser carregada.") from None


def start_bridge(config_path, secret_path, db_path, once=False):
    """Explicit foreground launch; secret goes only in the child's environment."""
    _windows_only()
    if type(once) is not bool:
        raise ValueError("Opção de execução inválida.")
    config_path, secret_path = _paths(config_path, secret_path)
    config = _read_config(config_path)
    if not all(config.get(flag) is True for flag in
               ("enabled", "ids_confirmed", "credential_rotation_confirmed")):
        raise ValueError("As confirmações para iniciar ainda estão pendentes.")
    child_env = os.environ.copy()
    try:
        child_env[TOKEN_ENV] = load_credential(secret_path)
        command = [sys.executable, str(Path(__file__).with_name("discord_bridge.py")),
                   "--run", "--config", str(config_path), "--db", str(Path(db_path).resolve())]
        if once:
            command.append("--once")
        return subprocess.run(command, env=child_env, shell=False, check=False).returncode
    finally:
        child_env.pop(TOKEN_ENV, None)


def setup_window(config_path, secret_path):
    """Only this explicit function imports Tkinter and opens a local window."""
    _windows_only()
    config_path, secret_path = _paths(config_path, secret_path)
    _read_config(config_path)
    import tkinter as tk
    from tkinter import messagebox, ttk

    window = tk.Tk()
    window.title("LCA · Credencial local do Discord")
    window.resizable(False, False)
    frame = ttk.Frame(window, padding=18)
    frame.grid()
    ttk.Label(frame, text="Cole a NOVA credencial do bot. Ela será protegida pelo seu usuário do Windows.",
              wraplength=620).grid(row=0, column=0, columnspan=2, sticky="w")
    value, confirmation = tk.StringVar(), tk.BooleanVar(value=False)
    entry = ttk.Entry(frame, textvariable=value, show="*", width=75)
    entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=12)
    ttk.Label(frame, text="Salvar somente neste PC:\n" + str(secret_path),
              wraplength=620).grid(row=2, column=0, columnspan=2, sticky="w")
    tk.Checkbutton(frame, variable=confirmation, wraplength=620, justify="left",
                    text="Gerei uma nova credencial do bot no portal Discord e quero salvá-la somente neste PC"
                    ).grid(row=3, column=0, columnspan=2, sticky="w", pady=12)
    saved = False

    def close():
        value.set("")
        entry.delete(0, "end")
        window.destroy()

    def save():
        nonlocal saved
        try:
            save_new_credential(value.get(), config_path, secret_path, confirmation.get())
        except Exception:
            messagebox.showerror("Não foi possível salvar",
                "Confira a confirmação, a credencial e os arquivos locais. Nenhum detalhe da credencial é exibido.",
                parent=window)
            return
        saved = True
        close()

    ttk.Button(frame, text="Salvar", command=save).grid(row=4, column=0, sticky="e", padx=6)
    ttk.Button(frame, text="Cancelar", command=close).grid(row=4, column=1, sticky="w", padx=6)
    window.protocol("WM_DELETE_WINDOW", close)
    entry.focus_set()
    window.mainloop()
    return saved


class _SafeParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "Opções inválidas. Use --help; não passe credenciais na linha de comando.\n")


def main(argv=None):
    parser = _SafeParser(description="Credencial local protegida do bot LCA, somente Windows.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--setup", action="store_true")
    mode.add_argument("--start", action="store_true")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--secret-file", type=Path, required=True)
    parser.add_argument("--db", type=Path)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    if (args.start and args.db is None) or (args.setup and (args.once or args.db is not None)):
        parser.error("invalid mode options")
    try:
        if args.setup:
            return 0 if setup_window(args.config, args.secret_file) else 1
        return start_bridge(args.config, args.secret_file, args.db, once=args.once)
    except KeyboardInterrupt:
        return 130
    except Exception:
        print("A operação local não foi concluída. Verifique a configuração no PC.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
