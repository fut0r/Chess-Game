@echo off
echo Starting Chess Game Backend API...
echo Requires Uvicorn and FastAPI to be installed: pip install fastapi uvicorn
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
pause
