#!/usr/bin/env python3
"""poll-discord.py - OUVIDO do Drael: le linhas novas de Guilherme no canal LCA.
Requer no cofre: DISCORD_BOT_TOKEN e DISCORD_CHANNEL_ID (ainda nao presentes).
Uso: python3 poll-discord.py   -> imprime mensagens novas (depois do cursor) e atualiza o cursor.
Cada linha nova vira entrada no protocolo (autor=Guilherme), pronta para o proximo ciclo."""
import json, os, sys, urllib.request
cred = dict(l.strip().split("=", 1) for l in open("/workspace/drael.credentials") if "=" in l)
tok, ch = cred.get("DISCORD_BOT_TOKEN"), cred.get("DISCORD_CHANNEL_ID")
if not tok or not ch:
    print("sem DISCORD_BOT_TOKEN/DISCORD_CHANNEL_ID no cofre - ouvido ainda sem bot"); sys.exit(2)
CUR = "/workspace/.discord-cursor"
cursor = open(CUR).read().strip() if os.path.exists(CUR) else ""
url = "https://discord.com/api/v10/channels/" + ch + "/messages?limit=50" + ("&after=" + cursor if cursor else "")
req = urllib.request.Request(url, headers={"Authorization": "Bot " + tok, "User-Agent": "LCA-Drael-bot (canal privado, 1 uso)"})
try:
        with urllib.request.urlopen(req, timeout=20) as r:
            msgs = json.loads(r.read().decode())
except Exception as e:
    print("canal ainda nao legivel pelo bot (bot fora do servidor = esperado ate T-003):", e); raise SystemExit(0)
novas = [m for m in msgs if not cursor or m["id"] > cursor]
for m in novas:
    who = m["member"]["username"] if m.get("member") else m["author"]["username"]
    txt = (m.get("content") or "").strip()
    print("- [%s | %s] %s" % (m["timestamp"][:16].replace("T", " "), who, txt[:400]))
if novas:
    open(CUR, "w").write(max(m["id"] for m in novas))
    log = "/workspace/outputs/lca-mvp/docs/memory/NOITE-LOG.md"
    with open(log, "a") as f:
        f.write("- " + novas[-1]["timestamp"][:16] + " ENTRADA-DO-APP (Discord): " + (novas[-1].get("content") or "")[:300] + "\n")
print("n=" + str(len(novas)))
