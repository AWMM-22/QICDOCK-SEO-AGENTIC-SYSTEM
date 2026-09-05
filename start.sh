#!/bin/bash
set -e

echo "Starting Qicdock Marketing Calendar System..."
echo

echo "[1/3] Setting up backend..."
cd backend
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from example. Please configure your API keys."
fi
pip install -r requirements.txt -q
cd ..

echo "[2/3] Setting up frontend..."
cd frontend
npm install --silent
cd ..

echo "[3/3] Starting services..."
echo
echo "Starting backend on http://localhost:8000"
echo "Starting frontend on http://localhost:3000"
echo
echo "Press Ctrl+C to stop all services."
echo

cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 3
cd ../frontend && npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

wait