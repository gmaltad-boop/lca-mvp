#!/usr/bin/env python3
"""check_schema.py - validacao mecanica de entradas PROTOCOLO-MEMORIA-v1 (R6).
Uso: python3 check_schema.py <arquivo.json> -> exit 0 ok / 1 falha (com motivos)."""
import json, re, sys
REQ = ["id", "autor", "data_UTC", "tipo", "afirmacao", "fonte", "N", "status", "limite", "verificacao"]
ALIASES = {"fonte": ["fontes"], "limite": [], "verificacao": []}
def main(p):
    d = json.load(open(p))
    errs = []
    for f in REQ:
        if f not in d and f not in ALIASES.get(f, []):
            errs.append(f"campo ausente: {f}")
    if "data_UTC" in d and not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC$", d["data_UTC"]):
        errs.append("data_UTC sem minuto (R5)")
    if "N" in d and (not isinstance(d["N"], int) or d["N"] < 1):
        errs.append("N deve ser int >= 1 (R2)")
    if errs:
        print("FALHA " + p); [print(" -", e) for e in errs]; sys.exit(1)
    print(f"OK {p} | id={d.get('id')} | N={d.get('N')} | status={d.get('status')}")
if __name__ == "__main__":
    main(sys.argv[1])
