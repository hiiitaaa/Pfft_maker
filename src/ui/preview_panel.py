"""プレビューパネル

最終プロンプトのプレビューを表示するパネル。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QHBoxLayout, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QClipboard
from PyQt6.QtWidgets import QApplication
from pathlib import Path

from models import Scene, Project
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
        self.current_project: Project | None = None
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

        export_btn = QPushButton("ファイル出力")
        export_btn.clicked.connect(self._on_export_file)
        button_layout.addWidget(export_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

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

    def update_all_scenes(self, project: Project):
        """全シーンのプレビューを表示（保存済みシーンのみ）

        Args:
            project: プロジェクトオブジェクト
        """
        self.current_project = project  # プロジェクトを保存

        if not project or not project.scenes:
            self.prompt_text.setPlainText("")
            self.char_count_label.setText("文字数: 0")
            return

        # 全シーンのプロンプトを構築
        all_prompts = []
        total_chars = 0

        for scene in project.scenes:
            # ブロックが空のシーンはスキップ（未保存シーン）
            if not scene.blocks:
                continue

            # シーンヘッダー
            scene_header = f"━━━ {scene.scene_name} ━━━"
            all_prompts.append(scene_header)

            # シーンのプロンプト
            scene_prompt = self.prompt_builder.build_scene_prompt(scene)
            all_prompts.append(scene_prompt)
            all_prompts.append("")  # 空行

            total_chars += len(scene_prompt)

        # 表示更新
        final_prompt = "\n".join(all_prompts)
        self.prompt_text.setPlainText(final_prompt)
        self.char_count_label.setText(f"文字数: {total_chars} ({len(project.scenes)}シーン)")
        self.char_count_label.setStyleSheet("color: gray;")
        self.prompt_text.setStyleSheet("")

    def _get_export_text(self) -> str:
        """出力用のテキストを取得（ヘッダーなし、1シーン1行）

        Returns:
            出力用のテキスト（各シーンが1行、改行区切り）
        """
        if not self.current_project or not self.current_project.scenes:
            return ""

        export_lines = []

        for scene in self.current_project.scenes:
            # ブロックが空のシーンはスキップ（未保存シーン）
            if not scene.blocks:
                continue

            # シーンのプロンプトを構築（1行にまとめる）
            scene_prompt = self.prompt_builder.build_scene_prompt(scene)
            export_lines.append(scene_prompt)

        # シーンごとに改行で区切る
        return "\n".join(export_lines)

    def _on_copy(self):
        """プロンプトをクリップボードにコピー（ヘッダーなし、1シーン1行）"""
        export_text = self._get_export_text()

        if export_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(export_text)

            # コピーした行数をカウント
            line_count = len(export_text.split('\n'))
            self.char_count_label.setText(f"文字数: {len(export_text)} ({line_count}シーンをコピーしました)")
        else:
            QMessageBox.warning(
                self,
                "コピーエラー",
                "コピーするプロンプトがありません。\n\n"
                "先にシーンを「🖼️ シーンを保存（プレビューへ表示）」してください。"
            )

    def _on_export_file(self):
        """ファイルに出力（ヘッダーなし、1シーン1行）"""
        export_text = self._get_export_text()

        if not export_text:
            QMessageBox.warning(
                self,
                "出力エラー",
                "出力するプロンプトがありません。\n\n"
                "先にシーンを「🖼️ シーンを保存（プレビューへ表示）」してください。"
            )
            return

        # ファイル保存ダイアログを表示
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "プロンプトをファイルに保存",
            str(Path.home() / "prompts.txt"),
            "テキストファイル (*.txt);;すべてのファイル (*.*)"
        )

        if not file_path:
            return

        try:
            # ファイルに書き込み
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(export_text)

            # 成功メッセージ
            line_count = len(export_text.split('\n'))
            QMessageBox.information(
                self,
                "出力完了",
                f"プロンプトをファイルに保存しました。\n\n"
                f"ファイル: {file_path}\n"
                f"シーン数: {line_count}\n"
                f"文字数: {len(export_text)}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "エラー",
                f"ファイルの保存に失敗しました:\n{e}"
            )
