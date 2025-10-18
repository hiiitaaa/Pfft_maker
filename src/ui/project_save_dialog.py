"""作品保存ダイアログ

プロジェクト全体を作品ライブラリに保存するダイアログ。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QDialogButtonBox, QMessageBox, QRadioButton, QButtonGroup,
    QGroupBox
)
from PyQt6.QtCore import Qt
from typing import Optional

from models import Project, ProjectLibraryItem
from core.project_library_manager import ProjectLibraryManager
from core.scene_library_manager import SceneLibraryManager


class ProjectSaveDialog(QDialog):
    """作品保存ダイアログ

    プロジェクト全体（複数シーン）を作品ライブラリに保存。

    Attributes:
        project: 保存するプロジェクト
        project_library_manager: 作品ライブラリマネージャー
        saved_item: 保存されたProjectLibraryItemオブジェクト
    """

    def __init__(
        self,
        project: Project,
        project_library_manager: ProjectLibraryManager,
        scene_library_manager: SceneLibraryManager,
        existing_item_id: Optional[str] = None,
        parent=None
    ):
        """初期化

        Args:
            project: 保存するプロジェクト
            project_library_manager: 作品ライブラリマネージャー
            scene_library_manager: シーンライブラリマネージャー
            existing_item_id: 既存の作品ID（上書き保存する場合）
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.project = project
        self.project_library_manager = project_library_manager
        self.scene_library_manager = scene_library_manager
        self.existing_item_id = existing_item_id
        self.existing_item: Optional[ProjectLibraryItem] = None
        self.saved_item: ProjectLibraryItem | None = None

        # 既存アイテムを取得
        if existing_item_id:
            self.existing_item = project_library_manager.get_item_by_id(existing_item_id)

        self.setWindowTitle("作品をライブラリに保存")
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)

        self._create_ui()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)

        # タイトル
        title_label = QLabel("📚 作品をライブラリに保存")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # 説明
        info_label = QLabel(
            f"このプロジェクトの全シーン（{len(self.project.scenes)}シーン）を\n"
            "作品ライブラリに保存します。\n\n"
            "後で別のプロジェクトで全シーン一括挿入、または\n"
            "個別シーンを選択して挿入できます。"
        )
        info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # 保存モード選択（既存アイテムがある場合のみ表示）
        if self.existing_item:
            save_mode_group = QGroupBox("保存モード")
            save_mode_layout = QVBoxLayout()

            self.save_mode_button_group = QButtonGroup()

            self.overwrite_radio = QRadioButton(f"上書き保存（既存の「{self.existing_item.name}」を更新）")
            self.overwrite_radio.setChecked(True)
            self.save_mode_button_group.addButton(self.overwrite_radio, 0)
            save_mode_layout.addWidget(self.overwrite_radio)

            self.new_save_radio = QRadioButton("新規保存（新しい作品として保存）")
            self.save_mode_button_group.addButton(self.new_save_radio, 1)
            save_mode_layout.addWidget(self.new_save_radio)

            save_mode_group.setLayout(save_mode_layout)
            layout.addWidget(save_mode_group)
        else:
            # 既存アイテムがない場合は新規保存のみ
            self.save_mode_button_group = None

        # 作品名
        layout.addWidget(QLabel("作品名:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例: 学園メイドCG集")
        # デフォルトでプロジェクト名を設定
        self.name_edit.setText(self.project.name)
        layout.addWidget(self.name_edit)

        # 説明
        layout.addWidget(QLabel("説明（オプション）:"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(
            "この作品の説明を入力してください。\n"
            "例: 保健室を舞台にしたメイド物のCG集"
        )
        self.description_edit.setMaximumHeight(100)
        # デフォルトでプロジェクトの説明を設定
        if self.project.description:
            self.description_edit.setPlainText(self.project.description)
        layout.addWidget(self.description_edit)

        # カテゴリ
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("カテゴリ:"))

        self.category_combo = QComboBox()
        # 既存のカテゴリを取得
        categories = self.project_library_manager.get_categories()
        default_categories = ["CG集", "漫画", "イラスト", "その他"]

        # 既存カテゴリ + デフォルトカテゴリを統合
        all_categories = list(set(categories + default_categories))
        all_categories.sort()

        self.category_combo.addItems(all_categories)
        self.category_combo.setCurrentText("CG集")
        self.category_combo.setEditable(True)  # 新しいカテゴリを入力可能
        category_layout.addWidget(self.category_combo)

        category_layout.addStretch()
        layout.addLayout(category_layout)

        # タグ
        layout.addWidget(QLabel("タグ（カンマ区切り、オプション）:"))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("例: 学園, メイド, 保健室")
        layout.addWidget(self.tags_edit)

        # スペーサー
        layout.addStretch()

        # シーン数の確認表示
        scene_count_label = QLabel(
            f"✅ {len(self.project.scenes)}シーンを保存します"
        )
        scene_count_label.setStyleSheet(
            "color: green; font-weight: bold; margin-top: 10px;"
        )
        layout.addWidget(scene_count_label)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_save(self):
        """保存ボタンクリック"""
        # 入力チェック
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                "入力エラー",
                "作品名を入力してください。"
            )
            return

        # シーン数チェック
        if not self.project.scenes:
            QMessageBox.warning(
                self,
                "エラー",
                "シーンが1つもありません。\n"
                "シーンを追加してから保存してください。"
            )
            return

        description = self.description_edit.toPlainText().strip()
        category = self.category_combo.currentText().strip()
        tags_text = self.tags_edit.text().strip()

        # タグをリストに変換
        tags = []
        if tags_text:
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]

        # 保存モードを判定
        is_overwrite = False
        if self.save_mode_button_group and self.existing_item:
            is_overwrite = self.save_mode_button_group.checkedId() == 0

        try:
            if is_overwrite and self.existing_item:
                # 上書き保存
                # 既存アイテムを更新
                updated_item = ProjectLibraryItem.create_from_project(
                    project=self.project,
                    name=name,
                    description=description,
                    category=category,
                    tags=tags
                )
                # IDと使用統計を保持
                updated_item.id = self.existing_item.id
                updated_item.usage_count = self.existing_item.usage_count
                updated_item.last_used = self.existing_item.last_used
                updated_item.usage_history = self.existing_item.usage_history

                # 更新
                success = self.project_library_manager.update_item(updated_item)

                if success:
                    self.saved_item = updated_item

                    # 各シーンもシーンライブラリに自動保存
                    saved_scene_count = self._save_scenes_to_library(category, tags)

                    QMessageBox.information(
                        self,
                        "上書き保存完了",
                        f"作品「{name}」を上書き保存しました。\n\n"
                        f"シーン数: {len(self.project.scenes)}\n"
                        f"カテゴリ: {category}\n\n"
                        f"各シーン {saved_scene_count}件もシーンライブラリに保存しました。\n"
                        f"ライブラリパネルから挿入できます。"
                    )
                    self.accept()
                else:
                    QMessageBox.critical(
                        self,
                        "保存エラー",
                        "作品の上書き保存に失敗しました。"
                    )
            else:
                # 新規保存
                self.saved_item = self.project_library_manager.save_project_to_library(
                    project=self.project,
                    name=name,
                    description=description,
                    category=category,
                    tags=tags
                )

                # 各シーンもシーンライブラリに自動保存
                saved_scene_count = self._save_scenes_to_library(category, tags)

                # 成功メッセージ
                QMessageBox.information(
                    self,
                    "保存完了",
                    f"作品「{name}」を新規保存しました。\n\n"
                    f"シーン数: {len(self.project.scenes)}\n"
                    f"カテゴリ: {category}\n\n"
                    f"各シーン {saved_scene_count}件もシーンライブラリに保存しました。\n"
                    f"ライブラリパネルから挿入できます。"
                )

                self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "保存エラー",
                f"作品の保存に失敗しました:\n{e}"
            )

    def _save_scenes_to_library(self, category: str, tags: list) -> int:
        """各シーンをシーンライブラリに保存

        Args:
            category: カテゴリ
            tags: タグリスト

        Returns:
            保存したシーンの数
        """
        saved_count = 0

        for scene in self.project.scenes:
            # ブロックがないシーンはスキップ
            if not scene.blocks:
                continue

            try:
                # シーンをシーンライブラリに保存
                self.scene_library_manager.save_scene_to_library(
                    scene=scene,
                    name=scene.scene_name,
                    description=f"{self.project.name} - {scene.scene_name}",
                    category=category,
                    tags=tags
                )
                saved_count += 1
            except Exception as e:
                # エラーがあってもログだけ出力して続行
                from utils.logger import get_logger
                logger = get_logger()
                logger.warning(f"シーン「{scene.scene_name}」のライブラリ保存に失敗: {e}")

        return saved_count

    def get_saved_item(self) -> ProjectLibraryItem | None:
        """保存されたアイテムを取得

        Returns:
            保存されたProjectLibraryItemオブジェクト、保存されていない場合None
        """
        return self.saved_item
