# LCA — coordenação Drael, pesquisa e aprendizado

Data: 02/11/2026, America/Fortaleza. Auditoria com leitura de fontes, revisão cruzada Codex/Drael e protótipo local. Não equivale a avaliação clínica, validação comercial ou treinamento dos pesos do modelo.

## Decisão de implementação nesta rodada

Preparar um pacote local pequeno, com ferramentas de consulta, memória rastreável e entrada de pedidos pelo Discord. Preservar o OpenHands já usado e o piloto de segunda às 9h. Nenhum framework de memória, CLI Drael, nova distro ou serviço automático foi instalado nesta rodada.

O primeiro exemplo é a própria missão de engenharia T-002. O proprietário ainda não escolheu processo de prospecção, atendimento ou automação clínica; esses usos não foram inventados ou ativados.

## Pedido 1 — caminhos reais para o Drael participar

| Opção | Evidência | Decisão e teste |
|---|---|---|
| MCP local compartilhado | Drael CLI documenta cliente MCP por comando/URL e configuração por projeto | Principal: pacote de consulta preparado; falta instalar/conectar no cliente escolhido e verificar descoberta real |
| Drael como revisor via API | `/v1/chat/completions`, modelo `drael-v1`, credencial própria e elegibilidade de plano | Alternativa futura; não foi criada chave nem conferido plano. Enviar pacote mínimo, sem presumir memória do chat |
| Conversa atual no navegador | Coordenação de fato realizada nesta conversa, incluindo correções e caminhos dos scripts | Continuidade atual, com supervisão e registro. Não é hospedagem MCP comprovada |

Fontes oficiais: [CLI/MCP](https://drael.sh/docs/install), [quickstart](https://drael.sh/docs/quickstart), [chat](https://drael.sh/docs/chat), [conta](https://drael.sh/docs/account), [chaves](https://drael.sh/docs/keys).

A API `/v1` é stateless. Um cabeçalho de sessão pode registrar turnos/workspace; isso não prova carregar automaticamente todo o histórico da conversa web. API da conta e API de modelo usam contratos de autenticação distintos. Não foi localizada agenda nativa de agentes nos guias lidos; não afirmar que inexiste. O relatório detalhado de opções está em `opcoes-plugin-drael.md`.

## Discord — estado observado e correções

- Aplicação/bot Drael-LCA: `1566599445238390865`. Drael informou autenticação 200 em `/users/@me`, mas 403 na leitura de canal. Esses resultados são relatos do Drael, não chamada independente do Codex.
- Tela OAuth conferida pelo Codex: servidor selecionado **Tempestade De Ideias**, permissões ver canais/enviar mensagens/ler histórico, botão Autorizar ainda pendente. A tela mostrava uso em zero servidores naquele momento.
- Servidor/canal `759916034731278358` / `1566593781430616247` conferidos depois na interface: **Tempestade De Ideias / #lca-alertas**. O perfil da conta conectada também permitiu conferir o ID do remetente; ele foi preenchido apenas na configuração privada desativada. Isso não comprova acesso do bot.
- Drael confirmou que não há processo contínuo, daemon ou agenda ativa. Scripts rodavam quando a conversa os acionava. Nenhum heartbeat real foi comprovado.
- O convite inicial tinha anexos/embeds desnecessários. O mínimo preparado passou de 117760 para 68608, sem administrador.
- O histórico antigo contém credencial do bot e webhook. Nenhum valor foi copiado para este pacote. A renovação pelo proprietário fora do chat precede a ativação real.

Scripts legados conferidos no commit `1d0194c6695a`: `ops/poll-discord.py`, `ops/ping.py`, `ops/gitpush.py`. O poller não filtra remetente/bot/webhook, importa conteúdo para log/memória, inicia sem cursor sobre histórico e converte erros em sucesso com explicação não provada. **Não liberar esse código como entrada de comandos.** Drael aceitou os cinco defeitos e adicionou aviso LEGACY no commit `dec65a35b14f`. Esse aviso sozinho não bloqueia execução; o branch desta rodada acrescenta uma interrupção antes de ler credenciais. O novo adaptador tem comandos fixos, allowlist, deduplicação, proposta aguardando revisão e interrupção em acesso negado. Seus testes são locais; rede ainda pendente.

O publicador legado reconstrói uma árvore inteira e considera arquivo ausente como exclusão; somente `.env` exato é ignorado. Não usar para sincronizar checkout parcial ou o pacote Codex. O commit desta rodada usa branch separada, árvore base existente e arquivos explicitamente selecionados; não apaga arquivos remotos por ausência local.

## Pedido 2 — auditoria dos catálogos e fontes primárias

| Fonte pedida | Cobertura real | Utilidade e limite |
|---|---|---|
| [SkillsMP](https://skillsmp.com/pt) | Página ao vivo obtida pelo Firecrawl; links de candidatos localizados | Índice para descobrir fontes. Contagem, estrelas ou presença no índice não certificam qualidade/segurança |
| [Skills Library](https://skills-library.com/pt-br/) | Página respondeu; grade principal mostrou nenhuma skill, enquanto cartões populares tinham links | Cobertura parcial da interface; não significa catálogo vazio. Dois procedimentos conferidos no repositório original |
| [Start.me](https://start.me/p/jvwdkz/copia-de-awesome_start-me_page) | Firecrawl retornou a estrutura sem lista; navegador carregou os favoritos públicos | Lista de listas, com self-hosting, bots, IA, Docker e muitas áreas alheias ao LCA. Serve para descoberta seletiva; não é playbook validado para o projeto |
| GitHub | README, procedimentos e licenças originais de Superpowers e Mem0 conferidos; repositório LCA e scripts auditados | Inspeção de código/documentação não equivale a execução, segurança de toda dependência ou ganho medido |

**Adotar como procedimento agora:** verificação antes de declarar conclusão e investigação de falhas por hipótese/teste mínimo. O [verification-before-completion](https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md) e o [systematic-debugging](https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md) sustentam essas práticas. O repositório tem [licença MIT](https://github.com/obra/superpowers/blob/main/LICENSE). Adaptamos a ideia, sem instalar o pacote inteiro nem importar todas as suas regras.

**Mem0: candidato posterior.** [README](https://github.com/mem0ai/mem0/blob/main/README.md) e [licença Apache 2.0](https://github.com/mem0ai/mem0/blob/main/LICENSE) conferidos. Há memória persistente/recuperação, mas os benchmarks gerenciados incluem otimizações proprietárias ausentes do código aberto. A extração automática de fatos exige governança de origem/revisão. O exemplo básico usa modelo e embeddings; não presumir execução local sem chamadas pagas. Não instalado nem testado nesta rodada.

**Memória textual e reflexão:** [Reflexion, paper original](https://arxiv.org/abs/2303.11366), usa feedback linguístico e memória episódica sem atualizar os pesos. É uma referência para o ciclo proposto, não evidência de melhoria já obtida no LCA. O teste local compara comportamentos do armazenamento; não mede inteligência ou capacidade do modelo.

**Outros candidatos levantados pelo Drael:** ai-memory teve tentativa de instalação bloqueada por pré-requisito ausente; não foi repetida. Basic Memory/Letta ficaram como pistas de pesquisa, sem adoção ou benchmark local. Nenhum desses rótulos é uma decisão de arquitetura.

## Os seis processos como inspiração de projeto

A [ACBS](https://contextualscience.org/six_core_processes_act) descreve processos humanos de flexibilidade psicológica. O mapeamento para software é uma analogia nossa, sem equivalência psicológica comprovada. Valores não se reduzem a pontos e self-as-context não é simplesmente um banco de dados.

| Inspiração | Módulo proposto/implementado | Evidência de aceitação |
|---|---|---|
| Valores | Contrato versionado: fidelidade, escopo, privacidade, utilidade e limites de custo | Violação crítica reprova a tarefa mesmo que seja rápida/barata; não somar pontos para compensar erro grave |
| Desfusão | Plano como hipótese + crítica apoiada em fonte | Parecer diferencia dado, inferência e informação ausente; autocrítica não é prova independente |
| Aceitação | Classes de erro, limite de tentativas e estado de envio incerto | 401/403 interrompem; 429 segue espera limitada; timeout de escrita não gera envio cego duplicado |
| Presente | Estado datado, versão, observação e resultado de ferramenta | Retrato antigo continua identificado como documental; não vira serviço ativo por inferência |
| Eu como contexto | Experiências persistidas com fonte, escopo, revisão e retirada | Candidato não aparece como regra; atualização não apaga o erro anterior |
| Ação comprometida | Pedido autorizado → execução delimitada → artefato → revisão | Comando Discord não vira shell; pedido entra aguardando revisão e fechamento exige evidência |

Não guardamos raciocínio interno detalhado do modelo. Registramos decisão resumida, ferramenta, entrada/saída necessárias, erro, evidência e revisão. Não há função de recompensa treinando política ou atualização de pesos nesta versão. Otimização de sequência permanece hipótese até comparação em tarefas novas.

## Pendências encontradas no protocolo e no T-002

1. `check_schema.py` valida campos/data/N, não verdade. Campo de revisão preenchido e schema OK não substituem avaliação de conteúdo; `bool` também passava como inteiro no N antigo.
2. O seed reconstruído mistura contrato histórico de pelo menos oito linhas com fechamento de seis itens JSON+relatório. Preservar ambos como histórico, sem chamar o seed de padrão-ouro.
3. O vínculo de gpt-4.1-mini com 401 no protocolo/seed não é sustentado pelo fechamento: a autodeclaração errada veio de tentativa que terminou e escreveu arquivos. Modelo vem do recibo de execução, não do texto do executor. **Corrigido pelo Drael e conferido no GitHub:** commit `dec65a35b14f157f57ffb3c885de4c747441acbd`, seed v1.3 revoga o vínculo. O seed continua reconstruído/N=1 e fora do padrão-ouro.
4. Aprovação final T-002 veio após recorte e feedback, sobre a mesma fonte. Não multiplicar tentativas como N independente ou generalizar autonomia.
5. Limitar a pasta montada no OpenHands não comprova isolamento da chave dentro do contêiner compartilhado com o terminal. Resolver antes de ampliar ferramentas/tarefas.

Evidência de fechamento: [PR #1](https://github.com/gmaltad-boop/lca-mvp/pull/1), commit `c4751f864b2cb0deac725a26c153972661d44e72`, `docs/evidence/T-002/2026-11-01/resultado-execucao.md` e `extracao.json`; registro canônico <https://app.notion.com/p/40bb2f94a518813d905ccacb144abdb2>. Esses arquivos estão no repositório privado autorizado. Drael reconheceu as divergências e aplicou a correção rastreável de C3.

## Verificação do protótipo

56 testes determinísticos aprovados: Discord 25, memória 20, MCP 8 e integração 3. Usaram dados sintéticos, duas conexões SQLite em testes de concorrência e processos locais reais para inicialização/descoberta MCP. Nenhum teste chamou modelos ou a rede Discord. Um candidato documental T-002 foi registrado no estado privado com hashes reais, sem copiar fonte bruta nem promover a regra.

A revisão cruzada reproduziu uma corrida de promoção/retirada, consulta de histórico sem escopo e criação de banco por consulta declarada de leitura. Foram corrigidas com transação reservada antes da validação, escopo exigido no histórico MCP e abertura somente leitura. O iniciador passou a usar Node e o Python real, após bloqueio de PowerShell; a política do Windows foi preservada.

Esses testes verificam o software local e seus limites. Não são um ensaio de ganho do modelo, compatibilidade no cliente Drael/Codex instalado, ida/volta Discord ou prova de operação contínua. Detecção de credenciais é parcial por padrões; uma revisão escrita é fornecida pelo coordenador, não uma autenticação automática de sua autoridade.

## Teste seguinte que decide avanço

Primeiro concluir o canal Discord com identidade e credencial renovada; provar ida/volta, recusa de remetente não autorizado, deduplicação e parada. Depois conectar o MCP no cliente escolhido e recuperar uma experiência com fonte.

Para medir aprendizado do agente: comparar contrato atual com/sem recuperação de memória numa fonte nova não usada na elaboração das regras; manter material de referência fora do executor e não dar correção durante a primeira entrega. Registrar fidelidade, cobertura, distinção fato/hipótese, intervenções, tempo e custo reportado. Só decidir ampliar depois de observar o resultado. Essa comparação ainda não foi executada.
