@echo off
REM Pfft_maker アプリケーション起動スクリプト

echo ========================================
echo Pfft_maker 起動
echo ========================================
echo.

REM Pythonの存在確認
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Pythonが見つかりません。Python 3.11以上をインストールしてください。
    pause
    exit /b 1
)

echo Python確認: OK
echo.

REM 依存関係の確認
echo 依存関係を確認中...
pip show chardet >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] 依存関係がインストールされていません。
    echo インストールしますか？ (Y/N)
    set /p install_deps=
    if /i "%install_deps%"=="Y" (
        pip install -r requirements.txt
    ) else (
        echo インストールをキャンセルしました。
        pause
        exit /b 1
    )
)

echo.
echo アプリケーションを起動中...
echo [NOTE] Phase 4.1では、UIは未実装です。

REM 将来的にはここでメインアプリを起動
REM python src\main.py

echo.
echo [INFO] Phase 4.2以降でUIが実装されます。
echo [INFO] 現在はテストのみ実行可能です: run_tests.bat
echo.
pause
