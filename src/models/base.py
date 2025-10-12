"""共通データモデル基底クラス

すべてのデータモデルで使用する共通機能を提供します。
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any
from datetime import datetime
import json


@dataclass
class SerializableMixin:
    """シリアライズ可能なMixin

    JSONへの変換・復元機能を提供。コードの再利用を促進。
    """

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換

        Returns:
            辞書形式のデータ
        """
        data = asdict(self)
        # datetimeオブジェクトをISO形式文字列に変換
        return self._serialize_datetime(data)

    def to_json(self) -> str:
        """JSON文字列に変換

        Returns:
            JSON形式の文字列
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """辞書から復元

        Args:
            data: 辞書形式のデータ

        Returns:
            復元されたオブジェクト
        """
        # datetimeフィールドを自動変換
        data = cls._deserialize_datetime(data, cls)
        return cls(**data)

    @staticmethod
    def _serialize_datetime(data: Dict[str, Any]) -> Dict[str, Any]:
        """datetimeオブジェクトをISO形式文字列に変換（再帰的）

        Args:
            data: 変換対象の辞書

        Returns:
            変換後の辞書
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = SerializableMixin._serialize_datetime(value)
            elif isinstance(value, list):
                result[key] = [
                    SerializableMixin._serialize_datetime(item) if isinstance(item, dict)
                    else item.isoformat() if isinstance(item, datetime)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

    @staticmethod
    def _deserialize_datetime(data: Dict[str, Any], cls) -> Dict[str, Any]:
        """ISO形式文字列をdatetimeオブジェクトに変換

        Args:
            data: 変換対象の辞書
            cls: データクラスの型

        Returns:
            変換後の辞書
        """
        result = {}
        annotations = getattr(cls, '__annotations__', {})

        for key, value in data.items():
            # 型ヒントを確認してdatetime変換
            field_type = annotations.get(key)

            if field_type and 'datetime' in str(field_type) and isinstance(value, str):
                try:
                    result[key] = datetime.fromisoformat(value)
                except (ValueError, AttributeError):
                    result[key] = value
            else:
                result[key] = value

        return result


def generate_id(prefix: str, *parts) -> str:
    """一意なIDを生成

    Args:
        prefix: IDのプレフィックス
        *parts: ID構成要素

    Returns:
        生成されたID

    Example:
        >>> generate_id("prompt", "tipo_play", 14)
        "prompt_tipo_play_14"
    """
    parts_str = "_".join(str(p) for p in parts)
    return f"{prefix}_{parts_str}" if parts_str else prefix
