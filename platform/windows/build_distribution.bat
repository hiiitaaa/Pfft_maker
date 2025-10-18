@echo off
REM Pfft_maker 配布版ビルドスクリプト (Windows)
REM 個人情報を除外したクリーンなビルドを作成
REM
REM 使用方法: プロジェクトルートディレクトリから実行してください
REM   platform\windows\build_distribution.bat

echo ========================================
echo Pfft_maker 配布版ビルド (Windows)
echo ========================================
echo.

REM 1. 個人情報ファイルの確認
echo [1/5] 個人情報ファイルの確認...
if exist "data\.api_keys.enc" (
    echo WARNING: APIキーファイルが存在します
    echo このファイルは配布版に含まれません
)
if exist "data\.master_key" (
    echo WARNING: マスターキーファイルが存在します
    echo このファイルは配布版に含まれません
)
if exist "data\settings.json" (
    echo INFO: settings.json が存在します
    echo 配布版には settings.default.json のみが含まれます
)
echo.

REM 2. 既存のビルドをクリーンアップ
echo [2/5] 既存のビルドをクリーンアップ...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo クリーンアップ完了
echo.

REM 3. PyInstallerでビルド
echo [3/5] PyInstallerでビルド中...
echo これには数分かかる場合があります...
python -m PyInstaller --clean platform\windows\Pfft_maker.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: ビルドに失敗しました
    echo PyInstallerがインストールされているか確認してください:
    echo   pip install pyinstaller
    pause
    exit /b 1
)
echo ビルド完了
echo.

REM 4. 配布ファイルの検証
echo [4/5] 配布ファイルの検証...
if not exist "dist\Pfft_maker\Pfft_maker.exe" (
    echo ERROR: EXEファイルが見つかりません
    pause
    exit /b 1
)

REM 個人情報ファイルが含まれていないか確認
if exist "dist\Pfft_maker\data\.api_keys.enc" (
    echo ERROR: APIキーファイルが配布版に含まれています！
    echo ビルドを中止します
    pause
    exit /b 1
)
if exist "dist\Pfft_maker\data\.master_key" (
    echo ERROR: マスターキーファイルが配布版に含まれています！
    echo ビルドを中止します
    pause
    exit /b 1
)
if exist "dist\Pfft_maker\data\settings.json" (
    echo WARNING: settings.json が配布版に含まれています
    echo 個人情報が含まれる可能性があります
    del "dist\Pfft_maker\data\settings.json"
    echo 削除しました
)

echo 検証完了：個人情報ファイルは含まれていません
echo.

REM 5. README の作成
echo [5/5] README ファイルの作成...
(
echo Pfft_maker - 配布版
echo.
echo セットアップ手順:
echo 1. このフォルダ全体を好きな場所にコピーしてください
echo 2. Pfft_maker.exe を実行してください
echo 3. 初回起動時にウェルカムダイアログが表示されます
echo.
echo 動作環境:
echo - Windows 10/11 64bit
echo - インターネット接続（AI機能を使用する場合）
echo.
echo ■ セキュリティ警告について
echo このアプリケーションはPyInstallerでビルドされているため、
echo 一部のアンチウイルスソフトで誤検知される場合があります。
echo.
echo - これは「偽陽性（False Positive）」です
echo - ソースコードは公開されています
echo - 個人情報やAPIキーは一切含まれていません
echo - UPX圧縮を無効化し、製品情報を埋め込んでいます
echo.
echo 安全性を確認するには:
echo 1. VirusTotal でスキャン結果を確認（URLは配布ページに記載）
echo 2. Windows Defenderの除外設定に追加
echo 3. ソースコードから自身でビルド
echo.
echo 詳細はドキュメントを参照してください
) > "dist\Pfft_maker\README.txt"
echo README.txt を作成しました
echo.

REM 完了
echo ========================================
echo ビルド完了！
echo ========================================
echo.
echo 配布ファイル: dist\Pfft_maker\
echo.
echo 次のステップ:
echo 1. dist\Pfft_maker フォルダを確認してください
echo 2. 別のPCでテスト実行してください
echo 3. ZIP圧縮して配布してください
echo.
pause
