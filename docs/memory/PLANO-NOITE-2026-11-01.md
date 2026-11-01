# PLANO-NOITE 2026-11-01 — autonomia Drael até o retorno do Codex

Janela: 21:45 UTC → 00:45 UTC (Codex volta 21:50 BRT = 00:50 UTC).
Autorização: Guilherme, 2026-11-01 ("autorização para total controle"), com limites já acordados mantidos:
nada no PC dele, sem instalar fora do sandbox, sem dinheiro/nome/terceiros, sem publicar,
.env/data intactos, L4 (Notion) só acrescenta, segunda 09h sagrada.
Gemini = segundo leitor / apoio à coordenação. Manus reservado (sem chave nesta janela).

## Critérios de parada (globais)
P1 Prazo de handoff vale mais que completude (R7): wrap-up obrigatório até 00:40 UTC.
P2 Cada teste ≤ 2 iterações; cada bloqueio ≤ 2 tentativas → vira pendência documentada e segue o resto.
P3 Falha de rede/instalador repetida → marca-se BLOCKED com causa e não consome bloco seguinte.
P4 Todo bloco termina em SAVE POINT (commit + SHA verificado) — se algo quebrar, recupera pelo último SP.
P5 Sem surpresa: nada sai do repo+Notion+fila; qualquer exceção exigiria voltar a chamar o dono.

## Blocos (horários reais de execução)
| bloco | janela UTC | objetivo | intervenção | ferramenta | Fato (baseado em) / Hipótese (devido a) | critério de parada | save point |
|---|---|---|---|---|---|---|---|
| B0 | 21:45–21:50 | congelar protocolo + seed | escrever PROTOCOLO-MEMORIA-v1 + seeds/t002-seed.json + este plano | run_code + gitpush | Fato: contrato T-002 verbatim no repo (git API 200). Hipótese: seed reconstruído é âncora estável p/ A e B, devido a conter vínculos idênticos nos dois testes | erro de escrita/push | SP-1 |
| B1 | 21:50–22:15 | Drael fala MCP? | smoke client↔server MCP oficial (stdio) na sandbox | node22+npm (@modelcontextprotocol/sdk + server-everything) | Fato: spec v2026-07-28 exige cliente/host; node22+npm presentes (listado). Hipótese: SDK TS conecta em <5 min, devido a pacotes oficiais no registry | 2 tentativas de install/conexão | SP-2 |
| B2 | 22:15–22:25 | 2º leitor do protocolo | Gemini critica v1 com as 3 perguntas + "impede F1–F4?" | Gemini API (200 ping ok) | Fato: chave Gemini válida (ping). Hipótese: crítica de 2º leitor pega 1+ gap real, devido a viés de autorrecompensa já provado no T-002 | 1 chamada; sem resposta útil → segue e registra | SP-2b (só se houver mudança) |
| B3 | 22:25–23:10 | handoff preserva vínculos? | POC ai-memory semeado com SEED-T002; assert programática V1–V8 | pip/npx + seed | Fato: MIT, README publicado. Hipótese: handoff textual preserva vínculos, devido a serem strings exatas — o teste existe exatamente p/ checar isso | 2 iterações (1º com template puro, 2º com contrato anexado) | SP-3 |
| B4 | 23:10–23:30 | fechar lacunas de pesquisa | retry skillsmp.com/pt; 1ª tentativa start.me; amostra de licenças de skills | web_fetch/web_search | Fato: 408 anterior; start.me sem texto (JS). Hipótese: retry resolve o 408 (transiente), devido a gateway timeout | 1 retry por fonte; senão → pendência Manus com tarefa pronta | SP-4 |
| B5 | 23:30–23:50 | kit TESTE-B p/ Codex | documento-execução do mem0 (comandos, asserções, custo) | escrita | Fato: Apache-2.0, ativo (push 2026-10-30). Hipótese: mem0 responde "qual modelo executou?" por metadado, devido a guardar contexto estruturado — incerteza: extração por LLM reescreve fatos (injeção) | — | SP-5 |
| B6 | 23:50–00:20 | handoff Notion | página 📡 HANDOFF-01NOITE + filas p/ GPT e p/ Guilherme + roadmap + 1 linha decisão (append) | Notion API | Fato: API 200 repetidas vezes hoje; IDs em notion.ids.json. Hipótese: POST /v1/pages direto (lição aprendida: databases/{id}/pages dava 400) | 2 tentativas por escrita | (registro no SP-6) |
| B7 | 00:20–00:40 | relatório + treino v2 | RELATORIO-NOITE com lacunas preenchidas/faltantes + TREINO-V2 | escrita + git | — | wrap-up até 00:40 | SP-6 |

## Loop de reavaliação (qualidade → lacunas → novo treino)
Após cada teste: registrar (1) o que PASSOU, (2) qual gap específico falhou, (3) o ajuste mínimo,
(4) RE-RUN uma única vez com o ajuste (treino v2 mirado) → resultado entra no relatório.
Replicação: vínculos que passaram no 1º run precisam passar no 2º também (senão viram instáveis, N sobe).
Isso é o "novo treino com propósito": não treinar por treinar, mas fechar a lacuna medida e confirmar a vitória.

## O que o Codex recebe às 21:50 BRT (resumo para a fila)
1. Ler SP-1..SPn deste plano e o HANDOFF no Notion.
2. Rodar TESTE-B (mem0) com o mesmo SEED-T002 → comparar contra SP-3 (ai-memory).
3. Conferir seed reconstruído × JSON original do fechamento (corrige N=1).
4. Decidir face de memória padrão (critério: quem passou checklist V1–V8 + menor superfície de injeção).
5. Revisar PROTOCOLO-MEMORIA-v1 (2º leitor dele, Gemini já foi o 1º).
