@echo off
REM Pfft_maker Test Runner

echo ========================================
echo Pfft_maker Tests
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

echo Python: OK
echo.

REM Run tests
echo Running data model tests...
python tests\test_models.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Tests failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo All tests passed!
echo ========================================
pause
