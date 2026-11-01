$ErrorActionPreference = 'Stop'
& docker stop lca-openhands-t002
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível parar o ambiente LCA.' }
Write-Output 'Ambiente LCA parado. Arquivos e configuração preservados.'
