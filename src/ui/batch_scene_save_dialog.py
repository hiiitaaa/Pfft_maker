"""バッチシーン保存ダイアログ

完成したシーンを一括でライブラリに保存するためのダイアログです。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QComboBox,
    QMessageBox, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt
from typing import List

from models import Scene
from core.scene_library_manager import SceneLibraryManager
from utils.logger import get_logger


class BatchSceneSaveDialog(QDialog):
    """バッチシーン保存ダイアログ

    複数の完成シーンを一括でライブラリに保存します。

    Attributes:
        scenes: 保存候補のシーンリスト
        scene_library_manager: シーンライブラリマネージャー
        saved_count: 保存されたシーン数
    """

    def __init__(
        self,
        scenes: List[Scene],
        scene_library_manager: SceneLibraryManager,
        parent=None
    ):
        """初期化

        Args:
            scenes: 保存候補のシーンリスト
            scene_library_manager: シーンライブラリマネージャー
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.scenes = scenes
        self.scene_library_manager = scene_library_manager
        self.saved_count = 0
        self.logger = get_logger()

        # ダイアログ設定
        self.setWindowTitle("シーンを一括保存")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        # UI構築
        self._create_ui()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # タイトル
        title_label = QLabel("シーンを一括保存")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # 説明
        desc_label = QLabel(
            "完成したシーンをライブラリに一括保存できます。\n"
            "保存したいシーンにチェックを入れてください。"
        )
        desc_label.setStyleSheet("color: #666;")
        layout.addWidget(desc_label)

        # シーンリスト
        list_group = QGroupBox("シーン一覧")
        list_layout = QVBoxLayout()

        # 選択ボタン
        select_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("全選択")
        select_all_btn.clicked.connect(self._on_select_all)
        select_btn_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("全解除")
        deselect_all_btn.clicked.connect(self._on_deselect_all)
        select_btn_layout.addWidget(deselect_all_btn)

        select_btn_layout.addStretch()
        list_layout.addLayout(select_btn_layout)

        self.scene_list = QListWidget()
        self.scene_list.setAlternatingRowColors(True)

        # シーンをリストに追加
        for scene in self.scenes:
            block_count = len(scene.blocks)
            item_text = f"{scene.scene_name} ({block_count}ブロック)"

            item = QListWidgetItem(item_text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)  # デフォルトで選択
            item.setData(Qt.ItemDataRole.UserRole, scene)
            self.scene_list.addItem(item)

        list_layout.addWidget(self.scene_list)

        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # 共通設定
        settings_group = QGroupBox("共通設定")
        settings_layout = QVBoxLayout()

        # カテゴリ
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("保存先カテゴリ:"))

        self.category_combo = QComboBox()

        # 既存のカテゴリを取得
        existing_categories = self.scene_library_manager.get_categories()
        default_categories = ["その他", "恋愛", "学園", "日常", "アクション", "ファンタジー"]

        # 既存カテゴリと合わせて重複なしのリストを作成
        all_categories = list(set(default_categories + existing_categories))
        all_categories.sort()

        self.category_combo.addItems(all_categories)
        self.category_combo.setEditable(True)  # 手動入力も可能
        cat_layout.addWidget(self.category_combo)

        settings_layout.addLayout(cat_layout)

        # タグ自動生成
        self.auto_tag_checkbox = QCheckBox("シーン名からタグを自動生成")
        self.auto_tag_checkbox.setChecked(True)
        self.auto_tag_checkbox.setToolTip("シーン名を分割してタグとして設定します")
        settings_layout.addWidget(self.auto_tag_checkbox)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("一括保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save_batch)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _on_select_all(self):
        """全選択"""
        for i in range(self.scene_list.count()):
            item = self.scene_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)

    def _on_deselect_all(self):
        """全解除"""
        for i in range(self.scene_list.count()):
            item = self.scene_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)

    def _on_save_batch(self):
        """一括保存"""
        # チェックされたシーンを取得
        selected_scenes = []
        for i in range(self.scene_list.count()):
            item = self.scene_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                scene = item.data(Qt.ItemDataRole.UserRole)
                selected_scenes.append(scene)

        if not selected_scenes:
            QMessageBox.warning(
                self,
                "選択エラー",
                "保存するシーンを選択してください。"
            )
            return

        # カテゴリ
        category = self.category_combo.currentText().strip()
        if not category:
            category = "その他"

        # タグ自動生成
        auto_tag = self.auto_tag_checkbox.isChecked()

        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "確認",
            f"{len(selected_scenes)}個のシーンをライブラリに保存しますか？\n\n"
            f"カテゴリ: {category}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 一括保存
        self.saved_count = 0
        failed_scenes = []

        for scene in selected_scenes:
            try:
                # タグ生成
                tags = []
                if auto_tag:
                    # シーン名をスペースで分割してタグ化
                    tags = [t.strip() for t in scene.scene_name.split() if t.strip()]

                # 保存
                self.scene_library_manager.save_scene_to_library(
                    scene=scene,
                    name=scene.scene_name,
                    description=f"バッチ保存されたシーン（ブロック数: {len(scene.blocks)}）",
                    category=category,
                    tags=tags
                )

                self.saved_count += 1
                self.logger.info(f"バッチ保存成功: {scene.scene_name}")

            except Exception as e:
                self.logger.error(f"バッチ保存失敗: {scene.scene_name} - {e}", exc_info=True)
                failed_scenes.append(scene.scene_name)

        # 結果表示
        if failed_scenes:
            QMessageBox.warning(
                self,
                "一部失敗",
                f"✅ 保存成功: {self.saved_count}個\n"
                f"❌ 保存失敗: {len(failed_scenes)}個\n\n"
                f"失敗したシーン:\n" + "\n".join(failed_scenes)
            )
        else:
            QMessageBox.information(
                self,
                "保存完了",
                f"✅ {self.saved_count}個のシーンをライブラリに保存しました！"
            )

        self.accept()

    def get_saved_count(self) -> int:
        """保存されたシーン数を取得

        Returns:
            保存されたシーン数
        """
        return self.saved_count
