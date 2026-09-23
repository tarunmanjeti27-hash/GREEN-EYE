@echo off
echo ========================================================
echo   GREEN-EYE Vision Suite - Starting FastAPI Backend
echo   URL: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo ========================================================
cd /d "%~dp0"
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
