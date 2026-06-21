$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot

Push-Location (Join-Path $RootDir "apps/api")
python -m ruff check .
python -m pytest -q
python -m pip_audit -r requirements.txt
Pop-Location

Push-Location (Join-Path $RootDir "apps/web")
npm.cmd run lint
npm.cmd run typecheck
if (Test-Path ".next") {
    Remove-Item -Recurse -Force ".next"
}
npm.cmd run build
npm.cmd audit --audit-level=high

$nextOutputPaths = @(".next/static", ".next/server") | Where-Object { Test-Path $_ }
if ($nextOutputPaths.Count -gt 0) {
    $unsafeMatches = @(Get-ChildItem $nextOutputPaths -Recurse -File | Select-String -SimpleMatch "http://localhost:8000" -List)
    if ($unsafeMatches.Count -gt 0) {
        throw "Unsafe localhost API fallback found in Next production output."
    }
}
Pop-Location

Push-Location $RootDir
if (-not $env:SECRET_KEY) {
    $env:SECRET_KEY = "release-check-secret-key-that-is-long-enough"
}
if (-not $env:ENCRYPTION_KEY) {
    $env:ENCRYPTION_KEY = "0J4FyJwHnYmeFz7r5Zk8F0KJxl-2mFY9hqqIetQxZj0="
}
if (-not $env:ADMIN_PASSWORD) {
    $env:ADMIN_PASSWORD = "release-check-admin-password"
}
docker compose -f docker-compose.yml config

if ($env:RUN_DOCKER_BUILD -eq "1") {
    docker compose -f docker-compose.yml build api worker web
}
Pop-Location
