"""ライブラリマネージャー

ワイルドカードファイルの読み込み、CSV保存、同期を管理。
"""

import csv
import shutil
from pathlib import Path
from typing import List, Optional, Callable
from datetime import datetime

from models import Prompt
from config.settings import Settings
from .wildcard_parser import WildcardParser


class LibraryManager:
    """ライブラリマネージャー

    ワイルドカードファイルの一元管理を提供。

    主な機能:
    - ワイルドカードファイルのスキャン・コピー
    - CSV形式でのライブラリ保存・読み込み
    - ファイル更新チェック
    """

    def __init__(self, settings: Optional[Settings] = None):
        """初期化

        Args:
            settings: 設定オブジェクト（Noneの場合は新規作成）
        """
        self.settings = settings or Settings()
        self.parser = WildcardParser(self.settings.get_local_dir())
        self.prompts: List[Prompt] = []

    def initialize_library(
        self,
        force_copy: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> bool:
        """ライブラリを初期化

        初回起動時または強制コピー時に、元ディレクトリから
        ローカルディレクトリにワイルドカードファイルをコピー。

        Args:
            force_copy: 強制的にコピーするか
            progress_callback: 進捗コールバック(current, total, message)

        Returns:
            成功した場合True
        """
        source_dir = self.settings.get_source_dir()
        local_dir = self.settings.get_local_dir()

        # 元ディレクトリの存在チェック
        if not source_dir.exists():
            if progress_callback:
                progress_callback(0, 0, f"[Error] Source directory not found: {source_dir}")
            return False

        # ローカルディレクトリが存在しないか、強制コピーの場合
        if not local_dir.exists() or force_copy:
            if progress_callback:
                progress_callback(0, 1, "Copying wildcard files...")

            # ローカルディレクトリを作成
            local_dir.mkdir(parents=True, exist_ok=True)

            # 全ファイルをコピー（除外パターンを考慮）
            from utils.file_utils import scan_text_files
            txt_files = scan_text_files(
                source_dir,
                recursive=True,
                exclude_patterns=self.settings.exclude_patterns
            )
            total_files = len(txt_files)

            for i, source_file in enumerate(txt_files, 1):
                # 相対パスを取得
                relative_path = source_file.relative_to(source_dir)
                dest_file = local_dir / relative_path

                # 親ディレクトリを作成
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # ファイルをコピー
                shutil.copy2(source_file, dest_file)

                if progress_callback:
                    progress_callback(i, total_files, f"Copied: {relative_path}")

        if progress_callback:
            progress_callback(1, 1, "File copy completed")

        return True

    def scan_and_build_library(
        self,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Prompt]:
        """ワイルドカードファイルをスキャンしてライブラリを構築

        既存のCSVがあれば読み込み、ラベル情報をマージします。

        Args:
            progress_callback: 進捗コールバック(current, total, message)

        Returns:
            Promptオブジェクトのリスト
        """
        # 既存のCSVがあれば読み込んでラベル情報を保持
        csv_path = self.settings.get_library_csv_path()
        if csv_path.exists():
            if progress_callback:
                progress_callback(0, 1, "Loading existing labels from CSV...")
            existing_prompts = self.load_from_csv(csv_path)
            self.parser.set_existing_prompts(existing_prompts)

        if progress_callback:
            progress_callback(0, 1, "Scanning wildcard files...")

        # ファイルをスキャン（除外パターンを渡す）
        self.prompts = self.parser.scan_directory(
            progress_callback,
            exclude_patterns=self.settings.exclude_patterns
        )

        if progress_callback:
            progress_callback(1, 1, f"Found {len(self.prompts)} prompts")

        return self.prompts

    def save_to_csv(self, csv_path: Optional[Path] = None):
        """ライブラリをCSVに保存

        Args:
            csv_path: CSVファイルパス（Noneの場合は設定から取得）
        """
        if csv_path is None:
            csv_path = self.settings.get_library_csv_path()

        # ディレクトリが存在しない場合は作成
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # CSVに書き込み（BOM付きUTF-8でExcel対応）
        with csv_path.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)

            # ヘッダー
            writer.writerow([
                'id', 'source_file', 'original_line_number', 'original_number',
                'label_ja', 'label_en', 'prompt', 'category', 'tags',
                'created_date', 'last_used', 'label_source'
            ])

            # データ
            for prompt in self.prompts:
                writer.writerow([
                    prompt.id,
                    prompt.source_file,
                    prompt.original_line_number,
                    prompt.original_number if prompt.original_number is not None else '',
                    prompt.label_ja,
                    prompt.label_en,
                    prompt.prompt,
                    prompt.category,
                    ','.join(prompt.tags),
                    prompt.created_date.isoformat() if prompt.created_date else '',
                    prompt.last_used.isoformat() if prompt.last_used else '',
                    prompt.label_source
                ])

    def load_from_csv(self, csv_path: Optional[Path] = None) -> List[Prompt]:
        """CSVからライブラリを読み込み

        Args:
            csv_path: CSVファイルパス（Noneの場合は設定から取得）

        Returns:
            Promptオブジェクトのリスト
        """
        if csv_path is None:
            csv_path = self.settings.get_library_csv_path()

        if not csv_path.exists():
            return []

        prompts = []

        # BOM付きUTF-8で読み込み（BOMがない場合も自動対応）
        with csv_path.open('r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # 日付の変換
                created_date = None
                if row['created_date']:
                    try:
                        created_date = datetime.fromisoformat(row['created_date'])
                    except:
                        created_date = datetime.now()

                last_used = None
                if row['last_used']:
                    try:
                        last_used = datetime.fromisoformat(row['last_used'])
                    except:
                        pass

                # original_numberの変換
                original_number = None
                if row['original_number']:
                    try:
                        original_number = int(row['original_number'])
                    except:
                        pass

                # Promptオブジェクト作成
                prompt = Prompt(
                    id=row['id'],
                    source_file=row['source_file'],
                    original_line_number=int(row['original_line_number']),
                    original_number=original_number,
                    label_ja=row['label_ja'],
                    label_en=row['label_en'],
                    prompt=row['prompt'],
                    category=row['category'],
                    tags=row['tags'].split(',') if row['tags'] else [],
                    created_date=created_date,
                    last_used=last_used,
                    label_source=row['label_source']
                )

                prompts.append(prompt)

        self.prompts = prompts
        return prompts

    def rebuild_library(
        self,
        force_copy: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> bool:
        """ライブラリを再構築

        ファイルのコピー → スキャン → CSV保存の一連の処理を実行。

        Args:
            force_copy: 強制的にファイルをコピーするか
            progress_callback: 進捗コールバック(current, total, message)

        Returns:
            成功した場合True
        """
        # ステップ1: ファイルコピー
        if not self.initialize_library(force_copy, progress_callback):
            return False

        # ステップ2: スキャン
        self.scan_and_build_library(progress_callback)

        # ステップ3: CSV保存
        if progress_callback:
            progress_callback(0, 1, "Saving to CSV...")

        self.save_to_csv()

        if progress_callback:
            progress_callback(1, 1, f"Library saved: {len(self.prompts)} prompts")

        return True

    def get_prompts(self) -> List[Prompt]:
        """現在のプロンプトリストを取得

        Returns:
            Promptオブジェクトのリスト
        """
        return self.prompts
