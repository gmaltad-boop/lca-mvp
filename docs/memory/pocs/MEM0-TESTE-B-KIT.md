# KIT TESTE-B — mem0 × SEED-T002 (executor: Codex, container/ambiente isolado)

Contrato da casa: mesma semente do Teste A (`seeds/t002-seed.json`), checklist V1–V8 do `PROTOCOLO-MEMORIA-v1`,
parada em 2 iterações, bloqueio vira BLOCKED com causa. Sem chave nova: OPENAI_API_KEY existente foi validada em
2026-11-01 21:44 UTC (GET /v1/models → 200).

## Execução (comandos mínimos, ajustar caminho do repo)
```bash
pip install mem0ai
python3 - <<'PY'
import json
from mem0 import Memory
m = Memory()  # store local padrão; LLM = OpenAI gpt-5.1
seed = json.load(open("<REPO>/docs/memory/seeds/t002-seed.json"))
itens = []
for v in seed["vinculos"]: itens.append(v["id"] + ": " + v["regra"] + ((" | " + v["detalhe"]) if v.get("detalhe") else ""))
for v in seed["identidade_e_tempo"]: itens.append(v["id"] + ": " + v["regra"])
itens.append("CUSTO: US$ 0,3683 em 5 conversas - autodeclarado pelo agente, NAO fatura.")
itens.append("MISSAO T-002 encerrada; executor declarado OpenHands 1.34.0; saida missao-2-extracao.md.")
for i, t in enumerate(itens):
    print(i, m.add(t, user_id="t002-seed"))
print("===R1==="); print(m.search("qual foi o modelo EXECUTADO nas execucoes da misao?", user_id="t002-seed"))
print("===R2==="); print(m.search("churn 27 percentual", user_id="t002-seed"))
print("===R3==="); print(m.search("SubidoCast e G4 sao o mesmo produto?", user_id="t002-seed"))
PY
```

## Aprovação (todas obrigatórias)
- A1 resposta de modelo identifica gpt-5.1 por metadado/fonte (não autodeclaração genérica) [V7];
- A2 churn volta rotulado como relato não verificado — nunca como meta ou "tolerado" [V2];
- A3 SubidoCast e G4 permanecem produtos distintos [V4];
- A4 custo US$ 0,3683 vem marcado como autodeclarado [R1];
- A5 registrar contagem de chamadas LLM extras observadas (relato de custo → hipótese de COGS).

## Injeção
Se a extração do mem0 reescrever fato, anexar o trecho original ao resultado (R3) e marcar
"extração reescreveu: sim/não". Divergência entre o que foi gravado e o que voltou = FAIL parcial documentado.

## Saída obrigatória
`docs/memory/pocs/mem0-RESULTADO.md` com transcrição bruta + tabela A1–A5 + veredito. Depois: push nomeado
(SP contínuo da noite, ver NOITE-LOG) e linha de comparação contra o resultado do Teste A.
