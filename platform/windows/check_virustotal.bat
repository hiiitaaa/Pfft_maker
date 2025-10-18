@echo off
REM VirusTotal チェックガイド
REM ビルド後のEXEファイルをVirusTotalでスキャンする手順

echo ========================================
echo VirusTotal チェックガイド
echo ========================================
echo.

REM EXEファイルの存在確認
if not exist "dist\Pfft_maker\Pfft_maker.exe" (
    echo ERROR: EXEファイルが見つかりません
    echo 先に build_distribution.bat を実行してください
    pause
    exit /b 1
)

echo 1. ブラウザで以下のURLを開きます:
echo    https://www.virustotal.com/gui/home/upload
echo.
echo 2. 以下のファイルをアップロードします:
echo    %CD%\dist\Pfft_maker\Pfft_maker.exe
echo.
echo 3. スキャン完了後、結果ページのURLをコピーします
echo    例: https://www.virustotal.com/gui/file/xxxxx
echo.
echo 4. 配布時にそのURLを共有してください
echo.
echo ========================================
echo ヒント
echo ========================================
echo.
echo ■ 主要なアンチウイルスの結果を確認:
echo   - Microsoft Defender
echo   - Kaspersky
echo   - Avast
echo   - AVG
echo   - Avira
echo.
echo ■ 誤検知が報告されている場合:
echo   - 各ベンダーに誤検知報告を提出できます
echo   - Microsoft: https://www.microsoft.com/wdsi/filesubmission
echo   - Kaspersky: https://opentip.kaspersky.com/
echo.
echo ■ 結果の見方:
echo   - 70+ のアンチウイルスエンジンでスキャン
echo   - 0-3 検知: 誤検知の可能性が高い
echo   - 10+ 検知: 要確認（ただしPyInstallerは誤検知が多い）
echo.
pause

REM ブラウザを開く
start https://www.virustotal.com/gui/home/upload
