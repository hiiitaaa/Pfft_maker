"""自作プロンプト保存ダイアログ

ユーザーが作成したプロンプトをライブラリに保存するダイアログUI。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Optional

from core.custom_prompt_manager import CustomPromptManager
from models.custom_prompt import CustomPrompt


class CustomPromptDialog(QDialog):
    """自作プロンプト保存ダイアログ

    プロンプトの保存・編集を行うダイアログ。

    Attributes:
        custom_prompt_manager: 自作プロンプト管理
        prompt_text: プロンプト本体
        existing_prompt: 編集対象のプロンプト（編集モード時）
    """

    def __init__(
        self,
        custom_prompt_manager: CustomPromptManager,
        prompt_text: str = "",
        existing_prompt: Optional[CustomPrompt] = None,
        parent=None
    ):
        """初期化

        Args:
            custom_prompt_manager: 自作プロンプト管理
            prompt_text: プロンプト本体
            existing_prompt: 編集対象のプロンプト（編集モード時）
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.custom_prompt_manager = custom_prompt_manager
        self.prompt_text = prompt_text
        self.existing_prompt = existing_prompt
        self.saved_prompt: Optional[CustomPrompt] = None

        # タイトル設定
        if existing_prompt:
            self.setWindowTitle("プロンプトを編集")
        else:
            self.setWindowTitle("ライブラリに保存")

        self.setModal(True)
        self.resize(500, 450)

        self._create_ui()
        self._load_data()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # プロンプト編集
        prompt_label = QLabel("プロンプト:")
        layout.addWidget(prompt_label)

        self.prompt_display = QTextEdit()
        self.prompt_display.setPlainText(self.prompt_text)
        self.prompt_display.setMaximumHeight(80)
        self.prompt_display.setStyleSheet("""
            QTextEdit {
                background-color: white;
                color: black;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.prompt_display)

        # 日本語ラベル（必須）
        label_ja_layout = QHBoxLayout()
        label_ja_label = QLabel("日本語ラベル:")
        label_ja_required = QLabel("<span style='color: red;'>*必須</span>")
        label_ja_layout.addWidget(label_ja_label)
        label_ja_layout.addWidget(label_ja_required)
        label_ja_layout.addStretch()
        layout.addLayout(label_ja_layout)

        self.label_ja_edit = QLineEdit()
        self.label_ja_edit.setPlaceholderText("例: 服の上から愛撫")
        layout.addWidget(self.label_ja_edit)

        # 英語ラベル（オプション）
        label_en_label = QLabel("英語ラベル:")
        layout.addWidget(label_en_label)

        self.label_en_edit = QLineEdit()
        self.label_en_edit.setPlaceholderText("例: touching over clothes")
        layout.addWidget(self.label_en_edit)

        # カテゴリ
        category_label = QLabel("カテゴリ:")
        layout.addWidget(category_label)

        self.category_combo = QComboBox()
        self._populate_categories()
        layout.addWidget(self.category_combo)

        # タグ
        tags_label = QLabel("タグ: (カンマ区切り)")
        layout.addWidget(tags_label)

        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("例: 愛撫,服装付き,clothed")
        layout.addWidget(self.tags_edit)

        # メモ
        notes_label = QLabel("メモ:")
        layout.addWidget(notes_label)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("特によく使うプロンプト")
        self.notes_edit.setMaximumHeight(60)
        layout.addWidget(self.notes_edit)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self._on_save)
        self.save_button.setDefault(True)
        self.save_button.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

    def _populate_categories(self):
        """カテゴリドロップダウンを設定"""
        # デフォルトカテゴリ
        default_categories = [
            "自作",
            "行為",
            "背景",
            "キャラ",
            "ポージング",
            "アングル",
            "その他"
        ]

        # 既存のカスタムカテゴリを追加
        existing_categories = self.custom_prompt_manager.get_categories()

        # 重複を除いて統合
        all_categories = default_categories.copy()
        for cat in existing_categories:
            if cat not in all_categories:
                all_categories.append(cat)

        self.category_combo.addItems(all_categories)

        # デフォルトで「自作」を選択
        default_index = self.category_combo.findText("自作")
        if default_index >= 0:
            self.category_combo.setCurrentIndex(default_index)

    def _load_data(self):
        """データを読み込み（編集モード時）"""
        if self.existing_prompt:
            # 編集モード: 既存データを表示
            self.label_ja_edit.setText(self.existing_prompt.label_ja)
            self.label_en_edit.setText(self.existing_prompt.label_en)

            # カテゴリ設定
            category_index = self.category_combo.findText(self.existing_prompt.category)
            if category_index >= 0:
                self.category_combo.setCurrentIndex(category_index)

            # タグ設定（カンマ区切りに変換）
            self.tags_edit.setText(", ".join(self.existing_prompt.tags))

            # メモ設定
            self.notes_edit.setPlainText(self.existing_prompt.notes)

            # プロンプト表示更新
            self.prompt_display.setPlainText(self.existing_prompt.prompt)

        else:
            # 新規保存モード: タグを自動生成
            if self.prompt_text:
                auto_tags = self.custom_prompt_manager._generate_tags(self.prompt_text)
                self.tags_edit.setText(", ".join(auto_tags))

    def _on_save(self):
        """保存ボタンクリック"""
        # バリデーション
        label_ja = self.label_ja_edit.text().strip()
        if not label_ja:
            QMessageBox.warning(
                self,
                "入力エラー",
                "日本語ラベルは必須です。"
            )
            self.label_ja_edit.setFocus()
            return

        # 入力値取得
        label_en = self.label_en_edit.text().strip()
        category = self.category_combo.currentText()
        tags_text = self.tags_edit.text().strip()
        notes = self.notes_edit.toPlainText().strip()

        # タグをリストに変換
        if tags_text:
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        else:
            tags = []

        # プロンプト内容を取得
        prompt_content = self.prompt_display.toPlainText().strip()

        if not prompt_content:
            QMessageBox.warning(
                self,
                "入力エラー",
                "プロンプト内容を入力してください。"
            )
            self.prompt_display.setFocus()
            return

        try:
            if self.existing_prompt:
                # 更新モード
                success = self.custom_prompt_manager.update_prompt(
                    prompt_id=self.existing_prompt.id,
                    prompt=prompt_content,
                    label_ja=label_ja,
                    label_en=label_en,
                    category=category,
                    tags=tags,
                    notes=notes
                )

                if success:
                    self.saved_prompt = self.custom_prompt_manager.get_prompt_by_id(
                        self.existing_prompt.id
                    )
                    QMessageBox.information(
                        self,
                        "完了",
                        "プロンプトを更新しました。"
                    )
                    self.accept()
                else:
                    QMessageBox.critical(
                        self,
                        "エラー",
                        "プロンプトの更新に失敗しました。"
                    )

            else:
                # 新規保存モード
                self.saved_prompt = self.custom_prompt_manager.add_prompt(
                    prompt=prompt_content,
                    label_ja=label_ja,
                    label_en=label_en,
                    category=category,
                    tags=tags,
                    notes=notes
                )

                QMessageBox.information(
                    self,
                    "完了",
                    f"プロンプトをライブラリに保存しました。\n\nID: {self.saved_prompt.id}"
                )
                self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "エラー",
                f"保存中にエラーが発生しました:\n{e}"
            )

    def get_saved_prompt(self) -> Optional[CustomPrompt]:
        """保存されたプロンプトを取得

        Returns:
            保存されたCustomPromptオブジェクト
        """
        return self.saved_prompt
