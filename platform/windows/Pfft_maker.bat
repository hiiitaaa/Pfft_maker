@echo off
REM Pfft_maker Application Launcher (Windows)
REM
REM 使用方法: このスクリプトはplatform/windows/から実行されます
REM プロジェクトルートに移動してからrun.pyを実行します

echo ========================================
echo Pfft_maker Starting...
echo ========================================
echo.

REM プロジェクトルートディレクトリに移動
cd /d "%~dp0..\.."

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo Python: OK
echo.

REM Check dependencies
echo Checking dependencies...
python -m pip show PyQt6 >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing dependencies...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)
echo Dependencies: OK

echo.
echo Starting application...
echo.

REM Launch app
python run.py

REM Check error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application failed to start.
    pause
    exit /b 1
)

pause
