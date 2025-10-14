"""シーン保存ダイアログ

シーンをライブラリに保存するためのダイアログです。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt

from models import Scene
from core.scene_library_manager import SceneLibraryManager
from utils.logger import get_logger


class SceneSaveDialog(QDialog):
    """シーン保存ダイアログ

    シーンをライブラリに保存する際の設定を行います。

    Attributes:
        scene: 保存するシーン
        scene_library_manager: シーンライブラリマネージャー
        saved_item: 保存されたライブラリアイテム
    """

    def __init__(
        self,
        scene: Scene,
        scene_library_manager: SceneLibraryManager,
        parent=None
    ):
        """初期化

        Args:
            scene: 保存するシーン
            scene_library_manager: シーンライブラリマネージャー
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.scene = scene
        self.scene_library_manager = scene_library_manager
        self.saved_item = None
        self.logger = get_logger()

        # ダイアログ設定
        self.setWindowTitle("シーンをライブラリに保存")
        self.setMinimumWidth(500)

        # UI構築
        self._create_ui()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # タイトル
        title_label = QLabel("シーンをライブラリに保存")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # シーン情報
        info_group = QGroupBox("シーン情報")
        info_layout = QVBoxLayout()

        # 現在のシーン名
        current_name_label = QLabel(f"現在のシーン名: {self.scene.scene_name}")
        current_name_label.setStyleSheet("color: gray;")
        info_layout.addWidget(current_name_label)

        # ブロック数
        block_count_label = QLabel(f"ブロック数: {len(self.scene.blocks)}")
        block_count_label.setStyleSheet("color: gray;")
        info_layout.addWidget(block_count_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # ライブラリ設定
        library_group = QGroupBox("ライブラリ設定")
        library_layout = QVBoxLayout()

        # シーン名
        library_layout.addWidget(QLabel("シーン名（必須）:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例: 学園廊下でのキス")
        self.name_input.setText(self.scene.scene_name)  # デフォルトで現在の名前を設定
        library_layout.addWidget(self.name_input)

        # カテゴリ
        library_layout.addWidget(QLabel("カテゴリ:"))

        category_layout = QHBoxLayout()
        self.category_combo = QComboBox()

        # 既存のカテゴリを取得
        existing_categories = self.scene_library_manager.get_categories()
        default_categories = ["その他", "恋愛", "学園", "日常", "アクション", "ファンタジー"]

        # 既存カテゴリと合わせて重複なしのリストを作成
        all_categories = list(set(default_categories + existing_categories))
        all_categories.sort()

        self.category_combo.addItems(all_categories)
        self.category_combo.setEditable(True)  # 手動入力も可能
        category_layout.addWidget(self.category_combo)

        library_layout.addLayout(category_layout)

        # タグ
        library_layout.addWidget(QLabel("タグ（カンマ区切り）:"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("例: キス, 廊下, 学園, 放課後")
        library_layout.addWidget(self.tags_input)

        # 説明（オプション）
        library_layout.addWidget(QLabel("説明（オプション）:"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("例: 学園の廊下で放課後にキスするシーン。よく使う。")
        self.description_input.setMaximumHeight(80)
        library_layout.addWidget(self.description_input)

        library_group.setLayout(library_layout)
        layout.addWidget(library_group)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _on_save(self):
        """保存ボタンクリック"""
        # 入力チェック
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                "入力エラー",
                "シーン名を入力してください。"
            )
            self.name_input.setFocus()
            return

        # ブロック数チェック
        if not self.scene.blocks:
            QMessageBox.warning(
                self,
                "エラー",
                "ブロックが1つもありません。\nシーンにブロックを追加してから保存してください。"
            )
            return

        # カテゴリ
        category = self.category_combo.currentText().strip()
        if not category:
            category = "その他"

        # タグをパース
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]

        # 説明
        description = self.description_input.toPlainText().strip()

        # ライブラリに保存
        try:
            self.saved_item = self.scene_library_manager.save_scene_to_library(
                scene=self.scene,
                name=name,
                description=description,
                category=category,
                tags=tags
            )

            self.logger.info(f"シーンをライブラリに保存: {name}")

            QMessageBox.information(
                self,
                "保存完了",
                f"シーン「{name}」をライブラリに保存しました。\n\n"
                f"カテゴリ: {category}\n"
                f"ブロック数: {len(self.scene.blocks)}\n"
                f"タグ: {', '.join(tags) if tags else 'なし'}"
            )

            self.accept()

        except Exception as e:
            self.logger.error(f"シーン保存失敗: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "エラー",
                f"シーンの保存に失敗しました:\n{e}"
            )

    def get_saved_item(self):
        """保存されたライブラリアイテムを取得

        Returns:
            保存されたSceneLibraryItemオブジェクト、保存されていない場合None
        """
        return self.saved_item
