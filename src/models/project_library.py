"""作品ライブラリモデル

複数のシーンをまとめた「作品」を保存・管理するためのモデルです。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import SerializableMixin, generate_id
from .scene_library import SceneLibraryItem


@dataclass
class ProjectLibraryItem(SerializableMixin):
    """作品ライブラリアイテム

    複数のシーンをまとめた「作品」の情報を保持します。

    Attributes:
        id: ライブラリアイテムID
        name: 作品名（例: "学園メイドCG集"）
        description: 説明
        category: カテゴリ（"CG集", "漫画"など）
        tags: タグのリスト（検索用）
        scenes: シーンライブラリアイテムのリスト
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
    scenes: List[SceneLibraryItem] = field(default_factory=list)
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
        data['scenes'] = [scene.to_dict() for scene in self.scenes]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectLibraryItem':
        """辞書から復元

        Args:
            data: 辞書形式のデータ

        Returns:
            復元されたProjectLibraryItemオブジェクト
        """
        # scenesをSceneLibraryItemオブジェクトに変換
        if 'scenes' in data:
            data['scenes'] = [
                SceneLibraryItem.from_dict(scene)
                for scene in data['scenes']
            ]

        # datetimeフィールドを変換
        data = cls._deserialize_datetime(data, cls)

        return cls(**data)

    @classmethod
    def create_from_project(
        cls,
        project,  # Project型だがcircular importを避けるため型ヒントなし
        name: str,
        description: str = "",
        category: str = "その他",
        tags: Optional[List[str]] = None
    ) -> 'ProjectLibraryItem':
        """プロジェクトから作品ライブラリアイテムを作成

        Args:
            project: Projectオブジェクト
            name: 作品名
            description: 説明
            category: カテゴリ
            tags: タグのリスト

        Returns:
            作成されたProjectLibraryItemオブジェクト
        """
        # シーンライブラリアイテムを作成
        scene_items = []
        for scene in project.scenes:
            scene_item = SceneLibraryItem.create_from_scene(
                scene=scene,
                name=scene.scene_name,
                description="",
                category=category,
                tags=tags or []
            )
            scene_items.append(scene_item)

        # IDを生成
        item_id = generate_id("project_lib", datetime.now().strftime("%Y%m%d%H%M%S"))

        return cls(
            id=item_id,
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            scenes=scene_items,
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

        # 作品名で検索
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

        # シーン名で検索
        for scene in self.scenes:
            if query_lower in scene.name.lower():
                return True

        return False

    def get_scene_count(self) -> int:
        """シーン数を取得

        Returns:
            シーン数
        """
        return len(self.scenes)
