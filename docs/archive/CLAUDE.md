# Pfft_maker 開発ガイド（Claude向け）

このドキュメントは、AIアシスタント（Claude）がPfft_makerの開発を支援する際のガイドラインです。

バージョン: 1.1
最終更新日: 2025-10-12

---

## 1. プロジェクト概要

### 1.1 このツールは何をするのか？

Pfft_makerは、**Stable Diffusion WebUI用のプロンプト管理ツール**です。

**主な役割**:
- ワイルドカードファイルを一元管理
- 日本語ラベル付きで検索・選択を容易化
- 30シーン分のプロンプトを効率的に構築
- 1行1プロンプト形式でファイル出力（Prompts from file形式）

**ユースケース**:
CG集制作者が、複数シーン（例: 30シーン = 30枚の画像）のプロンプトを管理・生成する。

---

## 2. 重要なドキュメント

開発前に必ず以下を読むこと:

1. **requirements.md** - 機能要件定義書（何を作るか）
2. **technical_requirements.md** - 技術要件定義書（どう作るか）
3. **requirements_discussion.md** - 要件検討メモ（背景・詳細議論）

特に `requirements.md` の「用語集」セクションは必読。

---

## 3. 技術スタック（確定版）

| カテゴリ | 技術 |
|---------|------|
| 言語 | Python 3.11+ |
| GUIフレームワーク | PyQt6 |
| データ管理 | pandas (CSV), json (プロジェクト) |
| ファイル監視 | watchdog |
| AI連携 | anthropic, requests (LM Studio) |
| セキュリティ | cryptography (Fernet), keyring |
| exe化 | PyInstaller |

**配布形式**: 単一exeファイル（30-50MB）

---

## 4. 開発の進め方

### 4.1 実装の優先順位

**Phase 1: コア機能（MVP）**
1. ✅ ワイルドカードパーサー実装
2. ✅ CSV管理機能
3. ✅ 基本UI（3カラムレイアウト）
4. ✅ シーン編集機能
5. ✅ プロジェクト保存・読み込み
6. ✅ 出力機能

**Phase 2: 高度な機能**
7. ⏳ ファイル監視・同期
8. ⏳ 検索機能
9. ⏳ 共通プロンプト機能
10. ⏳ テンプレート機能

**Phase 3: AI機能（オプション）**
11. ⏳ AI自動生成（Claude API）
12. ⏳ LM Studio連携
13. ⏳ APIキー管理

**Phase 4: 仕上げ**
14. ⏳ UI/UX改善
15. ⏳ exe化・配布準備
16. ⏳ ドキュメント整備

### 4.2 開発セットアップ

```bash
# 1. ディレクトリ作成
mkdir Pfft_maker
cd Pfft_maker

# 2. ディレクトリ構造作成
mkdir -p src/{ui,core,ai,models,data,utils,config}
mkdir -p resources/{icons,styles}
mkdir -p tests
mkdir -p docs

# 3. 仮想環境作成
python -m venv venv
venv\Scripts\activate  # Windows

# 4. 依存関係インストール
pip install PyQt6 pandas watchdog anthropic cryptography keyring chardet requests
pip install pytest black flake8 mypy  # 開発用

# 5. requirements.txt作成
pip freeze > requirements.txt
```

---

## 5. コーディング規約

### 5.1 基本ルール

- **PEP 8** 準拠
- **型ヒント** 必須（Python 3.11+）
- **Docstring** 必須（Google Style）
- **フォーマッター**: Black
- **最大行長**: 100文字

### 5.2 命名規則

```python
# クラス: PascalCase
class WildcardParser:
    pass

# 関数・変数: snake_case
def parse_file(file_path: Path) -> List[Prompt]:
    prompt_list = []
    return prompt_list

# 定数: UPPER_SNAKE_CASE
MAX_SCENES = 30
DEFAULT_WILDCARD_DIR = Path("E:/EasyReforge/Model/wildcards/")

# プライベートメソッド: _で開始
def _internal_method(self):
    pass
```

### 5.3 Docstring例

```python
def parse_file(self, file_path: Path) -> List[Prompt]:
    """ワイルドカードファイルをパースしてプロンプトリストを返す

    Args:
        file_path (Path): パース対象のファイルパス

    Returns:
        List[Prompt]: パースされたプロンプトのリスト

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        UnicodeDecodeError: エンコーディングエラーの場合

    Example:
        >>> parser = WildcardParser(Path("wildcards"))
        >>> prompts = parser.parse_file(Path("tipo_play.txt"))
        >>> len(prompts)
        90
    """
    pass
```

### 5.4 型ヒント

```python
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# 基本型
def get_name() -> str:
    return "Pfft_maker"

# Optional（None許可）
def get_label(prompt_id: str) -> Optional[str]:
    return None

# List, Dict
def get_prompts() -> List[Prompt]:
    return []

def get_categories() -> Dict[str, List[str]]:
    return {}

# Tuple
def extract_label(line: str) -> Tuple[str, str]:
    return ("label", "prompt")
```

---

## 6. 重要な設計判断

### 6.1 ワイルドカードパース

**4パターン対応（優先度順）**:
```python
# パターン1: 番号+テーブル型
r'^(\d+)→\s*\|\s*([^|]+?)\s*\|\s*`?([^|`]+?)`?\s*\|'

# パターン2: テーブル型
r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'

# パターン3: 番号付き型
r'^(\d+)→(.+)'

# パターン4: シンプル型（上記に該当しない場合）
```

**注意点**:
- BOM（`\uFEFF`）除去必須
- 空行スキップ
- エンコーディング自動検出（chardet使用）

---

### 6.2 固定テキスト vs ワイルドカード

**重要な区別**:

| 挿入方法 | 結果 | 動作 |
|---------|------|------|
| ファイル名の[+]クリック | `__tipo_play__` | Stable Diffusion実行時にランダム展開 |
| 個別プロンプトの[+]クリック | `clothed masturbation` | 常にこのプロンプトが使用される |

**UIでの明示**:
- 📌 固定テキスト
- 🎲 ワイルドカード

---

### 6.3 BREAK仕様

**バリデーションルール**:
- ❌ 連続BREAK禁止（BREAK → BREAK）
- ✅ 最初にBREAK可
- ✅ 最後にBREAK可

**実装**:
```python
def validate_blocks(blocks: List[Block]) -> bool:
    """ブロックのバリデーション"""
    for i in range(len(blocks) - 1):
        if blocks[i].type == BlockType.BREAK and blocks[i+1].type == BlockType.BREAK:
            return False  # 連続BREAK
    return True
```

---

### 6.4 1シーン = 1行 = 1画像

**重要**: Prompts from file機能の正しい理解

- 1行 = 1プロンプト = 1枚の画像生成
- 30シーン = 30行 = 30枚生成
- BREAKは文字列として1行内に含まれる

**出力例（output.txt）**:
```
clothed masturbation, school infirmary, __キャラ/SAYA__, BREAK, __posing/arm__, BREAK, masterpiece, best quality
deepthroat, classroom interior, __キャラ/SAYA__, BREAK, __posing/leg__, BREAK, masterpiece, best quality
exhibitionism, school rooftop, __キャラ/SAYA__, BREAK, standing, spread legs, BREAK, masterpiece, best quality
```

---

### 6.5 APIキー管理（セキュリティ重要）

**3層セキュリティ**:
1. Fernet（AES128）で暗号化
2. マスターキーはOSキーチェーン（Windows資格情報マネージャー）
3. ファイルパーミッション制限（600）

**実装チェックリスト**:
- ✅ APIキーは暗号化保存
- ✅ マスターキーはOSキーチェーン管理
- ✅ アプリ終了時にメモリクリア（`_api_key_cache = None`）
- ✅ ログにAPIキーを出力しない
- ✅ UI上ではマスク表示（`●●●●●●`）

---

## 7. 実装のヒント

### 7.1 ワイルドカードパーサー

```python
# core/wildcard_parser.py
import re
import chardet
from pathlib import Path

class WildcardParser:
    PATTERN_1 = r'^(\d+)→\s*\|\s*([^|]+?)\s*\|\s*`?([^|`]+?)`?\s*\|'
    PATTERN_2 = r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'
    PATTERN_3 = r'^(\d+)→(.+)'

    def parse_file(self, file_path: Path) -> List[Prompt]:
        """ファイルをパース"""
        # 1. エンコーディング検出
        encoding = self.detect_encoding(file_path)

        # 2. ファイル読み込み
        with file_path.open('r', encoding=encoding) as f:
            content = f.read()

        # 3. BOM除去
        content = content.lstrip('\ufeff')

        # 4. 行ごとにパース
        prompts = []
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line:  # 空行スキップ
                continue

            # パターンマッチング
            label, prompt = self.extract_label(line)
            prompts.append(Prompt(
                id=f"{file_path.stem}_{line_num}",
                source_file=str(file_path),
                line_number=line_num,
                label_ja=label,
                prompt=prompt,
                # ...
            ))
        return prompts

    def extract_label(self, line: str) -> Tuple[str, str]:
        """ラベルとプロンプトを抽出"""
        # パターン1: 番号+テーブル型
        match = re.match(self.PATTERN_1, line)
        if match:
            number, label, prompt = match.groups()
            return label.strip(), prompt.strip()

        # パターン2: テーブル型
        match = re.match(self.PATTERN_2, line)
        if match:
            label, prompt = match.groups()
            return label.strip(), prompt.strip()

        # パターン3: 番号付き型
        match = re.match(self.PATTERN_3, line)
        if match:
            number, prompt = match.groups()
            return prompt.strip(), prompt.strip()

        # パターン4: シンプル型
        return line, line

    def detect_encoding(self, file_path: Path) -> str:
        """エンコーディング検出"""
        with file_path.open('rb') as f:
            raw = f.read()
        result = chardet.detect(raw)
        return result['encoding'] or 'utf-8'
```

---

### 7.2 プロンプトビルダー

```python
# core/prompt_builder.py
class PromptBuilder:
    def build_scene_prompt(self, scene: Scene,
                          common_prompts: Dict[str, str] = None) -> str:
        """シーンの最終プロンプトを構築

        Args:
            scene: シーンオブジェクト
            common_prompts: 共通プロンプト（オプション）

        Returns:
            1行のプロンプト文字列（カンマ区切り）

        Example:
            Input blocks: [
                Block(type=FIXED_TEXT, content="clothed masturbation"),
                Block(type=BREAK),
                Block(type=WILDCARD, content="__posing/arm__")
            ]
            Output: "clothed masturbation, BREAK, __posing/arm__"
        """
        parts = []

        for block in scene.blocks:
            if block.type == BlockType.BREAK:
                parts.append("BREAK")
            else:
                # プロンプト内容をそのまま追加
                parts.append(block.content.strip())

        # カンマ + スペース区切りで結合
        prompt = ", ".join(parts)

        # 念のため連続カンマを削除
        import re
        prompt = re.sub(r',\s*,', ', ', prompt)

        return prompt
```

---

### 7.3 PyQt6 UI実装

```python
# ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pfft_maker")
        self.resize(1920, 1080)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # レイアウト
        layout = QHBoxLayout()

        # 3カラム
        self.library_panel = LibraryPanel()
        self.library_panel.setFixedWidth(600)

        self.scene_editor = SceneEditorPanel()
        self.scene_editor.setFixedWidth(750)

        self.preview_panel = PreviewPanel()
        self.preview_panel.setFixedWidth(550)

        layout.addWidget(self.library_panel)
        layout.addWidget(self.scene_editor)
        layout.addWidget(self.preview_panel)

        central_widget.setLayout(layout)

        # シグナル・スロット接続
        self.library_panel.prompt_selected.connect(
            self.scene_editor.insert_block
        )
        self.scene_editor.scene_changed.connect(
            self.preview_panel.update_preview
        )
```

---

### 7.4 ファイル監視

```python
# core/file_watcher.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WildcardFileWatcher(FileSystemEventHandler):
    def __init__(self, wildcard_dir: Path, callback):
        self.wildcard_dir = wildcard_dir
        self.callback = callback

    def on_modified(self, event):
        """ファイル変更時"""
        if not event.is_directory and event.src_path.endswith('.txt'):
            self.callback(Path(event.src_path))

    def start(self):
        """監視開始"""
        observer = Observer()
        observer.schedule(self, str(self.wildcard_dir), recursive=True)
        observer.start()
        return observer
```

---

## 8. トラブルシューティング

### 8.1 よくある問題

#### 問題1: PyQt6のインストールエラー
```bash
# 解決策
pip install --upgrade pip
pip install PyQt6
```

#### 問題2: exe化時にアイコンが見つからない
```python
# build.specでdatasを正しく設定
datas=[('resources', 'resources')],
```

#### 問題3: APIキーが保存できない
```bash
# keyringが正しくインストールされているか確認
pip install keyring
```

#### 問題4: ワイルドカードファイルが読み込めない
- BOM除去を確認
- エンコーディング検出（chardet）を使用
- 空行スキップを実装

---

### 8.2 デバッグのヒント

```python
# ログ出力
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Parsing file: {file_path}")

# PyQt6のデバッグ
from PyQt6.QtCore import qDebug
qDebug("Button clicked")

# pandas DataFrame確認
df = pd.read_csv("prompts_library.csv")
print(df.head())
print(df.info())
```

---

## 9. テスト

### 9.1 ユニットテスト例

```python
# tests/test_wildcard_parser.py
import pytest
from pathlib import Path
from src.core.wildcard_parser import WildcardParser

def test_parse_table_type():
    """テーブル型のパース"""
    parser = WildcardParser(Path("tests/fixtures"))
    line = "| 教室 | classroom interior |"
    label, prompt = parser.extract_label(line)
    assert label == "教室"
    assert prompt == "classroom interior"

def test_parse_numbered_type():
    """番号付き型のパース"""
    parser = WildcardParser(Path("tests/fixtures"))
    line = "14→clothed masturbation"
    label, prompt = parser.extract_label(line)
    assert label == "clothed masturbation"

def test_bom_removal():
    """BOM除去のテスト"""
    content = "\ufefftest content"
    cleaned = content.lstrip('\ufeff')
    assert cleaned == "test content"
```

---

## 10. よくある質問（FAQ）

### Q1: なぜPyQt6なのか？
**A**: exe化が容易で、配布サイズが適切（30-50MB）。複雑な3カラムUIに対応可能。

### Q2: なぜCSVでプロンプト管理？
**A**: pandasで高速検索・フィルタリングが可能。SQLiteより軽量でメンテナンスが容易。

### Q3: AI自動生成は必須機能？
**A**: いいえ、オプション機能。手動ラベル付けでも動作する。

### Q4: ワイルドカード形式とは？
**A**: `__filename__` 形式。Stable Diffusionの「Dynamic Prompts」拡張が実行時にランダム展開する。

### Q5: BREAKとは？
**A**: プロンプトブロックの区切り。Stable Diffusionで異なる重み付けを行うために使用。

### Q6: 30シーンの制限理由は？
**A**: UI設計上の制約。タブ表示が現実的な範囲。拡張は可能だが、Phase 1では30シーン固定。

---

## 11. 開発時の注意事項

### 11.1 絶対にやってはいけないこと

- ❌ APIキーを平文でログ出力
- ❌ 暗号化なしでAPIキーをファイル保存
- ❌ BOM除去を忘れる
- ❌ 連続BREAKを許可する
- ❌ ワイルドカード形式と固定テキストを混同する

### 11.2 推奨事項

- ✅ 型ヒントを必ず付ける
- ✅ Docstringを書く
- ✅ ログを適切に出力
- ✅ エラーハンドリングを忘れない
- ✅ ユニットテストを書く
- ✅ requirements.mdを参照しながら実装

---

## 12. 次のステップ

### Phase 1: コア機能実装

**実装順序**:
1. データモデル（`models/`）
2. ワイルドカードパーサー（`core/wildcard_parser.py`）
3. CSV管理（`data/csv_handler.py`）
4. 基本UI（`ui/main_window.py`, `ui/*_panel.py`）
5. プロンプトビルダー（`core/prompt_builder.py`）
6. プロジェクト管理（`core/project_manager.py`）
7. 出力機能

**目標**: 手動でプロンプトを組み立て→出力できる状態

---

## 13. 参考リソース

### 公式ドキュメント
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [pandas Documentation](https://pandas.pydata.org/docs/)
- [watchdog Documentation](https://python-watchdog.readthedocs.io/)
- [anthropic SDK](https://github.com/anthropics/anthropic-sdk-python)

### PyInstaller
- [PyInstaller Manual](https://pyinstaller.org/en/stable/)
- [spec file options](https://pyinstaller.org/en/stable/spec-files.html)

---

## 14. 変更履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| 1.1 | 2025-10-12 | 仕様確定反映版<br>- プロンプトビルダー実装例更新（BREAK処理ロジック明確化）<br>- ワイルドカード形式：サブディレクトリ対応 |
| 1.0 | 2025-01-15 | 初版作成 |

---

**このドキュメントを読んだら、実装を開始してください。**

**まず何をすべきか？**
1. `src/models/` のデータモデルを実装
2. `src/core/wildcard_parser.py` を実装
3. `tests/test_wildcard_parser.py` でテスト

Good luck! 🚀
