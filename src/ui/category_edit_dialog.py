"""カテゴリ編集ダイアログ

シーンライブラリのカテゴリを編集するためのダイアログです。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from core.scene_library_manager import SceneLibraryManager
from utils.logger import get_logger


class CategoryEditDialog(QDialog):
    """カテゴリ編集ダイアログ

    カテゴリの追加、削除、名前変更を行います。

    Attributes:
        scene_library_manager: シーンライブラリマネージャー
        category_list: カテゴリリストウィジェット
        categories: カテゴリリスト
    """

    def __init__(
        self,
        scene_library_manager: SceneLibraryManager,
        parent=None
    ):
        """初期化

        Args:
            scene_library_manager: シーンライブラリマネージャー
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.scene_library_manager = scene_library_manager
        self.logger = get_logger()

        # 既存のカテゴリを取得
        existing_categories = self.scene_library_manager.get_categories()
        default_categories = ["その他", "恋愛", "学園", "日常", "アクション", "ファンタジー"]

        # 既存カテゴリと合わせて重複なしのリストを作成
        self.categories = list(set(default_categories + existing_categories))
        self.categories.sort()

        # ダイアログ設定
        self.setWindowTitle("カテゴリ編集")
        self.setMinimumWidth(400)
        self.setMinimumHeight(350)

        # UI構築
        self._create_ui()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # タイトル
        title_label = QLabel("カテゴリ管理")
        title_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(title_label)

        # 説明
        info_label = QLabel("シーンライブラリで使用するカテゴリを編集できます。")
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)

        # カテゴリリスト
        layout.addWidget(QLabel("カテゴリ一覧:"))
        self.category_list = QListWidget()
        self.category_list.addItems(self.categories)
        self.category_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.category_list)

        # ボタンレイアウト（編集操作）
        edit_button_layout = QHBoxLayout()

        add_btn = QPushButton("追加")
        add_btn.clicked.connect(self._on_add)
        edit_button_layout.addWidget(add_btn)

        rename_btn = QPushButton("名前変更")
        rename_btn.clicked.connect(self._on_rename)
        edit_button_layout.addWidget(rename_btn)

        delete_btn = QPushButton("削除")
        delete_btn.clicked.connect(self._on_delete)
        edit_button_layout.addWidget(delete_btn)

        layout.addLayout(edit_button_layout)

        # 閉じるボタン
        close_button_layout = QHBoxLayout()
        close_button_layout.addStretch()

        close_btn = QPushButton("閉じる")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        close_button_layout.addWidget(close_btn)

        layout.addLayout(close_button_layout)

    def _on_add(self):
        """カテゴリ追加"""
        text, ok = QInputDialog.getText(
            self,
            "カテゴリ追加",
            "新しいカテゴリ名を入力してください:"
        )

        if ok and text.strip():
            category_name = text.strip()

            # 重複チェック
            if category_name in self.categories:
                QMessageBox.warning(
                    self,
                    "エラー",
                    f"カテゴリ「{category_name}」は既に存在します。"
                )
                return

            # カテゴリを追加
            self.categories.append(category_name)
            self.categories.sort()

            # リストを更新
            self._refresh_list()

            # 追加したアイテムを選択
            items = self.category_list.findItems(category_name, Qt.MatchFlag.MatchExactly)
            if items:
                self.category_list.setCurrentItem(items[0])

            self.logger.info(f"カテゴリ追加: {category_name}")

    def _on_rename(self):
        """カテゴリ名前変更"""
        current_item = self.category_list.currentItem()
        if not current_item:
            QMessageBox.information(
                self,
                "情報",
                "名前を変更するカテゴリを選択してください。"
            )
            return

        old_name = current_item.text()

        text, ok = QInputDialog.getText(
            self,
            "カテゴリ名変更",
            "新しいカテゴリ名を入力してください:",
            text=old_name
        )

        if ok and text.strip() and text.strip() != old_name:
            new_name = text.strip()

            # 重複チェック
            if new_name in self.categories:
                QMessageBox.warning(
                    self,
                    "エラー",
                    f"カテゴリ「{new_name}」は既に存在します。"
                )
                return

            # カテゴリ名を変更
            index = self.categories.index(old_name)
            self.categories[index] = new_name
            self.categories.sort()

            # リストを更新
            self._refresh_list()

            # 変更したアイテムを選択
            items = self.category_list.findItems(new_name, Qt.MatchFlag.MatchExactly)
            if items:
                self.category_list.setCurrentItem(items[0])

            self.logger.info(f"カテゴリ名変更: {old_name} -> {new_name}")

    def _on_delete(self):
        """カテゴリ削除"""
        current_item = self.category_list.currentItem()
        if not current_item:
            QMessageBox.information(
                self,
                "情報",
                "削除するカテゴリを選択してください。"
            )
            return

        category_name = current_item.text()

        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "確認",
            f"カテゴリ「{category_name}」を削除しますか？\n\n"
            f"注: このカテゴリを使用している既存のシーンは影響を受けません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # カテゴリを削除
            self.categories.remove(category_name)

            # リストを更新
            self._refresh_list()

            self.logger.info(f"カテゴリ削除: {category_name}")

    def _refresh_list(self):
        """リストを再描画"""
        self.category_list.clear()
        self.category_list.addItems(self.categories)

    def get_categories(self):
        """編集後のカテゴリリストを取得

        Returns:
            カテゴリリスト
        """
        return self.categories
