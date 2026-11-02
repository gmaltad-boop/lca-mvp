# Drael na coordenação LCA — possibilidades verificadas

Verificação pública iniciada em 01/11/2026; fechamento em 02/11/2026 (America/Fortaleza). Pesquisa somente leitura. Não foram instalados programas, criadas credenciais, chamados endpoints autenticados, consultados tokens do navegador ou alteradas contas.

## Conclusão

Há três caminhos plausíveis, com níveis diferentes de prova. O mais alinhado ao ambiente local é um pequeno servidor MCP de coordenação/memória, utilizável pelo Drael CLI e por outros clientes. A documentação oficial do Drael afirma que seu CLI é cliente MCP. Isso não comprova que a conversa web atualmente aberta aceite plugins arbitrários nem que uma integração já esteja funcionando.

## Fatos documentados e revalidados

| Superfície | O que a documentação sustenta | Limite da evidência |
|---|---|---|
| API de modelo | Base `https://drael.sh/v1`, modelo público `drael-v1`, `POST /v1/chat/completions` e `GET /v1/models`; autenticação própria `dk-...` | Sem chamada autenticada nesta auditoria; elegibilidade/plano da conta não verificados |
| Credencial | API key com escopos `chat` e `images`; a chave só é mostrada uma vez. A credencial do terminal `dt-...` é diferente, criada por aprovação da máquina | Nunca reutilizar a chave OpenAI no domínio Drael; nenhuma chave deve trafegar por mensagens de chat |
| API versus conta | A API OpenAI-compatible é stateless. `X-Drael-Session` vincula workspace e pode gravar o turno numa conversa da própria conta | O cabeçalho não concede posse/acesso a conversa alheia. Gravar no chat não equivale a carregar automaticamente todo o histórico ou a memória do coordenador |
| Histórico da conta | Documentação separada lista `GET /api/sessions`, `GET /api/sessions/{id}`, instruções, sync e export, autenticados por sessão | Não foi confirmado que uma chave `dk-` permita ler essas rotas; não extrair sessão do navegador para contornar essa diferença |
| CLI | `@drael/code` documenta `--resume`, `--continue`, modo `plan`, saída JSON/stream e limite de turnos | Não instalado nem testado nesta máquina nesta auditoria |
| MCP | CLI documenta `drael mcp`, `mcp add` por comando ou URL e arquivos `.mcp.json` por projeto/usuário; ele inicia clientes/servidores configurados e descobre suas ferramentas | Evidência de cliente MCP no CLI, não de endpoint MCP hospedado pelo site nem de catálogo de plugins arbitrários na conversa web |
| Skills/agentes locais | CLI documenta skills, comandos, arquivos AGENTS/CLAUDE e agentes locais com ferramentas e modo próprios | Precisa testar descoberta/carregamento e restrição efetiva no projeto; documentação não prova instalação atual |
| Agenda nativa | Não localizei mecanismo de agenda de tarefas documentado nos guias públicos consultados | Isso não prova inexistência. A menção de scheduled change em billing é de plano, não de agendamento de agentes |

Fontes primárias: [quickstart](https://drael.sh/docs/quickstart), [chat](https://drael.sh/docs/chat), [autenticação](https://drael.sh/docs/keys), [API da conta](https://drael.sh/docs/account), [instalação e CLI](https://drael.sh/docs/install), [ferramentas](https://drael.sh/docs/tools).

## Três opções, com um teste pequeno para cada uma

### 1. Servidor MCP local de coordenação e memória — recomendação principal

**Desenho proposto:** uma interface pequena sobre o registro LCA, com funções como listar missão, obter resumo, recuperar experiências pertinentes e ler evidências. O mesmo servidor poderia ser ligado ao Drael CLI e ao cliente coordenador. A memória não fica presa a uma conversa ou a um provedor.

**Primeira versão:** somente leitura para o Drael: um pacote de tarefa aprovado, uma lista de experiências validadas e referências para resultados. O Drael produz parecer em saída estruturada; o coordenador valida e registra. Uma gravação direta de revisão, se vier depois, terá permissão e esquema próprios. Sem shell geral, compra, publicação, acesso irrestrito a pastas ou seleção automática de conduta clínica.

**O que é documentado:** suporte de cliente MCP por comando ou URL no CLI; suporte de plugin local/MCP no fluxo do Codex. **O que é projeto nosso:** ferramentas do servidor, contratos, autenticação do serviço, escopo da pasta e política de escrita.

**Teste:** uma missão T-002 sanitizada; Drael recupera uma experiência anterior por uma ferramenta de leitura e devolve crítica rastreável; confirmar que uma tentativa fora do escopo é recusada. Não usar segredo nem dados de paciente como material de teste. Isso não depende de um banco vetorial no primeiro passo.

**Pendências:** escolher cliente alvo, instalar por fonte oficial, autorizar máquina/credencial pelo proprietário e testar ferramentas. Não há plugin instalado nesta pesquisa. Um plugin local não vira automaticamente ferramenta web/mobile.

### 2. Drael como revisor via API, atrás de um adaptador controlado

**Desenho proposto:** o coordenador envia um pacote mínimo de tarefa, fonte e saída a `drael-v1`; recebe parecer com evidência e objeções. A memória e a fila continuam no registro canônico; o modelo não recebe autorização para executar ações.

**Vantagem:** contrato claro e execução sem dirigir a página. **Limite:** chamar o modelo por API não recupera por si só a personalidade, anexos, memória ou conversa da conta usada hoje.

**Teste:** pacote público/sintético, chave própria Drael limitada a chat, parecer estruturado e verificação de citações. Antes do teste, confirmar a elegibilidade de API e o consumo permitido. Nenhuma chave foi procurada ou usada nesta auditoria.

**Cuidados específicos documentados:** a API pode servir as próprias ferramentas quando não recebe catálogo do cliente; o modo exato para impedir ferramentas precisa ser conferido num teste pequeno. `max_tokens` é descartado nos turnos com chave, segundo o provedor; não considerá-lo teto de gasto. Timeout de conexão não comprova que o processamento parou: preferir stream, identificador estável, estado consultável e prevenção de duplicação, sem repetição automática cega.

### 3. Manter a ponte atual com a conversa web, formalizando os pacotes

**Desenho proposto:** Codex prepara resumo/experiências/evidências; interage com a conversa Drael já autorizada; recebe parecer e registra. É a continuidade mais próxima da sessão atual e permite aprender o contrato antes de instalar outro componente.

**Vantagem:** usa a conversa existente. **Limites:** depende de navegador, login, disponibilidade da página e supervisão; não é uma integração autônoma comprovada. Não extrair cookie/token nem automatizar criação de acesso por este caminho.

**Teste:** um pacote de revisão com identificação de missão e hash, uma resposta do Drael e uma gravação do parecer pelo coordenador. Medir tempo, omissões e necessidade de intervenção. Não apresentar isso como hospedagem MCP ou plugin nativo do site.

## Padrões de projeto a preservar

1. Drael, OpenAI e GitHub têm credenciais distintas; uma chave de um provedor não vai ao outro.
2. O histórico relevante deve ser selecionado por missão, com origem e validade; não enviar arquivos, logs ou memórias privados em massa.
3. O revisor não promove sozinho a própria lição a regra global nem transforma opinião em decisão do proprietário.
4. A fila precisa distinguir proposto, executando, aguardando revisão e concluído, com evidência e dono.
5. O erro do provedor deve preservar a classe: não encontrado, acesso negado, limite/plano, falha temporária e execução desconhecida não são a mesma coisa.
6. A ausência de agenda documentada não autoriza prometer que o Drael observa o Notion por iniciativa própria. Um agendador externo só entra após definir objetivo e autorização.

## Lacunas e divergências documentais

- A página de quickstart descreve leitura nativa de imagens; a página de chat ainda descreve leitura externa cobrada por imagem. Não resolvi essa contradição. Não basear a primeira integração em imagens.
- A página de instalação diz que a conversa fica na máquina, mas também descreve retomada a partir da conta e o uso de `X-Drael-Session`. Confirmar persistência/sincronização em teste antes de prometer onde tudo fica guardado.
- `/developers` público redirecionou para login. Não entrei no console privado, não vi plano/chaves e não concluo que a conta atual tenha API ativa.
- Metadados públicos do npm, obtidos sem instalação: `@drael/code` versão 0.8.1, licença declarada MIT, Node >=20. O guia de instalação recomenda Node >=22.19; manter a condição mais restritiva até testar. A licença é metadado do pacote, não auditoria de todo seu código.
- Nada nesta pesquisa confirma segurança por propaganda de ausência de filtros. A governança precisa existir no adaptador e nas permissões reais.

## Fontes e cobertura

Foram lidas as seis páginas oficiais acima e o mapa público de URLs do domínio. Registro npm consultado por `npm view @drael/code version engines license repository dist.integrity --json`, sem instalar ou executar o pacote. Guias de plugin local consultados no plugin-creator disponível ao coordenador. Não houve auditoria de código-fonte do CLI, teste de autenticação, chamada de modelo, instalação de servidor ou avaliação de desempenho.

