"""ファイル同期マネージャー

元ディレクトリとローカルディレクトリの同期を管理します。
"""

import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Callable
from datetime import datetime

from config.settings import Settings
from utils.file_utils import scan_text_files
from utils.logger import get_logger


class FileSyncManager:
    """ファイル同期マネージャー

    元ディレクトリとローカルディレクトリの差分を検出し、
    更新されたファイルを同期します。
    """

    def __init__(self, settings: Settings):
        """初期化

        Args:
            settings: 設定オブジェクト
        """
        self.settings = settings
        self.source_dir = settings.get_source_dir()
        self.local_dir = settings.get_local_dir()
        self.logger = get_logger()

    def check_updates(self) -> Dict[str, List[Path]]:
        """更新チェック

        元ディレクトリとローカルディレクトリを比較し、
        変更されたファイルを検出します。

        Returns:
            差分情報の辞書:
                - "added": 新規追加されたファイル
                - "modified": 変更されたファイル
                - "deleted": 削除されたファイル
        """
        # 元ディレクトリのファイル
        source_files = scan_text_files(
            self.source_dir,
            recursive=True,
            exclude_patterns=self.settings.exclude_patterns
        )

        # ローカルディレクトリのファイル
        local_files = scan_text_files(
            self.local_dir,
            recursive=True,
            exclude_patterns=[]  # ローカルは除外なし
        )

        # 相対パスに変換
        source_paths = {
            f.relative_to(self.source_dir): f
            for f in source_files
        }

        local_paths = {
            f.relative_to(self.local_dir): f
            for f in local_files
        }

        # 差分検出
        added = []
        modified = []
        deleted = []

        # 新規追加・変更検出
        for rel_path, source_file in source_paths.items():
            if rel_path not in local_paths:
                # 新規追加
                added.append(source_file)
            else:
                # 変更チェック
                local_file = local_paths[rel_path]
                if self._is_file_modified(source_file, local_file):
                    modified.append(source_file)

        # 削除検出
        for rel_path, local_file in local_paths.items():
            if rel_path not in source_paths:
                deleted.append(local_file)

        return {
            "added": added,
            "modified": modified,
            "deleted": deleted
        }

    def _is_file_modified(self, source_file: Path, local_file: Path) -> bool:
        """ファイルが変更されているかチェック

        更新日時とファイルサイズを比較します。

        Args:
            source_file: 元ファイル
            local_file: ローカルファイル

        Returns:
            変更されている場合True
        """
        # 更新日時比較
        source_mtime = source_file.stat().st_mtime
        local_mtime = local_file.stat().st_mtime

        if source_mtime > local_mtime:
            return True

        # ファイルサイズ比較
        source_size = source_file.stat().st_size
        local_size = local_file.stat().st_size

        if source_size != local_size:
            return True

        return False

    def has_updates(self) -> bool:
        """更新があるかチェック

        Returns:
            更新がある場合True
        """
        updates = self.check_updates()
        return any([
            updates["added"],
            updates["modified"],
            updates["deleted"]
        ])

    def get_update_summary(self) -> str:
        """更新サマリーを取得

        Returns:
            更新サマリー文字列
        """
        updates = self.check_updates()

        summary_parts = []

        if updates["added"]:
            summary_parts.append(f"追加: {len(updates['added'])}ファイル")

        if updates["modified"]:
            summary_parts.append(f"更新: {len(updates['modified'])}ファイル")

        if updates["deleted"]:
            summary_parts.append(f"削除: {len(updates['deleted'])}ファイル")

        if not summary_parts:
            return "更新はありません"

        return "\n".join(summary_parts)

    def sync_files(
        self,
        updates: Dict[str, List[Path]] = None,
        preserve_user_labels: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[int, Optional[Dict[str, int]]]:
        """ファイルを同期

        Args:
            updates: 更新情報（Noneの場合は自動検出）
            preserve_user_labels: ユーザーラベルを保持するか
            progress_callback: 進捗コールバック

        Returns:
            (同期したファイル数, ラベル保持統計)
        """
        if updates is None:
            updates = self.check_updates()

        self.logger.info(
            f"ファイル同期開始: 追加={len(updates['added'])}, "
            f"更新={len(updates['modified'])}, 削除={len(updates['deleted'])}"
        )

        sync_count = 0
        label_stats = None

        # ユーザーラベル保持が有効な場合、既存のプロンプトを保存
        old_prompts = None
        if preserve_user_labels:
            if progress_callback:
                progress_callback("既存のラベルデータを保存中...")

            # 既存のCSVからプロンプトを読み込み
            from core.library_manager import LibraryManager
            manager = LibraryManager(self.settings)
            csv_path = self.settings.get_library_csv_path()

            if csv_path.exists():
                old_prompts = manager.load_from_csv()
                self.logger.info(f"既存プロンプト: {len(old_prompts)}件")

        # 追加・更新ファイルをコピー
        if progress_callback:
            progress_callback("ファイルを同期中...")

        for file_list in [updates["added"], updates["modified"]]:
            for source_file in file_list:
                rel_path = source_file.relative_to(self.source_dir)
                dest_file = self.local_dir / rel_path

                # 親ディレクトリ作成
                dest_file.parent.mkdir(parents=True, exist_ok=True)

                # ファイルコピー
                import shutil
                shutil.copy2(source_file, dest_file)

                sync_count += 1
                self.logger.debug(f"同期: {rel_path}")

        # 削除ファイルを削除
        for local_file in updates["deleted"]:
            if local_file.exists():
                local_file.unlink()
                sync_count += 1
                rel_path = local_file.relative_to(self.local_dir)
                self.logger.debug(f"削除: {rel_path}")

        self.logger.info(f"ファイル同期完了: {sync_count}ファイル")

        # ユーザーラベル保持処理
        if preserve_user_labels and old_prompts:
            if progress_callback:
                progress_callback("ユーザーラベルを保持中...")

            label_stats = self._preserve_user_labels_after_sync(old_prompts, progress_callback)

        return sync_count, label_stats

    def _preserve_user_labels_after_sync(
        self,
        old_prompts: List,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, int]:
        """同期後にユーザーラベルを保持

        Args:
            old_prompts: 既存のプロンプトリスト

        Returns:
            ラベル保持統計
        """
        from core.library_manager import LibraryManager
        from core.label_preserver import LabelPreserver

        self.logger.info("ユーザーラベル保持処理開始")

        # 新しいプロンプトを再スキャン
        manager = LibraryManager(self.settings)
        new_prompts = manager.scan_and_build_library()

        # ラベル保持
        preserver = LabelPreserver()
        preserved_prompts = preserver.preserve_labels(old_prompts, new_prompts, progress_callback)

        # 統計情報取得
        stats = preserver.get_preservation_stats(old_prompts, preserved_prompts)

        self.logger.info(
            f"ラベル保持完了: 保持={stats['preserved']}件, "
            f"失われた={stats['lost']}件"
        )

        # CSVに保存
        manager.prompts = preserved_prompts
        manager.save_to_csv()

        return stats

    def calculate_file_hash(self, file_path: Path) -> str:
        """ファイルハッシュを計算

        Args:
            file_path: ファイルパス

        Returns:
            SHA256ハッシュ
        """
        sha256 = hashlib.sha256()

        with file_path.open('rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)

        return sha256.hexdigest()
