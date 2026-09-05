@echo off
echo Starting Qicdock Marketing Calendar System...
echo.

echo [1/3] Setting up backend...
cd backend
if not exist ".env" (
    copy .env.example .env
    echo Created .env from example. Please configure your API keys.
)
python -m pip install -r requirements.txt --quiet
cd ..

echo [2/3] Setting up frontend...
cd frontend
npm install --silent
cd ..

echo [3/3] Starting services...
echo.
echo Starting backend on http://localhost:8000
echo Starting frontend on http://localhost:3000
echo.
echo Press Ctrl+C to stop all services.
echo.

start "Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul
start "Frontend" cmd /k "cd frontend && npm run dev"

echo Services started! Check the opened command windows.
pause