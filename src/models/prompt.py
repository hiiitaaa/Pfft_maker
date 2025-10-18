"""プロンプトモデル

ライブラリ内のプロンプトを表現します。
"""

from dataclasses import dataclass, field
from typing import List
from datetime import datetime

from .base import SerializableMixin


@dataclass
class Prompt(SerializableMixin):
    """プロンプトモデル

    ワイルドカードファイルから読み込んだプロンプト情報。

    Attributes:
        id: プロンプトID（一意）
        source_file: ソースファイル（相対パス）
        original_line_number: 元ファイルの行番号（参考情報）
        original_number: 元の番号（14→の14、照合に使用）
        label_ja: 日本語ラベル
        label_en: 英語ラベル
        prompt: プロンプト本文
        category: カテゴリ
        tags: タグリスト
        created_date: 作成日時
        last_used: 最終使用日時
        label_source: ラベルのソース（auto_extract, ai_generated, manual, auto_word_split）
        lora_metadata: LoRA専用メタデータ（JSON文字列）
    """
    id: str
    source_file: str
    original_line_number: int | None
    original_number: int | None
    label_ja: str
    label_en: str
    prompt: str
    category: str
    tags: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    last_used: datetime | None = None
    label_source: str = "auto_extract"
    lora_metadata: str | None = None

    def mark_as_used(self):
        """使用済みとしてマーク

        Note:
            実際のCSV書き込みはLibraryManagerが担当（キャッシュ方式）
        """
        self.last_used = datetime.now()

    def add_tag(self, tag: str):
        """タグを追加

        Args:
            tag: 追加するタグ
        """
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """タグを削除

        Args:
            tag: 削除するタグ
        """
        if tag in self.tags:
            self.tags.remove(tag)

    def matches_search(self, query: str) -> bool:
        """検索クエリにマッチするかチェック

        label_ja, label_en, prompt, tags, source_fileを検索対象とする。

        Args:
            query: 検索クエリ

        Returns:
            マッチする場合True
        """
        query_lower = query.lower()

        # 各フィールドを検索
        searchable_fields = [
            self.label_ja.lower(),
            self.label_en.lower(),
            self.prompt.lower(),
            self.source_file.lower(),
            " ".join(self.tags).lower()
        ]

        return any(query_lower in field for field in searchable_fields)

    @classmethod
    def create_from_line(
        cls,
        file_path: str,
        line_number: int,
        line_content: str,
        category: str
    ) -> 'Prompt':
        """ファイルの行からプロンプトを作成

        Args:
            file_path: ファイルパス
            line_number: 行番号
            line_content: 行内容
            category: カテゴリ

        Returns:
            新規Promptオブジェクト
        """
        from .base import generate_id

        # ファイル名からIDを生成
        file_name = file_path.split('/')[-1].replace('.txt', '')
        prompt_id = generate_id("prompt", file_name, line_number)

        return cls(
            id=prompt_id,
            source_file=file_path,
            original_line_number=line_number,
            original_number=None,  # パーサーが設定
            label_ja=line_content,  # パーサーが更新
            label_en="",
            prompt=line_content,
            category=category,
            tags=[],
            label_source="auto_extract"
        )
