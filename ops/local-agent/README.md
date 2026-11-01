# Executor local LCA — registro experimental da POC T-002

Este diretório guarda os controles e o contrato usados na prova supervisionada de 01/11/2026. Ele não é um instalador completo nem uma plataforma de agentes pronta para qualquer tarefa.

Leia primeiro [o guia simples de configuração e revisão](../../docs/AGENTE-LCA-CONFIGURACAO-E-REVISAO.md) e [o resultado observado](../../docs/evidence/T-002/2026-11-01/resultado-execucao.md).

## O que foi testado

- OpenHands Agent Canvas 1.34.0, SDK 1.58.1 e `openai/gpt-5.1`.
- Um contêiner local, porta 127.0.0.1:8000, limite de 1,5 GiB e dois processadores.
- Transcrição de um episódio sobre agências. A entrega final usa oito blocos selecionados, depois de feedback.
- Seis análises distintas com origem literal, limites, hipótese para o LCA e tarefa proposta.

Os scripts continuam específicos dessa missão: nomes de pastas, contêiner, perfil, minutos e formato de saída estão fixos. Não executar `start`, `run` ou `feedback` para apenas revisar o commit: essas ações podem consumir API. O modo `probe` verifica o serviço; os validadores conferem arquivos existentes sem chamar o modelo.

## Organização e dependências

`agent/` contém os controles. `workspaces/t002-missao1/` contém contrato e validador. A transcrição completa e o recorte não estão no GitHub; o manifesto em `input/source-manifest.json` registra origem e hash. Sem esses arquivos locais, não se reproduz a execução. As saídas finais revisadas estão em `docs/evidence/T-002/2026-11-01/`.

O ambiente efetivamente instalado vive em `%LOCALAPPDATA%/LCA/`, com a mesma disposição de `agent`, `state` e `workspaces`. Copiar estes arquivos para outro local não copia a chave, o estado do servidor, os perfis ou a fonte. A criação de novas credenciais exige o fluxo seguro e a escolha do proprietário.

## Limite de isolamento

A montagem protege a fonte contra escrita e evita montar outros projetos e pastas de credenciais do Windows como área de trabalho. Isso **não demonstra isolamento da credencial dentro do contêiner**: o servidor e o terminal do executor compartilham esse ambiente, e o script de início usa `--env-file`. O perfil é salvo criptografado, mas o serviço tem meios de usá-lo. A ordem para não ler segredos é uma regra comportamental, não uma barreira técnica comprovada. Não ampliar para tarefas não confiáveis ou dados clínicos reais sem tratar essa pendência.

O executante final recebeu apenas a ferramenta `terminal`. Firecrawl, Computador, GitHub e OpenAI Developers foram usados pelo coordenador; não foram integrados ao executor.

## Validação

Os validadores Python e Node conferem campos obrigatórios, exatamente seis itens, trecho literal de até 180 caracteres, marca de tempo, metadado de modelo e presença da divergência. Eles não aprovam a qualidade do raciocínio. O caso em que cinco análises se repetiam passou no formato e foi reprovado na revisão de conteúdo. A revisão humana continua obrigatória.

## Referências verificadas

- [Guia oficial Windows](https://github.com/OpenHands/OpenHands/blob/v1.34.0/README.windows.md).
- [Exemplo de integração usado como referência](https://github.com/OpenHands/OpenHands/blob/v1.34.0/tests/e2e/live/utils/agent-server-conversation.ts).
- [Campos do modelo no SDK 1.58.1](https://github.com/OpenHands/software-agent-sdk/blob/v1.58.1/openhands-sdk/openhands/sdk/llm/llm.py).
