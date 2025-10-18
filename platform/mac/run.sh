#!/bin/bash
# Pfft_maker 起動スクリプト (macOS用)
# 開発環境で直接実行するためのスクリプト

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# Python3の確認
if ! command -v python3 &> /dev/null; then
    echo "エラー: Python3がインストールされていません"
    echo "Homebrewでインストールしてください:"
    echo "  brew install python@3.11"
    exit 1
fi

# 必要なパッケージの確認
echo "依存関係を確認中..."
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo "警告: 必要なパッケージがインストールされていません"
    echo "以下のコマンドでインストールしてください:"
    echo "  pip3 install -r requirements.txt"
    read -p "今すぐインストールしますか？ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip3 install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo "インストールに失敗しました"
            exit 1
        fi
    else
        echo "インストールせずに続行します"
    fi
fi

# Pfft_makerを起動
echo "Pfft_makerを起動中..."
python3 run.py
