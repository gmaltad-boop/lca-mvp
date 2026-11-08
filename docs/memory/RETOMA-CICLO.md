# RETOMA-CICLO — instrução exata para qualquer retomada (Drael em novo ciclo, agendador da plataforma ou humano)

Disparador padrão: mensagem "retomada de ciclo LCA — noite 01" (ou tarefa agendada +5 min após um ciclo encerrado com pendência).

Procedimento (ordem fixa, sem saltos):
1. Ler `PLANO-NOITE-2026-11-01.md` (blocos + paradas P1–P5).
2. Ler `NOITE-LOG.md` (o que já rodou; SHAs publicados; vereditos).
3. Identificar o PRÓXIMO bloco pendente (menor índice não concluído).
4. Executá-lo dentro do SEU critério de parada (P2/P3 do plano).
5. Terminar em SAVE POINT: commit + SHA verificado + linha no NOITE-LOG (mesma noite, mesmo padrão SP-n).
6. Condição de término GLOBAL (toda ou nada): todos os blocos concluídos OU restantes marcados BLOCKED/pendência
   COM causa + `RELATORIO-NOITE` publicado + `HANDOFF-01NOITE` no Notion publicado.
   → Se atingida: NÃO re-agendar; enviar relatório final ao dono.
7. Se não atingida: re-agendar próxima retomada +5 min e parar o ciclo (um bloco por ciclo, estado nos logs).

Regra de ouro: o estado vive nos save points e nos logs; nenhum conhecimento pode existir só na conversa.
Se o log estiver ausente/ilegível: considerar tudo pendente a partir de SP-1 (`8ad7f5aaf14f`) e re-verificar o GitHub antes de agir.

Notificacao ao dono: todo evento AMARELO/VERMELHO (fila nova p/ terceiros, handoff, decisao, falha, dinheiro, gate) termina com `python3 /workspace/ping.py "resumo + horario + link"` (webhook no cofre).
Rotina interna (logs, SP de evidencia) fica somente no NOITE-LOG, sem ping.


## SP-12 — 2026-11-02 23:51Z — fechamento auditoria (discord ao vivo + fontes)

- DECISÃO (titular): 9º nome do piloto = RESERVA DE EMPATE — entra só se houver empate entre os 8 oficiais.
- FAPITEC: estado corrigido — sem contato prévio; aviso veio de familiar (professor da universidade). E-mail = apresentação fria, slot ter 04/11. Passo antes: mapear responsáveis + dores via Firecrawl (input pro raciocínio, não pitch).
- C:\Users\guima\Downloads\drael (exportações antigas + 'cerebro' Second Brain): status = MATÉRIA-PRIMA/HISTÓRIA, não instrução. 4 ZIPs c/ entrada credentials selados (segredos não lidos; 2 idênticos). Inventário recursivo pendente com a mão local.
- VIVO (evidência Codex): bot respondeu !lca status e !lca ajuda em 02/11 17:03–17:05 (hora local); helper 1400 e bridge 24404 via Win32_Process. Credencial nova guardada pelo titular via DPAPI.
- Segunda 9h intacta; nenhuma mensagem externa criada neste fechamento além deste registro.
