# PROTOCOLO-MEMORIA-v1 — face de trabalho partilhada das MÃOS

Status: ATIVO | criado: 2026-11-01 21:45 UTC (Drael, sob autorização total de Guilherme até 21:50 BRT)
Versão atual: **v1.1** (2026-11-01 21:50 UTC — aplica críticas do 2º leitor Gemini; 3º leitor = Codex em 21:50 BRT)
Leitores: Drael · Codex/OpenHands · OpenAI · Gemini (como segundo leitor)
Próxima revisão: somente por decisão humana registrada no Log de Decisões.
Escopo mínimo intencional: sem vetores, sem extração por LLM, sem memória entre janelas de chat.
  (esses recursos só entram aqui passando pelo teste mínimo próprio + gate humano.)

## 0. Por que existe (falhas que ele impede, provadas em T-002)
- F1 identidade do produto/modelo ausente na saída (SubidoCast × G4; nome sozinho não prova produto).
- F2 identidade do modelo executado por autodeclaração (candidato gpt-4.1-mini do 401 vs. modelo real por metadado).
- F3 tempo de fonte sem minuto verificável.
- F4 divergência tratada como média em vez de linhas separadas.

## 1. Hierarquia (quem prevalece)
1. Tese fundadora + camada L4 (Notion) — acrescenta, não edita.
2. Contratos ativos deste repo (docs/**/*TASK*.md, docs/contratos/*) — válidos enquanto status != revogado.
3. Entradas deste protocolo (memória de trabalho).
Colisão entre camadas: registra-se divergência como pendência e segue a camada da operação em curso
(repo para execução, Notion para decisão), com limite explícito; resolução final = revisão humana no próximo gate.
Nunca sobreescrita em silêncio (correção v1.1: evita que camada superior desatualizada vença erro operacional).

## 2. Onde vive a memória
- Cérebro canônico (decisões, visão, estado): Notion LCA OS — arquivo único.
- Face de trabalho das mãos (execução, código, evidências): este repo (arquivos + git).
- SAVE POINT: commit publicado + SHA verificado via API = ponto de recuperação; o SHA também é registrado
   no log de saída local (`git rev-parse HEAD` equivale quando offline). Toda entrega termina em save point nomeado (SP-n).
- Conversa de chat: sessão descartável. Se não está no Notion ou no repo, não existe.

## 3. Schema mínimo de entrada (obrigatório)
| campo | regra |
|---|---|
| id | único, ex.: MEM-20261101-01 |
| autor | agente ou pessoa + versão/canais conhecidos |
| data_UTC | sempre com minuto |
| tipo | fato \| hipótese \| proposta \| pendência \| correção \| decisão \| métrica |
| afirmação | uma afirmação por entrada |
| fonte | URL+data de acesso, arquivo+linha, ou minuto+autor+produto |
| N | confirmações independentes (fato) ou ocorrências (incidente) |
| status | ativo \| pendente \| bloqueado \| encerrado \| revogado |
| limite | quando/deixa de valer (data, gate, condição) |
| verificação | comando/URL/asserção mecânica que confirma ou desmente |
| evidencia_identidade | hash de binário/arquivo, header de API ou SHA que sustenta R1 quando a entrada declara identidade (v1.1) |
Entrada sem schema completo: rejeitada OU aceita apenas como tipo=pendência.

## 4. Regras de ferro (válidas até revogação explícita)
R1 Identidade (produto/modelo/ambiente) nunca por autodeclaração — sempre por metadado
   (header, manifesto, hash de arquivo, SHA de commit, resposta versionada da API).
R2 N=1 nunca vira regra. Observação fica observação, com data de reabertura.
R3 Trecho original sobrevive junto de qualquer derivado (resumo, extração, tradução).
R4 Append-only: entrada não é editada após criada; só transição de status, registrada
   (de → para + autor + data_UTC).
R5 Tempo em UTC com minuto; horas locais só com fuso explicitado.
R6 Tudo que vai para base canônica (main do repo / Notion) passa por segundo leitor
   diferente do produtor OU por verificação mecânica definida (ex.: check_schema.py antes do commit).
R7 Paradas: cada teste ≤ 2 iterações; cada bloqueio sem progresso ≤ 2 tentativas;
   prazo de handoff vale mais que completude. Incompleto documentado > completo atrasado.

## 5. Checklist de handoff (os seis vínculos do T-002, verbatim do contrato)
Um handoff FALHA se qualquer vínculo abaixo vier quebrado, resumido numa média ou ausente:
V1 Divergência em DUAS linhas separadas, ambas as escolas, sem média
   (39:27 Chorane/C2G "primeiro contrato = quem você consegue supervisionar" ×
    40:38–42:05 Ricotta/Mestre "primeiro contrato = vendedor/SDR").
V2 Churn 27% [75:28] = relato não verificado (equipe de tráfego) — nunca alegação sustentada nem "tolerado".
V3 Regra 10x = relato de custo de equipe de tráfego — NÃO meta aprovada de slot do LCA.
V4 Fonte = agências de marketing digital, não saúde: toda transferência ao LCA é hipótese/analogia. SubidoCast ≠ G4.
V5 Transcrição sem rótulo de falante: atribuição inferida marcada como "atribuída por contexto".
V6 O executor NADA escreve no Notion durante a missão: saída = somente os arquivos locais do contrato.
   A sincronização repo → Notion é tarefa exclusiva de script de integração ou humano (v1.1).
Adicionais de identidade/tempo: V7 modelo executado identificado por metadado; V8 todo dado de fonte carrega minuto verificável.

## 6. Operações permitidas (conjunto mínimo)
append(entrada) · verificar(id) → passou/falhou + evidência · transicionar(id, status, motivo)
· vincular(A,B) · checkpoint(mensagem) → save point (commit + SHA verificado)
Qualquer outra operação = nova proposta, vai por contrato, não por improviso.

## 7. Registro desta versão
v1 2026-11-01 — congelada em SP-1.
v1.1 2026-11-01 21:50 UTC — aplicadas 4 mudanças mínimas da crítica Gemini (GEMINI-critica-PROTO-v1.txt):
   (a) campo evidencia_identidade no schema; (b) colisão por operação-em-curso + gate humano;
   (c) R6 define verificação mecânica = check_schema.py; (d) V6 explicita repo→Notion via script/humano.
   Crítica Gemini registrada com autor+data; pendências que ela apontou e ficaram ABERTAS: viés compartilhado
   entre leitores da mesma família (mitigação: Codex 3º leitor + seed fixo) e latência/permissão do token
   (aceito como risco operacional conhecido nesta janela).
