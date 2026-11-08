#!/usr/bin/env python3
"""check_schema.py v2 - validacao mecanica de entradas PROTOCOLO-MEMORIA-v1 (R6). Tolerante a acentos."""
import json, re, sys, unicodedata

REQ = {"id", "autor", "data_utc", "tipo", "afirmacao", "fonte", "n", "status", "limite", "verificacao"}


def norm(s):
    s = unicodedata.normalize("NFC", str(s)).lower()
    return s.replace("ç", "c").replace("ã", "a").replace("é", "e").replace("ê", "e").replace("á", "a")


def main(p):
    d = json.load(open(p, encoding="utf-8"))
    dd = {norm(k): v for k, v in d.items()}
    errs = ["campo ausente: " + f for f in sorted(REQ) if f not in dd]
    if "data_utc" in dd and not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC$", str(dd["data_utc"])):
        errs.append("data_UTC sem minuto (R5)")
    if "n" in dd and (not isinstance(dd["n"], int) or dd["n"] < 1):
        errs.append("N deve ser int >= 1 (R2)")
    if errs:
        print("FALHA " + p)
        for x in errs:
            print(" - " + x)
        sys.exit(1)
    print("OK " + p + " | id=" + str(dd.get("id")) + " | N=" + str(dd.get("n")) + " | status=" + str(dd.get("status")))


main(sys.argv[1])
