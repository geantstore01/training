$ErrorActionPreference = 'Stop'
$trainingRoot = Split-Path $PSScriptRoot -Parent
$webRoot = Join-Path $trainingRoot 'apps\web'
$previewLogs = Join-Path $trainingRoot 'artifacts\cm2-preview'
New-Item -ItemType Directory -Force -Path $previewLogs | Out-Null
foreach ($previewPort in @(19092,19093)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $previewPort -ErrorAction SilentlyContinue) {
        throw "Le port $previewPort est déjà occupé. Aucun processus n'a été arrêté."
    }
}
$pythonExe = Join-Path $trainingRoot '.venv\Scripts\python.exe'
$nodeExe = (Get-Command node.exe).Source
$apiProcess = Start-Process -FilePath $pythonExe -ArgumentList @('-m','uvicorn','scripts.preview_cm2_training:app','--host','127.0.0.1','--port','19092') -WorkingDirectory $trainingRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $previewLogs 'api.log') -RedirectStandardError (Join-Path $previewLogs 'api-error.log')
$webProcess = Start-Process -FilePath $nodeExe -ArgumentList @('node_modules/vite/bin/vite.js','--config','vite.cm2.config.mjs') -WorkingDirectory $webRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $previewLogs 'web.log') -RedirectStandardError (Join-Path $previewLogs 'web-error.log')
@{api_pid=$apiProcess.Id;web_pid=$webProcess.Id;url='http://127.0.0.1:19093/tests/cm2-preview/'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $previewLogs 'processes.json')
Write-Output 'Recette locale : http://127.0.0.1:19093/tests/cm2-preview/'
Write-Output "Processus : API $($apiProcess.Id), interface $($webProcess.Id). Les essais disparaissent à l'arrêt de l'API."
