"""自作プロンプト管理ダイアログ

保存済みの自作プロンプトを一覧表示・編集・削除するダイアログ。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from typing import List

from core.custom_prompt_manager import CustomPromptManager
from models.custom_prompt import CustomPrompt


class CustomPromptManagerDialog(QDialog):
    """自作プロンプト管理ダイアログ

    保存済みの自作プロンプトを一覧表示し、編集・削除を行うダイアログ。

    Attributes:
        custom_prompt_manager: 自作プロンプト管理
    """

    def __init__(self, custom_prompt_manager: CustomPromptManager, parent=None):
        """初期化

        Args:
            custom_prompt_manager: 自作プロンプト管理
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.custom_prompt_manager = custom_prompt_manager
        self.filtered_prompts: List[CustomPrompt] = []

        self.setWindowTitle("自作プロンプト管理")
        self.setModal(True)
        self.resize(900, 600)

        self._create_ui()
        self._load_prompts()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # タイトル
        title_label = QLabel("自作プロンプト管理")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # 検索バー
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("検索:"))

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("ラベル、プロンプト、タグで検索...")
        self.search_bar.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_bar)

        layout.addLayout(search_layout)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "日本語ラベル", "カテゴリ", "プロンプト", "使用回数", "ID"
        ])

        # カラム幅設定
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 300)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 120)

        # ヘッダー設定
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # 選択設定
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # ダブルクリックで編集
        self.table.itemDoubleClicked.connect(self._on_edit_clicked)

        layout.addWidget(self.table)

        # ステータス
        self.status_label = QLabel("プロンプト: 0件")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        # ボタン
        button_layout = QHBoxLayout()

        # 新規追加
        add_button = QPushButton("➕ 新規追加")
        add_button.clicked.connect(self._on_add_clicked)
        add_button.setStyleSheet("""
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
        button_layout.addWidget(add_button)

        # 編集
        edit_button = QPushButton("✏️ 編集")
        edit_button.clicked.connect(self._on_edit_clicked)
        button_layout.addWidget(edit_button)

        # 削除
        delete_button = QPushButton("🗑️ 削除")
        delete_button.clicked.connect(self._on_delete_clicked)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        button_layout.addWidget(delete_button)

        button_layout.addStretch()

        # 閉じる
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _load_prompts(self):
        """プロンプト読み込み"""
        self.custom_prompt_manager.load()
        self.filtered_prompts = self.custom_prompt_manager.prompts
        self._update_table()

    def _update_table(self):
        """テーブル更新"""
        self.table.setRowCount(0)

        for prompt in self.filtered_prompts:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 日本語ラベル
            label_item = QTableWidgetItem(prompt.label_ja)
            label_item.setData(Qt.ItemDataRole.UserRole, prompt)
            self.table.setItem(row, 0, label_item)

            # カテゴリ
            category_item = QTableWidgetItem(prompt.category)
            self.table.setItem(row, 1, category_item)

            # プロンプト（50文字まで）
            prompt_text = prompt.prompt[:50] + "..." if len(prompt.prompt) > 50 else prompt.prompt
            prompt_item = QTableWidgetItem(prompt_text)
            self.table.setItem(row, 2, prompt_item)

            # 使用回数
            usage_item = QTableWidgetItem(f"{prompt.usage_count}回")
            usage_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, usage_item)

            # ID
            id_item = QTableWidgetItem(prompt.id)
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, id_item)

        # ステータス更新
        total = len(self.custom_prompt_manager.prompts)
        filtered = len(self.filtered_prompts)

        if total == filtered:
            self.status_label.setText(f"プロンプト: {total}件")
        else:
            self.status_label.setText(f"検索結果: {filtered}件 / {total}件")

    def _on_search(self, query: str):
        """検索"""
        if not query.strip():
            self.filtered_prompts = self.custom_prompt_manager.prompts
        else:
            self.filtered_prompts = self.custom_prompt_manager.search(query.strip())

        self._update_table()

    def _on_add_clicked(self):
        """新規追加"""
        from .custom_prompt_dialog import CustomPromptDialog

        dialog = CustomPromptDialog(
            custom_prompt_manager=self.custom_prompt_manager,
            prompt_text="",
            parent=self
        )

        if dialog.exec():
            # 再読み込み
            self._load_prompts()

    def _on_edit_clicked(self):
        """編集"""
        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(
                self,
                "選択エラー",
                "編集するプロンプトを選択してください。"
            )
            return

        row = selected_rows[0].row()
        item = self.table.item(row, 0)
        prompt = item.data(Qt.ItemDataRole.UserRole)

        if not prompt:
            return

        # 編集ダイアログ表示
        from .custom_prompt_dialog import CustomPromptDialog

        dialog = CustomPromptDialog(
            custom_prompt_manager=self.custom_prompt_manager,
            prompt_text=prompt.prompt,
            existing_prompt=prompt,
            parent=self
        )

        if dialog.exec():
            # 再読み込み
            self._load_prompts()

    def _on_delete_clicked(self):
        """削除"""
        selected_rows = self.table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.warning(
                self,
                "選択エラー",
                "削除するプロンプトを選択してください。"
            )
            return

        row = selected_rows[0].row()
        item = self.table.item(row, 0)
        prompt = item.data(Qt.ItemDataRole.UserRole)

        if not prompt:
            return

        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "削除確認",
            f"プロンプト「{prompt.label_ja}」を削除しますか？\n\n"
            f"この操作は取り消せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 削除
            success = self.custom_prompt_manager.remove_prompt(prompt.id)

            if success:
                QMessageBox.information(
                    self,
                    "削除完了",
                    f"プロンプト「{prompt.label_ja}」を削除しました。"
                )
                # 再読み込み
                self._load_prompts()
            else:
                QMessageBox.critical(
                    self,
                    "エラー",
                    "削除に失敗しました。"
                )
