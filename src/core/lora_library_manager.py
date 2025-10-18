"""LoRAライブラリマネージャー

LoRAファイルの読み込み、CSV保存、同期を管理。
"""

import csv
from pathlib import Path
from typing import List, Optional, Callable
from datetime import datetime

from models import Prompt
from config.settings import Settings
from core.lora_parser import LoraParser


class LoraLibraryManager:
    """LoRAライブラリマネージャー

    LoRAファイルの一元管理を提供。

    主な機能:
    - LoRAファイルのスキャン
    - CSV形式でのライブラリ保存・読み込み
    - メタデータ管理
    """

    def __init__(self, settings: Optional[Settings] = None):
        """初期化

        Args:
            settings: 設定オブジェクト（Noneの場合は新規作成）
        """
        self.settings = settings or Settings()
        self.parser = LoraParser()
        self.prompts: List[Prompt] = []

    def scan_and_build_library(
        self,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Prompt]:
        """LoRAフォルダをスキャンしてライブラリを構築

        Args:
            progress_callback: 進捗コールバック(current, total, message)

        Returns:
            Promptオブジェクトのリスト
        """
        lora_dir = self.settings.get_lora_dir()

        if not lora_dir or not lora_dir.exists():
            if progress_callback:
                progress_callback(0, 0, "LoRA directory not configured or not found")
            return []

        if progress_callback:
            progress_callback(0, 1, "Scanning LoRA files...")

        # ファイルをスキャン
        self.prompts = self.parser.scan_directory(lora_dir, progress_callback)

        if progress_callback:
            progress_callback(1, 1, f"Found {len(self.prompts)} LoRA files")

        return self.prompts

    def save_to_csv(self, csv_path: Optional[Path] = None):
        """ライブラリをCSVに保存

        Args:
            csv_path: CSVファイルパス（Noneの場合は設定から取得）
        """
        if csv_path is None:
            csv_path = self.settings.get_lora_library_csv_path()

        # ディレクトリが存在しない場合は作成
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # CSVに書き込み（BOM付きUTF-8でExcel対応）
        with csv_path.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)

            # ヘッダー
            writer.writerow([
                'id', 'source_file', 'original_line_number', 'original_number',
                'label_ja', 'label_en', 'prompt', 'category', 'tags',
                'created_date', 'last_used', 'label_source', 'lora_metadata'
            ])

            # データ
            for prompt in self.prompts:
                writer.writerow([
                    prompt.id,
                    prompt.source_file,
                    prompt.original_line_number if prompt.original_line_number is not None else '',
                    prompt.original_number if prompt.original_number is not None else '',
                    prompt.label_ja,
                    prompt.label_en,
                    prompt.prompt,
                    prompt.category,
                    ','.join(prompt.tags),
                    prompt.created_date.isoformat() if prompt.created_date else '',
                    prompt.last_used.isoformat() if prompt.last_used else '',
                    prompt.label_source,
                    prompt.lora_metadata if prompt.lora_metadata else ''
                ])

    def load_from_csv(self, csv_path: Optional[Path] = None) -> List[Prompt]:
        """CSVからライブラリを読み込み

        Args:
            csv_path: CSVファイルパス（Noneの場合は設定から取得）

        Returns:
            Promptオブジェクトのリスト
        """
        if csv_path is None:
            csv_path = self.settings.get_lora_library_csv_path()

        if not csv_path.exists():
            return []

        prompts = []

        # BOM付きUTF-8で読み込み（BOMがない場合も自動対応）
        with csv_path.open('r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # 日付の変換
                created_date = None
                if row.get('created_date'):
                    try:
                        created_date = datetime.fromisoformat(row['created_date'])
                    except:
                        created_date = datetime.now()

                last_used = None
                if row.get('last_used'):
                    try:
                        last_used = datetime.fromisoformat(row['last_used'])
                    except:
                        pass

                # original_numberの変換
                original_number = None
                if row.get('original_number'):
                    try:
                        original_number = int(row['original_number'])
                    except:
                        pass

                # original_line_numberの変換
                original_line_number = None
                if row.get('original_line_number'):
                    try:
                        original_line_number = int(row['original_line_number'])
                    except:
                        pass

                # タグの変換
                tags = []
                if row.get('tags'):
                    tags = [t.strip() for t in row['tags'].split(',') if t.strip()]

                # Promptオブジェクト作成
                prompt = Prompt(
                    id=row['id'],
                    source_file=row['source_file'],
                    original_line_number=original_line_number,
                    original_number=original_number,
                    label_ja=row.get('label_ja', ''),
                    label_en=row.get('label_en', ''),
                    prompt=row['prompt'],
                    category=row.get('category', 'LoRA'),
                    tags=tags,
                    created_date=created_date,
                    last_used=last_used,
                    label_source=row.get('label_source', 'auto_extract'),
                    lora_metadata=row.get('lora_metadata', None)
                )

                prompts.append(prompt)

        return prompts

    def get_lora_absolute_path(self, prompt: Prompt) -> Optional[Path]:
        """LoRAの絶対パスを取得

        Args:
            prompt: Promptオブジェクト

        Returns:
            絶対パス（LoRAディレクトリが設定されていない場合はNone）
        """
        lora_dir = self.settings.get_lora_dir()
        if not lora_dir:
            return None

        # source_fileは常にUnix形式（/）で保存されているので、Pathで自動変換
        return lora_dir / prompt.source_file
