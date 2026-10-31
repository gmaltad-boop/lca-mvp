# LCA MVP — copiloto clínico-operacional (dados fictícios)

Protótipo privativo, single-user, 100% local. O sistema organiza; ele não
diagnostica, não prescreve e não substitui julgamento clínico. Toda saída é
um rascunho sujeito à revisão do profissional (editar ≠ aprovar).

## Como rodar
Pré-requisito: Node.js 18+ (recomendado 22). Sem dependências npm.

    cp .env.example .env     # e cole sua OPENAI_API_KEY
    npm start                # abre http://localhost:3000

Testes automáticos (offline, sem gastar API):

    npm test

## Configuração (.env)
- OPENAI_API_KEY: chave da OpenAI (nunca commitar — veja .gitignore)
- OPENAI_MODEL: vazio = gpt-5.1 (defina se quiser outro)
- PORT: 3000

## Apagar dados locais
Botão "Apagar dados locais" na tela de pacientes, ou:

    rm data/lca.json

## Fluxo
1. Criar paciente fictício (com objetivo opcional nas palavras do paciente).
2. Nova sessão: colar a nota e gerar o resumo estruturado.
3. Revisão item a item: aprovar / descartar / editar (editar volta a "aguarda aprovação").
   "Localizar na nota" destaca o trecho de origem.
4. Barra-resumo mostra pendentes/editados/aprovados/descartados.

## Limites (leia antes de usar com qualquer dado real)
- Apenas dados fictícios ou anonimizados nesta fase.
- store:false é preferência na chamada, não garantia de retenção zero.
- Armazenamento local ≠ processamento local (o texto vai para a API).
- Revisão humana é obrigatória antes de qualquer uso do texto.
- Sem login/multiusuário nesta fase (decisão registrada em DECISÕES.md).

## Mapa dos arquivos
- src/schema.js        schema JSON (strict) + prompt de regras + validação
- src/state.js         máquina de estados da revisão (editar nunca aprova)
- src/storage.js       leitura/escrita local em JSON (data/lca.json)
- src/organize-note.js chamada à Responses API (Structured Outputs)
- src/server.js        servidor local (estáticos + /api/*)
- public/              interface (três telas: pacientes, timeline, revisão)
- tests/               testes offline (node:test) + caso-âncora e saída de referência
- smoke/live-t0.mjs    execução real do caso-âncora contra a API (gera a referência)
