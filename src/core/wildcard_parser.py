"""ワイルドカードパーサー

ワイルドカードファイルをパースしてプロンプトライブラリを構築します。
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional

from models import Prompt, generate_id
from utils.file_utils import (
    read_text_file,
    extract_category_from_path,
    format_wildcard_path,
    scan_text_files
)


class WildcardParser:
    """ワイルドカードパーサー

    4種類のファイル形式に対応:
    1. 番号+テーブル型: `14→ | 服着たままオナニー | clothed masturbation |`
    2. テーブル型: `| 教室 | classroom interior |`
    3. 番号付き型: `14→clothed masturbation`
    4. シンプル型: `clothed masturbation`
    """

    # パターン定義（優先度順）
    PATTERN_1 = re.compile(r'^(\d+)→\s*\|\s*([^|]+?)\s*\|\s*`?([^|`]+?)`?\s*\|')
    PATTERN_2 = re.compile(r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|')
    PATTERN_3 = re.compile(r'^(\d+)→(.+)')

    def __init__(self, wildcard_dir: Path):
        """初期化

        Args:
            wildcard_dir: ワイルドカードディレクトリ
        """
        self.wildcard_dir = wildcard_dir
        self.prompts: List[Prompt] = []

    def scan_directory(self, progress_callback=None, exclude_patterns: Optional[List[str]] = None) -> List[Prompt]:
        """ディレクトリを再帰的にスキャン

        Args:
            progress_callback: 進捗コールバック関数（オプション）
                              progress_callback(current, total, message)
            exclude_patterns: 除外パターンのリスト（例: ["backup_*", ".git"]）

        Returns:
            Promptオブジェクトのリスト
        """
        self.prompts.clear()

        # テキストファイルをスキャン
        text_files = scan_text_files(self.wildcard_dir, recursive=True, exclude_patterns=exclude_patterns)

        total_files = len(text_files)
        for i, file_path in enumerate(text_files):
            # ファイルをパース
            file_prompts = self.parse_file(file_path)
            self.prompts.extend(file_prompts)

            # 進捗通知
            if progress_callback:
                relative_path = file_path.relative_to(self.wildcard_dir)
                progress_callback(i + 1, total_files, f"Parsing: {relative_path}")

        return self.prompts

    def parse_file(self, file_path: Path) -> List[Prompt]:
        """ファイルをパース

        Args:
            file_path: ファイルパス

        Returns:
            Promptオブジェクトのリスト
        """
        prompts = []

        # カテゴリ抽出
        category = extract_category_from_path(file_path, self.wildcard_dir)

        # 相対パス取得（CSV保存用）
        relative_path = str(file_path.relative_to(self.wildcard_dir))

        # ファイル読み込み（エンコーディング自動検出、BOM除去、空行スキップ）
        lines = read_text_file(file_path)

        # 行ごとにパース
        for line_num, line in enumerate(lines, 1):
            label, prompt, original_number = self.extract_label_and_prompt(line)

            # プロンプトID生成
            file_stem = file_path.stem
            prompt_id = generate_id("prompt", file_stem, line_num)

            # Promptオブジェクト生成
            prompt_obj = Prompt(
                id=prompt_id,
                source_file=relative_path,
                original_line_number=line_num,
                original_number=original_number,
                label_ja=label,
                label_en="",
                prompt=prompt,
                category=category,
                tags=[],
                label_source="auto_extract"
            )

            prompts.append(prompt_obj)

        return prompts

    def extract_label_and_prompt(self, line: str) -> Tuple[str, str, int | None]:
        """行からラベルとプロンプトを抽出

        Args:
            line: 行内容

        Returns:
            (label, prompt, original_number)
        """
        # パターン1: 番号+テーブル型
        match = self.PATTERN_1.match(line)
        if match:
            number, label, prompt = match.groups()
            return label.strip(), prompt.strip(), int(number)

        # パターン2: テーブル型
        match = self.PATTERN_2.match(line)
        if match:
            label, prompt = match.groups()
            return label.strip(), prompt.strip(), None

        # パターン3: 番号付き型
        match = self.PATTERN_3.match(line)
        if match:
            number, prompt = match.groups()
            prompt = prompt.strip()
            return prompt, prompt, int(number)

        # パターン4: シンプル型
        return line.strip(), line.strip(), None

    def get_wildcard_path(self, file_path: Path) -> str:
        """ワイルドカードパスを取得

        Args:
            file_path: ファイルパス

        Returns:
            ワイルドカード形式（例: __posing/arm__）
        """
        return format_wildcard_path(file_path, self.wildcard_dir)
