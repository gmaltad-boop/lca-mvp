#!/usr/bin/env python3
"""Rota oficial de publicacao do LCA MVP (REST git-data). Uso: python3 gitpush.py "msg" """
import os, sys, json, hashlib, base64, urllib.request, urllib.error

P = "/workspace/outputs/lca-mvp"
O, R = "gmaltad-boop", "lca-mvp"
MSG = sys.argv[1] if len(sys.argv) > 1 else "update"

tok = None
for line in open("/workspace/drael.credentials"):
    if line.startswith("GITHUB_PAT="):
        tok = line.strip().split("=", 1)[1]
assert tok and tok.startswith("github_pat_"), "token nao encontrado no cofre"

def api(method, path, payload=None):
    req = urllib.request.Request(f"https://api.github.com{path}",
        data=json.dumps(payload).encode() if payload is not None else None, method=method,
        headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {tok}",
                 "User-Agent": "lca-bot", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode()[:160]}")

local = {}
for root, ds, files in os.walk(P):
    ds[:] = [d for d in ds if d not in ("node_modules", ".git", "data")]
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), P).replace(os.sep, "/")
        if rel == ".env":
            continue
        data = open(os.path.join(root, f), "rb").read()
        local[rel] = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
print("arquivos rastreados:", len(local))

head_sha = api("GET", f"/repos/{O}/{R}/branches/main")["commit"]["sha"]
head_tree = api("GET", f"/repos/{O}/{R}/git/commits/{head_sha}")["tree"]["sha"]
remote = {e["path"]: e["sha"] for e in api("GET", f"/repos/{O}/{R}/git/trees/{head_tree}?recursive=1")["tree"] if e["type"] == "blob"}
added  = [p for p in sorted(local) if p not in remote or remote[p] != local[p]]
deleted = [p for p in remote if p not in local]
print("mudancas: +", added, "-", deleted)
if not added and not deleted:
    print("SEM MUDANCAS - nada a publicar")
    sys.exit(0)

for p in added:
    b64 = base64.b64encode(open(os.path.join(P, p), "rb").read()).decode()
    local[p] = api("POST", f"/repos/{O}/{R}/git/blobs", {"content": b64, "encoding": "base64"})["sha"]
dirs = set()
for p in local:
    if "/" in p:
        d = p.rsplit("/", 1)[0]
        while d:
            dirs.add(d); d = d.rsplit("/", 1)[0] if "/" in d else ""
trees = {}
def make_tree(d):
    sub = d + "/" if d else ""
    entries = [{"path": p[len(sub):], "mode": "100644", "type": "blob", "sha": local[p]}
               for p in local if p.startswith(sub) and "/" not in p[len(sub):]]
    entries += [{"path": s[len(sub):], "mode": "040000", "type": "tree", "sha": trees[s]}
                for s in dirs if s.startswith(sub) and "/" not in s[len(sub):]]
    trees[d] = api("POST", f"/repos/{O}/{R}/git/trees", {"tree": entries})["sha"]
for d in sorted(dirs, key=lambda x: -x.count("/")):
    make_tree(d)
make_tree("")
cm = api("POST", f"/repos/{O}/{R}/git/commits", {
    "tree": trees[""], "parents": [head_sha],
    "author": {"name": "Drael (LCA)", "email": "drael@drael.sh"},
    "committer": {"name": "Drael (LCA)", "email": "drael@drael.sh"},
    "message": MSG})
api("PATCH", f"/repos/{O}/{R}/git/refs/heads/main", {"sha": cm["sha"]})
open(os.path.join(P, ".git", "refs", "heads", "main"), "w").write(cm["sha"] + "\n")
print("PUSH OK:", cm["sha"][:12], "| msg:", MSG)
top = api("GET", f"/repos/{O}/{R}/commits?per_page=1")[0]
print("verificado no GitHub:", top["sha"][:12], "|", top["commit"]["message"][:60])
