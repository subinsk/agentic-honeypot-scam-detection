# Quick start script for mock scammer testing
# Run from project root: .\scripts\start_mock_test.ps1

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Mock Scammer Testing - Quick Start" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan

# Check if in venv
if (-not $env:VIRTUAL_ENV) {
    Write-Host "`n⚠️  Virtual environment not activated!" -ForegroundColor Yellow
    Write-Host "Run: .\venv\Scripts\Activate.ps1`n" -ForegroundColor Yellow
    exit 1
}

# Check if Ollama is running
Write-Host "`nChecking Ollama..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Ollama not running!" -ForegroundColor Red
    Write-Host "Start it: ollama serve" -ForegroundColor Yellow
    Write-Host "Pull model: ollama pull deepseek-r1:8b`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nStarting services..." -ForegroundColor Yellow
Write-Host "(Press Ctrl+C in each terminal to stop)`n" -ForegroundColor Gray

# Start honeypot in new terminal
Write-Host "1️⃣  Starting Honeypot API (port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python run.py"
Start-Sleep -Seconds 3

# Start mock scammer in new terminal
Write-Host "2️⃣  Starting Mock Scammer API (port 8001)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python scripts\mock_scammer.py"
Start-Sleep -Seconds 3

# Wait for both to be ready
Write-Host "`n⏳ Waiting for services to start..." -ForegroundColor Yellow
$maxRetries = 10
$ready = $false

for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        $honeypot = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 1 -ErrorAction Stop
        $scammer = Invoke-RestMethod -Uri "http://localhost:8001/health" -TimeoutSec 1 -ErrorAction Stop
        $ready = $true
        break
    } catch {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 1
    }
}

if (-not $ready) {
    Write-Host "`n❌ Services failed to start" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Both services ready!" -ForegroundColor Green

# Run conversation test
Write-Host "`n3️⃣  Running 20-turn conversation test (quick results)..." -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Gray
python scripts\test_conversation.py --turns 20

Write-Host "`n" + "=" * 80 -ForegroundColor Cyan
Write-Host "✅ Test complete!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "`nTo run again: python scripts\test_conversation.py" -ForegroundColor Yellow
Write-Host "To adjust turns: python scripts\test_conversation.py --turns 30" -ForegroundColor Yellow
Write-Host "For quick test: python scripts\test_conversation.py --turns 10" -ForegroundColor Yellow
Write-Host "`nThe honeypot and mock scammer are still running in other windows." -ForegroundColor Gray
Write-Host "Close those terminals when done.`n" -ForegroundColor Gray
