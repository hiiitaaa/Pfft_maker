"""プレビューパネル

最終プロンプトのプレビューを表示するパネル。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QClipboard
from PyQt6.QtWidgets import QApplication

from models import Scene
from core.prompt_builder import PromptBuilder
from config.settings import Settings


class PreviewPanel(QWidget):
    """プレビューパネル

    最終プロンプトの表示とコピー機能を提供。
    """

    def __init__(self):
        """初期化"""
        super().__init__()

        self.current_scene: Scene | None = None
        self.settings = Settings()
        self.prompt_builder = PromptBuilder(self.settings)

        # UI構築
        self._create_ui()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # タイトル
        title_label = QLabel("プレビュー")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # プロンプト表示
        layout.addWidget(QLabel("最終プロンプト:"))

        self.prompt_text = QTextEdit()
        self.prompt_text.setReadOnly(True)
        self.prompt_text.setPlaceholderText("プロンプトがここに表示されます")
        layout.addWidget(self.prompt_text)

        # 文字数カウント
        self.char_count_label = QLabel("文字数: 0")
        self.char_count_label.setStyleSheet("color: gray;")
        layout.addWidget(self.char_count_label)

        # ボタン
        button_layout = QHBoxLayout()

        copy_btn = QPushButton("コピー")
        copy_btn.clicked.connect(self._on_copy)
        button_layout.addWidget(copy_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        # ワイルドカード展開候補（将来実装）
        layout.addWidget(QLabel("ワイルドカード展開候補:"))

        self.candidates_text = QTextEdit()
        self.candidates_text.setReadOnly(True)
        self.candidates_text.setPlaceholderText(
            "ワイルドカード展開候補がここに表示されます\n"
            "（Phase 4.3で実装予定）"
        )
        self.candidates_text.setMaximumHeight(200)
        layout.addWidget(self.candidates_text)

    def update_preview(self, scene: Scene):
        """プレビュー更新

        Args:
            scene: シーンオブジェクト
        """
        self.current_scene = scene

        # プロンプト構築
        if scene.blocks:
            prompt = self.prompt_builder.build_scene_prompt(scene)
        else:
            prompt = ""

        # 表示更新
        self.prompt_text.setPlainText(prompt)
        self.char_count_label.setText(f"文字数: {len(prompt)}")

        # バリデーション
        is_valid, error_msg = self.prompt_builder.validate_blocks(scene)
        if not is_valid:
            self.prompt_text.setStyleSheet("background-color: #ffe6e6;")
            self.char_count_label.setText(f"エラー: {error_msg}")
            self.char_count_label.setStyleSheet("color: red;")
        else:
            self.prompt_text.setStyleSheet("")
            self.char_count_label.setStyleSheet("color: gray;")

    def _on_copy(self):
        """プロンプトをクリップボードにコピー"""
        prompt = self.prompt_text.toPlainText()
        if prompt:
            clipboard = QApplication.clipboard()
            clipboard.setText(prompt)
            self.char_count_label.setText(f"文字数: {len(prompt)} (コピーしました)")
