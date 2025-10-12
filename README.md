# Pfft_maker

Stable Diffusion WebUI用のプロンプト管理ツール

## 概要

Pfft_makerは、Stable Diffusion WebUIのワイルドカードファイルを一元管理し、効率的にプロンプトを構築するためのツールです。

**主な機能**:
- ワイルドカードファイルの一元管理
- 日本語ラベル付きで検索・選択を容易化
- 30シーン分のプロンプトを効率的に構築
- 1行1プロンプト形式でファイル出力（Prompts from file形式）

## 開発状況

**Phase 4.1 完了** (2025-10-12)
- ✅ データモデル実装（Project, Scene, Block, Prompt）
- ✅ コアロジック実装（ワイルドカードパーサー、プロンプトビルダー）
- ✅ ファイル操作ユーティリティ
- ✅ 動作確認テスト

**Phase 4.2 予定**:
- UI実装（PyQt6）
- プロジェクト管理機能
- CSV/JSONハンドラー

## セットアップ

### 必須環境
- Python 3.11以上
- Windows 10/11

### インストール

```bash
# 依存関係のインストール
pip install -r requirements.txt
```

## 使用方法

### テスト実行

```bash
# データモデルのテスト
run_tests.bat
```

## ディレクトリ構成

```
Pfft_maker/
├── src/                      # ソースコード
│   ├── models/               # データモデル
│   ├── core/                 # コアロジック
│   ├── ui/                   # UI（未実装）
│   ├── ai/                   # AI連携（未実装）
│   └── utils/                # ユーティリティ
├── tests/                    # テストコード
├── docs/                     # ドキュメント
├── requirements.txt          # 依存関係
└── README.md                 # このファイル
```

## 設計方針

1. **コードの再利用**: 共通処理はユーティリティに集約
2. **軽量化**: 標準ライブラリ優先、必要最小限の外部ライブラリ
3. **効率的なフォルダ構成**: 責任を明確に分離
4. **ユーザーフロー重視**: 直感的で効率的な操作

## ドキュメント

- [機能要件定義書](requirements.md)
- [技術要件定義書](technical_requirements.md)
- [開発ガイド](docs/archive/CLAUDE.md)
- [進捗サマリー](PROGRESS_SUMMARY.md)

## ライセンス

（未定）

## 作者

Pfft_maker Development Team
