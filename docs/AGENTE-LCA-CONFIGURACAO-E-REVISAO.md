# O agente LCA, explicado de forma simples

Estado verificado em 01/11/2026. Este documento descreve a POC de pesquisa operacional, não um agente autorizado a atender pacientes ou decidir condutas.

## O que construímos

Imagine uma pequena oficina. A caixa separada é o Docker. A bancada é a pasta da missão. A folha de instruções diz o que fazer e quando parar. OpenHands é o ajudante que usa ferramentas. GPT-5.1 é o modelo que interpreta o texto e prepara a resposta. O coordenador confere se o trabalho faz sentido antes de aceitar.

A chave da OpenAI permite usar o modelo. Ela ficou no computador, fora do OneDrive e do GitHub. O commit é uma fotografia com nome e data dos arquivos; a branch é um rascunho separado para revisão.

## Como foi o processo

1. Recuperamos a transcrição completa e conferimos seu tamanho e hash, uma impressão digital do arquivo.
2. Criamos uma chave separada com autorização do proprietário e verificamos uma resposta real da API.
3. Instalamos OpenHands no Docker existente e limitamos a área de trabalho à missão.
4. Rodamos tentativas e guardamos as falhas: configuração incompatível, contexto errado, citações imprecisas, limite de ações e análises repetidas.
5. Ajustamos o contrato e o roteiro. O agente final usou apenas terminal, leu o material de forma agrupada e verificou a própria saída.
6. Conferimos os arquivos e o conteúdo. A entrega aprovada tem seis análises distintas sobre oito trechos selecionados, após feedback. Não é prova de autonomia em qualquer fonte.

## Personalidade, habilidades e ferramentas: estado real

Personalidade é o jeito de trabalhar e as regras de comportamento. Uma skill é uma receita reutilizável, com passos e critérios de conclusão. Uma ferramenta é a mão usada para executar um passo.

| Camada | O que está configurado de fato | O que falta |
|---|---|---|
| Motor | OpenHands Agent Canvas 1.34.0 / SDK 1.58.1 | Avaliar atualizações antes de trocar a versão |
| Modelo | `openai/gpt-5.1`, esforço `none`, limite de saída de 6000 tokens por chamada | Comparar qualidade/custo em fonte nova; não presumir melhor configuração para toda tarefa |
| Ferramenta do executor | Apenas terminal na execução final | Adicionar outra ferramenta somente quando uma tarefa demonstrar necessidade |
| Identidade LCA | Contexto do produto, limites e objetivo dentro da mensagem e do contrato desta missão | Uma configuração persistente geral, versionada e testada para novas missões |
| Personalidade própria | Padrão do OpenHands, orientado pelas instruções da missão | Não configuramos um perfil persistente próprio do LCA nesta sessão |
| Skills próprias do LCA | Nenhuma skill reutilizável própria foi instalada e comprovadamente carregada | Transformar um método aprovado em skill e verificar que ela é usada sem carregar a resposta esperada |
| Aprendizado | Registro externo de tentativas, erros, feedback e correções | Testar se uma missão nova recupera o aprendizado pertinente e evita repetir o erro |
| Coordenação com Drael | Troca intermediada pelo Codex nesta sessão e registros no Notion | Não há ponte autônoma comprovada de fila, notificações ou execução contínua |
| Firecrawl, Computador e GitHub | Usados pelo coordenador | Não estão instalados como integrações do executor |
| Limites de gasto | Limites de ações e de saída por chamada; custo observado registrado | Não há teto monetário rígido por missão comprovado |
| Credenciais | Arquivo fora do repositório e perfil criptografado | Isolamento técnico entre credencial do serviço e terminal do executor ainda não demonstrado |

As regras clínicas continuam: a IA estrutura; o fisioterapeuta decide. Não diagnosticar, prescrever ou inferir além das notas. Esta POC trabalhou com conteúdo de podcast e hipóteses de operação, sem validar uso clínico.

O arquivo de referência `lca_project_copilot_skill.md` fornecido no chat não foi instalado como skill do executor. Um arquivo chamado skill não passa a funcionar só por estar anexado: é preciso instalá-lo, carregar seu conteúdo no momento certo e testar seu efeito.

## Como revisar sem rodar a API novamente

1. Abra `docs/evidence/T-002/2026-11-01/resultado-execucao.md`. Leia primeiro o que foi provado e os limites.
2. Abra `extracao.json`. Escolha um item e confira o minuto e o trecho na sua cópia local da fonte.
3. Pergunte: o resumo descreve aquele trecho? A hipótese está marcada como hipótese? A tarefa é uma proposta ou foi apresentada como decisão?
4. Compare os seis itens: cada um precisa ensinar algo diferente. O verificador formal não detectou sozinho as análises repetidas.
5. No item da primeira contratação, confira as duas posições em 39:27 versus 40:38–42:05. Elas não devem virar um consenso inventado.
6. Confira que não aparecem preço, margem, benefício clínico ou resultado comercial inventados. Os resultados do LCA continuam como não medidos.
7. Abra `validacao.json` para conferir o resultado formal e `painel.png` para ver a execução. Uma imagem ou um teste de formato não substitui a revisão do conteúdo.

Para revisar o commit, use a aba Files changed do pedido de revisão. Os arquivos do aplicativo clínico em `src/` e `public/` não fazem parte desta alteração. Não clique em executar uma missão só para revisar os arquivos: isso pode gerar consumo da API.

## Pendências por ordem

| Prioridade | Pendência | Responsável proposto | Evidência necessária para fechar |
|---|---|---|---|
| 1 | Fonte nova sem feedback corretivo na primeira entrega | Codex executa; Drael e proprietário revisam | Saída, referências, tempo, custo e intervenções registradas |
| 2 | Contrato geral de comportamento e uma primeira skill reutilizável | Drael + Codex | Arquivos versionados e teste que confirme carregamento e efeito |
| 3 | Separar credencial do serviço e acesso do terminal antes de tarefas mais amplas | Codex | Teste de acesso negado e configuração de uso do modelo sem leitura do segredo pelo executor |
| 4 | Definir limites operacionais e de consumo para novas missões | Proprietário define; Codex implementa | Regra explícita e mecanismo de parada conferido |
| 5 | Decidir como buscar fila e avisar conclusão | Drael + proprietário | Canal escolhido, autorização e uma notificação real conferida |

Nenhuma dessas pendências altera o piloto ou as mensagens de segunda-feira às 9h. A primeira recomendação é testar uma fonte nova antes de ampliar o uso.
