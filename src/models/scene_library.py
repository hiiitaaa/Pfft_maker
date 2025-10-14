"""シーンライブラリモデル

よく使うシーンを保存・管理するためのモデルです。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import SerializableMixin, generate_id
from .template import BlockTemplate


@dataclass
class SceneLibraryItem(SerializableMixin):
    """シーンライブラリアイテム

    保存されたシーンの情報を保持します。

    Attributes:
        id: ライブラリアイテムID
        name: シーン名
        description: 説明
        category: カテゴリ（"恋愛", "学園", "日常"など）
        tags: タグのリスト（検索用）
        block_templates: ブロックテンプレートのリスト
        created_date: 作成日時
        last_used: 最終使用日時
        usage_count: 使用回数
        used_in_projects: 使用したプロジェクト名のリスト
    """
    id: str
    name: str
    description: str = ""
    category: str = "その他"
    tags: List[str] = field(default_factory=list)
    block_templates: List[BlockTemplate] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    used_in_projects: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換

        Returns:
            辞書形式のデータ
        """
        data = super().to_dict()
        data['block_templates'] = [bt.to_dict() for bt in self.block_templates]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneLibraryItem':
        """辞書から復元

        Args:
            data: 辞書形式のデータ

        Returns:
            復元されたSceneLibraryItemオブジェクト
        """
        # block_templatesをBlockTemplateオブジェクトに変換
        if 'block_templates' in data:
            data['block_templates'] = [
                BlockTemplate.from_dict(bt)
                for bt in data['block_templates']
            ]

        # datetimeフィールドを変換
        data = cls._deserialize_datetime(data, cls)

        return cls(**data)

    @classmethod
    def create_from_scene(
        cls,
        scene,  # Scene型だがcircular importを避けるため型ヒントなし
        name: str,
        description: str = "",
        category: str = "その他",
        tags: Optional[List[str]] = None
    ) -> 'SceneLibraryItem':
        """シーンからライブラリアイテムを作成

        Args:
            scene: Sceneオブジェクト
            name: シーン名
            description: 説明
            category: カテゴリ
            tags: タグのリスト

        Returns:
            作成されたSceneLibraryItemオブジェクト
        """
        # ブロックテンプレートを作成
        block_templates = []
        for block in scene.blocks:
            block_template = BlockTemplate(
                type=block.type.value,
                content=block.content
            )
            block_templates.append(block_template)

        # IDを生成
        item_id = generate_id("scene_lib", datetime.now().strftime("%Y%m%d%H%M%S"))

        return cls(
            id=item_id,
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            block_templates=block_templates,
            created_date=datetime.now()
        )

    def increment_usage(self, project_name: str):
        """使用回数をインクリメント

        Args:
            project_name: 使用したプロジェクト名
        """
        self.usage_count += 1
        self.last_used = datetime.now()

        # プロジェクト名を記録（重複しないように）
        if project_name not in self.used_in_projects:
            self.used_in_projects.append(project_name)

    def matches_search(self, query: str) -> bool:
        """検索クエリにマッチするか判定

        Args:
            query: 検索クエリ

        Returns:
            マッチする場合True
        """
        query_lower = query.lower()

        # 名前で検索
        if query_lower in self.name.lower():
            return True

        # 説明で検索
        if query_lower in self.description.lower():
            return True

        # カテゴリで検索
        if query_lower in self.category.lower():
            return True

        # タグで検索
        for tag in self.tags:
            if query_lower in tag.lower():
                return True

        return False
