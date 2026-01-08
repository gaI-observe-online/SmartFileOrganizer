@echo off
REM SmartFileOrganizer Installation Script
REM For Windows

echo ========================================================
echo      SmartFileOrganizer - Installation Wizard
echo              One-Click Setup with Web UI
echo ========================================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3 not found. Please install Python 3.8 or higher.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

REM Check disk space
echo.
echo Checking disk space...
for /f "tokens=3" %%a in ('dir /-c ^| find "bytes free"') do set FREE_SPACE=%%a
echo [OK] Disk space check passed

REM Check if Ollama is installed
echo.
echo Checking for Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama not found.
    echo Please install Ollama from: https://ollama.com/download
    echo After installation, run this script again.
    pause
    exit /b 1
) else (
    echo [OK] Ollama found
)

REM Pull Ollama models
echo.
echo Pulling AI models (this may take a few minutes^)...
echo   Downloading llama3.3...
ollama pull llama3.3
echo   Downloading qwen2.5...
ollama pull qwen2.5

REM Create virtual environment
echo.
echo Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment created

REM Activate virtual environment and install dependencies
echo.
echo Installing Python dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Initialize database
echo.
echo Initializing database...
if not exist "%USERPROFILE%\.organizer" mkdir "%USERPROFILE%\.organizer"

REM Create config file
echo.
echo Creating default configuration...
if not exist "%USERPROFILE%\.organizer\config.json" (
    copy config.example.json "%USERPROFILE%\.organizer\config.json"
    echo [OK] Configuration created at %USERPROFILE%\.organizer\config.json
) else (
    echo [WARNING] Configuration already exists, skipping
)

REM Create start script
echo.
echo Creating start script...
(
echo @echo off
echo REM SmartFileOrganizer - Start Script
echo.
echo cd /d "%%~dp0"
echo call venv\Scripts\activate.bat
echo.
echo echo Starting SmartFileOrganizer server...
REM Bind to localhost only for security (prevents external network access)
echo start /B python -m uvicorn src.main:app --host 127.0.0.1 --port 8001
echo.
echo echo Server started!
echo echo Web UI: http://localhost:8001
echo echo.
echo echo Press any key to stop the server...
echo pause ^>nul
echo.
echo REM Kill the server process
echo taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*"
) > start.bat
echo [OK] Start script created: start.bat

REM Start server
echo.
echo Starting SmartFileOrganizer server...
REM Bind to localhost only for security (prevents external network access)
start /B python -m uvicorn src.main:app --host 127.0.0.1 --port 8001

REM Wait for server to be ready
echo.
echo Waiting for server to be ready...
set /a ATTEMPTS=0
:wait_loop
set /a ATTEMPTS+=1
timeout /t 1 /nobreak >nul
curl -s http://localhost:8001/health >nul 2>&1
if %errorlevel% equ 0 goto server_ready
if %ATTEMPTS% geq 30 goto server_failed
goto wait_loop

:server_ready
echo [OK] Server is ready!

REM Open browser
echo.
echo Opening browser...
start http://localhost:8001

REM Success message
echo.
echo ========================================================
echo          Installation Complete!
echo ========================================================
echo.
echo Web UI:      http://localhost:8001
echo API Docs:    http://localhost:8001/docs
echo.
echo Quick Start:
echo   1. Click 'Auto-Scan' in the web UI
echo   2. Review organization plans
echo   3. Click 'Approve' and 'Execute'
echo.
echo CLI Usage (Advanced^):
echo   * Activate venv:   venv\Scripts\activate.bat
echo   * Scan folder:     python organize.py scan C:\Users\%USERNAME%\Downloads
echo   * Watch folder:    python organize.py watch C:\Users\%USERNAME%\Downloads
echo.
echo Server Management:
echo   * Restart server:  start.bat
echo   * Stop server:     taskkill /IM python.exe /F
echo.
echo Documentation:
echo   * README.md         - Overview
echo   * docs\USAGE.md     - Detailed guide
echo   * docs\PRIVACY.md   - Privacy info
echo.
echo [OK] All processing is 100%% local. Your files never leave your computer.
echo.
echo Happy organizing!
echo.
pause
exit /b 0

:server_failed
echo [ERROR] Server failed to start within 30 seconds
echo.
echo Troubleshooting:
echo   1. Check if port 8001 is already in use
echo   2. Try starting manually: start.bat
echo   3. Check server logs for errors
echo.
pause
exit /b 1
