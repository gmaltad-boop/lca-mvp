# T-002 — execução local e revisão

Data: 01/11/2026, America/Fortaleza.

## Resultado

Ambiente local criado e prova técnica supervisionada concluída. OpenHands Agent Canvas 1.34.0 / SDK 1.58.1 executou a missão com openai/gpt-5.1, produziu arquivos e terminou com status finished.

Conversa final: dfd8aa0e-7083-4a0b-b188-a6503b093a47.
Painel: http://localhost:8000/canvas/conversations/dfd8aa0e-7083-4a0b-b188-a6503b093a47?backend=default-local .

A saída final contém seis análises distintas, baseadas em oito blocos selecionados da mesma transcrição. O verificador do coordenador aprovou as referências literais, os minutos, o modelo informado, os campos obrigatórios e a divergência. Revisão semântica adicional aprovou a fidelidade e as hipóteses administrativas/comerciais, com limites.

Isso não demonstra autonomia ampla, cobertura integral da fonte, generalização para outros materiais, validação clínica ou resultado comercial. A tentativa final recebeu contexto, recorte e feedback corretivo. Não é teste independente.

## Entregas

- T-002-openhands-extracao.json — saída bruta final do executor, preservada.
- T-002-openhands-relatorio.md — síntese produzida pelo executor.
- T-002-openhands-validacao.json — validação do coordenador: passed=true, seis itens, zero falhas.
- ambiente-local-windows.md — acesso, pastas, limites e controles para iniciar/parar.

## Tentativas e aprendizado

| Tentativa | Resultado observado | Ajuste |
|---|---|---|
| 1 | Erro de configuração antes de consumir tokens | Remover temperature=0 e definir reasoning_effort=none |
| 2 | Arquivos produzidos, mas LCA interpretado como ferramenta para agências; autodeclaração incorreta do modelo; divergência ausente | Contexto explícito do produto e metadados reais fornecidos pelo coordenador |
| 3 | Limite de seis ações atingido, citação alterada | Verificador de literalidade disponível ao executor |
| 4 | Limite de dez ações atingido com releituras e tentativas de substituir texto | Reduzir ferramentas para terminal, agrupar leitura e gerar JSON por programa |
| 5 | Execução terminou e citações passaram; primeira versão repetia cinco análises | Feedback semântico no mesmo chat; versão final com seis temas distintos, conferida novamente |

As tentativas anteriores foram preservadas em runs, fora da pasta de entrada. A saída final não foi corrigida manualmente pelo coordenador para simular aprovação: o executor recebeu feedback e reescreveu os próprios arquivos.

Custo somado reportado pelo SDK nas quatro conversas com uso: aproximadamente US$ 0,3683. É um valor informado pela ferramenta, não conferência da fatura. O teste curto de acesso com 23 tokens é separado. Os valores são da sessão observada, sem estimativa de receita ou retorno.

## Limites e proteção do projeto

- Chave separada criada pelo fluxo seguro, após seleção da conta/projeto e aprovação explícita do destino; validade solicitada de 30 dias.
- Configuração e estado fora do OneDrive. O perfil salvo foi verificado sem a chave em texto simples. Nenhum segredo enviado ao Drael ou às entregas.
- Contêiner restrito à porta local, 1,5 GiB de memória e dois processadores; consumo observado ao final de cerca de 820 MiB.
- Entrada e contrato montados como somente leitura; somente saída gravável na missão.
- Execução sem acesso ao Notion, ao Drael, ao Drive ou às mensagens do piloto. Escrita de status feita pelos coordenadores.
- Não foi criado Dev Drive ou Linux adicional. A auditoria recomenda o Docker existente para esta máquina e esta tarefa.
- Segunda-feira às 9h preservada.

## Revisão de conteúdo

Temas finais: corresponsabilidade e expectativas; domínio do segmento e referências; estruturar do zero versus manter; contratar por capacidade de supervisão versus priorizar vendas; custos/margem conforme estágio; preço, escopo e excesso de entrega. Nenhum resultado do LCA foi observado ou medido na fonte.

Nuance editorial do item 2: a formulação sobre o que o contratante valoriza deve ser entendida como recomendação do entrevistado, não pesquisa de preferência. A saída bruta foi mantida; esta nota limita sua interpretação.

## Próxima qualificação proposta

Uma fonte nova, com o contrato atual e sem feedback corretivo durante a primeira entrega. Medir fidelidade, distinção entre fonte e hipótese, cobertura, intervenções do coordenador, tempo e custo. Decidir sobre ampliar o uso somente após observar esse resultado. Não abrir novas frentes comerciais nem alterar o piloto a partir desta POC.

Referências de implementação: https://github.com/OpenHands/OpenHands/blob/v1.34.0/README.windows.md e https://github.com/OpenHands/OpenHands/blob/v1.34.0/tests/e2e/live/utils/agent-server-conversation.ts .

