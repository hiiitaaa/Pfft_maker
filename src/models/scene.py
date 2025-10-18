"""シーンモデル

1つのシーン（1枚の画像生成単位）を表現します。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

from .base import SerializableMixin
from .block import Block, BlockType


@dataclass
class Scene(SerializableMixin):
    """シーンモデル

    1シーン = 1プロンプト = 1画像生成。

    Attributes:
        scene_id: シーンID（1から始まる連番）
        scene_name: シーン名（例: "保健室", "教室"）
        is_completed: 完成フラグ（手動マーク方式）
        blocks: ブロックのリスト
        created_date: 作成日時
        source_library_id: 元のシーンライブラリアイテムのID（読み込み元がある場合）
    """
    scene_id: int
    scene_name: str
    is_completed: bool = False
    blocks: List[Block] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    source_library_id: str | None = None  # 元のシーンライブラリアイテムのID

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換

        Blockオブジェクトも再帰的に変換。

        Returns:
            辞書形式のデータ
        """
        data = super().to_dict()
        data['blocks'] = [block.to_dict() for block in self.blocks]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scene':
        """辞書から復元

        Args:
            data: 辞書形式のデータ

        Returns:
            復元されたSceneオブジェクト
        """
        # blocksをBlockオブジェクトに変換
        if 'blocks' in data:
            data['blocks'] = [Block.from_dict(b) for b in data['blocks']]

        # datetimeフィールドを変換
        data = cls._deserialize_datetime(data, cls)

        return cls(**data)

    def add_block(self, block: Block):
        """ブロックを追加

        Args:
            block: 追加するブロック
        """
        self.blocks.append(block)

    def insert_block(self, index: int, block: Block):
        """ブロックを挿入

        Args:
            index: 挿入位置
            block: 挿入するブロック
        """
        self.blocks.insert(index, block)

    def remove_block(self, block_id: int):
        """ブロックを削除

        Args:
            block_id: 削除するブロックのID
        """
        self.blocks = [b for b in self.blocks if b.block_id != block_id]

    def move_block(self, block_id: int, direction: int):
        """ブロックを移動

        Args:
            block_id: 移動するブロックのID
            direction: 移動方向（-1: 上、1: 下）
        """
        for i, block in enumerate(self.blocks):
            if block.block_id == block_id:
                new_index = i + direction
                if 0 <= new_index < len(self.blocks):
                    self.blocks.pop(i)
                    self.blocks.insert(new_index, block)
                break

    def get_wildcard_blocks(self) -> List[Block]:
        """ワイルドカードブロックのみを取得

        Returns:
            ワイルドカードブロックのリスト
        """
        return [b for b in self.blocks if b.type == BlockType.WILDCARD]

    def validate(self) -> tuple[bool, str]:
        """シーンのバリデーション

        連続BREAKなどのエラーをチェック。

        Returns:
            (有効かどうか, エラーメッセージ)
        """
        # 連続BREAKチェック
        for i in range(len(self.blocks) - 1):
            if (self.blocks[i].type == BlockType.BREAK and
                self.blocks[i + 1].type == BlockType.BREAK):
                return False, "連続したBREAKは使用できません"

        return True, ""

    def get_next_block_id(self) -> int:
        """次のブロックIDを取得

        Returns:
            次に使用可能なブロックID
        """
        if not self.blocks:
            return 1
        return max(b.block_id for b in self.blocks) + 1
