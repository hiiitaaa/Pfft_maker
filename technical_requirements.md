# Pfft_maker 技術要件定義書

バージョン: 1.1
最終更新日: 2025-10-12
ステータス: 確定版（仕様確定反映）

---

## 1. 技術スタック

### 1.1 コア技術
- **言語**: Python 3.11+
- **GUIフレームワーク**: PyQt6 (6.6+)
- **パッケージ管理**: pip + requirements.txt
- **exe化ツール**: PyInstaller 6.0+

### 1.2 主要ライブラリ

#### GUI関連
```
PyQt6==6.6.1
PyQt6-Qt6==6.6.1
```

#### データ処理
```
pandas==2.1.4          # CSV/データ管理
chardet==5.2.0         # 文字エンコーディング検出（BOM対応）
```

#### ファイル監視
```
watchdog==4.0.0        # リアルタイムファイル監視
```

#### AI API連携
```
anthropic==0.8.1       # Claude API SDK
requests==2.31.0       # LM Studio HTTP通信
```

#### セキュリティ
```
cryptography==41.0.7   # Fernet暗号化（AES128ベース）
keyring==24.3.0        # OS資格情報管理
```

#### 標準ライブラリ（追加インストール不要）
- `json` - プロジェクトファイル管理
- `pathlib` - パス操作
- `re` - 正規表現（ワイルドカードパース）
- `csv` - CSV読み書き
- `os` - ファイル操作
- `datetime` - 日時管理
- `typing` - 型ヒント

---

## 2. 開発環境

### 2.1 必須環境
- **OS**: Windows 10/11（開発・テスト）
- **Python**: 3.11.x（3.11.7推奨）
- **エディタ**: VS Code（推奨） / PyCharm

### 2.2 推奨VS Code拡張機能
- Python (Microsoft)
- Pylance (Microsoft)
- PyQt6 Snippets
- Python Docstring Generator

### 2.3 開発用追加ライブラリ
```
pytest==7.4.3          # ユニットテスト
black==23.12.1         # コードフォーマッター
flake8==7.0.0          # リンター
mypy==1.8.0            # 型チェッカー
```

---

## 3. アーキテクチャ設計

### 3.1 ディレクトリ構造

```
Pfft_maker/
├── src/
│   ├── main.py                      # エントリーポイント
│   │
│   ├── ui/                          # UI層
│   │   ├── __init__.py
│   │   ├── main_window.py           # メインウィンドウ (QMainWindow)
│   │   ├── library_panel.py         # ライブラリパネル (QWidget)
│   │   ├── scene_editor_panel.py    # シーン編集パネル (QWidget)
│   │   ├── preview_panel.py         # プレビューパネル (QWidget)
│   │   ├── dialogs/                 # ダイアログ
│   │   │   ├── project_settings.py  # プロジェクト設定ダイアログ
│   │   │   ├── ai_settings.py       # AI設定ダイアログ
│   │   │   ├── export_dialog.py     # 出力設定ダイアログ
│   │   │   └── template_dialog.py   # テンプレート選択ダイアログ
│   │   └── widgets/                 # カスタムウィジェット
│   │       ├── block_widget.py      # ブロック表示ウィジェット
│   │       ├── prompt_item.py       # プロンプトアイテム
│   │       └── scene_tab.py         # シーンタブ
│   │
│   ├── core/                        # ビジネスロジック層
│   │   ├── __init__.py
│   │   ├── wildcard_parser.py       # ワイルドカードパーサー
│   │   ├── project_manager.py       # プロジェクト管理
│   │   ├── prompt_builder.py        # プロンプト構築
│   │   ├── file_watcher.py          # ファイル監視
│   │   ├── library_manager.py       # ライブラリ管理
│   │   └── search_engine.py         # 検索エンジン
│   │
│   ├── ai/                          # AI機能層
│   │   ├── __init__.py
│   │   ├── label_generator.py       # ラベル・タグ自動生成
│   │   ├── api_manager.py           # APIキー管理
│   │   ├── claude_client.py         # Claude API クライアント
│   │   └── lm_studio_client.py      # LM Studio クライアント
│   │
│   ├── models/                      # データモデル層
│   │   ├── __init__.py
│   │   ├── project.py               # プロジェクトモデル
│   │   ├── scene.py                 # シーンモデル
│   │   ├── block.py                 # ブロックモデル
│   │   ├── prompt.py                # プロンプトモデル
│   │   └── category.py              # カテゴリモデル
│   │
│   ├── data/                        # データ層
│   │   ├── __init__.py
│   │   ├── csv_handler.py           # CSV読み書き
│   │   ├── json_handler.py          # JSON読み書き
│   │   └── prompts_library.csv      # プロンプトライブラリ（初期は空）
│   │
│   ├── utils/                       # ユーティリティ層
│   │   ├── __init__.py
│   │   ├── logger.py                # ログ管理
│   │   ├── encryption.py            # 暗号化ユーティリティ
│   │   ├── file_utils.py            # ファイル操作ユーティリティ
│   │   └── constants.py             # 定数定義
│   │
│   └── config/                      # 設定層
│       ├── __init__.py
│       ├── settings.py              # 設定管理
│       └── default_config.json      # デフォルト設定
│
├── resources/                       # リソース
│   ├── icons/                       # アイコン素材
│   │   ├── app.ico                  # アプリアイコン
│   │   ├── folder.png               # フォルダアイコン
│   │   ├── fixed.png                # 固定テキストアイコン (📌)
│   │   ├── wildcard.png             # ワイルドカードアイコン (🎲)
│   │   └── lock.png                 # ロックアイコン (🔒)
│   └── styles/                      # スタイルシート
│       └── default.qss              # Qt Stylesheet
│
├── tests/                           # テストコード
│   ├── __init__.py
│   ├── test_wildcard_parser.py
│   ├── test_prompt_builder.py
│   ├── test_project_manager.py
│   └── test_ai_generator.py
│
├── docs/                            # ドキュメント
│   ├── requirements.md              # 機能要件定義書
│   ├── technical_requirements.md   # 技術要件定義書（本書）
│   └── CLAUDE.md                    # 開発ガイド
│
├── .gitignore
├── requirements.txt                 # 本番環境用
├── requirements-dev.txt             # 開発環境用
├── build.spec                       # PyInstaller設定
├── README.md
└── LICENSE
```

---

### 3.2 レイヤー構成

```
┌─────────────────────────────────────┐
│         UI Layer (PyQt6)            │  ← ユーザー操作、画面表示
│  main_window, panels, dialogs       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Business Logic Layer           │  ← ビジネスロジック
│  wildcard_parser, project_manager,  │
│  prompt_builder, file_watcher       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Data Model Layer              │  ← データモデル
│  Project, Scene, Block, Prompt      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Data Access Layer            │  ← データ永続化
│  csv_handler, json_handler          │
└─────────────────────────────────────┘
```

**依存関係のルール**:
- 上位レイヤーは下位レイヤーに依存できる
- 下位レイヤーは上位レイヤーに依存してはならない
- 各レイヤーは同じレイヤー内で依存できる

---

### 3.3 主要クラス設計

#### 3.3.1 データモデル

```python
# models/project.py
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime

@dataclass
class Project:
    """プロジェクトモデル"""
    name: str
    created_date: datetime
    last_modified: datetime
    description: str = ""
    scenes: List['Scene'] = field(default_factory=list)
    common_prompts: Dict[str, str] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """JSON出力用"""
        pass

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """JSON読み込み用"""
        pass


# models/scene.py
@dataclass
class Scene:
    """シーンモデル"""
    scene_id: int
    scene_name: str
    is_completed: bool = False  # 手動マーク方式: ユーザーがUIでチェックボックスで指定
    blocks: List['Block'] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)

    def get_final_prompt(self) -> str:
        """最終プロンプトを生成

        Returns:
            1行のプロンプト文字列（カンマ区切り、BREAK処理済み）

        Note:
            - BREAK前後の処理はPromptBuilderが担当
            - ワイルドカード形式（__filename__）はそのまま出力
        """
        pass


# models/block.py
from enum import Enum

class BlockType(Enum):
    """ブロックタイプ"""
    FIXED_TEXT = "fixed_text"
    WILDCARD = "wildcard"
    BREAK = "break"
    COMMON = "common"

@dataclass
class Block:
    """ブロックモデル"""
    block_id: int
    type: BlockType
    content: str
    source: Dict = field(default_factory=dict)
    is_common: bool = False


# models/prompt.py
@dataclass
class Prompt:
    """プロンプトモデル"""
    id: str
    source_file: str
    original_line_number: int | None  # 元ファイルの行番号（**参考情報**、元ファイル変更時は無効）
    original_number: int | None  # 元の番号（`14→`の14、**プロンプト照合に使用**）
    label_ja: str
    label_en: str
    prompt: str
    category: str
    tags: List[str]
    created_date: datetime
    last_used: datetime | None
    label_source: str  # "auto_extract", "ai_generated", "manual"

    # 照合ロジック:
    # 1. original_numberで照合（優先）
    # 2. プロンプト内容の類似度（90%以上）
    # 3. 新規エントリとして追加
```

---

#### 3.3.2 ビジネスロジック

```python
# core/wildcard_parser.py
import re
from pathlib import Path
from typing import List, Dict
import chardet

class WildcardParser:
    """ワイルドカードファイルパーサー"""

    # パターン定義（優先度順）
    PATTERN_1 = r'^(\d+)→\s*\|\s*([^|]+?)\s*\|\s*`?([^|`]+?)`?\s*\|'  # 番号+テーブル型
    PATTERN_2 = r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'                # テーブル型
    PATTERN_3 = r'^(\d+)→(.+)'                                        # 番号付き型
    # パターン4: 上記に該当しない場合、行全体（シンプル型）

    def __init__(self, wildcard_dir: Path):
        self.wildcard_dir = wildcard_dir
        self.prompts: List[Prompt] = []

    def scan_directory(self) -> List[Prompt]:
        """ディレクトリを再帰的にスキャン"""
        pass

    def parse_file(self, file_path: Path) -> List[Prompt]:
        """ファイルをパース"""
        # 1. BOM除去
        # 2. 空行スキップ
        # 3. パターンマッチング
        # 4. Promptオブジェクト生成
        pass

    def detect_encoding(self, file_path: Path) -> str:
        """文字エンコーディングを検出（フォールバック付き）

        優先エンコーディングを順に試行し、すべて失敗した場合はchardetで検出する。

        Args:
            file_path: 対象ファイルパス

        Returns:
            検出されたエンコーディング名（例: 'utf-8', 'shift_jis'）

        Note:
            - 短いファイルや日本語ファイルでのchardet誤判定を防ぐため、
              一般的なエンコーディングを優先的に試行する
            - デコードエラー時は errors='replace' で読み込む
        """
        import logging
        logger = logging.getLogger(__name__)

        # 試行順序（優先度順）
        encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932']

        # バイナリ読み込み
        with file_path.open('rb') as f:
            raw = f.read()

        # 優先エンコーディングで順次試行
        for encoding in encodings:
            try:
                raw.decode(encoding)
                logger.info(f"Detected encoding: {encoding} for {file_path.name}")
                return encoding
            except UnicodeDecodeError:
                continue

        # すべて失敗した場合: chardetで検出
        detected = chardet.detect(raw)
        encoding = detected['encoding'] or 'utf-8'
        confidence = detected.get('confidence', 0)

        logger.warning(
            f"Fallback to chardet: {encoding} (confidence: {confidence:.2f}) "
            f"for {file_path.name}"
        )

        return encoding

    def extract_label(self, line: str) -> tuple:
        """ラベルとプロンプトを抽出"""
        pass


# core/project_manager.py
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ProjectManager:
    """プロジェクト管理"""

    def __init__(self):
        self.current_project: Project | None = None
        self.project_path: Path | None = None
        self.auto_save_timer = None

    def create_new_project(self, name: str) -> Project:
        """新規プロジェクト作成"""
        pass

    def save_project(self, file_path: Path) -> bool:
        """プロジェクトを保存"""
        # 1. JSON形式でシリアライズ
        # 2. ファイル書き込み
        # 3. バックアップ作成
        pass

    def load_project(self, file_path: Path) -> Project:
        """プロジェクトを読み込み"""
        pass

    def create_backup(self, file_path: Path):
        """世代バックアップ作成（最大5世代）"""
        pass

    def start_auto_save(self):
        """自動保存開始（30秒間隔）"""
        pass

    def auto_save(self):
        """自動保存（エラーハンドリング付き）

        一時ファイル方式でプロジェクトを安全に保存する。
        ネットワークドライブ、書き込みエラー、ファイルロック等に対応。

        処理フロー:
            1. 一時ファイル（.pfft.tmp）に保存
            2. 保存成功 → 本番ファイルに上書き（アトミック操作）
            3. 保存失敗 → エラーログ記録 + UI通知

        Example:
            >>> manager = ProjectManager()
            >>> manager.project_path = Path("E:/projects/学園メイド.pfft")
            >>> manager.auto_save()
            # 成功時: INFO: Auto-saved successfully
            # 失敗時: ERROR: Auto-save failed: [Errno 13] Permission denied

        Note:
            - Path.replace()はWindowsでアトミックな上書きを保証
            - 一時ファイルは保存成功時に自動削除される
            - エラー時は一時ファイルが残る場合がある（次回保存時に上書き）

        Raises:
            Exception: ファイル書き込みエラー時（内部でキャッチしてログ記録）
        """
        if not self.project_path or not self.current_project:
            logger.warning("No project loaded, skipping auto-save")
            return

        try:
            # 1. 一時ファイルに保存
            temp_path = self.project_path.with_suffix('.pfft.tmp')
            self._save_to_file(temp_path)

            # 2. 成功したら本番ファイルに上書き（アトミック操作）
            temp_path.replace(self.project_path)

            logger.info("Auto-saved successfully")

        except PermissionError as e:
            logger.error(f"Auto-save failed (Permission denied): {e}")
            self._show_notification(
                "自動保存に失敗しました",
                f"理由: ファイルへのアクセス権限がありません\n\n手動保存を推奨します。",
                error=True
            )

        except OSError as e:
            logger.error(f"Auto-save failed (OS error): {e}")
            self._show_notification(
                "自動保存に失敗しました",
                f"理由: ネットワークドライブへの書き込みがタイムアウトしました\n\n手動保存を推奨します。",
                error=True
            )

        except Exception as e:
            logger.error(f"Auto-save failed (unexpected error): {e}")
            self._show_notification(
                "自動保存に失敗しました",
                f"理由: 予期しないエラーが発生しました\n\n手動保存を推奨します。",
                error=True
            )

    def _save_to_file(self, file_path: Path):
        """プロジェクトをファイルに保存（内部メソッド）

        Args:
            file_path: 保存先ファイルパス

        Raises:
            Exception: ファイル書き込みエラー
        """
        # JSONシリアライズ＆ファイル書き込み
        # 実装は save_project() と共通化
        pass

    def _show_notification(self, title: str, message: str, error: bool = False):
        """UI通知バナーを表示（内部メソッド）

        Args:
            title: 通知タイトル
            message: 通知メッセージ
            error: エラー通知かどうか

        Note:
            実際の実装ではUIレイヤーのNotificationManagerを呼び出す
        """
        # UIレイヤーに通知リクエスト送信
        # 例: self.ui_controller.show_notification(title, message, error)
        pass

    def delete_scene(self, project: Project, scene_id: int):
        """シーンを削除（番号付け直し方式）

        Args:
            project: プロジェクトオブジェクト
            scene_id: 削除するシーンのID（1から始まる番号）

        Note:
            削除後、以降のシーンのscene_idを自動的に詰める
            例: シーン3削除 → [1,2,4,5] → [1,2,3,4]
        """
        # シーンを削除
        project.scenes = [s for s in project.scenes if s.scene_id != scene_id]

        # 以降のシーンの番号を詰める
        for i, scene in enumerate(project.scenes, start=1):
            scene.scene_id = i


# core/prompt_builder.py
class PromptBuilder:
    """プロンプト構築"""

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
                Block(type=WILDCARD, content="__posing/arm__"),
                Block(type=BREAK),
                Block(type=FIXED_TEXT, content="masterpiece, best quality")
            ]
            Output: "clothed masturbation, BREAK, __posing/arm__, BREAK, masterpiece, best quality"
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

    def build_all_prompts(self, project: Project) -> List[str]:
        """全シーンのプロンプトを構築"""
        pass

    def validate_blocks(self, blocks: List[Block]) -> bool:
        """ブロックのバリデーション"""
        # 連続BREAK禁止チェック
        pass


# core/file_watcher.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WildcardFileWatcher(FileSystemEventHandler):
    """ワイルドカードファイル監視"""

    def __init__(self, wildcard_dir: Path, callback):
        self.wildcard_dir = wildcard_dir
        self.callback = callback

    def on_modified(self, event):
        """ファイル変更時"""
        if event.src_path.endswith('.txt'):
            self.callback(event.src_path)

    def start(self):
        """監視開始"""
        observer = Observer()
        observer.schedule(self, self.wildcard_dir, recursive=True)
        observer.start()


# core/library_manager.py
import pandas as pd

class LibraryManager:
    """ライブラリ管理"""

    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.df: pd.DataFrame | None = None

    def load_library(self) -> pd.DataFrame:
        """CSVからライブラリを読み込み"""
        pass

    def save_library(self, df: pd.DataFrame):
        """ライブラリをCSVに保存"""
        pass

    def add_prompt(self, prompt: Prompt):
        """プロンプトを追加"""
        pass

    def update_prompt(self, prompt_id: str, updates: Dict):
        """プロンプトを更新"""
        pass

    def search(self, query: str, category: str = None) -> List[Prompt]:
        """検索"""
        # 全文検索（label_ja, label_en, prompt, tags, source_file）
        pass

    def get_by_category(self, category: str) -> List[Prompt]:
        """カテゴリでフィルタ"""
        pass


# core/search_engine.py
class SearchEngine:
    """検索エンジン"""

    def search(self, query: str, prompts: List[Prompt],
              case_sensitive: bool = False,
              multi_keyword: bool = False) -> List[Prompt]:
        """シンプル全文検索"""
        # 部分一致検索
        # 複数キーワード対応（AND検索）
        pass
```

---

#### 3.3.3 AI機能

```python
# ai/label_generator.py
from typing import List, Tuple

class LabelGenerator:
    """ラベル・タグ自動生成"""

    def __init__(self, api_manager: 'APIManager'):
        self.api_manager = api_manager

    def generate_labels_batch(self, prompts: List[Prompt]) -> List[Tuple[str, str]]:
        """一括ラベル生成"""
        # Claude API / LM Studio / 辞書ベースのフォールバック
        pass

    def generate_label_claude(self, prompt_text: str) -> Tuple[str, str]:
        """Claude APIでラベル生成"""
        pass

    def generate_label_lm_studio(self, prompt_text: str) -> Tuple[str, str]:
        """LM Studioでラベル生成"""
        pass

    def generate_tags_auto(self, prompt_text: str) -> List[str]:
        """自動タグ生成（単語分割）

        シンプルな単語分割でタグを生成（AI不要、常時動作）

        Args:
            prompt_text: "school_infirmary, beds with curtain dividers"

        Returns:
            ["school", "infirmary", "beds", "with", "curtain", "dividers"]

        Note:
            - Phase 1では日本語の形態素解析は実装しない
            - AI生成で日本語タグを補完することを推奨
        """
        import re

        # 1. 小文字化
        text = prompt_text.lower()

        # 2. カンマ、アンダースコア、スペースで分割
        words = re.split(r'[,_\s]+', text)

        # 3. フィルタリング
        tags = [w.strip() for w in words
                if w.strip() and len(w.strip()) > 1 and w.strip().isalnum()]

        # 4. 重複削除（順序保持）
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        # 5. 最大10タグ
        return unique_tags[:10]

    def generate_label_dict_based(self, prompt_text: str) -> Tuple[str, str]:
        """辞書ベースでラベル生成

        タグ生成のみ実行。ラベルは空文字列を返す。

        Returns:
            (label_ja, label_en) の空文字列タプルと、タグリスト
        """
        tags = self.generate_tags_auto(prompt_text)
        return ("", ""), tags


# ai/api_manager.py
from cryptography.fernet import Fernet
import keyring

class APIManager:
    """APIキー管理"""

    APP_NAME = "Pfft_maker"

    def __init__(self):
        self._api_key_cache = None
        self._fernet = self._get_or_create_fernet()

    def set_api_key(self, api_key: str):
        """APIキーを保存（暗号化）"""
        # 1. Fernetで暗号化
        # 2. ファイルに保存
        # 3. マスターキーをOSキーチェーンに保存
        pass

    def get_api_key(self) -> str:
        """APIキーを取得（復号化）"""
        if not self._api_key_cache:
            self._api_key_cache = self._decrypt_from_file()
        return self._api_key_cache

    def test_connection(self) -> bool:
        """接続テスト"""
        pass

    def clear_cache(self):
        """メモリクリア（アプリ終了時）"""
        self._api_key_cache = None

    def _get_or_create_fernet(self) -> Fernet:
        """Fernetインスタンス取得"""
        master_key = keyring.get_password(self.APP_NAME, "master_key")
        if not master_key:
            master_key = Fernet.generate_key().decode()
            keyring.set_password(self.APP_NAME, "master_key", master_key)
        return Fernet(master_key.encode())


# ai/claude_client.py
from anthropic import Anthropic

class ClaudeClient:
    """Claude API クライアント"""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def generate_label(self, prompt_text: str) -> str:
        """ラベル生成"""
        # Claude Haiku使用（コスト削減）
        pass


# ai/lm_studio_client.py
import requests

class LMStudioClient:
    """LM Studio クライアント"""

    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url

    def generate_label(self, prompt_text: str) -> str:
        """ラベル生成"""
        # HTTP POST
        pass

    def test_connection(self) -> bool:
        """接続テスト"""
        pass
```

---

#### 3.3.4 UI層

```python
# ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout

class MainWindow(QMainWindow):
    """メインウィンドウ"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pfft_maker")
        self.resize(1920, 1080)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 3カラムレイアウト
        layout = QHBoxLayout()

        # 左: ライブラリパネル (600px)
        self.library_panel = LibraryPanel()
        self.library_panel.setFixedWidth(600)

        # 中央: シーン編集パネル (750px)
        self.scene_editor = SceneEditorPanel()
        self.scene_editor.setFixedWidth(750)

        # 右: プレビューパネル (550px)
        self.preview_panel = PreviewPanel()
        self.preview_panel.setFixedWidth(550)

        layout.addWidget(self.library_panel)
        layout.addWidget(self.scene_editor)
        layout.addWidget(self.preview_panel)

        central_widget.setLayout(layout)

        # メニューバー・ツールバー
        self._create_menu_bar()
        self._create_toolbar()

        # シグナル・スロット接続
        self._connect_signals()

    def _create_menu_bar(self):
        """メニューバー作成"""
        pass

    def _create_toolbar(self):
        """ツールバー作成"""
        pass

    def _connect_signals(self):
        """シグナル・スロット接続"""
        # library_panel.prompt_selected → scene_editor.insert_block
        pass


# ui/library_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QLineEdit, QComboBox
from PyQt6.QtCore import QTimer

class LibraryPanel(QWidget):
    """ライブラリパネル"""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # 検索バー
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 検索...")

        # 検索デバウンスタイマー
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)  # 1回のみ発火
        self.search_timer.timeout.connect(self._execute_search)

        # 検索バーのテキスト変更時にデバウンス処理を開始
        self.search_bar.textChanged.connect(self._on_search_input)

        # カテゴリフィルタ
        self.category_filter = QComboBox()

        # ツリー表示
        self.tree = QTreeWidget()

        layout.addWidget(self.search_bar)
        layout.addWidget(self.category_filter)
        layout.addWidget(self.tree)

        self.setLayout(layout)

    def load_library(self, prompts: List[Prompt]):
        """ライブラリを読み込み"""
        pass

    def _on_search_input(self, text: str):
        """入力後300ms待機してから検索実行（デバウンス処理）

        Note:
            ユーザーが入力を続けている間は検索を実行せず、
            入力が止まってから300ms後に検索を実行する。
            これにより、UIの重さを防ぎ、快適な検索体験を提供する。
        """
        # 既存のタイマーを停止
        self.search_timer.stop()
        # 300ms後に検索実行
        self.search_timer.start(300)

    def _execute_search(self):
        """実際の検索実行

        Note:
            デバウンス処理によって、入力後300ms経過後に呼び出される。
        """
        query = self.search_bar.text()
        # 検索エンジンで検索実行
        results = self.search_engine.search(query)
        # ツリー表示を更新
        self.update_tree(results)

    def update_tree(self, results: List[Prompt]):
        """検索結果でツリーを更新"""
        pass


# ui/scene_editor_panel.py
class SceneEditorPanel(QWidget):
    """シーン編集パネル"""

    def __init__(self):
        super().__init__()
        # ブロックリスト表示
        # [+ブロック] [+BREAK]ボタン
        pass

    def insert_block(self, block: Block):
        """ブロックを挿入"""
        pass

    def move_block_up(self, block_id: int):
        """ブロックを上に移動"""
        pass


# ui/preview_panel.py
class PreviewPanel(QWidget):
    """プレビューパネル"""

    def __init__(self):
        super().__init__()
        # 最終プロンプト表示
        # 文字数カウント
        # [コピー]ボタン
        # ワイルドカード展開候補表示エリア
        pass

    def update_preview(self, scene: Scene):
        """プレビュー更新"""
        # 最終プロンプトを構築
        final_prompt = self.build_final_prompt(scene)

        # ワイルドカード展開候補を表示
        self.update_wildcard_candidates(scene)

        pass

    def update_wildcard_candidates(self, scene: Scene):
        """ワイルドカード展開候補を更新

        Note:
            個別ファイルごとに候補を表示（全組み合わせは表示しない）。
            各ファイルの候補を最大5個まで表示し、残りは「（残りN候補...）」と表示。

        Example:
            シーンに __posing/arm__ と __posing/leg__ がある場合:

            posing/arm (10候補):
             • arms crossed
             • arms up
             • arms behind back
             • arms at sides
             • arms behind head
             （残り5候補...）

            posing/leg (8候補):
             • standing
             • sitting
             • kneeling
             • spread legs
             • lying down
             （残り3候補...）
        """
        # シーン内のワイルドカードブロックを抽出
        wildcard_blocks = [b for b in scene.blocks
                          if b.type == BlockType.WILDCARD]

        # 各ワイルドカードファイルの候補を取得（最大5個）
        for block in wildcard_blocks:
            wildcard_path = block.content  # 例: __posing/arm__
            candidates = self.load_wildcard_candidates(wildcard_path, limit=5)
            # UI表示を更新
            self.display_candidates(wildcard_path, candidates)

        pass

    def load_wildcard_candidates(self, wildcard_path: str, limit: int = 5) -> List[str]:
        """ワイルドカードファイルから候補を読み込み

        Args:
            wildcard_path: ワイルドカードパス（例: __posing/arm__）
            limit: 取得する候補の最大数

        Returns:
            候補リスト（最大limit個）
        """
        # ワイルドカードパスからファイルパスを取得
        # 例: __posing/arm__ → E:\tool\Pfft_maker\wildcards\posing\arm.txt
        file_path = self.resolve_wildcard_path(wildcard_path)

        # ファイルを読み込み、最初のlimit行を取得
        # 実際の実装では LibraryManager を使用して取得
        pass
```

---

## 4. データベース設計（CSV）

### 4.1 prompts_library.csv

**スキーマ**:
```csv
id,source_file,original_line_number,original_number,label_ja,label_en,prompt,category,tags,created_date,last_used,label_source
```

**インデックス**: `id` (一意キー)

**データ型**:
- `id`: string (例: `tipo_play_14`)
- `source_file`: string (相対パス)
- `original_line_number`: integer | null (元ファイルの行番号、**参考情報**、元ファイル変更時は無効)
- `original_number`: integer | null (元の番号`14→`の14、**プロンプト照合に使用**)
- `label_ja`: string
- `label_en`: string
- `prompt`: text
- `category`: string
- `tags`: string (カンマ区切り)
- `created_date`: datetime (ISO8601)
- `last_used`: datetime | null (ISO8601)
- `label_source`: enum (`auto_extract`, `ai_generated`, `manual`, `auto_word_split`)

**カラムの役割**:
- `original_line_number`: 元ファイルのどの行から読み込んだかの記録（デバッグ用、参考情報）
- `original_number`: ワイルドカードファイルの番号（`14→`の14）、ファイル更新時の照合に使用
- 照合ロジック: `original_number` → プロンプト内容の類似度（90%以上） → 新規エントリ

**サンプルデータ**:
```csv
tipo_play_14,tipo_play.txt,14,14,服着たままオナニー,clothed masturbation,clothed masturbation,行為,"clothed,masturbation,服,オナニー",2025-01-15T10:00:00,2025-01-15T15:30:00,auto_extract
bg_school_9,背景/学校.txt,9,9,教室,classroom,"classroom interior, desks in rows, chalkboard",背景,"school,classroom,教室",2025-01-15T10:05:00,,auto_extract
custom_001,手動入力,,,服の上から愛撫,fondling over clothes,"crotch_grab,fondling,over_clothes,fingering,embarrassed",行為,"愛撫,服,crotch_grab,fondling",2025-01-15T14:20:00,2025-01-15T16:00:00,manual
```

**重要な注意事項**:
- `original_line_number`は**参考情報**であり、元ファイルが変更されると無効になります
- プロンプト照合には`original_number`（`14→`の番号）や内容の類似度を使用してください
- 手動入力プロンプトは`original_line_number`と`original_number`が空（null）です

---

### 4.2 categories.json

**スキーマ**:
```json
{
  "categories": [
    {
      "name": "行為",
      "files": ["tipo_play.txt", "tipo_1girl.txt"],
      "color": "#ff6b6b",
      "icon": "action"
    },
    {
      "name": "背景",
      "files": ["背景/学校.txt", "背景/ビーチ.txt"],
      "color": "#4ecdc4",
      "icon": "location"
    }
  ]
}
```

---

### 4.3 プロジェクトファイル（.pfft）

**形式**: JSON

**スキーマ**: requirements.md の FR-010 を参照

---

## 5. 外部依存関係

### 5.1 ワイルドカードファイル
- **パス**: `E:\EasyReforge\Model\wildcards\`（デフォルト、設定で変更可能）
- **形式**: UTF-8 テキストファイル（`.txt`）
- **更新**: 外部エディタで編集可能
- **監視**: `watchdog`でリアルタイム監視

### 5.2 Claude API
- **エンドポイント**: `https://api.anthropic.com/v1/messages`
- **モデル**: `claude-3-haiku-20240307`（推奨、コスト削減）
- **認証**: APIキー（暗号化保存）
- **レート制限**: 遵守必須

### 5.3 LM Studio
- **エンドポイント**: `http://localhost:1234/v1/chat/completions`（デフォルト）
- **プロトコル**: OpenAI互換API
- **モデル**: ユーザーが任意に選択
- **接続**: オプション、オフライン動作可能

---

## 6. ビルド・デプロイ戦略

### 6.1 PyInstaller設定

**build.spec**:
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('src/config/default_config.json', 'config'),
    ],
    hiddenimports=[
        'anthropic',
        'keyring',
        'keyring.backends.Windows',
        'pandas',
        'watchdog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',  # 不要なモジュール除外
        'matplotlib',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Pfft_maker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                   # UPX無効化（Windows Defender誤検知防止）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,               # GUIモード（コンソール非表示）
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app.ico'  # アプリアイコン
)
```

**ビルドコマンド**:
```bash
pyinstaller build.spec
```

**出力**:
- `dist/Pfft_maker.exe`（単一実行ファイル、約30-50MB）

---

### 6.2 配布パッケージ構成

```
Pfft_maker_v1.0/
├── Pfft_maker.exe           # メイン実行ファイル
├── README.txt               # 使い方
├── LICENSE.txt              # ライセンス
└── config/                  # 初回起動時に自動生成
    └── default_config.json
```

---

### 6.3 ビルド前チェックリスト

- [ ] すべてのテストが成功
- [ ] requirements.txtが最新
- [ ] アイコンファイルが配置済み
- [ ] default_config.jsonが配置済み
- [ ] build.specのバージョン番号更新
- [ ] ログレベルをINFOに設定
- [ ] デバッグコードを削除

---

## 7. セキュリティ要件

### 7.1 APIキー保護

**実装仕様**:
```python
# utils/encryption.py
from cryptography.fernet import Fernet
import keyring
from pathlib import Path

class SecureAPIKeyManager:
    APP_NAME = "Pfft_maker"
    KEY_FILE = Path.home() / ".pfft_maker" / "api.enc"

    def __init__(self):
        self.KEY_FILE.parent.mkdir(exist_ok=True)
        self._fernet = self._get_or_create_fernet()
        self._api_key_cache = None

    def save_api_key(self, api_key: str):
        """APIキーを暗号化して保存"""
        encrypted = self._fernet.encrypt(api_key.encode())
        self.KEY_FILE.write_bytes(encrypted)

        # プラットフォーム別のファイル保護
        self._protect_file(self.KEY_FILE)

    def _protect_file(self, file_path: Path):
        """ファイル保護（プラットフォーム別）"""
        import platform

        if platform.system() == 'Windows':
            # Windows: ACL設定 + フォールバック
            try:
                import win32security
                import win32api
                import ntsecuritycon as con

                # 現在のユーザー取得
                user, domain, type = win32security.LookupAccountName("", win32api.GetUserName())

                # セキュリティ記述子作成
                sd = win32security.SECURITY_DESCRIPTOR()
                dacl = win32security.ACL()

                # 現在のユーザーにのみフルコントロール許可
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.FILE_ALL_ACCESS,
                    user
                )

                sd.SetSecurityDescriptorDacl(1, dacl, 0)
                win32security.SetFileSecurity(
                    str(file_path),
                    win32security.DACL_SECURITY_INFORMATION,
                    sd
                )
            except ImportError:
                # pywin32がない場合のフォールバック: 隠しファイル化
                import os
                os.system(f'attrib +h +s "{file_path}"')
        else:
            # Unix/Linux/Mac: chmod 600
            file_path.chmod(0o600)

    def load_api_key(self) -> str:
        """APIキーを復号化して取得"""
        if not self._api_key_cache:
            encrypted = self.KEY_FILE.read_bytes()
            self._api_key_cache = self._fernet.decrypt(encrypted).decode()
        return self._api_key_cache

    def _get_or_create_fernet(self) -> Fernet:
        """Fernetインスタンス取得（マスターキーはOSキーチェーン）"""
        master_key = keyring.get_password(self.APP_NAME, "master_key")
        if not master_key:
            master_key = Fernet.generate_key().decode()
            keyring.set_password(self.APP_NAME, "master_key", master_key)
        return Fernet(master_key.encode())

    def clear_cache(self):
        """メモリクリア"""
        self._api_key_cache = None
```

**セキュリティ対策**:
1. ✅ Fernet（AES128）で暗号化
2. ✅ マスターキーはOSキーチェーンで管理
3. ✅ ファイルパーミッション制限:
   - Windows: ACL設定（pywin32） + フォールバック（隠しファイル化）
   - Unix/Linux/Mac: chmod 600
4. ✅ アプリ終了時にメモリクリア
5. ✅ ログにAPIキーを出力しない
6. ✅ .gitignoreに追加

---

### 7.2 ログセキュリティ

```python
# utils/logger.py
import logging
from pathlib import Path

class SecureLogger:
    """セキュアなログ管理"""

    SENSITIVE_KEYS = ["api_key", "password", "token", "secret"]

    def __init__(self, log_dir: Path):
        self.logger = logging.getLogger("Pfft_maker")
        self.logger.setLevel(logging.INFO)

        # ファイルハンドラ
        fh = logging.FileHandler(log_dir / "pfft_maker.log")
        fh.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(fh)

    def info(self, message: str, **kwargs):
        """情報ログ（機密情報マスク）"""
        masked_kwargs = self._mask_sensitive_data(kwargs)
        self.logger.info(message, extra=masked_kwargs)

    def _mask_sensitive_data(self, data: dict) -> dict:
        """機密情報をマスク"""
        masked = {}
        for key, value in data.items():
            if any(sk in key.lower() for sk in self.SENSITIVE_KEYS):
                masked[key] = "***MASKED***"
            else:
                masked[key] = value
        return masked
```

---

## 8. パフォーマンス要件

### 8.1 応答時間

| 操作 | 目標応答時間 |
|------|-------------|
| アプリ起動 | < 3秒 |
| プロジェクト読み込み | < 1秒 |
| ワイルドカード読み込み（2,000プロンプト） | < 5秒 |
| 検索実行（リアルタイム） | < 100ms |
| シーン切り替え | < 50ms |
| プレビュー更新 | < 50ms |
| プロジェクト保存 | < 500ms |
| 出力ファイル生成（30シーン） | < 1秒 |

---

### 8.2 最適化戦略

#### UI最適化
- **遅延ロード**: ライブラリツリーは表示時にロード
- **仮想スクロール**: 大量データ表示時は仮想スクロール実装
- **バックグラウンド処理**: ファイル読み込み・AI生成は別スレッド

```python
# バックグラウンド処理例
from PyQt6.QtCore import QThread, pyqtSignal

class FileLoadThread(QThread):
    """ファイル読み込みスレッド"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)

    def __init__(self, wildcard_dir: Path):
        super().__init__()
        self.wildcard_dir = wildcard_dir

    def run(self):
        parser = WildcardParser(self.wildcard_dir)
        prompts = parser.scan_directory()
        self.finished.emit(prompts)
```

#### データ処理最適化
- **Pandasのインデックス活用**: CSV検索高速化
- **キャッシュ**: 頻繁にアクセスするデータはメモリキャッシュ
- **差分更新**: ファイル監視時は変更ファイルのみ再読み込み

---

## 9. テスト戦略

### 9.1 ユニットテスト

**テスト対象**:
- `wildcard_parser.py`
- `prompt_builder.py`
- `project_manager.py`
- `search_engine.py`

**テストフレームワーク**: pytest

**カバレッジ目標**: 80%以上

**例**:
```python
# tests/test_wildcard_parser.py
import pytest
from pathlib import Path
from src.core.wildcard_parser import WildcardParser

def test_parse_table_type():
    """テーブル型のパース"""
    parser = WildcardParser(Path("tests/fixtures"))
    line = "| 教室 | classroom interior, desks in rows |"
    label, prompt = parser.extract_label(line)
    assert label == "教室"
    assert prompt == "classroom interior, desks in rows"

def test_parse_numbered_type():
    """番号付き型のパース"""
    parser = WildcardParser(Path("tests/fixtures"))
    line = "14→clothed masturbation"
    label, prompt = parser.extract_label(line)
    assert label == "clothed masturbation"
    assert prompt == "clothed masturbation"
```

---

### 9.2 統合テスト

**テスト対象**:
- プロジェクト保存 → 読み込み → 再保存の一貫性
- ワイルドカード読み込み → 検索 → シーン挿入の連携
- ファイル監視 → 自動更新の動作

---

### 9.3 E2Eテスト

**シナリオ**:
1. アプリ起動 → ワイルドカード読み込み
2. 新規プロジェクト作成
3. ライブラリから検索 → プロンプト挿入
4. 30シーン編集
5. プロジェクト保存
6. 出力ファイル生成
7. アプリ終了

---

## 10. エラーハンドリング

### 10.1 エラー分類

| エラータイプ | ハンドリング |
|-------------|-------------|
| ファイル読み込みエラー | エラーダイアログ表示 + ログ記録 |
| API接続エラー | リトライ（3回） → フォールバック |
| 暗号化エラー | エラーダイアログ + APIキー再入力 |
| プロジェクト保存エラー | エラーダイアログ + バックアップから復元提案 |
| ワイルドカードパースエラー | 警告表示 + 該当行スキップ |

---

### 10.2 ログレベル

| レベル | 用途 |
|-------|------|
| DEBUG | 開発時のみ、詳細な動作ログ |
| INFO | 通常動作、プロジェクト保存・読み込み等 |
| WARNING | パース失敗、API警告等 |
| ERROR | ファイル読み込み失敗、暗号化エラー等 |
| CRITICAL | アプリ起動失敗等 |

---

## 11. 開発ワークフロー

### 11.1 開発環境セットアップ

```bash
# 1. リポジトリクローン
git clone https://github.com/your-repo/Pfft_maker.git
cd Pfft_maker

# 2. 仮想環境作成
python -m venv venv
venv\Scripts\activate  # Windows

# 3. 依存関係インストール
pip install -r requirements-dev.txt

# 4. テスト実行
pytest tests/

# 5. アプリ起動
python src/main.py
```

---

### 11.2 ブランチ戦略

- `main`: 本番リリース用
- `develop`: 開発用
- `feature/*`: 機能開発用
- `bugfix/*`: バグ修正用

---

### 11.3 コーディング規約

- **PEP 8** 準拠
- **型ヒント** 必須（Python 3.11+）
- **Docstring**: Google Style
- **フォーマッター**: Black
- **リンター**: Flake8
- **型チェック**: Mypy

---

## 12. 低優先度問題の実装ガイドライン

以下は低優先度の問題（問題17, 19-25）の実装ガイドラインです。実装時の参考にしてください。

### 12.1 問題17: ライブラリ使用履歴のキャッシュ化

**問題**: CSVの`last_used`カラムの頻繁な書き込みでパフォーマンス低下

**解決策**: メモリキャッシュ + アプリ終了時一括書き込み

**実装ガイド**:
```python
# core/library_manager.py に追加
from datetime import datetime

class LibraryManager:
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.df: pd.DataFrame | None = None
        self.usage_cache: Dict[str, datetime] = {}  # {prompt_id: last_used}

    def on_prompt_used(self, prompt_id: str):
        """プロンプト使用時（メモリ更新のみ）

        ブロック挿入時に呼び出される。CSVは更新せず、メモリキャッシュのみ更新。
        """
        self.usage_cache[prompt_id] = datetime.now()
        logger.debug(f"Prompt used: {prompt_id}")

    def save_usage_history(self):
        """アプリ終了時にCSVに書き込み

        アプリケーション終了時（MainWindow.closeEvent）に呼び出される。
        キャッシュされた使用履歴をCSVに一括書き込み。
        """
        if not self.usage_cache:
            return

        for prompt_id, last_used in self.usage_cache.items():
            self.df.loc[self.df['id'] == prompt_id, 'last_used'] = last_used

        self.save_library(self.df)
        logger.info(f"Saved usage history for {len(self.usage_cache)} prompts")
        self.usage_cache.clear()
```

**呼び出しタイミング**:
- `on_prompt_used()`: ブロック挿入時
- `save_usage_history()`: アプリ終了時（MainWindow.closeEvent）

---

### 12.2 問題19: シーン番号コメント形式

**問題**: Stable Diffusion WebUIがコメントとして認識する形式が不明

**解決策**: シンプルな `# Scene N: シーン名` 形式を採用

**実装ガイド**:
```python
# core/prompt_builder.py の build_all_prompts() に追加
def build_all_prompts(self, project: Project, include_comment: bool = False) -> List[str]:
    """全シーンのプロンプトを構築

    Args:
        project: プロジェクトオブジェクト
        include_comment: シーン番号をコメントで追記するか

    Returns:
        プロンプトの行リスト
    """
    lines = []

    for scene in project.scenes:
        # コメント追加（オプション）
        if include_comment:
            lines.append(f"# Scene {scene.scene_id}: {scene.scene_name}")

        # プロンプト追加
        prompt = self.build_scene_prompt(scene)
        lines.append(prompt)

    return lines
```

**出力例**:
```
# Scene 1: 保健室
clothed masturbation, school infirmary, BREAK, __posing/arm__, BREAK, masterpiece
# Scene 2: 教室
deepthroat, classroom interior, BREAK, __posing/leg__, BREAK, best quality
```

---

### 12.3 問題20: キーボードショートカット

**問題**: `Ctrl + →` / `Ctrl + ←` がユーザーの習慣と異なる可能性

**解決策**: カスタマイズ可能なショートカット設定

**実装ガイド**:
```python
# ui/main_window.py に追加
from PyQt6.QtGui import QKeySequence, QAction

class MainWindow(QMainWindow):
    def _create_keyboard_shortcuts(self):
        """キーボードショートカットを設定"""
        # シーン切り替え（カスタマイズ可能）
        self.next_scene_shortcut = QAction(self)
        self.next_scene_shortcut.setShortcut(QKeySequence("Ctrl+Right"))
        self.next_scene_shortcut.triggered.connect(self.scene_editor.next_scene)
        self.addAction(self.next_scene_shortcut)

        self.prev_scene_shortcut = QAction(self)
        self.prev_scene_shortcut.setShortcut(QKeySequence("Ctrl+Left"))
        self.prev_scene_shortcut.triggered.connect(self.scene_editor.prev_scene)
        self.addAction(self.prev_scene_shortcut)

        # 代替ショートカット
        # Alt + → / Alt + ← も使用可能にする
        alt_next = QAction(self)
        alt_next.setShortcut(QKeySequence("Alt+Right"))
        alt_next.triggered.connect(self.scene_editor.next_scene)
        self.addAction(alt_next)

        alt_prev = QAction(self)
        alt_prev.setShortcut(QKeySequence("Alt+Left"))
        alt_prev.triggered.connect(self.scene_editor.prev_scene)
        self.addAction(alt_prev)
```

**デフォルトショートカット**:
- シーン移動: `Ctrl + →` / `Ctrl + ←` または `Alt + →` / `Alt + ←`
- シーンジャンプ: `Ctrl + G`

---

### 12.4 問題21: ブロック複数選択

**問題**: PyQt6での実装が複雑

**解決策**: Phase 2に延期、まずは単一選択で実装

**実装ガイド**:
```python
# ui/scene_editor_panel.py
# Phase 1では単一選択のみ実装
# Phase 2で以下を追加予定:

class SceneEditorPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_blocks: List[int] = []  # Phase 2で使用

    # Phase 2実装予定:
    # def select_multiple_blocks(self, block_ids: List[int]):
    #     """複数ブロックを選択（Ctrlキー押しながらクリック）"""
    #     self.selected_blocks = block_ids
    #
    # def delete_selected_blocks(self):
    #     """選択中の複数ブロックを削除"""
    #     for block_id in sorted(self.selected_blocks, reverse=True):
    #         self.delete_block(block_id)
```

**Note**: Phase 1では単一選択で十分。Phase 2で必要に応じて実装。

---

### 12.5 問題22: バックアップディレクトリの場所

**問題**: `.backup/` ディレクトリの場所が不明確

**解決策**: プロジェクトファイルと同じディレクトリに `.pfft_backup/` を作成

**実装ガイド**:
```python
# core/project_manager.py の create_backup() 実装
def create_backup(self, file_path: Path):
    """世代バックアップ作成（最大5世代）

    Args:
        file_path: プロジェクトファイルパス

    Note:
        プロジェクトと同じディレクトリに .pfft_backup/ を作成
    """
    # バックアップディレクトリ作成
    backup_dir = file_path.parent / ".pfft_backup"
    backup_dir.mkdir(exist_ok=True)

    # タイムスタンプ付きバックアップファイル名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{timestamp}.pfft"
    backup_path = backup_dir / backup_name

    # ファイルコピー
    import shutil
    shutil.copy2(file_path, backup_path)

    # 古いバックアップを削除（5世代保持）
    backups = sorted(backup_dir.glob(f"{file_path.stem}_*.pfft"))
    if len(backups) > 5:
        for old_backup in backups[:-5]:
            old_backup.unlink()

    logger.info(f"Created backup: {backup_path}")
```

**ディレクトリ構成**:
```
E:\works\学園メイド\
├── 学園メイドCG集.pfft
└── .pfft_backup\
    ├── 学園メイドCG集_20250120_1430.pfft
    ├── 学園メイドCG集_20250120_1210.pfft
    └── ... (最大5世代)
```

---

### 12.6 問題23: CSVとJSONの混在

**問題**: データ管理が複雑、同期の問題

**解決策**: Phase 1ではCSV/JSON混在を許容、Phase 3以降でSQLite移行を検討

**実装ガイド**:
```python
# 現状のデータ形式（Phase 1-2）:
# - プロンプトライブラリ: CSV (pandas で高速検索)
# - プロジェクト: JSON (シリアライズが容易)
# - カテゴリ設定: JSON (小規模データ)
# - ラベルメタデータ: JSON (ユーザー設定)

# Phase 3以降での SQLite移行案:
# import sqlite3
#
# class DatabaseManager:
#     def __init__(self, db_path: Path):
#         self.conn = sqlite3.connect(db_path)
#         self._create_tables()
#
#     def _create_tables(self):
#         """テーブル作成"""
#         self.conn.execute("""
#             CREATE TABLE IF NOT EXISTS prompts (
#                 id TEXT PRIMARY KEY,
#                 source_file TEXT,
#                 original_line_number INTEGER,
#                 original_number INTEGER,
#                 label_ja TEXT,
#                 label_en TEXT,
#                 prompt TEXT,
#                 category TEXT,
#                 tags TEXT,
#                 created_date TEXT,
#                 last_used TEXT,
#                 label_source TEXT
#             )
#         """)
```

**Note**: Phase 1ではCSV/JSONで実装し、SQLite移行はPhase 3以降で検討。

---

### 12.7 問題24: パス区切り文字の統一

**問題**: Windowsパス vs Unix風パスの混在

**解決策**: 内部処理はすべて `pathlib.Path` 使用

**実装ガイド**:
```python
# すべてのファイルで pathlib.Path を使用

from pathlib import Path

# NG: 文字列でパス操作
file_path = "E:\\EasyReforge\\Model\\wildcards\\tipo_play.txt"

# OK: pathlib.Path を使用
file_path = Path("E:/EasyReforge/Model/wildcards/tipo_play.txt")
# または
file_path = Path("E:\\EasyReforge\\Model\\wildcards\\tipo_play.txt")

# Path オブジェクトは自動的にOSに応じた区切り文字に変換
print(file_path)  # Windows: E:\EasyReforge\Model\wildcards\tipo_play.txt
                   # Unix: E:/EasyReforge/Model/wildcards/tipo_play.txt

# パス結合も Path で
wildcard_dir = Path("E:/EasyReforge/Model/wildcards")
file_name = "tipo_play.txt"
full_path = wildcard_dir / file_name  # Path オブジェクトの / 演算子を使用
```

**ルール**:
- すべてのパス操作で `pathlib.Path` を使用
- 文字列での `os.path.join()` や手動の区切り文字結合は禁止
- ワイルドカード形式（`__folder/file__`）のみ Unix スタイル `/` を使用

---

### 12.8 問題25: サブディレクトリ対応

**問題**: 深い階層（`背景/学校/教室/1-A.txt`）の扱いが不明確

**解決策**: 最大2階層までサポート、それ以上は「その他」カテゴリ

**実装ガイド**:
```python
# core/wildcard_parser.py または utils/file_utils.py に追加

def extract_category(file_path: Path, wildcard_root: Path) -> str:
    """カテゴリ抽出（最大2階層まで）

    Args:
        file_path: ファイルパス（例: E:/wildcards/背景/学校/教室/1-A.txt）
        wildcard_root: ワイルドカードルート（例: E:/wildcards/）

    Returns:
        カテゴリ名（例: "背景/学校"）

    Example:
        >>> extract_category(Path("E:/wildcards/背景.txt"), Path("E:/wildcards/"))
        "その他"

        >>> extract_category(Path("E:/wildcards/背景/学校.txt"), Path("E:/wildcards/"))
        "背景"

        >>> extract_category(Path("E:/wildcards/背景/学校/教室.txt"), Path("E:/wildcards/"))
        "背景/学校"

        >>> extract_category(Path("E:/wildcards/背景/学校/教室/1-A.txt"), Path("E:/wildcards/"))
        "背景/学校"  # 最大2階層まで
    """
    relative = file_path.relative_to(wildcard_root)
    parts = relative.parts[:-1]  # ファイル名を除く

    if len(parts) == 0:
        return "その他"  # ルートディレクトリのファイル
    elif len(parts) == 1:
        return parts[0]  # 例: "背景"
    else:
        # 2階層以上: 最初の2階層のみ使用
        return f"{parts[0]}/{parts[1]}"  # 例: "背景/学校"
```

**ワイルドカード形式の生成**:
```python
def format_wildcard_path(file_path: Path, wildcard_root: Path) -> str:
    """ワイルドカード形式に変換

    Args:
        file_path: ファイルパス
        wildcard_root: ワイルドカードルート

    Returns:
        ワイルドカード形式（例: __背景/学校/教室/1-A__）

    Note:
        カテゴリは最大2階層だが、ワイルドカードパスは全階層を含む
    """
    relative_path = file_path.relative_to(wildcard_root)
    stem = relative_path.with_suffix('')  # 拡張子削除
    unix_path = str(stem).replace('\\', '/')  # Unixスタイル
    return f"__{unix_path}__"
```

---

## 13. 変更履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| 1.1 | 2025-10-12 | 仕様確定反映版<br>- build.spec: upx=False（Windows Defender誤検知防止）<br>- Windows ACL実装追加（セキュリティ強化）<br>- PromptBuilder: BREAK処理ロジック明確化<br>- CSVスキーマ: label_sourceカラム追加 |
| 1.0 | 2025-01-15 | 初版作成（確定版） |

---

**承認**:
- 作成者: Claude
- 承認者: （プロジェクトオーナー）
- 承認日: 2025-01-15
