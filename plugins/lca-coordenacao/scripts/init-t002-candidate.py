"""Register only a candidate from explicit source/artifact paths; no raw text copied."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from memory import Store

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", type=Path, required=True)
parser.add_argument("--artifact", type=Path, required=True)
parser.add_argument("--state-home", type=Path, default=Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "LCA/coordination")
args = parser.parse_args()
source_hash = hashlib.sha256(args.source.read_bytes()).hexdigest()
artifact = args.artifact.read_bytes()
artifact_hash = hashlib.sha256(artifact).hexdigest()
data = json.loads(artifact)
if not isinstance(data, dict) or len(data.get("itens", [])) != 6:
    raise SystemExit("Artefato não corresponde ao fechamento de seis itens; nenhuma memória foi criada.")
record = {
    "id": "T002-FECHAMENTO-20261101", "kind": "observacao", "scope": "T-002",
    "claim": "Registro documental T-002: saída final com seis itens após seleção de oito blocos e feedback corretivo na mesma fonte. Prova supervisionada; não é teste independente nem autonomia ampla. Modelo da execução depende de metadados do coordenador, não da declaração no JSON.",
    "source_ref": "https://github.com/gmaltad-boop/lca-mvp/blob/c4751f864b2cb0deac725a26c153972661d44e72/docs/evidence/T-002/2026-11-01/resultado-execucao.md",
    "source_hash": source_hash, "artifact_hash": artifact_hash,
    "source_group": "granola-5765e6d6-3b1e-40b4-8457-1deed552a9d1",
    "supervised": True, "feedback_used": True,
    "checks": {"format": None, "fidelity": None, "utility": None}, "reviewer": None
}
store = Store(args.state_home / "memory.db")
try:
    existing = [r for r in store.search("", "T-002", include_candidates=True) if r["id"] == record["id"]]
    if existing:
        if any(existing[0][k] != record[k] for k in ("source_hash", "artifact_hash")):
            raise SystemExit("Já há registro de outra versão. Criar correção rastreável, sem sobrescrever.")
        result = existing[0]
    else:
        result = store.add(record)
    print(json.dumps({"id": result["id"], "status": result["status"], "raw_source_copied": False, "promoted": False}, ensure_ascii=False))
finally:
    store.close()
