"""ライブラリパネル

プロンプトライブラリの表示・検索を行うパネル。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QLabel, QPushButton, QApplication, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from typing import List

from models import Prompt


class LibraryPanel(QWidget):
    """ライブラリパネル

    プロンプトの検索・選択機能を提供。

    Signals:
        prompt_selected: プロンプトが選択された時（Promptオブジェクト）
    """

    # シグナル定義
    prompt_selected = pyqtSignal(object)  # Prompt (固定テキストとして挿入)
    wildcard_selected = pyqtSignal(str)   # str (ワイルドカードパスとして挿入)

    def __init__(self):
        """初期化"""
        super().__init__()

        self.prompts: List[Prompt] = []
        self.filtered_prompts: List[Prompt] = []
        self.current_category: str = "全て"  # カテゴリフィルタ

        # UI構築
        self._create_ui()

        # デバウンスタイマー（検索用）
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._execute_search)

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # タイトル
        title_label = QLabel("プロンプトライブラリ")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # カテゴリフィルタ
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("カテゴリ:"))

        self.category_filter = QComboBox()
        self.category_filter.addItem("全て")
        self.category_filter.currentTextChanged.connect(self._on_category_changed)
        filter_layout.addWidget(self.category_filter)

        layout.addLayout(filter_layout)

        # 検索バー
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("検索...")
        self.search_bar.textChanged.connect(self._on_search_input)
        layout.addWidget(self.search_bar)

        # ボタン
        button_layout = QHBoxLayout()

        load_button = QPushButton("ライブラリを読み込み")
        load_button.clicked.connect(self._on_load_library)
        button_layout.addWidget(load_button)

        self.sync_button = QPushButton("同期")
        self.sync_button.clicked.connect(self._on_sync_files)
        self.sync_button.setEnabled(False)  # 初期は無効
        button_layout.addWidget(self.sync_button)

        layout.addLayout(button_layout)

        # AI機能ボタン
        ai_button_layout = QHBoxLayout()

        self.generate_labels_button = QPushButton("🤖 ラベル一括生成")
        self.generate_labels_button.clicked.connect(self._on_generate_labels)
        self.generate_labels_button.setEnabled(False)  # 初期は無効
        ai_button_layout.addWidget(self.generate_labels_button)

        layout.addLayout(ai_button_layout)

        # ツリー表示
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ラベル", "プロンプト"])
        self.tree.setColumnWidth(0, 200)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)

        # ステータス
        self.status_label = QLabel("ライブラリ: 0件")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

    def load_prompts(self, prompts: List[Prompt]):
        """プロンプトを読み込み

        Args:
            prompts: プロンプトのリスト
        """
        self.prompts = prompts
        self.filtered_prompts = prompts

        # カテゴリリストを更新
        self._update_category_filter()

        self._update_tree()
        self.status_label.setText(f"ライブラリ: {len(prompts)}件")

    def _update_category_filter(self):
        """カテゴリフィルタドロップダウンを更新"""
        # 現在の選択を保存
        current_selection = self.category_filter.currentText()

        # カテゴリ抽出
        categories = set()
        for prompt in self.prompts:
            category = prompt.category or "その他"
            categories.add(category)

        # ドロップダウン更新
        self.category_filter.clear()
        self.category_filter.addItem("全て")
        for category in sorted(categories):
            self.category_filter.addItem(category)

        # 選択を復元（可能なら）
        index = self.category_filter.findText(current_selection)
        if index >= 0:
            self.category_filter.setCurrentIndex(index)

    def _on_search_input(self, text: str):
        """検索入力時（デバウンス処理）

        Args:
            text: 検索クエリ
        """
        # 既存のタイマーを停止
        self.search_timer.stop()
        # 300ms後に検索実行
        self.search_timer.start(300)

    def _on_category_changed(self, category: str):
        """カテゴリフィルタ変更時

        Args:
            category: 選択されたカテゴリ
        """
        self.current_category = category
        self._execute_search()

    def _execute_search(self):
        """検索実行（検索 + カテゴリフィルタ）"""
        query = self.search_bar.text().strip()

        # フィルタリング
        filtered = self.prompts

        # カテゴリフィルタ
        if self.current_category != "全て":
            filtered = [
                p for p in filtered
                if (p.category or "その他") == self.current_category
            ]

        # 検索フィルタ
        if query:
            filtered = [
                p for p in filtered
                if p.matches_search(query)
            ]

        self.filtered_prompts = filtered

        self._update_tree()

        # ステータス表示
        if query or self.current_category != "全て":
            self.status_label.setText(
                f"絞り込み結果: {len(self.filtered_prompts)}件 / {len(self.prompts)}件"
            )
        else:
            self.status_label.setText(f"ライブラリ: {len(self.prompts)}件")

    def _update_tree(self):
        """ツリー表示更新"""
        self.tree.clear()

        # カテゴリごとにグループ化
        categories = {}
        for prompt in self.filtered_prompts:
            category = prompt.category or "その他"
            if category not in categories:
                categories[category] = []
            categories[category].append(prompt)

        # カテゴリごとにツリーアイテム作成
        for category, prompts in sorted(categories.items()):
            # カテゴリノード
            category_item = QTreeWidgetItem([f"{category} ({len(prompts)})", ""])
            category_item.setExpanded(True)
            self.tree.addTopLevelItem(category_item)

            # ファイルごとにグループ化
            files = {}
            for prompt in prompts:
                file_name = prompt.source_file
                if file_name not in files:
                    files[file_name] = []
                files[file_name].append(prompt)

            # ファイルノード
            for file_name, file_prompts in sorted(files.items()):
                file_display_name = file_name.replace("\\", "/").replace(".txt", "")
                file_item = QTreeWidgetItem([
                    f"[FILE] {file_display_name} ({len(file_prompts)})",
                    "[Wildcard]"
                ])
                # ファイル全体を示すデータを保存
                file_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "file",
                    "file_name": file_name,
                    "prompts": file_prompts
                })
                category_item.addChild(file_item)

                # プロンプトノード
                for prompt in file_prompts:
                    prompt_item = QTreeWidgetItem([
                        f"  {prompt.label_ja or prompt.prompt[:30]}",
                        prompt.prompt[:50] + "..." if len(prompt.prompt) > 50 else prompt.prompt
                    ])
                    prompt_item.setData(0, Qt.ItemDataRole.UserRole, prompt)
                    file_item.addChild(prompt_item)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """アイテムダブルクリック時

        Args:
            item: クリックされたアイテム
            column: カラム番号
        """
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if not data:
            return

        # ファイル全体の場合
        if isinstance(data, dict) and data.get("type") == "file":
            # ワイルドカードパス生成
            from utils.file_utils import format_wildcard_path
            from pathlib import Path
            from config.settings import Settings

            settings = Settings()
            local_dir = settings.get_local_dir()
            file_path = local_dir / data["file_name"]

            if file_path.exists():
                wildcard_path = format_wildcard_path(file_path, local_dir)
                self.wildcard_selected.emit(wildcard_path)

        # 個別プロンプトの場合
        elif hasattr(data, 'id'):  # Promptオブジェクト
            self.prompt_selected.emit(data)

    def _on_load_library(self):
        """ライブラリ読み込み（実際のワイルドカードファイル）"""
        from PyQt6.QtWidgets import QProgressDialog, QMessageBox
        from PyQt6.QtCore import Qt
        from core.library_manager import LibraryManager
        from config.settings import Settings

        # プログレスダイアログ作成
        progress = QProgressDialog("ワイルドカードファイルを読み込んでいます...", "キャンセル", 0, 100, self)
        progress.setWindowTitle("ライブラリ読み込み")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        try:
            # ライブラリマネージャー初期化
            settings = Settings()
            manager = LibraryManager(settings)

            # 進捗コールバック
            def on_progress(current: int, total: int, message: str):
                if total > 0:
                    percent = int((current / total) * 100)
                    progress.setValue(percent)
                progress.setLabelText(message)
                QApplication.processEvents()

            # CSVが既に存在する場合は読み込み
            csv_path = settings.get_library_csv_path()
            if csv_path.exists():
                progress.setLabelText("CSVからライブラリを読み込んでいます...")
                prompts = manager.load_from_csv()
                progress.setValue(100)
            else:
                # CSVが存在しない場合はスキャンして構築
                progress.setLabelText("初回セットアップを実行しています...")
                success = manager.rebuild_library(force_copy=False, progress_callback=on_progress)

                if not success:
                    QMessageBox.critical(
                        self,
                        "エラー",
                        f"ワイルドカードファイルの読み込みに失敗しました。\n"
                        f"元ディレクトリ: {settings.source_wildcard_dir}\n\n"
                        f"設定を確認してください。"
                    )
                    progress.close()
                    return

                prompts = manager.get_prompts()
                progress.setValue(100)

            # UIに表示
            self.load_prompts(prompts)

            progress.close()

            # 更新チェック
            self._check_for_updates(show_if_no_updates=False)

            # 成功メッセージ
            QMessageBox.information(
                self,
                "完了",
                f"ライブラリを読み込みました。\n\n"
                f"プロンプト数: {len(prompts)}\n"
                f"データ保存先: {csv_path}"
            )

            # ボタン有効化
            self.sync_button.setEnabled(True)
            self.generate_labels_button.setEnabled(True)

        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "エラー",
                f"ライブラリの読み込み中にエラーが発生しました:\n{e}"
            )

    def _check_for_updates(self, show_if_no_updates: bool = True):
        """ファイル更新チェック

        Args:
            show_if_no_updates: 更新がない場合も通知するか
        """
        from core.file_sync_manager import FileSyncManager
        from config.settings import Settings
        from PyQt6.QtWidgets import QMessageBox

        try:
            settings = Settings()
            sync_manager = FileSyncManager(settings)

            if sync_manager.has_updates():
                summary = sync_manager.get_update_summary()

                reply = QMessageBox.question(
                    self,
                    "ファイル更新検出",
                    f"ワイルドカードファイルに更新があります:\n\n{summary}\n\n今すぐ同期しますか？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self._on_sync_files()
            elif show_if_no_updates:
                QMessageBox.information(
                    self,
                    "更新チェック",
                    "ワイルドカードファイルに更新はありません。"
                )

        except Exception as e:
            QMessageBox.warning(
                self,
                "エラー",
                f"更新チェック中にエラーが発生しました:\n{e}"
            )

    def _on_sync_files(self):
        """ファイル同期"""
        from core.file_sync_manager import FileSyncManager
        from core.library_manager import LibraryManager
        from config.settings import Settings
        from PyQt6.QtWidgets import QMessageBox, QProgressDialog

        try:
            settings = Settings()
            sync_manager = FileSyncManager(settings)

            # 更新チェック
            updates = sync_manager.check_updates()

            if not any([updates["added"], updates["modified"], updates["deleted"]]):
                QMessageBox.information(
                    self,
                    "同期",
                    "同期するファイルがありません。"
                )
                return

            # 確認ダイアログ
            summary = sync_manager.get_update_summary()
            reply = QMessageBox.question(
                self,
                "ファイル同期",
                f"以下のファイルを同期します:\n\n{summary}\n\n実行しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # プログレスダイアログ
            progress = QProgressDialog("ファイルを同期しています...", "キャンセル", 0, 100, self)
            progress.setWindowTitle("同期")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

            # ファイル同期
            sync_count = sync_manager.sync_files(updates)

            progress.setValue(50)
            progress.setLabelText("ライブラリを再構築しています...")

            # ライブラリ再構築
            manager = LibraryManager(settings)

            def on_progress(current, total, message):
                if total > 0:
                    percent = 50 + int((current / total) * 50)
                    progress.setValue(percent)
                progress.setLabelText(message)
                QApplication.processEvents()

            manager.scan_and_build_library(progress_callback=on_progress)
            manager.save_to_csv()

            # UIに表示
            prompts = manager.get_prompts()
            self.load_prompts(prompts)

            progress.close()

            # 完了メッセージ
            QMessageBox.information(
                self,
                "完了",
                f"同期が完了しました。\n\n"
                f"同期ファイル数: {sync_count}\n"
                f"プロンプト数: {len(prompts)}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "エラー",
                f"同期中にエラーが発生しました:\n{e}"
            )

    def _on_generate_labels(self):
        """ラベル一括生成（AI）"""
        from PyQt6.QtWidgets import QProgressDialog
        from ai import LabelGenerator, APIKeyManager, CostEstimator
        from config.settings import Settings

        # label_jaが空のプロンプトをカウント
        empty_label_prompts = [
            p for p in self.prompts
            if not p.label_ja or p.label_ja == p.prompt
        ]

        if not empty_label_prompts:
            QMessageBox.information(
                self,
                "情報",
                "ラベル生成が必要なプロンプトがありません。\n\n全てのプロンプトに既にラベルが設定されています。"
            )
            return

        # コスト見積もり
        estimator = CostEstimator(model="claude-3-haiku-20240307")
        total_cost, count, details = estimator.estimate_label_generation_cost(empty_label_prompts)
        cost_summary = estimator.format_cost_summary(details)

        # 確認ダイアログ（コスト見積もり付き）
        reply = QMessageBox.question(
            self,
            "ラベル一括生成",
            f"AIを使用して{len(empty_label_prompts)}件のプロンプトに\n日本語ラベルを自動生成します。\n\n"
            f"{cost_summary}\n\n実行しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # プログレスダイアログ
        progress = QProgressDialog(
            "ラベルを生成しています...",
            "キャンセル",
            0,
            100,
            self
        )
        progress.setWindowTitle("ラベル生成")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        try:
            # APIキー管理とラベルジェネレーター初期化
            settings = Settings()
            api_key_manager = APIKeyManager(settings.get_data_dir())

            # APIキーの確認
            if not api_key_manager.has_api_key("claude"):
                progress.close()
                reply = QMessageBox.question(
                    self,
                    "APIキー未設定",
                    "Claude APIキーが設定されていません。\n\n設定ダイアログを開きますか？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    from .settings_dialog import SettingsDialog
                    dialog = SettingsDialog(self)
                    dialog.exec()

                return

            generator = LabelGenerator(api_key_manager, use_claude=True)

            # 進捗コールバック
            def on_progress(current: int, total: int, message: str):
                if total > 0:
                    percent = int((current / total) * 100)
                    progress.setValue(percent)
                progress.setLabelText(message)
                QApplication.processEvents()

            # ラベル生成実行
            success_count, failure_count, errors = generator.generate_labels_batch(
                empty_label_prompts,
                progress_callback=on_progress
            )

            progress.setValue(100)

            # 成功した場合はCSVを更新
            if success_count > 0:
                progress.setLabelText("CSVを更新しています...")
                from core.library_manager import LibraryManager
                manager = LibraryManager(settings)
                manager.prompts = self.prompts
                manager.save_to_csv()

            progress.close()

            # 結果表示
            if failure_count == 0:
                QMessageBox.information(
                    self,
                    "完了",
                    f"✅ ラベル生成が完了しました。\n\n"
                    f"成功: {success_count}件\n"
                    f"失敗: {failure_count}件"
                )
            else:
                error_summary = "\n".join(errors[:5])  # 最初の5件のみ表示
                if len(errors) > 5:
                    error_summary += f"\n... 他{len(errors) - 5}件"

                QMessageBox.warning(
                    self,
                    "一部失敗",
                    f"⚠ ラベル生成が一部失敗しました。\n\n"
                    f"成功: {success_count}件\n"
                    f"失敗: {failure_count}件\n\n"
                    f"エラー詳細:\n{error_summary}"
                )

            # UIを更新
            self._update_tree()

        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "エラー",
                f"ラベル生成中にエラーが発生しました:\n{e}"
            )
