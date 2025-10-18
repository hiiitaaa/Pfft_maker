"""バックアップ管理モジュール

ユーザーデータの自動バックアップと復元機能を提供
"""

import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from utils.logger import get_logger


class BackupManager:
    """ユーザーデータのバックアップ管理"""

    def __init__(self, data_dir: Path, backup_dir: Path):
        """初期化

        Args:
            data_dir: データディレクトリ
            backup_dir: バックアップディレクトリ
        """
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.logger = get_logger()

        # バックアップ対象ファイル
        self.backup_targets = [
            "project_library.json",
            "scene_library.json",
            "custom_prompts.json",
            "templates.json",
            "settings.json",
        ]

    def create_backup(self, backup_name: Optional[str] = None) -> Tuple[bool, str, Optional[Path]]:
        """バックアップを作成

        Args:
            backup_name: バックアップ名（Noneの場合は自動生成）

        Returns:
            (成功したか, メッセージ, バックアップパス)
        """
        try:
            # バックアップ名を生成
            if backup_name is None:
                backup_name = datetime.now().strftime("%Y%m%d_%H%M%S")

            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)

            # ファイルをコピー
            backed_up_files = []
            for filename in self.backup_targets:
                source = self.data_dir / filename
                if source.exists():
                    dest = backup_path / filename
                    shutil.copy2(source, dest)
                    backed_up_files.append(filename)
                    self.logger.debug(f"バックアップ: {filename} -> {dest}")

            if not backed_up_files:
                self.logger.warning("バックアップ対象のファイルが見つかりませんでした")
                return False, "バックアップ対象のファイルがありません", None

            # メタデータ保存
            metadata = {
                "created_at": datetime.now().isoformat(),
                "files": backed_up_files,
                "file_count": len(backed_up_files)
            }
            metadata_path = backup_path / "backup_metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

            self.logger.info(f"バックアップ作成完了: {backup_path} ({len(backed_up_files)}ファイル)")
            return True, f"{len(backed_up_files)}ファイルをバックアップしました", backup_path

        except Exception as e:
            self.logger.exception(f"バックアップ作成中にエラー: {e}")
            return False, f"バックアップ作成に失敗しました: {e}", None

    def restore_backup(self, backup_name: str) -> Tuple[bool, str]:
        """バックアップから復元

        Args:
            backup_name: バックアップ名

        Returns:
            (成功したか, メッセージ)
        """
        try:
            backup_path = self.backup_dir / backup_name
            if not backup_path.exists():
                return False, f"バックアップが見つかりません: {backup_name}"

            # メタデータ読み込み
            metadata_path = backup_path / "backup_metadata.json"
            if metadata_path.exists():
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                files_to_restore = metadata.get("files", [])
            else:
                # メタデータがない場合は全ファイルを対象
                files_to_restore = [f.name for f in backup_path.iterdir() if f.is_file()]

            # データディレクトリ作成
            self.data_dir.mkdir(parents=True, exist_ok=True)

            # ファイルを復元
            restored_files = []
            for filename in files_to_restore:
                if filename == "backup_metadata.json":
                    continue

                source = backup_path / filename
                if source.exists():
                    dest = self.data_dir / filename
                    shutil.copy2(source, dest)
                    restored_files.append(filename)
                    self.logger.debug(f"復元: {source} -> {dest}")

            if not restored_files:
                return False, "復元するファイルが見つかりませんでした"

            self.logger.info(f"バックアップ復元完了: {backup_name} ({len(restored_files)}ファイル)")
            return True, f"{len(restored_files)}ファイルを復元しました"

        except Exception as e:
            self.logger.exception(f"バックアップ復元中にエラー: {e}")
            return False, f"バックアップ復元に失敗しました: {e}"

    def list_backups(self) -> List[Tuple[str, datetime, int]]:
        """バックアップ一覧を取得

        Returns:
            (バックアップ名, 作成日時, ファイル数) のリスト
        """
        if not self.backup_dir.exists():
            return []

        backups = []
        for backup_path in sorted(self.backup_dir.iterdir(), reverse=True):
            if not backup_path.is_dir():
                continue

            # メタデータ読み込み
            metadata_path = backup_path / "backup_metadata.json"
            if metadata_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                    created_at = datetime.fromisoformat(metadata["created_at"])
                    file_count = metadata["file_count"]
                except:
                    created_at = datetime.fromtimestamp(backup_path.stat().st_mtime)
                    file_count = len([f for f in backup_path.iterdir() if f.is_file()])
            else:
                created_at = datetime.fromtimestamp(backup_path.stat().st_mtime)
                file_count = len([f for f in backup_path.iterdir() if f.is_file()])

            backups.append((backup_path.name, created_at, file_count))

        return backups

    def cleanup_old_backups(self, days: int = 30, keep_count: int = 10):
        """古いバックアップを削除

        Args:
            days: この日数より古いバックアップを削除
            keep_count: 最低限保持するバックアップ数
        """
        if not self.backup_dir.exists():
            return

        backups = self.list_backups()
        if len(backups) <= keep_count:
            return

        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for backup_name, created_at, _ in backups[keep_count:]:
            if created_at < cutoff_date:
                backup_path = self.backup_dir / backup_name
                try:
                    shutil.rmtree(backup_path)
                    deleted_count += 1
                    self.logger.info(f"古いバックアップを削除: {backup_name}")
                except Exception as e:
                    self.logger.warning(f"バックアップ削除に失敗: {backup_name} - {e}")

        if deleted_count > 0:
            self.logger.info(f"{deleted_count}個の古いバックアップを削除しました")

    def auto_backup_on_startup(self) -> bool:
        """起動時の自動バックアップ

        Returns:
            バックアップを作成した場合True
        """
        # 最新バックアップをチェック
        backups = self.list_backups()
        if backups:
            latest_backup_name, latest_backup_time, _ = backups[0]
            # 24時間以内にバックアップがあればスキップ
            if datetime.now() - latest_backup_time < timedelta(hours=24):
                self.logger.debug(f"最新バックアップ: {latest_backup_name} (スキップ)")
                return False

        # バックアップ作成
        success, message, _ = self.create_backup(backup_name=f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        if success:
            self.logger.info("起動時の自動バックアップを作成しました")
            # 古いバックアップを削除
            self.cleanup_old_backups()
            return True
        else:
            self.logger.warning(f"起動時の自動バックアップに失敗: {message}")
            return False
