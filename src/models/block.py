"""ブロックモデル

シーン内のプロンプトブロックを表現します。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any

from .base import SerializableMixin


class BlockType(Enum):
    """ブロックタイプ

    プロンプトブロックの種類を定義。
    """
    FIXED_TEXT = "fixed_text"  # 固定テキスト（📌）
    WILDCARD = "wildcard"      # ワイルドカード（🎲）
    BREAK = "break"            # BREAK区切り
    COMMON = "common"          # 共通プロンプト


@dataclass
class Block(SerializableMixin):
    """ブロックモデル

    シーン内の1つのプロンプトブロックを表現。

    Attributes:
        block_id: ブロックID（シーン内で一意）
        type: ブロックタイプ
        content: ブロックの内容
        source: ソース情報（ファイル名、プロンプトIDなど）
        is_common: 共通プロンプトかどうか
    """
    block_id: int
    type: BlockType
    content: str
    source: Dict[str, Any] = field(default_factory=dict)
    is_common: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換

        BlockTypeをJSON対応形式に変換。

        Returns:
            辞書形式のデータ
        """
        data = super().to_dict()
        data['type'] = self.type.value  # EnumをstringにBLOCK_TYPE変換
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """辞書から復元

        Args:
            data: 辞書形式のデータ

        Returns:
            復元されたBlockオブジェクト
        """
        # typeをBlockTypeに変換
        if 'type' in data and isinstance(data['type'], str):
            data['type'] = BlockType(data['type'])
        return cls(**data)

    def is_wildcard_block(self) -> bool:
        """ワイルドカードブロックかどうか

        Returns:
            ワイルドカードブロックの場合True
        """
        return self.type == BlockType.WILDCARD

    def get_wildcard_path(self) -> str | None:
        """ワイルドカードパスを取得

        Returns:
            ワイルドカードパス（例: __posing/arm__）、ワイルドカードでない場合None
        """
        if self.is_wildcard_block():
            return self.content
        return None
