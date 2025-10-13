"""プロンプトファイル出力ダイアログ

FR-018: プロンプトファイル出力機能のUIを提供します。
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QRadioButton,
    QButtonGroup, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from models import Project
from core.prompt_builder import PromptBuilder
from config.settings import Settings


class OutputDialog(QDialog):
    """プロンプトファイル出力ダイアログ

    プロンプトをファイルまたはクリップボードに出力する設定を提供。

    Attributes:
        project: プロジェクトオブジェクト
        output_path: 出力パス
    """

    def __init__(self, project: Project, parent=None):
        """初期化

        Args:
            project: プロジェクトオブジェクト
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.project = project
        self.settings = Settings()
        self.prompt_builder = PromptBuilder(self.settings)
        self.output_path: Path | None = None

        # ダイアログ設定
        self.setWindowTitle("プロンプトファイル出力")
        self.setMinimumWidth(500)

        # UI構築
        self._create_ui()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # タイトル
        title_label = QLabel("プロンプトファイル出力")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # 出力先選択
        layout.addWidget(QLabel("出力先:"))

        self.output_group = QButtonGroup(self)

        self.file_radio = QRadioButton("ファイル")
        self.file_radio.setChecked(True)
        self.file_radio.toggled.connect(self._on_output_type_changed)
        self.output_group.addButton(self.file_radio)
        layout.addWidget(self.file_radio)

        # ファイル設定
        file_layout = QHBoxLayout()
        file_layout.setContentsMargins(30, 0, 0, 0)

        self.file_name_edit = QLineEdit()
        self.file_name_edit.setPlaceholderText("prompts.txt")
        file_layout.addWidget(QLabel("ファイル名:"))
        file_layout.addWidget(self.file_name_edit)

        browse_btn = QPushButton("参照...")
        browse_btn.clicked.connect(self._on_browse)
        file_layout.addWidget(browse_btn)

        layout.addLayout(file_layout)

        # クリップボード
        self.clipboard_radio = QRadioButton("クリップボード")
        self.output_group.addButton(self.clipboard_radio)
        layout.addWidget(self.clipboard_radio)

        # オプション
        layout.addWidget(QLabel("オプション:"))

        self.completed_only_checkbox = QCheckBox("完成済みシーンのみ")
        self.completed_only_checkbox.setChecked(True)
        layout.addWidget(self.completed_only_checkbox)

        self.include_comment_checkbox = QCheckBox("シーン番号をコメントで追記")
        layout.addWidget(self.include_comment_checkbox)

        # プレビュー
        layout.addWidget(QLabel("出力プレビュー:"))

        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("color: gray;")
        layout.addWidget(self.preview_label)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        export_btn = QPushButton("出力")
        export_btn.setDefault(True)
        export_btn.clicked.connect(self._on_export)
        button_layout.addWidget(export_btn)

        layout.addLayout(button_layout)

        # 初期プレビュー更新
        self._update_preview()

        # シグナル接続
        self.completed_only_checkbox.toggled.connect(self._update_preview)
        self.include_comment_checkbox.toggled.connect(self._update_preview)

    def _on_output_type_changed(self, checked: bool):
        """出力先タイプ変更時

        Args:
            checked: ファイル出力が選択されているか
        """
        self.file_name_edit.setEnabled(checked)

    def _on_browse(self):
        """参照ボタンクリック"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "プロンプトファイルを保存",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            self.output_path = Path(file_path)
            self.file_name_edit.setText(str(self.output_path))

    def _update_preview(self):
        """プレビュー更新"""
        completed_only = self.completed_only_checkbox.isChecked()

        # シーン数カウント
        if completed_only:
            scene_count = sum(1 for scene in self.project.scenes if scene.is_completed)
        else:
            scene_count = len(self.project.scenes)

        self.preview_label.setText(
            f"{scene_count}シーンを出力します"
        )

    def _on_export(self):
        """出力ボタンクリック"""
        # 出力先確認
        if self.file_radio.isChecked():
            # ファイル出力
            file_path = self.file_name_edit.text().strip()

            if not file_path:
                QMessageBox.warning(
                    self,
                    "エラー",
                    "ファイル名を指定してください"
                )
                return

            # 拡張子確認
            if not file_path.endswith('.txt'):
                file_path += '.txt'

            self.output_path = Path(file_path)

            # プロンプト構築
            try:
                self.prompt_builder.export_to_file(
                    self.project,
                    str(self.output_path),
                    include_comment=self.include_comment_checkbox.isChecked(),
                    completed_only=self.completed_only_checkbox.isChecked()
                )

                QMessageBox.information(
                    self,
                    "完了",
                    f"プロンプトファイルを出力しました:\n{self.output_path}"
                )

                self.accept()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "エラー",
                    f"ファイル出力に失敗しました:\n{e}"
                )

        else:
            # クリップボード出力
            from PyQt6.QtWidgets import QApplication

            lines = self.prompt_builder.build_all_prompts(
                self.project,
                include_comment=self.include_comment_checkbox.isChecked(),
                completed_only=self.completed_only_checkbox.isChecked()
            )

            text = "\n".join(lines)

            clipboard = QApplication.clipboard()
            clipboard.setText(text)

            QMessageBox.information(
                self,
                "完了",
                f"{len(lines)}行をクリップボードにコピーしました"
            )

            self.accept()
