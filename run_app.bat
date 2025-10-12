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

REM メインアプリを起動
python src\main.py

REM エラーチェック
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] アプリケーションの起動に失敗しました。
    pause
    exit /b 1
)

pause
