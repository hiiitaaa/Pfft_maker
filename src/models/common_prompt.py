"""共通プロンプトモデル

新規シーン作成時に自動挿入されるプロンプトテンプレート。
"""

from dataclasses import dataclass, field
from typing import Dict, Any

from .base import SerializableMixin


@dataclass
class CommonPrompt(SerializableMixin):
    """共通プロンプトモデル

    Attributes:
        name: 共通プロンプト名（例: "品質タグ", "LoRA"）
        content: プロンプト内容
        enabled: 有効/無効
        position: 挿入位置（"start": 先頭, "end": 末尾）
        insert_break_after: BREAK挿入フラグ
    """
    name: str
    content: str
    enabled: bool = True
    position: str = "end"  # "start" or "end"
    insert_break_after: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return {
            "name": self.name,
            "content": self.content,
            "enabled": self.enabled,
            "position": self.position,
            "insert_break_after": self.insert_break_after
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommonPrompt':
        """辞書から復元"""
        return cls(**data)

    @classmethod
    def create_default_quality_tags(cls) -> 'CommonPrompt':
        """デフォルト品質タグを作成"""
        return cls(
            name="品質タグ",
            content="masterpiece, best quality, amazing quality, very aesthetic, absurdres",
            enabled=True,
            position="end",
            insert_break_after=False
        )

    @classmethod
    def create_default_lora(cls) -> 'CommonPrompt':
        """デフォルトLoRAを作成"""
        return cls(
            name="LoRA",
            content="<lora:example:0.7>",
            enabled=False,
            position="start",
            insert_break_after=True
        )
