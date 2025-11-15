# Frontend Dev Server Startup Script
Write-Host "=== FRONTEND DEV SERVER ===" -ForegroundColor Cyan
Write-Host "Starting on http://localhost:5173..." -ForegroundColor Green
Write-Host ""

Set-Location "$PSScriptRoot\frontend"

& "C:\Program Files\nodejs\npm.cmd" run dev

