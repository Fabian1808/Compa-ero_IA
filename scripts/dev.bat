@echo off
REM AI Workmate - Development startup script
echo Starting AI Workmate development environment...

echo.
echo ========================================
echo 1. Starting Ollama (if not running)...
echo ========================================
REM Check if Ollama is running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Ollama is already running
) else (
    echo Starting Ollama...
    start /B ollama serve
    timeout /t 3 /nobreak > NUL
)

echo.
echo ========================================
echo 2. Starting Backend (FastAPI)...
echo ========================================
cd backend
start "AI Workmate Backend" cmd /k "uvicorn app.main:app --reload --port 8000"
cd ..

echo.
echo ========================================
echo 3. Starting Frontend (Vite)...
echo ========================================
cd frontend
start "AI Workmate Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo 4. Starting Tauri...
echo ========================================
cd tauri
start "AI Workmate Tauri" cmd /k "cargo tauri dev"
cd ..

echo.
echo All services starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:1420
echo API Docs: http://localhost:8000/docs
echo.
pause