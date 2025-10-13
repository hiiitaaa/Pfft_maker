"""テンプレートモデル

プロジェクトテンプレート、シーンテンプレート、ブロックテンプレートを定義します。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import SerializableMixin, generate_id


@dataclass
class BlockTemplate(SerializableMixin):
    """ブロックテンプレートモデル

    シーン内のブロック構造を保存します。

    Attributes:
        type: ブロックタイプ ("fixed_text", "wildcard", "break")
        content: ブロック内容（構成テンプレートの場合は空）
    """
    type: str  # "fixed_text", "wildcard", "break"
    content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換

        Returns:
            辞書形式のデータ
        """
        return {
            'type': self.type,
            'content': self.content
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BlockTemplate':
        """辞書から復元

        Args:
            data: 辞書形式のデータ

        Returns:
            復元されたBlockTemplateオブジェクト
        """
        return cls(
            type=data.get('type', 'fixed_text'),
            content=data.get('content', '')
        )


@dataclass
class SceneTemplate(SerializableMixin):
    """シーンテンプレートモデル

    シーンの構造を保存します。

    Attributes:
        scene_name: シーン名（プレースホルダー可）
        block_templates: ブロックテンプレートのリスト
    """
    scene_name: str = ""
    block_templates: List[BlockTemplate] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換

        Returns:
            辞書形式のデータ
        """
        return {
            'scene_name': self.scene_name,
            'block_templates': [bt.to_dict() for bt in self.block_templates]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneTemplate':
        """辞書から復元

        Args:
            data: 辞書形式のデータ

        Returns:
            復元されたSceneTemplateオブジェクト
        """
        block_templates = [
            BlockTemplate.from_dict(bt)
            for bt in data.get('block_templates', [])
        ]

        return cls(
            scene_name=data.get('scene_name', ''),
            block_templates=block_templates
        )


@dataclass
class ProjectTemplate(SerializableMixin):
    """プロジェクトテンプレートモデル

    プロジェクトの構造を保存し、再利用可能にします。

    Attributes:
        id: テンプレートID
        name: テンプレート名
        description: 説明
        template_type: テンプレートタイプ（"structure" or "complete"）
        scene_count: シーン数
        scene_templates: シーンテンプレートのリスト
        common_prompts: 共通プロンプト設定（辞書形式）
        created_date: 作成日時
        last_used: 最終使用日時
        usage_count: 使用回数
    """
    id: str
    name: str
    description: str = ""
    template_type: str = "structure"  # "structure" or "complete"
    scene_count: int = 1
    scene_templates: List[SceneTemplate] = field(default_factory=list)
    common_prompts: List[Dict[str, Any]] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換

        Returns:
            辞書形式のデータ
        """
        data = super().to_dict()
        data['scene_templates'] = [st.to_dict() for st in self.scene_templates]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectTemplate':
        """辞書から復元

        Args:
            data: 辞書形式のデータ

        Returns:
            復元されたProjectTemplateオブジェクト
        """
        # scene_templatesをSceneTemplateオブジェクトに変換
        scene_templates = [
            SceneTemplate.from_dict(st)
            for st in data.get('scene_templates', [])
        ]

        # datetimeフィールドを変換
        data_copy = data.copy()
        data_copy['scene_templates'] = scene_templates
        data_copy = cls._deserialize_datetime(data_copy, cls)

        return cls(**data_copy)

    @classmethod
    def create_new(cls, name: str, description: str = "",
                   template_type: str = "structure") -> 'ProjectTemplate':
        """新規テンプレートを作成

        Args:
            name: テンプレート名
            description: 説明
            template_type: テンプレートタイプ

        Returns:
            新規テンプレートオブジェクト
        """
        template_id = generate_id("template", datetime.now().strftime("%Y%m%d%H%M%S"))

        return cls(
            id=template_id,
            name=name,
            description=description,
            template_type=template_type,
            created_date=datetime.now()
        )

    def increment_usage(self):
        """使用回数をインクリメント"""
        self.usage_count += 1
        self.last_used = datetime.now()
