"""APIキー管理モジュール

Claude APIキーを安全に保存・管理します。
FR-017: セキュアなAPIキー管理
"""

import os
import json
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet


class APIKeyManager:
    """APIキー管理クラス

    Fernet（AES128）で暗号化してAPIキーを保存します。
    マスターキーは環境変数またはOSキーチェーンに保存。
    """

    def __init__(self, data_dir: Path):
        """初期化

        Args:
            data_dir: データディレクトリ
        """
        self.data_dir = data_dir
        self.key_file = data_dir / ".api_keys.enc"

        # マスターキー取得または生成
        self.master_key = self._get_or_create_master_key()
        self.fernet = Fernet(self.master_key)

    def _get_or_create_master_key(self) -> bytes:
        """マスターキーを取得または生成

        Returns:
            マスターキー（bytes）
        """
        # 環境変数から取得を試みる
        env_key = os.environ.get("PFFT_MAKER_MASTER_KEY")
        if env_key:
            return env_key.encode()

        # マスターキーファイルから読み込み
        master_key_file = self.data_dir / ".master_key"

        if master_key_file.exists():
            return master_key_file.read_bytes()

        # 新規生成
        master_key = Fernet.generate_key()

        # ファイルに保存（隠しファイル化）
        self.data_dir.mkdir(parents=True, exist_ok=True)
        master_key_file.write_bytes(master_key)

        # Windows: 隠しファイル化
        try:
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(str(master_key_file), FILE_ATTRIBUTE_HIDDEN)
        except:
            pass

        return master_key

    def save_api_key(self, service: str, api_key: str):
        """APIキーを保存

        Args:
            service: サービス名（例: "claude", "lm_studio"）
            api_key: APIキー
        """
        # 既存のキーを読み込み
        keys = self._load_keys()

        # 暗号化して保存
        encrypted_key = self.fernet.encrypt(api_key.encode()).decode()
        keys[service] = encrypted_key

        # ファイルに保存
        self._save_keys(keys)

    def get_api_key(self, service: str) -> Optional[str]:
        """APIキーを取得

        Args:
            service: サービス名

        Returns:
            APIキー、存在しない場合None
        """
        keys = self._load_keys()

        if service not in keys:
            return None

        # 復号化
        try:
            encrypted_key = keys[service].encode()
            return self.fernet.decrypt(encrypted_key).decode()
        except Exception as e:
            print(f"[Warning] Failed to decrypt API key for {service}: {e}")
            return None

    def delete_api_key(self, service: str):
        """APIキーを削除

        Args:
            service: サービス名
        """
        keys = self._load_keys()

        if service in keys:
            del keys[service]
            self._save_keys(keys)

    def has_api_key(self, service: str) -> bool:
        """APIキーが存在するかチェック

        Args:
            service: サービス名

        Returns:
            存在する場合True
        """
        keys = self._load_keys()
        return service in keys

    def _load_keys(self) -> dict:
        """キーファイルを読み込み

        Returns:
            キー辞書
        """
        if not self.key_file.exists():
            return {}

        try:
            return json.loads(self.key_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Warning] Failed to load API keys: {e}")
            return {}

    def _save_keys(self, keys: dict):
        """キーファイルに保存

        Args:
            keys: キー辞書
        """
        # ディレクトリ作成
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # JSON保存
        self.key_file.write_text(
            json.dumps(keys, indent=2),
            encoding="utf-8"
        )

        # Windows: 隠しファイル化
        try:
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(str(self.key_file), FILE_ATTRIBUTE_HIDDEN)
        except:
            pass

    def test_connection(self, service: str) -> tuple[bool, str]:
        """接続テスト

        Args:
            service: サービス名

        Returns:
            (成功したか, メッセージ)
        """
        api_key = self.get_api_key(service)

        if not api_key:
            return False, "APIキーが設定されていません"

        if service == "claude":
            # Claude API接続テスト
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)

                # シンプルなリクエストでテスト
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "test"}]
                )

                return True, "接続成功"

            except Exception as e:
                return False, f"接続失敗: {str(e)}"

        elif service == "lm_studio":
            # LM Studio接続テスト（OpenAI互換API）
            # TODO: 実装
            return True, "接続テスト未実装"

        return False, "不明なサービス"
