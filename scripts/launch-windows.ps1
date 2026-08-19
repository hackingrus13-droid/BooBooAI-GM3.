$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
if ($env:BOOBOO_ADMIN_APPROVED -ne "1") {
    Write-Error "ADMIN APPROVAL REQUIRED: set BOOBOO_ADMIN_APPROVED=1 and rerun."
    exit 77
}
New-Item -ItemType Directory -Force config, state, knowledge\library | Out-Null
if (-not (Test-Path config\config.json)) { Copy-Item config\config.example.json config\config.json }
if (-not (Test-Path config\private_rules.local.json) -and (Test-Path config\private_rules.local.example.json)) { Copy-Item config\private_rules.local.example.json config\private_rules.local.json }
$env:PYTHONPATH = "$Root;$env:PYTHONPATH"
Write-Host "=== BooBooAI-GM diagnostics ==="
python -m booboo.diagnostics
Write-Host "=== Starting BooBooAI-GM ==="
Write-Host "Open http://127.0.0.1:8080/ in your browser."
$env:BOOBOO_ADMIN_APPROVED = "1"
python server.py
