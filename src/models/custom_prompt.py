"""自作プロンプトモデル

ユーザーが作成・保存したプロンプトを管理します。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import SerializableMixin


@dataclass
class CustomPrompt(SerializableMixin):
    """自作プロンプトモデル

    ユーザーが作成・保存したプロンプトを管理します。

    Attributes:
        id: 一意識別子（custom_001, custom_002, ...）
        prompt: プロンプト本体
        label_ja: 日本語ラベル
        label_en: 英語ラベル（オプション）
        category: カテゴリ（既存カテゴリ or 新規）
        tags: タグリスト
        created_date: 作成日時
        last_used: 最終使用日時
        usage_count: 使用回数
        used_in_projects: 使用したプロジェクト名のリスト
        notes: メモ（オプション）
    """
    id: str
    prompt: str
    label_ja: str
    label_en: str = ""
    category: str = "自作"
    tags: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    used_in_projects: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換

        Returns:
            辞書形式のデータ
        """
        return {
            "id": self.id,
            "prompt": self.prompt,
            "label_ja": self.label_ja,
            "label_en": self.label_en,
            "category": self.category,
            "tags": self.tags,
            "created_date": self.created_date.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "used_in_projects": self.used_in_projects,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomPrompt':
        """辞書から復元

        Args:
            data: 辞書形式のデータ

        Returns:
            復元されたCustomPromptオブジェクト
        """
        # datetimeフィールドを変換
        data = cls._deserialize_datetime(data, cls)

        return cls(**data)

    def record_usage(self, project_name: str):
        """使用履歴を記録

        Args:
            project_name: プロジェクト名
        """
        self.last_used = datetime.now()
        self.usage_count += 1

        if project_name not in self.used_in_projects:
            self.used_in_projects.append(project_name)

    def matches_search(self, query: str) -> bool:
        """検索クエリにマッチするかチェック

        Args:
            query: 検索クエリ

        Returns:
            マッチする場合True
        """
        query_lower = query.lower()

        # ラベル、プロンプト、タグを検索
        if query_lower in self.label_ja.lower():
            return True

        if query_lower in self.label_en.lower():
            return True

        if query_lower in self.prompt.lower():
            return True

        if any(query_lower in tag.lower() for tag in self.tags):
            return True

        return False
