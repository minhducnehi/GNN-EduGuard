# Script khởi động toàn bộ Hệ sinh thái GNN-EduGuard (100% Local AI)
$ErrorActionPreference = "Continue"
$env:CURL_CA_BUNDLE = $null
$env:PYTHONIOENCODING = "utf-8"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "   KHOI DONG HE THONG GNN-EDUGUARD (LOCAL AI + GNN)  " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Kiem tra Ollama
Write-Host "[1/3] Kiem tra Ollama Service (qwen2.5:3b & nomic-embed-text)..." -ForegroundColor Yellow
& "C:\Users\PC\AppData\Local\Programs\Ollama\ollama.exe" list

# 2. Khoi dong Python FastAPI AI Microservice (:8000)
Write-Host "[2/3] Khoi dong Python FastAPI AI Microservice tai http://127.0.0.1:8000 ..." -ForegroundColor Yellow
$aiDir = "C:\DulieuoD\DACN\GNN-EduGuard\ai-service"
$env:PYTHONPATH = $aiDir
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:CURL_CA_BUNDLE=`$null; `$env:PYTHONPATH='$aiDir'; `$env:PYTHONIOENCODING='utf-8'; & '$aiDir\.venv\Scripts\python.exe' -m uvicorn main:app --app-dir '$aiDir' --host 127.0.0.1 --port 8000"

Start-Sleep -Seconds 3

# 3. Khoi dong ASP.NET Core Web Portal
Write-Host "[3/3] Khoi dong Web Portal ASP.NET Core (GNN-EduGuard)..." -ForegroundColor Green
Set-Location "C:\DulieuoD\DACN\GNN-EduGuard\GNN-EduGuard"
dotnet run
