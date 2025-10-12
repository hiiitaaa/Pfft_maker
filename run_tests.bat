@echo off
REM Pfft_maker テスト実行スクリプト

echo ========================================
echo Pfft_maker テスト実行
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

REM データモデルテストを実行
echo データモデルのテストを実行中...
python tests\test_models.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] テストが失敗しました。
    pause
    exit /b 1
)

echo.
echo ========================================
echo すべてのテストが成功しました！
echo ========================================
pause
