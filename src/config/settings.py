"""アプリケーション設定管理

ワイルドカードディレクトリパスやその他の設定を管理。
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, List


class Settings:
    """アプリケーション設定クラス

    JSON形式で設定を保存・読み込み。
    """

    @staticmethod
    def get_user_data_root() -> Path:
        r"""ユーザーデータのルートディレクトリを取得

        Returns:
            Windows: %APPDATA%\Pfft_maker
            ポータブル: EXE実行フォルダ\user_data
        """
        # ポータブルモード判定（PORTABLE.txt の存在チェック）
        if getattr(sys, 'frozen', False):
            # PyInstallerでEXE化されている場合
            app_dir = Path(sys.executable).parent
            if (app_dir / "PORTABLE.txt").exists():
                # ポータブルモード
                return app_dir / "user_data"
        else:
            # 開発環境：プロジェクトルートを使用
            project_root = Path(__file__).parent.parent.parent
            if (project_root / "PORTABLE.txt").exists():
                return project_root / "user_data"

        # 通常モード: %APPDATA% を使用
        appdata = os.environ.get('APPDATA')
        if not appdata:
            # APPDATAが取得できない場合はホームディレクトリ
            appdata = str(Path.home())
        return Path(appdata) / "Pfft_maker"

    @classmethod
    def get_default_data_dir(cls) -> str:
        """デフォルトデータディレクトリ"""
        return str(cls.get_user_data_root() / "user_data")

    @classmethod
    def get_default_wildcard_dir(cls) -> str:
        """デフォルトワイルドカードディレクトリ"""
        return str(cls.get_user_data_root() / "wildcards")

    @classmethod
    def get_default_backup_dir(cls) -> str:
        """デフォルトバックアップディレクトリ"""
        return str(cls.get_user_data_root() / "backups")

    # デフォルト値（相対パスまたは%APPDATA%）
    DEFAULT_SOURCE_WILDCARD_DIR = ""  # 初回起動時にユーザーが設定
    DEFAULT_LOCAL_WILDCARD_DIR = ""   # get_default_wildcard_dir()で動的取得
    DEFAULT_DATA_DIR = ""              # get_default_data_dir()で動的取得
    DEFAULT_EXCLUDE_PATTERNS = [
        "backup_*",      # バックアップフォルダ
        ".git",          # Gitリポジトリ
        ".backup",       # その他のバックアップ
        "__pycache__",   # Pythonキャッシュ
        ".venv",         # 仮想環境
        "node_modules"   # Node.jsパッケージ
    ]

    # LM Studio デフォルト設定
    DEFAULT_LM_STUDIO_ENDPOINT = "http://localhost:1234/v1"
    DEFAULT_LM_STUDIO_MODEL = "local-model"
    DEFAULT_LM_STUDIO_MAX_CONCURRENT = 2  # VRAM 16GBで安全な同時実行数

    def __init__(self, config_path: Optional[Path] = None):
        """初期化

        Args:
            config_path: 設定ファイルパス（Noneの場合はデフォルトパス）
        """
        if config_path is None:
            # ユーザーデータルートに settings.json を保存
            user_root = self.get_user_data_root()
            config_path = user_root / "settings.json"

        self.config_path = config_path

        # デフォルト値を動的に設定
        self.source_wildcard_dir: str = self.DEFAULT_SOURCE_WILDCARD_DIR
        self.local_wildcard_dir: str = self.get_default_wildcard_dir()
        self.data_dir: str = self.get_default_data_dir()
        self.exclude_patterns: list = self.DEFAULT_EXCLUDE_PATTERNS.copy()
        self.common_prompts: List = []  # CommonPromptのリスト

        # LoRA設定
        self.lora_directory: str = ""  # LoRAディレクトリ（未設定の場合は空）

        # LM Studio設定
        self.lm_studio_endpoint: str = self.DEFAULT_LM_STUDIO_ENDPOINT
        self.lm_studio_model: str = self.DEFAULT_LM_STUDIO_MODEL
        self.lm_studio_max_concurrent: int = self.DEFAULT_LM_STUDIO_MAX_CONCURRENT

        # 設定を読み込み
        self.load()

    def load(self):
        """設定ファイルから読み込み"""
        if not self.config_path.exists():
            # 設定ファイルがない場合はデフォルト値で初期化
            self._initialize_default_common_prompts()
            self.save()
            return

        try:
            with self.config_path.open('r', encoding='utf-8') as f:
                data = json.load(f)

            self.source_wildcard_dir = data.get('source_wildcard_dir', self.DEFAULT_SOURCE_WILDCARD_DIR)
            self.local_wildcard_dir = data.get('local_wildcard_dir', self.get_default_wildcard_dir())
            self.data_dir = data.get('data_dir', self.get_default_data_dir())
            self.exclude_patterns = data.get('exclude_patterns', self.DEFAULT_EXCLUDE_PATTERNS.copy())

            # LoRA設定を読み込み
            self.lora_directory = data.get('lora_directory', '')

            # LM Studio設定を読み込み
            self.lm_studio_endpoint = data.get('lm_studio_endpoint', self.DEFAULT_LM_STUDIO_ENDPOINT)
            self.lm_studio_model = data.get('lm_studio_model', self.DEFAULT_LM_STUDIO_MODEL)
            self.lm_studio_max_concurrent = data.get('lm_studio_max_concurrent', self.DEFAULT_LM_STUDIO_MAX_CONCURRENT)

            # 共通プロンプトを読み込み
            common_prompts_data = data.get('common_prompts', [])
            if common_prompts_data:
                from models.common_prompt import CommonPrompt
                self.common_prompts = [
                    CommonPrompt.from_dict(cp_data)
                    for cp_data in common_prompts_data
                ]
            else:
                # データがない場合はデフォルトを初期化
                self._initialize_default_common_prompts()

        except Exception as e:
            print(f"[Warning] Failed to load settings: {e}")
            # 読み込み失敗時はデフォルト値を使用
            self._initialize_default_common_prompts()

    def save(self):
        """設定ファイルに保存"""
        # ディレクトリが存在しない場合は作成
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'source_wildcard_dir': self.source_wildcard_dir,
            'local_wildcard_dir': self.local_wildcard_dir,
            'data_dir': self.data_dir,
            'exclude_patterns': self.exclude_patterns,
            'common_prompts': [cp.to_dict() for cp in self.common_prompts],
            'lora_directory': self.lora_directory,
            'lm_studio_endpoint': self.lm_studio_endpoint,
            'lm_studio_model': self.lm_studio_model,
            'lm_studio_max_concurrent': self.lm_studio_max_concurrent
        }

        with self.config_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_source_dir(self) -> Path:
        """元ワイルドカードディレクトリを取得

        Returns:
            Pathオブジェクト
        """
        return Path(self.source_wildcard_dir)

    def get_local_dir(self) -> Path:
        """ローカルワイルドカードディレクトリを取得

        Returns:
            Pathオブジェクト
        """
        return Path(self.local_wildcard_dir)

    def get_data_dir(self) -> Path:
        """データディレクトリを取得

        Returns:
            Pathオブジェクト
        """
        return Path(self.data_dir)

    def get_library_csv_path(self) -> Path:
        """プロンプトライブラリCSVパスを取得

        Returns:
            Pathオブジェクト
        """
        return self.get_data_dir() / "prompts_library.csv"

    def get_lora_library_csv_path(self) -> Path:
        """LoRAライブラリCSVパスを取得

        Returns:
            Pathオブジェクト
        """
        return self.get_data_dir() / "lora_library.csv"

    def get_lora_dir(self) -> Path | None:
        """LoRAディレクトリを取得

        Returns:
            Pathオブジェクト（未設定の場合はNone）
        """
        if self.lora_directory:
            return Path(self.lora_directory)
        return None

    def get_labels_json_path(self) -> Path:
        """ラベルメタデータJSONパスを取得

        Returns:
            Pathオブジェクト
        """
        return self.get_data_dir() / "labels_metadata.json"

    def _initialize_default_common_prompts(self):
        """デフォルトの共通プロンプトを初期化"""
        from models.common_prompt import CommonPrompt

        self.common_prompts = [
            CommonPrompt.create_default_quality_tags(),
            CommonPrompt(
                name="ネガティブプロンプト",
                content="lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
                enabled=False,
                position="end",
                insert_break_after=False
            ),
            CommonPrompt.create_default_lora()
        ]

    def get_enabled_common_prompts(self) -> List:
        """有効な共通プロンプトを取得

        Returns:
            有効な共通プロンプトのリスト
        """
        return [cp for cp in self.common_prompts if cp.enabled]

    def get_common_prompts_by_position(self, position: str) -> List:
        """指定位置の有効な共通プロンプトを取得

        Args:
            position: 挿入位置（"start" または "end"）

        Returns:
            指定位置の有効な共通プロンプトのリスト
        """
        return [
            cp for cp in self.common_prompts
            if cp.enabled and cp.position == position
        ]
