$ErrorActionPreference = 'Stop'
$lcaRoot = Split-Path -Parent $PSScriptRoot
$missionPath = Join-Path $lcaRoot 'workspaces\t002-missao1'
$statePath = Join-Path $lcaRoot 'state'
$outputPath = Join-Path $missionPath 'output'
$keyPath = Join-Path $PSScriptRoot '.env.local'
$imageName = 'ghcr.io/openhands/agent-canvas:1.34.0'
$containerName = 'lca-openhands-t002'
foreach ($requiredPath in @($missionPath,$statePath,$outputPath,$keyPath)) {
  if (-not (Test-Path -LiteralPath $requiredPath)) { throw 'A pasta ou configuração necessária do LCA está ausente.' }
}
$existingId = & docker container ls -a --filter "name=^/$containerName$" --format '{{.ID}}'
if ($existingId) {
  & docker start $containerName
} else {
  & docker run --detach --name $containerName --memory 1536m --cpus 2 --pids-limit 512 --restart no `
    -p '127.0.0.1:8000:8000' `
    -e 'AGENT_CANVAS_ALLOW_LAN_SESSION_KEY=true' `
    --env-file $keyPath `
    --mount "type=bind,src=$statePath,dst=/home/openhands/.openhands" `
    --mount "type=bind,src=$missionPath,dst=/projects/t002,readonly" `
    --mount "type=bind,src=$outputPath,dst=/projects/t002/output" `
    $imageName
}
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível iniciar o ambiente LCA.' }
Write-Output 'LCA: inicialização solicitada em http://localhost:8000/canvas; conferir saúde antes de usar.'
