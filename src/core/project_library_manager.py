"""作品ライブラリ管理

複数のシーンをまとめた作品の保存・読み込み・管理を行います。
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from models import Project, Scene, ProjectLibraryItem, SceneLibraryItem
from utils.logger import get_logger


class ProjectLibraryManager:
    """作品ライブラリ管理クラス

    project_library.jsonファイルを読み書きし、
    作品ライブラリの保存・読み込み・削除を管理します。
    """

    def __init__(self, data_dir: Path):
        """初期化

        Args:
            data_dir: データディレクトリのパス
        """
        self.data_dir = data_dir
        self.library_file = data_dir / "project_library.json"
        self.items: List[ProjectLibraryItem] = []
        self.logger = get_logger()

        # ライブラリファイルが存在すれば読み込み
        if self.library_file.exists():
            self.load()

    def save_project_to_library(
        self,
        project: Project,
        name: str,
        description: str = "",
        category: str = "その他",
        tags: Optional[List[str]] = None
    ) -> ProjectLibraryItem:
        """プロジェクトを作品ライブラリに保存

        Args:
            project: Projectオブジェクト
            name: 作品名
            description: 説明
            category: カテゴリ
            tags: タグのリスト

        Returns:
            作成されたProjectLibraryItemオブジェクト
        """
        # ライブラリアイテムを作成
        item = ProjectLibraryItem.create_from_project(
            project=project,
            name=name,
            description=description,
            category=category,
            tags=tags or []
        )

        self.items.append(item)
        self.save()

        self.logger.info(
            f"作品ライブラリに保存: {name} ({len(project.scenes)}シーン)"
        )
        return item

    def create_scenes_from_library(
        self,
        item: ProjectLibraryItem,
        project_name: str,
        start_scene_id: int
    ) -> List[Scene]:
        """ライブラリアイテムから複数のシーンを作成

        Args:
            item: ProjectLibraryItemオブジェクト
            project_name: プロジェクト名（使用履歴記録用）
            start_scene_id: 開始シーンID

        Returns:
            作成されたSceneオブジェクトのリスト
        """
        scenes = []

        for i, scene_item in enumerate(item.scenes):
            scene_id = start_scene_id + i

            # シーン作成
            from models import Block, BlockType
            scene = Scene(
                scene_id=scene_id,
                scene_name=scene_item.name,
                is_completed=False
            )

            # ブロックを復元
            for j, block_template in enumerate(scene_item.block_templates, start=1):
                block_type = BlockType(block_template.type)

                block = Block(
                    block_id=j,
                    type=block_type,
                    content=block_template.content
                )
                scene.add_block(block)

            scenes.append(scene)

        # 使用履歴を記録
        item.increment_usage(project_name)
        self.save()

        self.logger.info(
            f"作品ライブラリからシーン作成: {item.name} -> {project_name} "
            f"({len(scenes)}シーン)"
        )
        return scenes

    def get_single_scene_from_library(
        self,
        item: ProjectLibraryItem,
        scene_index: int,
        project_name: str,
        scene_id: int
    ) -> Scene:
        """ライブラリアイテムから単一のシーンを作成

        Args:
            item: ProjectLibraryItemオブジェクト
            scene_index: シーンのインデックス（0から始まる）
            project_name: プロジェクト名（使用履歴記録用）
            scene_id: 新しいシーンのID

        Returns:
            作成されたSceneオブジェクト
        """
        if scene_index < 0 or scene_index >= len(item.scenes):
            raise IndexError(f"シーンインデックスが範囲外: {scene_index}")

        scene_item = item.scenes[scene_index]

        # シーン作成
        from models import Block, BlockType
        scene = Scene(
            scene_id=scene_id,
            scene_name=scene_item.name,
            is_completed=False
        )

        # ブロックを復元
        for i, block_template in enumerate(scene_item.block_templates, start=1):
            block_type = BlockType(block_template.type)

            block = Block(
                block_id=i,
                type=block_type,
                content=block_template.content
            )
            scene.add_block(block)

        # 使用履歴を記録
        item.increment_usage(project_name)
        self.save()

        self.logger.info(
            f"作品ライブラリからシーン作成: {item.name}[{scene_index}] -> {project_name}"
        )
        return scene

    def get_all_items(self) -> List[ProjectLibraryItem]:
        """全ライブラリアイテムを取得

        Returns:
            ライブラリアイテムのリスト
        """
        return self.items

    def get_item_by_id(self, item_id: str) -> Optional[ProjectLibraryItem]:
        """IDでライブラリアイテムを取得

        Args:
            item_id: ライブラリアイテムID

        Returns:
            ライブラリアイテム、見つからない場合None
        """
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def get_most_used(self, limit: int = 5) -> List[ProjectLibraryItem]:
        """最もよく使われるライブラリアイテムを取得

        Args:
            limit: 取得する件数

        Returns:
            使用回数でソートされたライブラリアイテムのリスト
        """
        sorted_items = sorted(self.items, key=lambda x: x.usage_count, reverse=True)
        return sorted_items[:limit]

    def get_recently_used(self, limit: int = 5) -> List[ProjectLibraryItem]:
        """最近使われたライブラリアイテムを取得

        Args:
            limit: 取得する件数

        Returns:
            最終使用日時でソートされたライブラリアイテムのリスト
        """
        # last_usedがNoneでないものだけフィルタ
        used_items = [item for item in self.items if item.last_used is not None]
        sorted_items = sorted(used_items, key=lambda x: x.last_used, reverse=True)
        return sorted_items[:limit]

    def get_by_category(self, category: str) -> List[ProjectLibraryItem]:
        """カテゴリでライブラリアイテムを取得

        Args:
            category: カテゴリ名

        Returns:
            該当するライブラリアイテムのリスト
        """
        return [item for item in self.items if item.category == category]

    def search(self, query: str) -> List[ProjectLibraryItem]:
        """検索クエリでライブラリアイテムを検索

        Args:
            query: 検索クエリ

        Returns:
            マッチするライブラリアイテムのリスト
        """
        return [item for item in self.items if item.matches_search(query)]

    def delete_item(self, item_id: str) -> bool:
        """ライブラリアイテムを削除

        Args:
            item_id: ライブラリアイテムID

        Returns:
            削除に成功したかどうか
        """
        for i, item in enumerate(self.items):
            if item.id == item_id:
                deleted_name = item.name
                del self.items[i]
                self.save()
                self.logger.info(f"作品ライブラリから削除: {deleted_name}")
                return True
        return False

    def update_item(self, item: ProjectLibraryItem) -> bool:
        """ライブラリアイテムを更新

        Args:
            item: 更新するライブラリアイテム

        Returns:
            更新に成功したかどうか
        """
        for i, existing_item in enumerate(self.items):
            if existing_item.id == item.id:
                self.items[i] = item
                self.save()
                self.logger.info(f"作品ライブラリを更新: {item.name}")
                return True
        return False

    def save(self):
        """ライブラリをファイルに保存"""
        data = {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

        # データディレクトリが存在しない場合は作成
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # JSONファイルに書き込み
        with self.library_file.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.debug(f"作品ライブラリ保存: {len(self.items)}件")

    def load(self):
        """ライブラリをファイルから読み込み"""
        try:
            with self.library_file.open('r', encoding='utf-8') as f:
                data = json.load(f)

            # ライブラリアイテムを復元
            self.items = [
                ProjectLibraryItem.from_dict(item)
                for item in data.get('items', [])
            ]

            self.logger.info(f"作品ライブラリ読み込み: {len(self.items)}件")

        except Exception as e:
            self.logger.error(f"作品ライブラリ読み込み失敗: {e}")
            self.items = []

    def get_categories(self) -> List[str]:
        """全カテゴリのリストを取得

        Returns:
            カテゴリ名のリスト（重複なし）
        """
        categories = set()
        for item in self.items:
            categories.add(item.category)
        return sorted(list(categories))
