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
