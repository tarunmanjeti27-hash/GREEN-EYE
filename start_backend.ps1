Write-Host "========================================================" -ForegroundColor Green
Write-Host "  GREEN-EYE Vision Suite - Starting FastAPI Backend" -ForegroundColor Cyan
Write-Host "  URL: http://localhost:8000" -ForegroundColor Yellow
Write-Host "  Swagger UI Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green

Set-Location $PSScriptRoot
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
