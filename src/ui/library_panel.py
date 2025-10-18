"""ライブラリパネル

プロンプトライブラリの表示・検索を行うパネル。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QLabel, QPushButton, QApplication, QComboBox,
    QTabWidget, QFrame, QScrollArea, QSizePolicy, QMenu, QInputDialog,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction
from typing import List

from models import Prompt
from models.custom_prompt import CustomPrompt
from models.scene_library import SceneLibraryItem
from models.project_library import ProjectLibraryItem
from core.custom_prompt_manager import CustomPromptManager
from core.scene_library_manager import SceneLibraryManager
from core.project_library_manager import ProjectLibraryManager
from core.lora_library_manager import LoraLibraryManager
from config.settings import Settings
from utils.logger import get_logger


class LibraryPanel(QWidget):
    """ライブラリパネル

    プロンプトの検索・選択機能を提供。

    Signals:
        prompt_selected: プロンプトが選択された時（Promptオブジェクト）
    """

    # シグナル定義
    prompt_selected = pyqtSignal(object)  # Prompt (固定テキストとして挿入)
    wildcard_selected = pyqtSignal(str)   # str (ワイルドカードパスとして挿入)
    scene_selected = pyqtSignal(object)   # SceneLibraryItem (シーン挿入)
    project_selected = pyqtSignal(object)  # ProjectLibraryItem (作品全体挿入)
    project_scene_selected = pyqtSignal(object, int)  # ProjectLibraryItem, scene_index (作品内の個別シーン挿入)

    def __init__(self):
        """初期化"""
        super().__init__()

        self.logger = get_logger()
        self.prompts: List[Prompt] = []
        self.filtered_prompts: List[Prompt] = []
        self.current_category: str = "全て"  # カテゴリフィルタ

        # 自作プロンプト管理
        settings = Settings()
        self.custom_prompt_manager = CustomPromptManager(settings.get_data_dir())
        self.custom_prompts: List[CustomPrompt] = []

        # シーンライブラリ管理
        self.scene_library_manager = SceneLibraryManager(settings.get_data_dir())
        self.scene_library_items: List[SceneLibraryItem] = []

        # 作品ライブラリ管理
        self.project_library_manager = ProjectLibraryManager(settings.get_data_dir())
        self.project_library_items: List[ProjectLibraryItem] = []

        # LoRAライブラリ管理
        self.lora_library_manager = LoraLibraryManager(settings)
        self.lora_prompts: List[Prompt] = []

        # UI構築
        self._create_ui()

        # デバウンスタイマー（検索用）
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._execute_search)

        # 自作プロンプトを読み込み
        self._load_custom_prompts()

        # シーンライブラリを読み込み
        self._load_scene_library()

        # 作品ライブラリを読み込み
        self._load_project_library()

        # LoRAライブラリを読み込み
        self._load_lora_library()

        # ライブラリを自動読み込み（CSVが存在する場合）
        self._auto_load_library()

        self.logger.debug("ライブラリパネル初期化完了")

    def _create_ui(self):
        """UI構築（タブ方式）"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # タイトル
        title_label = QLabel("プロンプトライブラリ")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # タブウィジェット
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # タブ1: ワイルドカード
        self.wildcard_tab = self._create_wildcard_tab()
        self.tab_widget.addTab(self.wildcard_tab, "ワイルドカード")

        # タブ2: LoRAライブラリ（プロンプト構築の初期段階）
        self.lora_tab = self._create_lora_tab()
        self.tab_widget.addTab(self.lora_tab, "🎨LoRA")

        # タブ3: 自作プロンプト
        self.custom_tab = self._create_custom_prompts_tab()
        self.tab_widget.addTab(self.custom_tab, "✨自作プロンプト")

        # タブ4: シーンライブラリ
        self.scene_library_tab = self._create_scene_library_tab()
        self.tab_widget.addTab(self.scene_library_tab, "🎬シーンライブラリ")

        # タブ5: 作品ライブラリ（複数シーンをまとめた作品）
        self.project_library_tab = self._create_project_library_tab()
        self.tab_widget.addTab(self.project_library_tab, "📚作品ライブラリ")

        # ステータス
        self.status_label = QLabel("ライブラリ: 0件")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

    def _create_wildcard_tab(self):
        """ワイルドカードタブを作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # クイックアクセスバー（折りたたみ可能）
        self.quick_access_frame = QFrame()
        self.quick_access_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.quick_access_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f8ff;
                border: 1px solid #4682b4;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        quick_layout = QVBoxLayout(self.quick_access_frame)
        quick_layout.setSpacing(5)

        # ヘッダー（折りたたみボタン付き）
        quick_header = QHBoxLayout()
        self.quick_toggle_btn = QPushButton("✨ よく使うプロンプト ▼")
        self.quick_toggle_btn.setFlat(True)
        self.quick_toggle_btn.setStyleSheet("font-weight: bold; text-align: left;")
        self.quick_toggle_btn.clicked.connect(self._toggle_quick_access)
        quick_header.addWidget(self.quick_toggle_btn)
        quick_header.addStretch()
        quick_layout.addLayout(quick_header)

        # クイックアクセスコンテンツ
        self.quick_content = QWidget()
        self.quick_content_layout = QVBoxLayout(self.quick_content)
        self.quick_content_layout.setSpacing(3)
        self.quick_content_layout.setContentsMargins(10, 0, 0, 0)
        quick_layout.addWidget(self.quick_content)

        layout.addWidget(self.quick_access_frame)

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
        self.sync_button.setEnabled(False)
        button_layout.addWidget(self.sync_button)

        layout.addLayout(button_layout)

        # AI機能ボタン
        ai_button_layout = QHBoxLayout()

        self.generate_labels_button = QPushButton("🤖 ラベル一括生成")
        self.generate_labels_button.clicked.connect(self._on_generate_labels)
        self.generate_labels_button.setEnabled(False)
        ai_button_layout.addWidget(self.generate_labels_button)

        layout.addLayout(ai_button_layout)

        # ツリー表示
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ラベル", "プロンプト"])
        self.tree.setColumnWidth(0, 200)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)

        return tab

    def _create_custom_prompts_tab(self):
        """自作プロンプトタブを作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # 検索バー
        self.custom_search_bar = QLineEdit()
        self.custom_search_bar.setPlaceholderText("自作プロンプトを検索...")
        self.custom_search_bar.textChanged.connect(self._on_custom_search_input)
        layout.addWidget(self.custom_search_bar)

        # ボタン
        button_layout = QHBoxLayout()

        self.add_custom_btn = QPushButton("➕ 新規追加")
        self.add_custom_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_custom_btn.clicked.connect(self._on_add_custom_prompt)
        button_layout.addWidget(self.add_custom_btn)

        self.manage_custom_btn = QPushButton("📂 管理")
        self.manage_custom_btn.clicked.connect(self._on_manage_custom_prompts)
        button_layout.addWidget(self.manage_custom_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 自作プロンプトツリー
        self.custom_tree = QTreeWidget()
        self.custom_tree.setHeaderLabels(["ラベル", "プロンプト", "使用回数"])
        self.custom_tree.setColumnWidth(0, 180)
        self.custom_tree.setColumnWidth(1, 250)
        self.custom_tree.setColumnWidth(2, 80)
        self.custom_tree.itemDoubleClicked.connect(self._on_custom_item_double_clicked)
        layout.addWidget(self.custom_tree)

        return tab

    def _create_scene_library_tab(self):
        """シーンライブラリタブを作成（提案4）"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # よく使うシーンTOP5
        top_frame = QFrame()
        top_frame.setFrameShape(QFrame.Shape.StyledPanel)
        top_frame.setStyleSheet("""
            QFrame {
                background-color: #fff8dc;
                border: 1px solid #ffa500;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        top_layout = QVBoxLayout(top_frame)
        top_layout.setSpacing(5)

        # ヘッダー（折りたたみボタン付き）
        top_header = QHBoxLayout()
        self.scene_top_toggle_btn = QPushButton("⭐ よく使うシーン TOP5 ▼")
        self.scene_top_toggle_btn.setFlat(True)
        self.scene_top_toggle_btn.setStyleSheet("font-weight: bold; text-align: left;")
        self.scene_top_toggle_btn.clicked.connect(self._toggle_scene_top)
        top_header.addWidget(self.scene_top_toggle_btn)
        top_header.addStretch()
        top_layout.addLayout(top_header)

        # コンテンツ
        self.scene_top_content = QWidget()
        self.scene_top_layout = QVBoxLayout(self.scene_top_content)
        self.scene_top_layout.setSpacing(3)
        self.scene_top_layout.setContentsMargins(10, 0, 0, 0)
        top_layout.addWidget(self.scene_top_content)

        layout.addWidget(top_frame)

        # 最近使ったシーン
        recent_frame = QFrame()
        recent_frame.setFrameShape(QFrame.Shape.StyledPanel)
        recent_frame.setStyleSheet("""
            QFrame {
                background-color: #f0fff0;
                border: 1px solid #90ee90;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        recent_layout = QVBoxLayout(recent_frame)
        recent_layout.setSpacing(5)

        # ヘッダー（折りたたみボタン付き）
        recent_header = QHBoxLayout()
        self.scene_recent_toggle_btn = QPushButton("🕒 最近使ったシーン ▼")
        self.scene_recent_toggle_btn.setFlat(True)
        self.scene_recent_toggle_btn.setStyleSheet("font-weight: bold; text-align: left;")
        self.scene_recent_toggle_btn.clicked.connect(self._toggle_scene_recent)
        recent_header.addWidget(self.scene_recent_toggle_btn)
        recent_header.addStretch()
        recent_layout.addLayout(recent_header)

        # コンテンツ
        self.scene_recent_content = QWidget()
        self.scene_recent_layout = QVBoxLayout(self.scene_recent_content)
        self.scene_recent_layout.setSpacing(3)
        self.scene_recent_layout.setContentsMargins(10, 0, 0, 0)
        recent_layout.addWidget(self.scene_recent_content)

        layout.addWidget(recent_frame)

        # 検索バー
        self.scene_search_bar = QLineEdit()
        self.scene_search_bar.setPlaceholderText("シーンを検索...")
        self.scene_search_bar.textChanged.connect(self._on_scene_search_input)
        layout.addWidget(self.scene_search_bar)

        # 全シーン一覧ツリー
        self.scene_tree = QTreeWidget()
        self.scene_tree.setHeaderLabels(["シーン名", "カテゴリ", "ブロック数", "使用回数"])
        self.scene_tree.setColumnWidth(0, 200)
        self.scene_tree.setColumnWidth(1, 100)
        self.scene_tree.setColumnWidth(2, 80)
        self.scene_tree.setColumnWidth(3, 80)
        self.scene_tree.itemDoubleClicked.connect(self._on_scene_item_double_clicked)
        self.scene_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.scene_tree.customContextMenuRequested.connect(self._on_scene_context_menu)
        layout.addWidget(self.scene_tree)

        # シーンライブラリステータス
        self.scene_status_label = QLabel("シーンライブラリ: 0件")
        self.scene_status_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(self.scene_status_label)

        return tab

    def _toggle_scene_top(self):
        """よく使うシーンTOP5の表示/非表示を切り替え"""
        is_visible = self.scene_top_content.isVisible()
        self.scene_top_content.setVisible(not is_visible)

        if is_visible:
            self.scene_top_toggle_btn.setText("⭐ よく使うシーン TOP5 ▶")
        else:
            self.scene_top_toggle_btn.setText("⭐ よく使うシーン TOP5 ▼")

    def _toggle_scene_recent(self):
        """最近使ったシーンの表示/非表示を切り替え"""
        is_visible = self.scene_recent_content.isVisible()
        self.scene_recent_content.setVisible(not is_visible)

        if is_visible:
            self.scene_recent_toggle_btn.setText("🕒 最近使ったシーン ▶")
        else:
            self.scene_recent_toggle_btn.setText("🕒 最近使ったシーン ▼")

    def _toggle_quick_access(self):
        """クイックアクセスバーの表示/非表示を切り替え"""
        is_visible = self.quick_content.isVisible()
        self.quick_content.setVisible(not is_visible)

        if is_visible:
            self.quick_toggle_btn.setText("✨ よく使うプロンプト ▶")
        else:
            self.quick_toggle_btn.setText("✨ よく使うプロンプト ▼")

    def _update_quick_access(self):
        """クイックアクセスバーを更新（よく使うプロンプトTOP5）"""
        # 既存のボタンをクリア
        while self.quick_content_layout.count():
            item = self.quick_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # よく使うプロンプトを取得（TOP5）
        most_used = self.custom_prompt_manager.get_most_used(limit=5)

        if not most_used:
            no_data_label = QLabel("まだ保存されたプロンプトがありません")
            no_data_label.setStyleSheet("color: gray; font-style: italic;")
            self.quick_content_layout.addWidget(no_data_label)
            return

        for cp in most_used:
            btn_layout = QHBoxLayout()

            # プロンプトボタン
            btn = QPushButton(f"📌 {cp.label_ja} ({cp.usage_count}回)")
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 4px 8px;
                    background-color: white;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #e8f4f8;
                    border-color: #4682b4;
                }
            """)
            btn.clicked.connect(lambda checked, p=cp: self._insert_custom_prompt(p))
            btn_layout.addWidget(btn)

            self.quick_content_layout.addLayout(btn_layout)

        # 新規追加ボタン
        add_btn = QPushButton("➕ 新規追加")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_btn.clicked.connect(self._on_add_custom_prompt)
        self.quick_content_layout.addWidget(add_btn)

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

        self.logger.info("ライブラリ読み込み開始")

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

            self.logger.info(f"ライブラリ読み込み完了: {len(prompts)}件")

        except Exception as e:
            self.logger.exception("ライブラリ読み込み中にエラーが発生")
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
            self.logger.error(f"更新チェック中にエラー: {e}", exc_info=True)
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

            # 進捗コールバック
            def on_sync_progress(message: str):
                progress.setLabelText(message)
                QApplication.processEvents()

            # ファイル同期（ユーザーラベル保持込み）
            self.logger.info("ファイル同期開始（ユーザーラベル保持あり）")
            sync_count, label_stats = sync_manager.sync_files(
                updates,
                preserve_user_labels=True,
                progress_callback=on_sync_progress
            )

            progress.setValue(100)

            # 新しいプロンプトをUIに表示
            manager = LibraryManager(settings)
            prompts = manager.load_from_csv()
            self.load_prompts(prompts)

            progress.close()

            # 完了メッセージ（ラベル保持統計付き）
            message = f"同期が完了しました。\n\n"
            message += f"同期ファイル数: {sync_count}\n"
            message += f"プロンプト数: {len(prompts)}\n"

            if label_stats:
                message += f"\n【ユーザーラベル保持】\n"
                message += f"保持: {label_stats['preserved']}件\n"
                if label_stats['lost'] > 0:
                    message += f"⚠️ 失われたラベル: {label_stats['lost']}件"
                else:
                    message += f"✅ 全てのラベルを保持しました"

            self.logger.info(f"同期完了: {sync_count}ファイル, ラベル保持: {label_stats}")

            QMessageBox.information(
                self,
                "完了",
                message
            )

        except Exception as e:
            self.logger.exception("ファイル同期中にエラーが発生")
            QMessageBox.critical(
                self,
                "エラー",
                f"同期中にエラーが発生しました:\n{e}"
            )

    def _on_generate_labels(self):
        """ラベル一括生成（AI）"""
        from PyQt6.QtWidgets import QProgressDialog, QMessageBox
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

        # モード選択と確認ダイアログ
        total_prompts = len(empty_label_prompts)

        # 自動判定モード
        if total_prompts > 1000:
            recommended_mode = "batch"
            mode_text = "Batch API（推奨）"
            mode_desc = "バックグラウンド処理、50%コスト削減\n※完了まで最大1時間"
        elif total_prompts > 50:
            recommended_mode = "async"
            mode_text = "並列処理（推奨）"
            mode_desc = "10件同時実行、高速処理"
        else:
            recommended_mode = "sync"
            mode_text = "通常処理"
            mode_desc = "1件ずつ順番に処理"

        # コスト見積もり
        estimator = CostEstimator(model="claude-3-haiku-20240307")
        total_cost, count, details = estimator.estimate_label_generation_cost(empty_label_prompts)
        cost_summary = estimator.format_cost_summary(details)

        # Batch APIの場合は50%オフ
        if recommended_mode == "batch":
            adjusted_cost = total_cost * 0.5
            cost_summary += f"\n\nBatch API割引（50%オフ）: ${adjusted_cost:.4f}"

        # 確認ダイアログ（コスト見積もり + モード表示）
        reply = QMessageBox.question(
            self,
            "ラベル一括生成",
            f"AIを使用して{total_prompts}件のプロンプトに\n日本語ラベルを自動生成します。\n\n"
            f"【処理モード】\n{mode_text}\n{mode_desc}\n\n"
            f"{cost_summary}\n\n実行しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 選択されたモードを保存
        selected_mode = recommended_mode

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

            # ラベル生成実行（選択されたモードで）
            success_count, failure_count, errors = generator.generate_labels_batch(
                empty_label_prompts,
                progress_callback=on_progress,
                mode=selected_mode
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
            self.logger.exception("ラベル生成中にエラーが発生")
            progress.close()
            QMessageBox.critical(
                self,
                "エラー",
                f"ラベル生成中にエラーが発生しました:\n{e}"
            )

    def _auto_load_library(self):
        """起動時にライブラリを自動読み込み（CSVが存在する場合のみ）"""
        try:
            from core.library_manager import LibraryManager
            from config.settings import Settings

            settings = Settings()
            csv_path = settings.get_library_csv_path()

            # CSVが存在する場合のみ読み込み
            if csv_path.exists():
                self.logger.info("既存のライブラリCSVを自動読み込み中...")

                manager = LibraryManager(settings)
                prompts = manager.load_from_csv()

                # UIに表示
                self.load_prompts(prompts)

                # ボタン有効化
                self.sync_button.setEnabled(True)
                self.generate_labels_button.setEnabled(True)

                self.logger.info(f"ライブラリ自動読み込み完了: {len(prompts)}件")
            else:
                self.logger.info("ライブラリCSVが存在しないため、自動読み込みをスキップ")

        except Exception as e:
            self.logger.error(f"ライブラリ自動読み込みエラー: {e}", exc_info=True)
            # エラーが発生しても続行（手動読み込みボタンは使える）

    def _load_custom_prompts(self):
        """自作プロンプトを読み込み"""
        try:
            self.custom_prompts = self.custom_prompt_manager.prompts
            self.logger.info(f"自作プロンプト読み込み: {len(self.custom_prompts)}件")

            # UI更新
            self._update_custom_tree()
            self._update_quick_access()
        except Exception as e:
            self.logger.error(f"自作プロンプト読み込みエラー: {e}", exc_info=True)
            self.custom_prompts = []

    def reload_custom_prompts(self):
        """自作プロンプトを再読み込み（保存後に呼び出す）"""
        # ファイルから再読み込み
        self.custom_prompt_manager.load()
        self._load_custom_prompts()
        self._update_tree()
        self._update_custom_tree()
        self._update_quick_access()


    def _filter_custom_prompts(self):
        """自作プロンプトをフィルタ"""
        query = self.search_bar.text().strip()

        filtered = self.custom_prompts

        # カテゴリフィルタ
        if self.current_category != "全て" and self.current_category != "自作":
            return []

        # 検索フィルタ
        if query:
            filtered = [p for p in filtered if p.matches_search(query)]

        return filtered

    def _on_custom_search_input(self, text: str):
        """自作プロンプト検索入力時

        Args:
            text: 検索クエリ
        """
        self._update_custom_tree()

    def _update_custom_tree(self):
        """自作プロンプトツリーを更新"""
        self.custom_tree.clear()

        query = self.custom_search_bar.text().strip().lower()

        # フィルタリング
        filtered = self.custom_prompts
        if query:
            filtered = [p for p in filtered if p.matches_search(query)]

        if not filtered:
            no_data = QTreeWidgetItem(["プロンプトがありません", "", ""])
            self.custom_tree.addTopLevelItem(no_data)
            return

        # カテゴリごとにグループ化
        categories = {}
        for cp in filtered:
            category = cp.category or "その他"
            if category not in categories:
                categories[category] = []
            categories[category].append(cp)

        # カテゴリごとに表示
        for category, prompts in sorted(categories.items()):
            category_item = QTreeWidgetItem([f"📁 {category} ({len(prompts)})", "", ""])
            category_item.setExpanded(True)
            self.custom_tree.addTopLevelItem(category_item)

            # プロンプトを使用回数順にソート
            sorted_prompts = sorted(prompts, key=lambda p: p.usage_count, reverse=True)

            for cp in sorted_prompts:
                prompt_item = QTreeWidgetItem([
                    f"📌 {cp.label_ja}",
                    cp.prompt[:50] + "..." if len(cp.prompt) > 50 else cp.prompt,
                    f"{cp.usage_count}回"
                ])
                prompt_item.setData(0, Qt.ItemDataRole.UserRole, cp)
                category_item.addChild(prompt_item)

    def _on_add_custom_prompt(self):
        """新規プロンプト追加ボタンクリック"""
        from .custom_prompt_dialog import CustomPromptDialog

        dialog = CustomPromptDialog(
            custom_prompt_manager=self.custom_prompt_manager,
            prompt_text="",
            parent=self
        )

        if dialog.exec():
            # 保存成功
            saved_prompt = dialog.get_saved_prompt()
            if saved_prompt:
                self._load_custom_prompts()
                self._update_custom_tree()
                self._update_quick_access()
                self.logger.info(f"新規プロンプト追加: {saved_prompt.label_ja}")

    def _on_manage_custom_prompts(self):
        """自作プロンプト管理ボタンクリック"""
        from .custom_prompt_manager_dialog import CustomPromptManagerDialog

        dialog = CustomPromptManagerDialog(
            custom_prompt_manager=self.custom_prompt_manager,
            parent=self
        )

        dialog.exec()

        # ダイアログを閉じた後、UIを更新
        self._load_custom_prompts()

    def _on_custom_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """自作プロンプトツリーのアイテムダブルクリック時

        Args:
            item: クリックされたアイテム
            column: カラム番号
        """
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if not data or not isinstance(data, CustomPrompt):
            return

        # 自作プロンプトを挿入
        self._insert_custom_prompt(data)

    def _insert_custom_prompt(self, custom_prompt: CustomPrompt):
        """自作プロンプトを挿入

        Args:
            custom_prompt: 挿入する自作プロンプト
        """
        # Promptオブジェクトに変換して挿入
        from models import Prompt
        from datetime import datetime

        prompt = Prompt(
            id=custom_prompt.id,
            source_file="custom_prompts",
            original_line_number=0,
            original_number=None,
            label_ja=custom_prompt.label_ja,
            label_en=custom_prompt.label_en,
            prompt=custom_prompt.prompt,
            category=custom_prompt.category,
            tags=custom_prompt.tags,
            created_date=custom_prompt.created_date,
            label_source="user_custom"
        )

        # シグナル発行
        self.prompt_selected.emit(prompt)

        # 使用履歴を記録（プロジェクト名は後で取得）
        self.custom_prompt_manager.record_usage(custom_prompt.id, "不明")

        # UI更新
        self._update_custom_tree()
        self._update_quick_access()

        self.logger.info(f"自作プロンプト挿入: {custom_prompt.label_ja}")

    # ========================================
    # シーンライブラリ関連（提案4）
    # ========================================

    def _load_scene_library(self):
        """シーンライブラリを読み込み"""
        try:
            self.scene_library_items = self.scene_library_manager.items
            self.logger.info(f"シーンライブラリ読み込み: {len(self.scene_library_items)}件")

            # UI更新
            self._update_scene_tree()
            self._update_scene_top()
            self._update_scene_recent()
        except Exception as e:
            self.logger.error(f"シーンライブラリ読み込みエラー: {e}", exc_info=True)
            self.scene_library_items = []

    def reload_scene_library(self):
        """シーンライブラリを再読み込み（保存後に呼び出す）"""
        # ファイルから再読み込み
        self.scene_library_manager.load()
        self._load_scene_library()

    def _update_scene_top(self):
        """よく使うシーンTOP5を更新"""
        # 既存のボタンをクリア
        while self.scene_top_layout.count():
            item = self.scene_top_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # よく使うシーンを取得（TOP5）
        most_used = sorted(
            self.scene_library_items,
            key=lambda s: s.usage_count,
            reverse=True
        )[:5]

        if not most_used:
            no_data_label = QLabel("まだ保存されたシーンがありません")
            no_data_label.setStyleSheet("color: gray; font-style: italic;")
            self.scene_top_layout.addWidget(no_data_label)
            return

        for scene_item in most_used:
            btn_layout = QHBoxLayout()

            # シーンボタン
            block_count = len(scene_item.block_templates)
            # シーン名が汎用的な名前の場合は省略
            if scene_item.name in ["無題のシーン", "Untitled Scene", "新規シーン", ""]:
                btn = QPushButton(f"🎬 {scene_item.usage_count}回使用 / {block_count}ブロック")
            else:
                btn = QPushButton(f"🎬 {scene_item.name} ({scene_item.usage_count}回 / {block_count}ブロック)")
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 4px 8px;
                    background-color: white;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #fff8dc;
                    border-color: #ffa500;
                }
            """)
            btn.clicked.connect(lambda checked, s=scene_item: self._insert_scene(s))
            btn_layout.addWidget(btn)

            self.scene_top_layout.addLayout(btn_layout)

    def _update_scene_recent(self):
        """最近使ったシーンを更新"""
        # 既存のボタンをクリア
        while self.scene_recent_layout.count():
            item = self.scene_recent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 最近使ったシーンを取得（last_usedでソート、TOP5）
        recent_used = [s for s in self.scene_library_items if s.last_used]
        recent_used = sorted(
            recent_used,
            key=lambda s: s.last_used,
            reverse=True
        )[:5]

        if not recent_used:
            no_data_label = QLabel("まだ使用されたシーンがありません")
            no_data_label.setStyleSheet("color: gray; font-style: italic;")
            self.scene_recent_layout.addWidget(no_data_label)
            return

        for scene_item in recent_used:
            btn_layout = QHBoxLayout()

            # シーンボタン
            block_count = len(scene_item.block_templates)
            last_used_str = scene_item.last_used.strftime("%m/%d %H:%M")
            # シーン名が汎用的な名前の場合は省略
            if scene_item.name in ["無題のシーン", "Untitled Scene", "新規シーン", ""]:
                btn = QPushButton(f"🎬 {last_used_str} / {block_count}ブロック")
            else:
                btn = QPushButton(f"🎬 {scene_item.name} ({last_used_str} / {block_count}ブロック)")
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 4px 8px;
                    background-color: white;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #f0fff0;
                    border-color: #90ee90;
                }
            """)
            btn.clicked.connect(lambda checked, s=scene_item: self._insert_scene(s))
            btn_layout.addWidget(btn)

            self.scene_recent_layout.addLayout(btn_layout)

    def _on_scene_search_input(self, text: str):
        """シーン検索入力時

        Args:
            text: 検索クエリ
        """
        self._update_scene_tree()

    def _update_scene_tree(self):
        """シーンツリーを更新"""
        self.scene_tree.clear()

        query = self.scene_search_bar.text().strip().lower()

        # フィルタリング
        filtered = self.scene_library_items
        if query:
            filtered = [s for s in filtered if s.matches_search(query)]

        if not filtered:
            no_data = QTreeWidgetItem(["シーンがありません", "", "", ""])
            self.scene_tree.addTopLevelItem(no_data)
            self.scene_status_label.setText("シーンライブラリ: 0件")
            return

        # カテゴリごとにグループ化
        categories = {}
        for scene_item in filtered:
            category = scene_item.category or "その他"
            if category not in categories:
                categories[category] = []
            categories[category].append(scene_item)

        # カテゴリごとに表示
        for category, scenes in sorted(categories.items()):
            category_item = QTreeWidgetItem([f"📁 {category} ({len(scenes)})", "", "", ""])
            category_item.setExpanded(True)
            self.scene_tree.addTopLevelItem(category_item)

            # シーンを使用回数順にソート
            sorted_scenes = sorted(scenes, key=lambda s: s.usage_count, reverse=True)

            for scene_item in sorted_scenes:
                block_count = len(scene_item.block_templates)
                scene_tree_item = QTreeWidgetItem([
                    f"🎬 {scene_item.name}",
                    scene_item.category,
                    f"{block_count}",
                    f"{scene_item.usage_count}回"
                ])
                scene_tree_item.setData(0, Qt.ItemDataRole.UserRole, scene_item)
                category_item.addChild(scene_tree_item)

        # ステータス更新
        if query:
            self.scene_status_label.setText(
                f"検索結果: {len(filtered)}件 / {len(self.scene_library_items)}件"
            )
        else:
            self.scene_status_label.setText(f"シーンライブラリ: {len(self.scene_library_items)}件")

    def _on_scene_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """シーンツリーのアイテムダブルクリック時

        Args:
            item: クリックされたアイテム
            column: カラム番号
        """
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if not data or not isinstance(data, SceneLibraryItem):
            return

        # シーンを挿入
        self._insert_scene(data)

    def _insert_scene(self, scene_item: SceneLibraryItem):
        """シーンを挿入

        Args:
            scene_item: 挿入するシーンライブラリアイテム
        """
        # シグナル発行
        self.scene_selected.emit(scene_item)

        # 使用履歴を記録（プロジェクト名は呼び出し側で設定）
        # ここでは使用回数のみインクリメント
        scene_item.increment_usage("不明")
        self.scene_library_manager.save()

        # UI更新
        self._update_scene_tree()
        self._update_scene_top()
        self._update_scene_recent()

        self.logger.info(f"シーン挿入: {scene_item.name}")

    # ========================================
    # 作品ライブラリ関連（複数シーンをまとめた作品）
    # ========================================

    def _create_project_library_tab(self):
        """作品ライブラリタブを作成（複数シーン管理）"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # タイトルと説明
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f8ff;
                border: 1px solid #4682b4;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(3)

        info_label = QLabel(
            "📚 作品ライブラリ：複数のシーンをまとめた「作品」を管理\n"
            "💡 作品名をダブルクリック → 全シーン一括挿入\n"
            "💡 個別シーン名をダブルクリック → 1シーンのみ挿入"
        )
        info_label.setStyleSheet("color: #333; font-size: 9pt;")
        info_layout.addWidget(info_label)

        layout.addWidget(info_frame)

        # よく使う作品TOP5
        top_frame = QFrame()
        top_frame.setFrameShape(QFrame.Shape.StyledPanel)
        top_frame.setStyleSheet("""
            QFrame {
                background-color: #fff8dc;
                border: 1px solid #ffa500;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        top_layout = QVBoxLayout(top_frame)
        top_layout.setSpacing(5)

        # ヘッダー（折りたたみボタン付き）
        top_header = QHBoxLayout()
        self.project_top_toggle_btn = QPushButton("⭐ よく使う作品 TOP5 ▼")
        self.project_top_toggle_btn.setFlat(True)
        self.project_top_toggle_btn.setStyleSheet("font-weight: bold; text-align: left;")
        self.project_top_toggle_btn.clicked.connect(self._toggle_project_top)
        top_header.addWidget(self.project_top_toggle_btn)
        top_header.addStretch()
        top_layout.addLayout(top_header)

        # コンテンツ
        self.project_top_content = QWidget()
        self.project_top_layout = QVBoxLayout(self.project_top_content)
        self.project_top_layout.setSpacing(3)
        self.project_top_layout.setContentsMargins(10, 0, 0, 0)
        top_layout.addWidget(self.project_top_content)

        layout.addWidget(top_frame)

        # 最近使った作品
        recent_frame = QFrame()
        recent_frame.setFrameShape(QFrame.Shape.StyledPanel)
        recent_frame.setStyleSheet("""
            QFrame {
                background-color: #f0fff0;
                border: 1px solid #90ee90;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        recent_layout = QVBoxLayout(recent_frame)
        recent_layout.setSpacing(5)

        # ヘッダー（折りたたみボタン付き）
        recent_header = QHBoxLayout()
        self.project_recent_toggle_btn = QPushButton("🕒 最近使った作品 ▼")
        self.project_recent_toggle_btn.setFlat(True)
        self.project_recent_toggle_btn.setStyleSheet("font-weight: bold; text-align: left;")
        self.project_recent_toggle_btn.clicked.connect(self._toggle_project_recent)
        recent_header.addWidget(self.project_recent_toggle_btn)
        recent_header.addStretch()
        recent_layout.addLayout(recent_header)

        # コンテンツ
        self.project_recent_content = QWidget()
        self.project_recent_layout = QVBoxLayout(self.project_recent_content)
        self.project_recent_layout.setSpacing(3)
        self.project_recent_layout.setContentsMargins(10, 0, 0, 0)
        recent_layout.addWidget(self.project_recent_content)

        layout.addWidget(recent_frame)

        # 検索バー
        self.project_search_bar = QLineEdit()
        self.project_search_bar.setPlaceholderText("作品を検索...")
        self.project_search_bar.textChanged.connect(self._on_project_search_input)
        layout.addWidget(self.project_search_bar)

        # 全作品一覧ツリー（階層表示: 作品 > シーン）
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabels(["作品名 / シーン名", "カテゴリ", "シーン数", "使用回数"])
        self.project_tree.setColumnWidth(0, 250)
        self.project_tree.setColumnWidth(1, 100)
        self.project_tree.setColumnWidth(2, 80)
        self.project_tree.setColumnWidth(3, 80)
        self.project_tree.itemDoubleClicked.connect(self._on_project_item_double_clicked)
        self.project_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.project_tree.customContextMenuRequested.connect(self._on_project_context_menu)
        layout.addWidget(self.project_tree)

        # 作品ライブラリステータス
        self.project_status_label = QLabel("作品ライブラリ: 0件")
        self.project_status_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(self.project_status_label)

        return tab

    def _toggle_project_top(self):
        """よく使う作品TOP5の表示/非表示を切り替え"""
        is_visible = self.project_top_content.isVisible()
        self.project_top_content.setVisible(not is_visible)

        if is_visible:
            self.project_top_toggle_btn.setText("⭐ よく使う作品 TOP5 ▶")
        else:
            self.project_top_toggle_btn.setText("⭐ よく使う作品 TOP5 ▼")

    def _toggle_project_recent(self):
        """最近使った作品の表示/非表示を切り替え"""
        is_visible = self.project_recent_content.isVisible()
        self.project_recent_content.setVisible(not is_visible)

        if is_visible:
            self.project_recent_toggle_btn.setText("🕒 最近使った作品 ▶")
        else:
            self.project_recent_toggle_btn.setText("🕒 最近使った作品 ▼")

    def _load_project_library(self):
        """作品ライブラリを読み込み"""
        try:
            self.project_library_items = self.project_library_manager.get_all_items()
            self.logger.info(f"作品ライブラリ読み込み: {len(self.project_library_items)}件")

            # UI更新
            self._update_project_tree()
            self._update_project_top()
            self._update_project_recent()
        except Exception as e:
            self.logger.error(f"作品ライブラリ読み込みエラー: {e}", exc_info=True)
            self.project_library_items = []

    def reload_project_library(self):
        """作品ライブラリを再読み込み（保存後に呼び出す）"""
        # ファイルから再読み込み
        self.project_library_manager.load()
        self._load_project_library()

    def _update_project_top(self):
        """よく使う作品TOP5を更新"""
        # 既存のボタンをクリア
        while self.project_top_layout.count():
            item = self.project_top_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # よく使う作品を取得（TOP5）
        most_used = self.project_library_manager.get_most_used(limit=5)

        if not most_used:
            no_data_label = QLabel("まだ保存された作品がありません")
            no_data_label.setStyleSheet("color: gray; font-style: italic;")
            self.project_top_layout.addWidget(no_data_label)
            return

        for project_item in most_used:
            btn_layout = QHBoxLayout()

            # 作品ボタン
            scene_count = project_item.get_scene_count()
            # プロジェクト名が汎用的な名前の場合は省略
            if project_item.name in ["無題のプロジェクト", "Untitled Project", "新規プロジェクト"]:
                btn = QPushButton(f"📚 {project_item.usage_count}回使用 / {scene_count}シーン")
            else:
                btn = QPushButton(f"📚 {project_item.name} ({project_item.usage_count}回 / {scene_count}シーン)")
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 4px 8px;
                    background-color: white;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #fff8dc;
                    border-color: #ffa500;
                }
            """)
            btn.clicked.connect(lambda checked, p=project_item: self._insert_project_all(p))
            btn_layout.addWidget(btn)

            self.project_top_layout.addLayout(btn_layout)

    def _update_project_recent(self):
        """最近使った作品を更新"""
        # 既存のボタンをクリア
        while self.project_recent_layout.count():
            item = self.project_recent_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 最近使った作品を取得（last_usedでソート、TOP5）
        recent_used = self.project_library_manager.get_recently_used(limit=5)

        if not recent_used:
            no_data_label = QLabel("まだ使用された作品がありません")
            no_data_label.setStyleSheet("color: gray; font-style: italic;")
            self.project_recent_layout.addWidget(no_data_label)
            return

        for project_item in recent_used:
            btn_layout = QHBoxLayout()

            # 作品ボタン
            scene_count = project_item.get_scene_count()
            last_used_str = project_item.last_used.strftime("%m/%d %H:%M")
            # プロジェクト名が汎用的な名前の場合は省略
            if project_item.name in ["無題のプロジェクト", "Untitled Project", "新規プロジェクト"]:
                btn = QPushButton(f"📚 {last_used_str} / {scene_count}シーン")
            else:
                btn = QPushButton(f"📚 {project_item.name} ({last_used_str} / {scene_count}シーン)")
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 4px 8px;
                    background-color: white;
                    color: #333;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #f0fff0;
                    border-color: #90ee90;
                }
            """)
            btn.clicked.connect(lambda checked, p=project_item: self._insert_project_all(p))
            btn_layout.addWidget(btn)

            self.project_recent_layout.addLayout(btn_layout)

    def _on_project_search_input(self, text: str):
        """作品検索入力時

        Args:
            text: 検索クエリ
        """
        self._update_project_tree()

    def _update_project_tree(self):
        """作品ツリーを更新（階層表示: 作品 > シーン）"""
        self.project_tree.clear()

        query = self.project_search_bar.text().strip().lower()

        # フィルタリング
        filtered = self.project_library_items
        if query:
            filtered = [p for p in filtered if p.matches_search(query)]

        if not filtered:
            no_data = QTreeWidgetItem(["作品がありません", "", "", ""])
            self.project_tree.addTopLevelItem(no_data)
            self.project_status_label.setText("作品ライブラリ: 0件")
            return

        # カテゴリごとにグループ化
        categories = {}
        for project_item in filtered:
            category = project_item.category or "その他"
            if category not in categories:
                categories[category] = []
            categories[category].append(project_item)

        # カテゴリごとに表示
        for category, projects in sorted(categories.items()):
            category_item = QTreeWidgetItem([f"📁 {category} ({len(projects)})", "", "", ""])
            category_item.setExpanded(True)
            self.project_tree.addTopLevelItem(category_item)

            # 作品を使用回数順にソート
            sorted_projects = sorted(projects, key=lambda p: p.usage_count, reverse=True)

            for project_item in sorted_projects:
                scene_count = project_item.get_scene_count()
                # 作品ノード
                project_tree_item = QTreeWidgetItem([
                    f"📚 {project_item.name}",
                    project_item.category,
                    f"{scene_count}",
                    f"{project_item.usage_count}回"
                ])
                # 作品全体を示すデータを保存
                project_tree_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "project",
                    "item": project_item
                })
                project_tree_item.setExpanded(False)  # デフォルトは折りたたみ
                category_item.addChild(project_tree_item)

                # シーンノード（作品の子として表示）
                for scene_index, scene_item in enumerate(project_item.scenes):
                    block_count = len(scene_item.block_templates)
                    scene_tree_item = QTreeWidgetItem([
                        f"  🎬 {scene_item.name}",
                        "",
                        f"{block_count}ブロック",
                        ""
                    ])
                    # 個別シーンを示すデータを保存
                    scene_tree_item.setData(0, Qt.ItemDataRole.UserRole, {
                        "type": "scene",
                        "project_item": project_item,
                        "scene_index": scene_index
                    })
                    project_tree_item.addChild(scene_tree_item)

        # ステータス更新
        if query:
            self.project_status_label.setText(
                f"検索結果: {len(filtered)}件 / {len(self.project_library_items)}件"
            )
        else:
            self.project_status_label.setText(f"作品ライブラリ: {len(self.project_library_items)}件")

    def _on_project_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """作品ツリーのアイテムダブルクリック時

        Args:
            item: クリックされたアイテム
            column: カラム番号
        """
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if not data or not isinstance(data, dict):
            return

        # 作品全体の場合 → 全シーン一括挿入
        if data.get("type") == "project":
            project_item = data["item"]
            self._insert_project_all(project_item)

        # 個別シーンの場合 → 1シーンのみ挿入
        elif data.get("type") == "scene":
            project_item = data["project_item"]
            scene_index = data["scene_index"]
            self._insert_project_scene(project_item, scene_index)

    def _insert_project_all(self, project_item: ProjectLibraryItem):
        """作品全体を挿入（全シーン一括）

        Args:
            project_item: 挿入する作品ライブラリアイテム
        """
        # シグナル発行（全シーン一括挿入）
        self.project_selected.emit(project_item)

        self.logger.info(f"作品全体挿入: {project_item.name} ({project_item.get_scene_count()}シーン)")

    def _insert_project_scene(self, project_item: ProjectLibraryItem, scene_index: int):
        """作品内の個別シーンを挿入

        Args:
            project_item: 作品ライブラリアイテム
            scene_index: シーンのインデックス
        """
        # シグナル発行（個別シーン挿入）
        self.project_scene_selected.emit(project_item, scene_index)

        scene_name = project_item.scenes[scene_index].name
        self.logger.info(f"作品内シーン挿入: {project_item.name}[{scene_index}] - {scene_name}")

    def _on_scene_context_menu(self, position):
        """シーンツリーの右クリックメニュー表示

        Args:
            position: 右クリックされた位置
        """
        # 右クリックされたアイテムを取得
        item = self.scene_tree.itemAt(position)
        if not item:
            return

        # アイテムのデータを取得
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or not isinstance(data, SceneLibraryItem):
            return

        scene_item = data

        # コンテキストメニューを作成
        menu = QMenu(self)

        # 挿入アクション
        insert_action = QAction("🎬 挿入", self)
        insert_action.triggered.connect(lambda: self._insert_scene(scene_item))
        menu.addAction(insert_action)

        menu.addSeparator()

        # 名前変更アクション
        rename_action = QAction("✏️ 名前変更", self)
        rename_action.triggered.connect(lambda: self._on_rename_scene(scene_item))
        menu.addAction(rename_action)

        # カテゴリ変更アクション
        category_action = QAction("📁 カテゴリ変更", self)
        category_action.triggered.connect(lambda: self._on_change_scene_category(scene_item))
        menu.addAction(category_action)

        menu.addSeparator()

        # 削除アクション
        delete_action = QAction("🗑️ 削除", self)
        delete_action.triggered.connect(lambda: self._on_delete_scene(scene_item))
        menu.addAction(delete_action)

        # メニューを表示
        menu.exec(self.scene_tree.viewport().mapToGlobal(position))

    def _on_rename_scene(self, scene_item: SceneLibraryItem):
        """シーン名を変更

        Args:
            scene_item: 変更するシーンアイテム
        """
        # ダイアログで新しい名前を入力
        new_name, ok = QInputDialog.getText(
            self,
            "シーン名変更",
            "新しいシーン名を入力してください:",
            text=scene_item.name
        )

        if not ok or not new_name.strip():
            return

        # 名前を更新
        old_name = scene_item.name
        scene_item.name = new_name.strip()

        # 保存
        if self.scene_library_manager.update_item(scene_item):
            self.logger.info(f"シーン名変更: {old_name} → {new_name}")
            # UI更新
            self._update_scene_tree()
            self._update_scene_top()
            self._update_scene_recent()

            QMessageBox.information(
                self,
                "成功",
                f"シーン名を変更しました。\n\n{old_name} → {new_name}"
            )
        else:
            self.logger.error(f"シーン名変更失敗: {old_name}")
            QMessageBox.critical(
                self,
                "エラー",
                "シーン名の変更に失敗しました。"
            )

    def _on_change_scene_category(self, scene_item: SceneLibraryItem):
        """シーンのカテゴリを変更

        Args:
            scene_item: 変更するシーンアイテム
        """
        # 既存のカテゴリリストを取得
        categories = self.scene_library_manager.get_categories()
        if not categories:
            categories = ["その他"]

        # カテゴリ選択ダイアログ
        from PyQt6.QtWidgets import QComboBox
        dialog = QInputDialog(self)
        dialog.setWindowTitle("カテゴリ変更")
        dialog.setLabelText("新しいカテゴリを選択または入力してください:")
        dialog.setComboBoxItems(categories)
        dialog.setComboBoxEditable(True)
        dialog.setTextValue(scene_item.category)

        if dialog.exec() != QInputDialog.DialogCode.Accepted:
            return

        new_category = dialog.textValue().strip()
        if not new_category:
            new_category = "その他"

        # カテゴリを更新
        old_category = scene_item.category
        scene_item.category = new_category

        # 保存
        if self.scene_library_manager.update_item(scene_item):
            self.logger.info(f"シーンカテゴリ変更: {scene_item.name} - {old_category} → {new_category}")
            # UI更新
            self._update_scene_tree()

            QMessageBox.information(
                self,
                "成功",
                f"カテゴリを変更しました。\n\nシーン: {scene_item.name}\n{old_category} → {new_category}"
            )
        else:
            self.logger.error(f"カテゴリ変更失敗: {scene_item.name}")
            QMessageBox.critical(
                self,
                "エラー",
                "カテゴリの変更に失敗しました。"
            )

    def _on_delete_scene(self, scene_item: SceneLibraryItem):
        """シーンを削除

        Args:
            scene_item: 削除するシーンアイテム
        """
        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "削除確認",
            f"以下のシーンを削除してもよろしいですか？\n\n"
            f"シーン名: {scene_item.name}\n"
            f"カテゴリ: {scene_item.category}\n"
            f"ブロック数: {len(scene_item.block_templates)}\n"
            f"使用回数: {scene_item.usage_count}回\n\n"
            f"※この操作は取り消せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 削除実行
        if self.scene_library_manager.delete_item(scene_item.id):
            self.logger.info(f"シーン削除: {scene_item.name}")

            # UI更新
            self._load_scene_library()

            QMessageBox.information(
                self,
                "削除完了",
                f"シーン「{scene_item.name}」を削除しました。"
            )
        else:
            self.logger.error(f"シーン削除失敗: {scene_item.name}")
            QMessageBox.critical(
                self,
                "エラー",
                "シーンの削除に失敗しました。"
            )

    def _on_project_context_menu(self, position):
        """作品ツリーの右クリックメニュー表示

        Args:
            position: 右クリックされた位置
        """
        # 右クリックされたアイテムを取得
        item = self.project_tree.itemAt(position)
        if not item:
            return

        # アイテムのデータを取得
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or not isinstance(data, dict):
            return

        # 作品全体の場合
        if data.get("type") == "project":
            project_item = data["item"]
            self._show_project_context_menu(position, project_item)

        # 個別シーンの場合（作品内シーン）は右クリックメニューなし
        # （個別シーンは作品の一部なので、直接編集させない）

    def _show_project_context_menu(self, position, project_item: ProjectLibraryItem):
        """作品の右クリックメニューを表示

        Args:
            position: 右クリックされた位置
            project_item: 作品ライブラリアイテム
        """
        # コンテキストメニューを作成
        menu = QMenu(self)

        # 全シーン挿入アクション
        insert_all_action = QAction("📚 全シーン挿入", self)
        insert_all_action.triggered.connect(lambda: self._insert_project_all(project_item))
        menu.addAction(insert_all_action)

        menu.addSeparator()

        # 名前変更アクション
        rename_action = QAction("✏️ 名前変更", self)
        rename_action.triggered.connect(lambda: self._on_rename_project(project_item))
        menu.addAction(rename_action)

        # カテゴリ変更アクション
        category_action = QAction("📁 カテゴリ変更", self)
        category_action.triggered.connect(lambda: self._on_change_project_category(project_item))
        menu.addAction(category_action)

        menu.addSeparator()

        # 削除アクション
        delete_action = QAction("🗑️ 削除", self)
        delete_action.triggered.connect(lambda: self._on_delete_project(project_item))
        menu.addAction(delete_action)

        # メニューを表示
        menu.exec(self.project_tree.viewport().mapToGlobal(position))

    def _on_rename_project(self, project_item: ProjectLibraryItem):
        """作品名を変更

        Args:
            project_item: 変更する作品アイテム
        """
        # ダイアログで新しい名前を入力
        new_name, ok = QInputDialog.getText(
            self,
            "作品名変更",
            "新しい作品名を入力してください:",
            text=project_item.name
        )

        if not ok or not new_name.strip():
            return

        # 名前を更新
        old_name = project_item.name
        project_item.name = new_name.strip()

        # 保存
        if self.project_library_manager.update_item(project_item):
            self.logger.info(f"作品名変更: {old_name} → {new_name}")
            # UI更新
            self._update_project_tree()
            self._update_project_top()
            self._update_project_recent()

            QMessageBox.information(
                self,
                "成功",
                f"作品名を変更しました。\n\n{old_name} → {new_name}"
            )
        else:
            self.logger.error(f"作品名変更失敗: {old_name}")
            QMessageBox.critical(
                self,
                "エラー",
                "作品名の変更に失敗しました。"
            )

    def _on_change_project_category(self, project_item: ProjectLibraryItem):
        """作品のカテゴリを変更

        Args:
            project_item: 変更する作品アイテム
        """
        # 既存のカテゴリリストを取得
        categories = self.project_library_manager.get_categories()
        if not categories:
            categories = ["その他"]

        # カテゴリ選択ダイアログ
        dialog = QInputDialog(self)
        dialog.setWindowTitle("カテゴリ変更")
        dialog.setLabelText("新しいカテゴリを選択または入力してください:")
        dialog.setComboBoxItems(categories)
        dialog.setComboBoxEditable(True)
        dialog.setTextValue(project_item.category)

        if dialog.exec() != QInputDialog.DialogCode.Accepted:
            return

        new_category = dialog.textValue().strip()
        if not new_category:
            new_category = "その他"

        # カテゴリを更新
        old_category = project_item.category
        project_item.category = new_category

        # 保存
        if self.project_library_manager.update_item(project_item):
            self.logger.info(f"作品カテゴリ変更: {project_item.name} - {old_category} → {new_category}")
            # UI更新
            self._update_project_tree()

            QMessageBox.information(
                self,
                "成功",
                f"カテゴリを変更しました。\n\n作品: {project_item.name}\n{old_category} → {new_category}"
            )
        else:
            self.logger.error(f"カテゴリ変更失敗: {project_item.name}")
            QMessageBox.critical(
                self,
                "エラー",
                "カテゴリの変更に失敗しました。"
            )

    def _on_delete_project(self, project_item: ProjectLibraryItem):
        """作品を削除

        Args:
            project_item: 削除する作品アイテム
        """
        # 確認ダイアログ
        scene_count = project_item.get_scene_count()
        reply = QMessageBox.question(
            self,
            "削除確認",
            f"以下の作品を削除してもよろしいですか？\n\n"
            f"作品名: {project_item.name}\n"
            f"カテゴリ: {project_item.category}\n"
            f"シーン数: {scene_count}\n"
            f"使用回数: {project_item.usage_count}回\n\n"
            f"※この操作は取り消せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 削除実行
        if self.project_library_manager.delete_item(project_item.id):
            self.logger.info(f"作品削除: {project_item.name}")

            # UI更新
            self._load_project_library()

            QMessageBox.information(
                self,
                "削除完了",
                f"作品「{project_item.name}」を削除しました。"
            )
        else:
            self.logger.error(f"作品削除失敗: {project_item.name}")
            QMessageBox.critical(
                self,
                "エラー",
                "作品の削除に失敗しました。"
            )

    def _create_lora_tab(self):
        """LoRAタブを作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # タイトルと説明
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #fff0f5;
                border: 1px solid #ff69b4;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(3)

        info_label = QLabel(
            "🎨 LoRAライブラリ：LoRAファイルを管理\n"
            "💡 LoRAをダブルクリック → <lora:filename:0.8>形式で挿入\n"
            "💡 「スキャン」で最新のLoRAファイルを取り込み"
        )
        info_label.setStyleSheet("color: #333; font-size: 9pt;")
        info_layout.addWidget(info_label)

        layout.addWidget(info_frame)

        # ボタン
        button_layout = QHBoxLayout()

        self.lora_scan_button = QPushButton("🔍 スキャン")
        self.lora_scan_button.setStyleSheet("""
            QPushButton {
                background-color: #ff69b4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff1493;
            }
        """)
        self.lora_scan_button.clicked.connect(self._on_lora_scan)
        button_layout.addWidget(self.lora_scan_button)

        self.lora_reload_button = QPushButton("🔄 再読み込み")
        self.lora_reload_button.clicked.connect(self._on_lora_reload)
        button_layout.addWidget(self.lora_reload_button)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 検索バー
        self.lora_search_bar = QLineEdit()
        self.lora_search_bar.setPlaceholderText("LoRAを検索...")
        self.lora_search_bar.textChanged.connect(self._on_lora_search_input)
        layout.addWidget(self.lora_search_bar)

        # カテゴリフィルタ
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("カテゴリ:"))

        self.lora_category_filter = QComboBox()
        self.lora_category_filter.addItem("全て")
        self.lora_category_filter.currentTextChanged.connect(self._on_lora_category_changed)
        category_layout.addWidget(self.lora_category_filter)

        layout.addLayout(category_layout)

        # LoRA一覧ツリー
        self.lora_tree = QTreeWidget()
        self.lora_tree.setHeaderLabels(["名前", "プロンプト", "タグ"])
        self.lora_tree.setColumnWidth(0, 250)
        self.lora_tree.setColumnWidth(1, 300)
        self.lora_tree.setColumnWidth(2, 150)
        self.lora_tree.itemDoubleClicked.connect(self._on_lora_item_double_clicked)
        layout.addWidget(self.lora_tree)

        # LoRAライブラリステータス
        self.lora_status_label = QLabel("LoRAライブラリ: 0件")
        self.lora_status_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(self.lora_status_label)

        return tab

    def _load_lora_library(self):
        """LoRAライブラリをCSVから読み込み"""
        try:
            self.lora_prompts = self.lora_library_manager.load_from_csv()
            self.logger.info(f"LoRAライブラリ読み込み: {len(self.lora_prompts)}件")

            # UI更新
            self._update_lora_tree()
            self._update_lora_categories()

        except Exception as e:
            self.logger.error(f"LoRAライブラリ読み込み失敗: {e}")

    def _on_lora_scan(self):
        """LoRAフォルダをスキャン"""
        from PyQt6.QtWidgets import QProgressDialog

        # LoRAディレクトリが設定されているか確認
        lora_dir = self.lora_library_manager.settings.get_lora_dir()
        if not lora_dir or not lora_dir.exists():
            QMessageBox.warning(
                self,
                "LoRAディレクトリ未設定",
                "LoRAディレクトリが設定されていません。\n"
                "設定画面でLoRAフォルダを指定してください。"
            )
            return

        # プログレスダイアログ
        progress = QProgressDialog("LoRAファイルをスキャン中...", "キャンセル", 0, 100, self)
        progress.setWindowTitle("LoRAスキャン")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        def progress_callback(current, total, message):
            if total > 0:
                progress.setMaximum(total)
                progress.setValue(current)
            progress.setLabelText(message)
            QApplication.processEvents()

        try:
            # スキャン実行
            self.lora_prompts = self.lora_library_manager.scan_and_build_library(progress_callback)

            # CSVに保存
            self.lora_library_manager.save_to_csv()

            # UI更新
            self._update_lora_tree()
            self._update_lora_categories()

            progress.close()

            QMessageBox.information(
                self,
                "スキャン完了",
                f"{len(self.lora_prompts)}件のLoRAファイルを検出しました。"
            )

        except Exception as e:
            progress.close()
            self.logger.error(f"LoRAスキャン失敗: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"LoRAスキャンに失敗しました。\n\n{str(e)}"
            )

    def _on_lora_reload(self):
        """LoRAライブラリを再読み込み"""
        self._load_lora_library()
        QMessageBox.information(
            self,
            "再読み込み完了",
            f"{len(self.lora_prompts)}件のLoRAを読み込みました。"
        )

    def _on_lora_search_input(self, text: str):
        """LoRA検索入力"""
        self._update_lora_tree(search_text=text)

    def _on_lora_category_changed(self, category: str):
        """LoRAカテゴリフィルタ変更"""
        self._update_lora_tree()

    def _update_lora_tree(self, search_text: str = ""):
        """LoRAツリーを更新"""
        self.lora_tree.clear()

        if not search_text:
            search_text = self.lora_search_bar.text()

        category_filter = self.lora_category_filter.currentText()

        # フィルタリング
        filtered_loras = []
        for lora in self.lora_prompts:
            # カテゴリフィルタ
            if category_filter != "全て" and lora.category != category_filter:
                continue

            # 検索フィルタ
            if search_text:
                search_lower = search_text.lower()
                if not (search_lower in lora.label_ja.lower() or
                        search_lower in lora.label_en.lower() or
                        search_lower in lora.prompt.lower() or
                        any(search_lower in tag.lower() for tag in lora.tags)):
                    continue

            filtered_loras.append(lora)

        # ツリーに追加
        for lora in filtered_loras:
            item = QTreeWidgetItem([
                lora.label_ja or lora.source_file,
                lora.prompt,
                ", ".join(lora.tags[:3]) if lora.tags else ""
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, lora)
            self.lora_tree.addTopLevelItem(item)

        # ステータス更新
        self.lora_status_label.setText(f"LoRAライブラリ: {len(filtered_loras)}件 / 全{len(self.lora_prompts)}件")

    def _update_lora_categories(self):
        """LoRAカテゴリリストを更新"""
        categories = set()
        for lora in self.lora_prompts:
            if lora.category:
                categories.add(lora.category)

        current_category = self.lora_category_filter.currentText()
        self.lora_category_filter.clear()
        self.lora_category_filter.addItem("全て")
        for category in sorted(categories):
            self.lora_category_filter.addItem(category)

        # 以前の選択を復元
        index = self.lora_category_filter.findText(current_category)
        if index >= 0:
            self.lora_category_filter.setCurrentIndex(index)

    def _on_lora_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """LoRA項目ダブルクリック"""
        lora = item.data(0, Qt.ItemDataRole.UserRole)
        if lora:
            # Promptオブジェクトとして送信（固定テキストとして挿入）
            self.prompt_selected.emit(lora)
            self.logger.info(f"LoRA選択: {lora.label_ja} - {lora.prompt}")

