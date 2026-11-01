# POC MCP-SMOKE — resultado (B1, 2026-11-01 21:45 UTC)

## Veredito: PASS
A sandbox do Drael atua como **cliente MCP** (stdio) contra o servidor de referência oficial.

## Evidência (transcrição bruta em SAIDA-smoke.txt)
- Instalação: `npm i @modelcontextprotocol/sdk @modelcontextprotocol/server-everything` → 108 pacotes, 11 s.
- `initialize`: server `{"name":"mcp-servers/everything","version":"1.0.0"}` — identidade por metadado (R1 satisfeito).
- `ping` ok; `tools/list` → 13 ferramentas com schemas (echo, get-sum, get-env, ...).
- Round-trip do payload de vínculos V1–V8 intacto:
  `ECHO in : V1-divergencia-2-linhas|V2-churn27-relato|V3-10x-custo|V4-subidocast-ne-G4|V5-atribuicao-contexto|V6-executor-nao-notion|V7-modelo-metadado|V8-minuto-verificavel`
- `get-sum(2,3)` → "The sum of 2 and 3 is 5."
- `resources/list` → 7 recursos; close limpo. Total: **840 ms**.

## O que isso prova / não prova
- Prova: com node22+npm na sandbox, o Drael consome servidores MCP reais (tools/resources) hoje.
- Não prova: que o Drael é *host* MCP nativo (pergunta para drael.sh/help) nem que servidor MCP
  valha mais que REST+credencial para nossos usos atuais.
- Custo/superfície: 108 pacotes npm instalados só na sandbox; nada foi publicado; nada novo no PC do dono.

## Reprodução (comandos exatos)
```bash
cd <sandbox>/mcp-test
npm i @modelcontextprotocol/sdk @modelcontextprotocol/server-everything
node smoke.mjs     # cliente em smoke.mjs neste diretório
```

## Critério de parada aplicado
1 tentativa de instalação (ok) + 1 execução (ok) → dentro de P2 (≤2).
