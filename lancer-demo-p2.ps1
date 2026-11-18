param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8000,
    [switch]$Install,
    [string]$PythonExecutable
)

$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $python = if ($PythonExecutable) { (Resolve-Path -LiteralPath $PythonExecutable).Path } else { Join-Path $PSScriptRoot '.venv/Scripts/python.exe' }
    if ($Install -or -not (Test-Path -LiteralPath $python)) {
        if (-not (Test-Path -LiteralPath $python)) {
            python -m venv .venv
            if ($LASTEXITCODE -ne 0) { throw 'Impossible de créer un environnement Python.' }
        }
        & $python -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) { throw 'Installation des dépendances interrompue.' }
    }
    if (-not $env:IMMIGRATION_CONSULTANT_INVITE) {
        $env:IMMIGRATION_CONSULTANT_INVITE = [guid]::NewGuid().ToString('N')
    }
    Write-Host "Démo locale : http://127.0.0.1:$Port/demo/"
    Write-Host "Invitation consultant pour cette session : $env:IMMIGRATION_CONSULTANT_INVITE"
    & $python -m uvicorn smart_immigration.api:app --app-dir src --host 127.0.0.1 --port $Port
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
