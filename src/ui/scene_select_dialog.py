"""シーン選択ダイアログ

ライブラリからシーンを選択して挿入するためのダイアログです。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QTextEdit, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from models import SceneLibraryItem
from core.scene_library_manager import SceneLibraryManager
from utils.logger import get_logger


class SceneSelectDialog(QDialog):
    """シーン選択ダイアログ

    ライブラリからシーンを選択して挿入します。

    Attributes:
        scene_library_manager: シーンライブラリマネージャー
        selected_item: 選択されたライブラリアイテム
    """

    # カスタムシグナル
    scene_deleted = pyqtSignal(str)  # シーン削除時に発火（アイテムID）

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
        self.selected_item = None
        self.logger = get_logger()

        # ダイアログ設定
        self.setWindowTitle("ライブラリからシーンを挿入")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        # UI構築
        self._create_ui()

        # ライブラリアイテムを読み込み
        self._load_items()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # タイトル
        title_label = QLabel("ライブラリからシーンを挿入")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # 検索バー
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("検索:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("シーン名、カテゴリ、タグで検索...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # シーンリスト
        list_layout = QHBoxLayout()

        # 左側: シーンリスト
        list_group = QGroupBox("シーンライブラリ")
        list_group_layout = QVBoxLayout()

        self.scene_list = QListWidget()
        self.scene_list.setAlternatingRowColors(True)
        self.scene_list.currentItemChanged.connect(self._on_selection_changed)
        self.scene_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        list_group_layout.addWidget(self.scene_list)

        list_group.setLayout(list_group_layout)
        list_layout.addWidget(list_group, 2)

        # 右側: 詳細情報
        detail_group = QGroupBox("詳細情報")
        detail_layout = QVBoxLayout()

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)

        detail_group.setLayout(detail_layout)
        list_layout.addWidget(detail_group, 1)

        layout.addLayout(list_layout)

        # ボタン
        button_layout = QHBoxLayout()

        # 左側: 削除ボタン
        self.delete_btn = QPushButton("削除")
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        # 右側: キャンセル・挿入ボタン
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        self.insert_btn = QPushButton("挿入")
        self.insert_btn.setDefault(True)
        self.insert_btn.clicked.connect(self._on_insert)
        self.insert_btn.setEnabled(False)
        button_layout.addWidget(self.insert_btn)

        layout.addLayout(button_layout)

    def _load_items(self):
        """ライブラリアイテムを読み込み"""
        self.scene_list.clear()

        items = self.scene_library_manager.get_all_items()

        if not items:
            # 空の場合
            item = QListWidgetItem("（ライブラリにシーンがありません）")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.scene_list.addItem(item)
            return

        # 使用回数順にソート
        items_sorted = sorted(items, key=lambda x: x.usage_count, reverse=True)

        for lib_item in items_sorted:
            # リストアイテム作成
            display_text = f"{lib_item.name} [{lib_item.category}]"
            if lib_item.usage_count > 0:
                display_text += f" (使用: {lib_item.usage_count}回)"

            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.ItemDataRole.UserRole, lib_item.id)
            self.scene_list.addItem(list_item)

    def _on_search(self, text: str):
        """検索テキスト変更時"""
        query = text.strip()

        if not query:
            # 検索クエリが空の場合は全て表示
            self._load_items()
            return

        # 検索
        items = self.scene_library_manager.search(query)

        # リストを更新
        self.scene_list.clear()

        if not items:
            item = QListWidgetItem(f"「{query}」に一致するシーンがありません")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.scene_list.addItem(item)
            return

        # 使用回数順にソート
        items_sorted = sorted(items, key=lambda x: x.usage_count, reverse=True)

        for lib_item in items_sorted:
            display_text = f"{lib_item.name} [{lib_item.category}]"
            if lib_item.usage_count > 0:
                display_text += f" (使用: {lib_item.usage_count}回)"

            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.ItemDataRole.UserRole, lib_item.id)
            self.scene_list.addItem(list_item)

    def _on_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        """選択変更時"""
        if not current:
            self.detail_text.clear()
            self.insert_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return

        # アイテムIDを取得
        item_id = current.data(Qt.ItemDataRole.UserRole)
        if not item_id:
            self.detail_text.clear()
            self.insert_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return

        # ライブラリアイテムを取得
        lib_item = self.scene_library_manager.get_item_by_id(item_id)
        if not lib_item:
            return

        # 詳細情報を表示
        detail_html = f"""
        <h3>{lib_item.name}</h3>
        <p><b>カテゴリ:</b> {lib_item.category}</p>
        <p><b>ブロック数:</b> {len(lib_item.block_templates)}</p>
        <p><b>タグ:</b> {', '.join(lib_item.tags) if lib_item.tags else 'なし'}</p>
        <p><b>使用回数:</b> {lib_item.usage_count}回</p>
        """

        if lib_item.last_used:
            detail_html += f"<p><b>最終使用:</b> {lib_item.last_used.strftime('%Y-%m-%d %H:%M')}</p>"

        if lib_item.description:
            detail_html += f"<p><b>説明:</b><br>{lib_item.description}</p>"

        if lib_item.used_in_projects:
            projects = ', '.join(lib_item.used_in_projects[:3])
            if len(lib_item.used_in_projects) > 3:
                projects += f" など({len(lib_item.used_in_projects)}件)"
            detail_html += f"<p><b>使用プロジェクト:</b><br>{projects}</p>"

        self.detail_text.setHtml(detail_html)
        self.insert_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """アイテムダブルクリック時"""
        # ダブルクリックで即座に挿入
        self._on_insert()

    def _on_insert(self):
        """挿入ボタンクリック"""
        current_item = self.scene_list.currentItem()
        if not current_item:
            return

        item_id = current_item.data(Qt.ItemDataRole.UserRole)
        if not item_id:
            return

        self.selected_item = self.scene_library_manager.get_item_by_id(item_id)
        if not self.selected_item:
            QMessageBox.warning(
                self,
                "エラー",
                "選択されたシーンが見つかりません"
            )
            return

        self.logger.info(f"シーン選択: {self.selected_item.name}")
        self.accept()

    def _on_delete(self):
        """削除ボタンクリック"""
        current_item = self.scene_list.currentItem()
        if not current_item:
            return

        item_id = current_item.data(Qt.ItemDataRole.UserRole)
        if not item_id:
            return

        lib_item = self.scene_library_manager.get_item_by_id(item_id)
        if not lib_item:
            return

        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "削除確認",
            f"シーン「{lib_item.name}」をライブラリから削除しますか？\n\n"
            f"この操作は取り消せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 削除
            if self.scene_library_manager.delete_item(item_id):
                self.logger.info(f"シーン削除: {lib_item.name}")

                # シグナル発火
                self.scene_deleted.emit(item_id)

                # リストを再読み込み
                self._load_items()

                QMessageBox.information(
                    self,
                    "削除完了",
                    f"シーン「{lib_item.name}」を削除しました"
                )
            else:
                QMessageBox.warning(
                    self,
                    "エラー",
                    "シーンの削除に失敗しました"
                )

    def get_selected_item(self) -> SceneLibraryItem:
        """選択されたライブラリアイテムを取得

        Returns:
            選択されたSceneLibraryItemオブジェクト、選択されていない場合None
        """
        return self.selected_item
