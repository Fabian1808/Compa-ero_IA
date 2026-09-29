#!/bin/bash
# AI Workmate - Development startup script

echo "Starting AI Workmate development environment..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
for cmd in ollama node npm cargo python3 uv pip; do
    if ! command_exists "$cmd"; then
        echo "Warning: $cmd not found in PATH"
    fi
done

echo ""
echo "========================================"
echo "1. Starting Ollama (if not running)..."
echo "========================================"
if pgrep -x "ollama" > /dev/null; then
    echo "Ollama is already running"
else
    echo "Starting Ollama..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 3
fi

echo ""
echo "========================================"
echo "2. Starting Backend (FastAPI)..."
echo "========================================"
cd backend
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .[dev]
else
    source .venv/bin/activate
fi

# Run migrations
python -m alembic upgrade head

# Start backend in background
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "3. Starting Frontend (Vite)..."
echo "========================================"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "========================================"
echo "4. Starting Tauri..."
echo "========================================"
cd tauri
cargo tauri dev &
TAURI_PID=$!
cd ..

echo ""
echo "All services starting..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:1420"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap SIGINT to kill all background processes
trap "kill $OLLAMA_PID $BACKEND_PID $FRONTEND_PID $TAURI_PID 2>/dev/null; exit" INT

# Wait for all background processes
wait