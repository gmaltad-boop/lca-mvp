# Git Playbook — LCA MVP
Última atualização: 01/11/2026 (coordenação Drael + Codex)

## Invariantes
- Repositório: **gmaltad-boop/lca-mvp** (privado), branch **main**. Fonte de verdade do código.
- Nunca entram no commit: `.env` (chaves reais), `data/` (estado local), `node_modules/`.
- Política: **toda rodada termina com push confirmado** — SHA verificado pelo lado do GitHub.
- Mensagem de commit: curta, pt-BR, prefixo tipo `feat:` / `fix:` / `docs:` / `infra:`.

## Rota oficial de publicação
- Autor: coordenação Drael/Codex. O Codex usa o conector GitHub autorizado; o fluxo git-data cria árvore e commit e atualiza a branch com verificação do SHA anterior. Nesta POC, uma branch de revisão preserva a main até a decisão de incorporar.
- O fluxo existente do Drael usa a API REST (git-data). A credencial da sandbox não deve ser copiada para o chat, o repositório ou os scripts do Codex.
- Por que não git tradicional: a sandbox não tem binário git; o cliente Python (dulwich) falha em entregar credenciais basic-auth pelo cabo HTTP. A rota REST é determinística e devolve o SHA para conferência.
- Comando: `python3 /workspace/gitpush.py "mensagem do commit"`. O script calcula os SHA locais, difere contra a árvore remota, sobe só o que mudou, cria o commit por cima do HEAD atual e sincroniza a referência local. Sem mudanças → sai sem commitar.
- Token: vive em `/workspace/drael.credentials` (linha `GITHUB_PAT=`). Fine-grained, só o repositório lca-mvp, permissão mínima Contents: Read and write. Nunca vai para dentro do repositório.

## Rotação do token (quando: pós-lançamento 06/11 e a cada troca de fase)
1. No GitHub: Settings → Developer settings → Fine-grained tokens → apagar o token atual (morte imediata).
2. Criar `drael-lca-N`: acesso somente ao repositório lca-mvp, Contents: Read and write.
3. Configurar a credencial pelo fluxo seguro do serviço ou gerenciador local apropriado. Nunca colar token no chat, em issues, em PRs ou em arquivos versionados.
4. Drael atualiza `drael.credentials`, confere `GET /user` (espera 200 + `gmaltad-boop`) e faz um push-teste.

## Fallback manual (Guilherme, Windows / PowerShell 5.1) — só se a sandbox estiver fora
Usar o conector GitHub autorizado ou o gerenciador de credenciais do Git. Nunca incluir token na URL do remoto, no histórico do terminal ou no corpo de mensagens.

```powershell
git remote set-url origin https://github.com/gmaltad-boop/lca-mvp.git
git push origin <branch-revisada>
```
Aposar: comunicar no chat e conferir o histórico para reconciliar com a referência da sandbox.

## Incidentes conhecidos
| Sinal | Causa | Ação |
|---|---|---|
| 401 "Bad credentials" em `GET /user` | token morto/corrompido (não é repo nem branch) | rotacionar |
| 409 "Git Repository is empty" em git-data | repo novo sem commit algum | primeiro arquivo via `PUT /contents/{path}` |
| 422 "Reference already exists" ao criar ref | ref já existe | usar `PATCH /git/refs/heads/main` |
| 405/409 no PATCH de ref | outro escritor chegou antes | reler HEAD e reparentear o commit |

