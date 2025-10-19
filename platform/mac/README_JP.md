# Pfft_maker - macOS版

Pfft_makerのmacOS用ビルド環境とセットアップ手順です。

## 📋 目次

1. [動作環境](#動作環境)
2. [セットアップ手順](#セットアップ手順)
3. [使用方法](#使用方法)
4. [ビルド手順](#ビルド手順)
5. [トラブルシューティング](#トラブルシューティング)

## 動作環境

- **OS**: macOS 10.15 (Catalina) 以降
- **Python**: Python 3.9 以降（推奨: Python 3.11）
- **依存関係**: requirements.txt を参照

## セットアップ手順

### 方法1: ソースコードから直接実行（開発環境）

1. **Python3のインストール**
   ```bash
   # Homebrewを使用してインストール
   brew install python@3.11
   ```

2. **依存パッケージのインストール**
   ```bash
   # プロジェクトルートディレクトリで
   pip3 install -r requirements.txt
   ```

3. **アプリケーションの起動**
   ```bash
   # プロジェクトルートディレクトリから
   platform/mac/run.sh
   ```

   または

   ```bash
   python3 run.py
   ```

### 方法2: アプリケーションバンドルからインストール（配布版）

1. **ビルド済みアプリの取得**
   - `dist/Pfft_maker.app` をダウンロードまたは自分でビルド

2. **インストール**
   - `Pfft_maker.app` を `/Applications` フォルダにコピー

3. **初回起動時の設定**
   - アプリを右クリック → 「開く」を選択
   - macOSのセキュリティ警告が表示された場合は「開く」をクリック
   - または「システム環境設定」→「セキュリティとプライバシー」から許可

## 使用方法

### 開発環境での実行

```bash
# プロジェクトルートディレクトリから
platform/mac/run.sh

# または直接実行
python3 run.py
```

### アプリケーションバンドルの実行

1. Finderから `Pfft_maker.app` をダブルクリック
2. または、ターミナルから:
   ```bash
   open -a Pfft_maker
   ```

## ビルド手順

配布用のアプリケーションバンドルを作成する場合：

### 1. 前提条件の確認

```bash
# PyInstallerのインストール
pip3 install pyinstaller
```

### 2. ビルドの実行

```bash
# プロジェクトルートディレクトリから実行
platform/mac/build_distribution.sh
```

ビルドが成功すると、`dist/Pfft_maker.app` が作成されます。

### 3. DMGファイルの作成（オプション）

配布用のDMGイメージを作成する場合：

```bash
# プロジェクトルートディレクトリから
hdiutil create -volname "Pfft_maker" -srcfolder dist -ov -format UDZO Pfft_maker.dmg
```

## トラブルシューティング

### Python3が見つからない

```bash
# Homebrewでインストール
brew install python@3.11

# PATHの確認
which python3
```

### PyQt6のインストールエラー

```bash
# Xcodeコマンドラインツールのインストール
xcode-select --install

# 再度インストール
pip3 install PyQt6
```

### アプリが起動しない（セキュリティエラー）

1. **Gatekeeper設定の変更**
   ```bash
   # 自分でビルドしたアプリの場合
   xattr -cr /Applications/Pfft_maker.app
   ```

2. **システム環境設定から許可**
   - 「システム環境設定」→「セキュリティとプライバシー」
   - 「一般」タブで「このまま開く」をクリック

### ビルドエラー

```bash
# ビルドキャッシュのクリア
rm -rf build dist __pycache__

# 再度ビルド（プロジェクトルートから）
platform/mac/build_distribution.sh
```

## ファイル構成

```
Pfft_maker/                    # プロジェクトルート
├── src/                       # 共通ソースコード
├── data/                      # データファイル
│   ├── prompts_library.csv   # プロンプトライブラリ
│   └── lora_library.csv      # LoRAライブラリ
├── resources/                 # 共通リソースファイル
├── requirements.txt           # Python依存パッケージ
├── run.py                     # 共通メインエントリーポイント
└── platform/
    └── mac/                   # macOS固有ファイル
        ├── run.sh             # 実行スクリプト（開発用）
        ├── build_distribution.sh    # ビルドスクリプト
        ├── Pfft_maker_mac.spec     # PyInstaller設定ファイル
        ├── README_JP.md       # このファイル
        └── SETUP.txt          # セットアップガイド
```

## 注意事項

### 個人情報の除外

このビルド環境では、以下の個人情報ファイルは自動的に除外されます：

- `data/settings.json` - 個人の設定
- `data/project_library.json` - 個人のプロジェクト
- `data/scene_library.json` - 個人のシーン
- `data/custom_prompts.json` - カスタムプロンプト
- `data/templates.json` - テンプレート
- `data/.api_keys.enc` - 暗号化されたAPIキー
- `data/.master_key` - マスターキー

配布版には `settings.default.json` と `prompts_library.csv` のみが含まれます。

## ライセンスとサポート

詳細は元のプロジェクトのドキュメントを参照してください。

- ドキュメント: `../docs/`
- チュートリアル: `../docs/TUTORIAL.md`
- ユーザーガイド: `../docs/USER_GUIDE.md`

## 開発者向け情報

### デバッグモード

開発時にコンソール出力を確認する場合：

```bash
# .specファイルのconsole設定を変更
# console=False -> console=True
```

### コード署名（オプション）

アプリケーションに署名する場合：

```bash
# Apple Developer証明書が必要
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/Pfft_maker.app
```

---

**作成日**: 2025-10-15
**対象バージョン**: Pfft_maker v1.x
