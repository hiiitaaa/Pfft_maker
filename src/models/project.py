"""プロジェクトモデル

Pfft_makerプロジェクト全体を表現します。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

from .base import SerializableMixin
from .scene import Scene


@dataclass
class Project(SerializableMixin):
    """プロジェクトモデル

    30シーン分のプロンプトをまとめたプロジェクト。

    Attributes:
        name: プロジェクト名
        created_date: 作成日時
        last_modified: 最終更新日時
        description: プロジェクト説明
        scenes: シーンのリスト（最大30個）
        common_prompts: 共通プロンプト（キー: 名前、値: プロンプト）
        metadata: メタデータ（拡張用）
    """
    name: str
    created_date: datetime
    last_modified: datetime
    description: str = ""
    scenes: List[Scene] = field(default_factory=list)
    common_prompts: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換

        Sceneオブジェクトも再帰的に変換。

        Returns:
            辞書形式のデータ
        """
        data = super().to_dict()
        data['scenes'] = [scene.to_dict() for scene in self.scenes]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """辞書から復元

        Args:
            data: 辞書形式のデータ

        Returns:
            復元されたProjectオブジェクト
        """
        # scenesをSceneオブジェクトに変換
        if 'scenes' in data:
            data['scenes'] = [Scene.from_dict(s) for s in data['scenes']]

        # datetimeフィールドを変換
        data = cls._deserialize_datetime(data, cls)

        return cls(**data)

    def add_scene(self, scene: Scene):
        """シーンを追加

        Args:
            scene: 追加するシーン
        """
        self.scenes.append(scene)
        self.update_modified_date()

    def remove_scene(self, scene_id: int):
        """シーンを削除（番号付け直し方式）

        削除後、以降のシーンのscene_idを詰める。

        Args:
            scene_id: 削除するシーンのID
        """
        self.scenes = [s for s in self.scenes if s.scene_id != scene_id]

        # 以降のシーンの番号を詰める
        for i, scene in enumerate(self.scenes, start=1):
            scene.scene_id = i

        self.update_modified_date()

    def get_scene_by_id(self, scene_id: int) -> Scene | None:
        """IDでシーンを取得

        Args:
            scene_id: シーンID

        Returns:
            シーンオブジェクト、見つからない場合None
        """
        for scene in self.scenes:
            if scene.scene_id == scene_id:
                return scene
        return None

    def update_modified_date(self):
        """最終更新日時を更新"""
        self.last_modified = datetime.now()

    def get_next_scene_id(self) -> int:
        """次のシーンIDを取得

        Returns:
            次に使用可能なシーンID
        """
        if not self.scenes:
            return 1
        return max(s.scene_id for s in self.scenes) + 1

    def validate(self) -> tuple[bool, str]:
        """プロジェクトのバリデーション

        Returns:
            (有効かどうか, エラーメッセージ)
        """
        # シーン数チェック
        if len(self.scenes) > 30:
            return False, "シーン数は最大30個までです"

        # 各シーンのバリデーション
        for scene in self.scenes:
            is_valid, error_msg = scene.validate()
            if not is_valid:
                return False, f"シーン{scene.scene_id}: {error_msg}"

        return True, ""

    @classmethod
    def create_new(cls, name: str, description: str = "") -> 'Project':
        """新規プロジェクトを作成

        Args:
            name: プロジェクト名
            description: プロジェクト説明

        Returns:
            新規プロジェクトオブジェクト
        """
        now = datetime.now()
        return cls(
            name=name,
            created_date=now,
            last_modified=now,
            description=description
        )
