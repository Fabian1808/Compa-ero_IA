@echo off
REM Build script for AI Workmate desktop app (Windows)
REM Run this from the root of the repository

REM IMPORTANT: Change to script directory so it works from anywhere
cd /d "%~dp0"

echo ========================================
echo   AI Workmate - Desktop App Builder
echo ========================================
echo.

REM Check prerequisites
echo Checking prerequisites...

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.11+ from https://python.org or run: winget install Python.Python.3.11
    goto :error_exit
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found in PATH
    echo Please install Node.js 18+ from https://nodejs.org or run: winget install OpenJS.NodeJS.LTS
    goto :error_exit
)

where cargo >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Rust/Cargo not found. Install from https://rustup.rs/
    goto :error_exit
)

where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller not found. Run: pip install pyinstaller
    goto :error_exit
)

echo All prerequisites found
echo.

REM Parse arguments
set BUILD_BACKEND=true
set BUILD_FRONTEND=true
set BUILD_TAURI=true

for %%a in (%*) do (
    if "%%a"=="--backend-only" set BUILD_FRONTEND=false&set BUILD_TAURI=false
    if "%%a"=="--frontend-only" set BUILD_BACKEND=false&set BUILD_TAURI=false
    if "%%a"=="--tauri-only" set BUILD_BACKEND=false&set BUILD_FRONTEND=false
)

REM Build backend
if "%BUILD_BACKEND%"=="true" (
    echo ========================================
    echo Building backend binary with PyInstaller...
    echo ========================================
    cd backend
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    pyinstaller ai-workmate-backend.spec --clean --noconfirm
    if not exist dist\ai-workmate-backend.exe (
        echo ERROR: Backend binary not found after build
        goto :error_exit
    )
    echo Backend binary built successfully
    cd ..
    echo.
)

REM Build frontend
if "%BUILD_FRONTEND%"=="true" (
    echo ========================================
    echo Building frontend...
    echo ========================================
    cd frontend
    if not exist node_modules (
        echo Installing npm dependencies...
        npm install
    )
    npm run build
    if not exist dist (
        echo ERROR: Frontend build failed
        goto :error_exit
    )
    echo Frontend built successfully
    cd ..
    echo.
)

REM Build Tauri app
if "%BUILD_TAURI%"=="true" (
    echo ========================================
    echo Building Tauri app...
    echo ========================================
    cd tauri
    cargo tauri build
    echo Tauri app built successfully
    cd ..
    echo.
)

echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Output files:
if exist tauri\target\release\bundle\msi\AI Workmate_0.1.0_x64.msi (
    echo   Windows MSI: tauri\target\release\bundle\msi\AI Workmate_0.1.0_x64.msi
)
if exist tauri\target\release\bundle\nsis\AI Workmate_0.1.0_x64-setup.exe (
    echo   Windows NSIS: tauri\target\release\bundle\nsis\AI Workmate_0.1.0_x64-setup.exe
)
if exist tauri\target\release\bundle\appimage\AI Workmate_0.1.0_amd64.AppImage (
    echo   Linux AppImage: tauri\target\release\bundle\appimage\
)
echo.
echo To distribute: share the .msi (Windows) or .AppImage (Linux)
echo.
goto :success_exit

:error_exit
echo.
echo ========================================
echo BUILD FAILED
echo ========================================
echo Check the error messages above.
pause
exit /b 1

:success_exit
echo.
echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo Press any key to exit...
pause
exit /b 0