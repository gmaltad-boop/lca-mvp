#!/usr/bin/env python3
"""ping.py - noticia Guilherme no canal LCA (Discord webhook do cofre).
Uso: python3 ping.py "mensagem" [--here]  |  exit 0 ok / 1 falha"""
import sys, json, urllib.request
wh = None
for l in open("/workspace/drael.credentials"):
    if l.startswith("DISCORD_WEBHOOK="):
        wh = l.strip().split("=", 1)[1]
if not wh:
    print("sem DISCORD_WEBHOOK no cofre"); sys.exit(1)
msg = sys.argv[1]
here = "--here" in sys.argv[2:]
if here and not msg.startswith("@here"):
    msg = "@here " + msg
payload = {"content": msg[:1900], "username": "Drael"}
req = urllib.request.Request(wh, data=json.dumps(payload).encode(), method="POST",
                             headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120 LCA-Drael"})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read().decode()[:200]
        print("PING ok http=" + str(r.status) + (" " + body if body else ""))
        sys.exit(0)
except urllib.error.HTTPError as ex:
    print("PING falhou http=" + str(ex.code) + " " + ex.read().decode()[:200]); sys.exit(1)
except Exception as ex:
    print("PING falhou: " + str(ex)[:160]); sys.exit(1)
