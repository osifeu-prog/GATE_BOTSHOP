param(
    [string]$Message = "GATE BOTSHOP full cycle"
)

$ErrorActionPreference = "Stop"

$projectPath = "D:\GATE_BOTSHOP"
Set-Location $projectPath

Write-Host "== GATE BOTSHOP FULL CYCLE START ==" -ForegroundColor Cyan

# 1) Ensure virtualenv
if (-not (Test-Path ".venv")) {
    Write-Host "== Creating virtualenv (.venv) ==" -ForegroundColor Yellow
    python -m venv .venv
}

# 2) Activate virtualenv
Write-Host "== Activating virtualenv ==" -ForegroundColor Yellow
. ".\.venv\Scripts\activate"

# 3) Install / update dependencies
Write-Host "== Installing requirements ==" -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4) Syntax check
Write-Host "== Compiling Python files ==" -ForegroundColor Yellow
python -m compileall app

# 5) Init DB schema
Write-Host "== Running init_db() to sync database schema ==" -ForegroundColor Yellow
python -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"

# 6) Start local server in a new PowerShell window for manual testing
Write-Host "== Starting local server on http://127.0.0.1:8000 ==" -ForegroundColor Cyan
Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd $projectPath; . .\.venv\Scripts\activate; uvicorn app.main:app --reload --port 8000"

Write-Host ""
Write-Host "בדוק עכשיו מקומית: http://127.0.0.1:8000/health, /docs, ותבדוק את הבוט בטלגרם (/start, /wallet, /admin)." -ForegroundColor Green
Write-Host "כשסיימת לבדוק והכל תקין, לחץ ENTER כדי להמשיך ל-git commit + push." -ForegroundColor Green
[void][System.Console]::ReadLine()

# 7) Git: add + commit + push
Write-Host "== Git status before commit ==" -ForegroundColor Yellow
git status

Write-Host "== Adding all changes ==" -ForegroundColor Yellow
git add .

Write-Host "== Commit with message: $Message ==" -ForegroundColor Yellow
git commit -m $Message

Write-Host "== Pushing to origin/main ==" -ForegroundColor Yellow
git push origin main

Write-Host ""
Write-Host "== DONE: Code pushed to GitHub. Railway will deploy the new version automatically ==" -ForegroundColor Green
