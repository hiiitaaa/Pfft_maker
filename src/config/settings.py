"""アプリケーション設定管理

ワイルドカードディレクトリパスやその他の設定を管理。
"""

import json
from pathlib import Path
from typing import Optional, List


class Settings:
    """アプリケーション設定クラス

    JSON形式で設定を保存・読み込み。
    """

    # デフォルト値
    DEFAULT_SOURCE_WILDCARD_DIR = r"E:\EasyReforge\Model\wildcards"
    DEFAULT_LOCAL_WILDCARD_DIR = r"E:\tool\Pfft_maker\wildcards"
    DEFAULT_DATA_DIR = r"E:\tool\Pfft_maker\data"
    DEFAULT_EXCLUDE_PATTERNS = [
        "backup_*",      # バックアップフォルダ
        ".git",          # Gitリポジトリ
        ".backup",       # その他のバックアップ
        "__pycache__",   # Pythonキャッシュ
        ".venv",         # 仮想環境
        "node_modules"   # Node.jsパッケージ
    ]

    def __init__(self, config_path: Optional[Path] = None):
        """初期化

        Args:
            config_path: 設定ファイルパス（Noneの場合はデフォルトパス）
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "data" / "settings.json"

        self.config_path = config_path
        self.source_wildcard_dir: str = self.DEFAULT_SOURCE_WILDCARD_DIR
        self.local_wildcard_dir: str = self.DEFAULT_LOCAL_WILDCARD_DIR
        self.data_dir: str = self.DEFAULT_DATA_DIR
        self.exclude_patterns: list = self.DEFAULT_EXCLUDE_PATTERNS.copy()
        self.common_prompts: List = []  # CommonPromptのリスト

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
            self.local_wildcard_dir = data.get('local_wildcard_dir', self.DEFAULT_LOCAL_WILDCARD_DIR)
            self.data_dir = data.get('data_dir', self.DEFAULT_DATA_DIR)
            self.exclude_patterns = data.get('exclude_patterns', self.DEFAULT_EXCLUDE_PATTERNS.copy())

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
            'common_prompts': [cp.to_dict() for cp in self.common_prompts]
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
