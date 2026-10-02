@echo off
echo Starting Dhvaani - Multilingual Government Services Assistant
echo Open browser at: http://localhost:8000
cd /d "%~dp0"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
