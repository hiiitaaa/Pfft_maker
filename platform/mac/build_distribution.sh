#!/bin/bash
# Pfft_maker 配布版ビルドスクリプト (macOS版)
# 個人情報を除外したクリーンなビルドを作成
#
# 使用方法: プロジェクトルートディレクトリから実行してください
#   platform/mac/build_distribution.sh

echo "========================================"
echo "Pfft_maker 配布版ビルド (macOS)"
echo "========================================"
echo ""

# 1. 個人情報ファイルの確認
echo "[1/5] 個人情報ファイルの確認..."
if [ -f "data/.api_keys.enc" ]; then
    echo "WARNING: APIキーファイルが存在します"
    echo "このファイルは配布版に含まれません"
fi
if [ -f "data/.master_key" ]; then
    echo "WARNING: マスターキーファイルが存在します"
    echo "このファイルは配布版に含まれません"
fi
if [ -f "data/settings.json" ]; then
    echo "INFO: settings.json が存在します"
    echo "配布版には settings.default.json のみが含まれます"
fi
echo ""

# 2. 既存のビルドをクリーンアップ
echo "[2/5] 既存のビルドをクリーンアップ..."
rm -rf build dist
echo "クリーンアップ完了"
echo ""

# 3. PyInstallerでビルド
echo "[3/5] PyInstallerでビルド中..."
echo "これには数分かかる場合があります..."
python3 -m PyInstaller --clean platform/mac/Pfft_maker_mac.spec

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: ビルドに失敗しました"
    echo "PyInstallerがインストールされているか確認してください:"
    echo "  pip3 install pyinstaller"
    exit 1
fi
echo "ビルド完了"
echo ""

# 4. 配布ファイルの検証
echo "[4/5] 配布ファイルの検証..."
if [ ! -d "dist/Pfft_maker.app" ]; then
    echo "ERROR: アプリケーションバンドルが見つかりません"
    exit 1
fi

# 個人情報ファイルが含まれていないか確認
if [ -f "dist/Pfft_maker.app/Contents/MacOS/data/.api_keys.enc" ]; then
    echo "ERROR: APIキーファイルが配布版に含まれています！"
    echo "ビルドを中止します"
    exit 1
fi
if [ -f "dist/Pfft_maker.app/Contents/MacOS/data/.master_key" ]; then
    echo "ERROR: マスターキーファイルが配布版に含まれています！"
    echo "ビルドを中止します"
    exit 1
fi
if [ -f "dist/Pfft_maker.app/Contents/MacOS/data/settings.json" ]; then
    echo "WARNING: settings.json が配布版に含まれています"
    echo "個人情報が含まれる可能性があります"
    rm "dist/Pfft_maker.app/Contents/MacOS/data/settings.json"
    echo "削除しました"
fi

echo "検証完了：個人情報ファイルは含まれていません"
echo ""

# 5. README の作成
echo "[5/5] README ファイルの作成..."
cat > "dist/README.txt" << 'EOF'
Pfft_maker - 配布版 (macOS)

セットアップ手順:
1. Pfft_maker.app を /Applications フォルダまたは好きな場所にコピーしてください
2. 初回起動時、macOSのセキュリティ設定により警告が表示される場合があります
   - 「システム環境設定」→「セキュリティとプライバシー」から許可してください
   - または、アプリを右クリック→「開く」で起動してください
3. 初回起動時にウェルカムダイアログが表示されます

動作環境:
- macOS 10.15 (Catalina) 以降
- インターネット接続（AI機能を使用する場合）

詳細はドキュメントを参照してください
EOF
echo "README.txt を作成しました"
echo ""

# 完了
echo "========================================"
echo "ビルド完了！"
echo "========================================"
echo ""
echo "配布ファイル: dist/Pfft_maker.app"
echo ""
echo "次のステップ:"
echo "1. dist/Pfft_maker.app を確認してください"
echo "2. 別のMacでテスト実行してください"
echo "3. DMGファイルを作成して配布してください"
echo "   例: hdiutil create -volname Pfft_maker -srcfolder dist -ov -format UDZO Pfft_maker.dmg"
echo ""
