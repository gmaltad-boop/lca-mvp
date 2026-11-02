# Missão T-003 — Convidar o bot Drael-LCA para o servidor LCA e ligar a Message Content Intent

Executor: agente de computador/navegador (as MÃOS) | cérebro e veredito: Drael | aberta: 2026-11-02 00:24 UTC
Contrato: PROTOCOLO-MEMORIA-v1 (identidade por metadado; N=1 não vira regra; parada ≤2 tentativas/etapa).

## Objetivo (um, verificável)
Deixar o bot Drael-LCA (application id 1566599445238390865) membro do servidor onde o usuário "Drael"
já publica mensagens iniciando com "🔔 LCA", e deixar a Message Content Intent dele LIGADA.

## Pré-requisito (se faltar → BLOCKED dizendo exatamente o que falta; nada de tentar senhas)
- Navegador aberto com a conta DISCORD correta já logada (a dona/membro daquele servidor).

## Passos (só estes; sem extras)
1. Abrir: https://discord.com/oauth2/authorize?client_id=1566599445238390865&scope=bot&permissions=117760
   -> tela "Add to Server": escolher o servidor onde chegam as notificações "🔔 LCA" -> confirmar.
2. Verificar na lista de membros desse servidor que o bot "Drael-LCA" consta (badge BOT).
3. Abrir: https://discord.com/developers/applications/1566599445238390865/bot
   -> em "Privileged Gateway Intents", ligar MESSAGE CONTENT INTENT -> salvar.
   Se o interruptor já estiver ligado: registrar isso, não tocar em nada.

## Linhas vermelhas (passou = ABORTA e reporta; sem nova ordem, não repete)
- NUNCA pressionar "Reset Token"/"Reset Token..." em nenhum ponto: o token vigente deixaria de existir.
- Não criar contas, não alterar permissões de outros cargos, não apagar/mover canais ou servidores.
- Pedido de 2FA/código que não estiver disponível na tela -> BLOCKED com motivo.
- Duas tentativas por etapa no máximo; o terceiro erro encerra a missão com o estado registrado.

## Saída única (formato exato, sem prosa)
STATUS: OK | BLOCKED(motivo) | ABORTADA(linha vermelha)
EVID1: bot "Drael-LCA" visível nos membros -> nome do servidor: ____________
EVID2: Message Content Intent = ON (ou "já estava ON")
EXTRAS: nomes de servidores candidatos em dúvida (ou "nenhum") | mais acontecimentos (ou "nenhum")

## Entrega
Postar a resposta no MESMO canal LCA do Discord. O Drael lê esse canal a cada ciclo e confere por
metadado a mudança de estado esperada (leitura do canal com o token do bot: de 401 para 200).
A palavra do executor é evidência; o veredito é do Drael.
