# Git Playbook — LCA MVP
Última atualização: 31/10/2026 (Drael)

## Invariantes
- Repositório: **gmaltad-boop/lca-mvp** (privado), branch **main**. Fonte de verdade do código.
- Nunca entram no commit: `.env` (chaves reais), `data/` (estado local), `node_modules/`.
- Política: **toda rodada termina com push confirmado** — SHA verificado pelo lado do GitHub.
- Mensagem de commit: curta, pt-BR, prefixo tipo `feat:` / `fix:` / `docs:` / `infra:`.

## Rota oficial de publicação
- Autor: Drael, a partir da sandbox, pela **API REST do GitHub (git-data)**: blobs → trees → commit → `PATCH /git/refs/heads/main`.
- Por que não git tradicional: a sandbox não tem binário git; o cliente Python (dulwich) falha em entregar credenciais basic-auth pelo cabo HTTP. A rota REST é determinística e devolve o SHA para conferência.
- Comando: `python3 /workspace/gitpush.py "mensagem do commit"`. O script calcula os SHA locais, difere contra a árvore remota, sobe só o que mudou, cria o commit por cima do HEAD atual e sincroniza a referência local. Sem mudanças → sai sem commitar.
- Token: vive em `/workspace/drael.credentials` (linha `GITHUB_PAT=`). Fine-grained, só o repositório lca-mvp, permissão mínima Contents: Read and write. Nunca vai para dentro do repositório.

## Rotação do token (quando: pós-lançamento 06/11 e a cada troca de fase)
1. No GitHub: Settings → Developer settings → Fine-grained tokens → apagar o token atual (morte imediata).
2. Criar `drael-lca-N`: acesso somente ao repositório lca-mvp, Contents: Read and write.
3. Colar o token novo no chat uma única vez (o canal do chat já é a classe de risco aceita; rotação mantém a vida útil curta).
4. Drael atualiza `drael.credentials`, confere `GET /user` (espera 200 + `gmaltad-boop`) e faz um push-teste.

## Fallback manual (Guilherme, Windows / PowerShell 5.1) — só se a sandbox estiver fora
```powershell
$env:T = '<token>'
Invoke-RestMethod -Uri "https://api.github.com/user" -Headers @{Authorization="Bearer $($env.T)"}
git remote set-url origin "https://x-access-token:$($env.T)@github.com/gmaltad-boop/lca-mvp.git"
git push origin main
```
Aposar: comunicar no chat e conferir o histórico para reconciliar com a referência da sandbox.

## Incidentes conhecidos
| Sinal | Causa | Ação |
|---|---|---|
| 401 "Bad credentials" em `GET /user` | token morto/corrompido (não é repo nem branch) | rotacionar |
| 409 "Git Repository is empty" em git-data | repo novo sem commit algum | primeiro arquivo via `PUT /contents/{path}` |
| 422 "Reference already exists" ao criar ref | ref já existe | usar `PATCH /git/refs/heads/main` |
| 405/409 no PATCH de ref | outro escritor chegou antes | reler HEAD e reparentear o commit |
