"""テンプレート保存ダイアログ

プロジェクトをテンプレートとして保存するUIを提供します。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QRadioButton, QPushButton,
    QGroupBox, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt

from utils.logger import get_logger


class TemplateSaveDialog(QDialog):
    """テンプレート保存ダイアログ

    プロジェクトをテンプレートとして保存する際の設定を行います。
    """

    def __init__(self, parent=None):
        """初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.logger = get_logger()

        # 戻り値用の変数
        self.template_name = ""
        self.template_description = ""
        self.template_type = "structure"  # "structure" or "complete"

        self._init_ui()

    def _init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("テンプレート保存")
        self.setMinimumWidth(450)

        layout = QVBoxLayout()

        # テンプレート名
        name_label = QLabel("テンプレート名:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例: 学園メイド基本構成")
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        layout.addSpacing(10)

        # テンプレートタイプ選択
        type_group = QGroupBox("テンプレートタイプ:")
        type_layout = QVBoxLayout()

        self.structure_radio = QRadioButton("構成テンプレート")
        self.structure_radio.setChecked(True)
        structure_desc = QLabel("（プロンプト内容は保存しない）")
        structure_desc.setStyleSheet("color: gray; font-size: 10pt; margin-left: 20px;")

        self.complete_radio = QRadioButton("完全テンプレート")
        complete_desc = QLabel("（プロンプト内容も含めて保存）")
        complete_desc.setStyleSheet("color: gray; font-size: 10pt; margin-left: 20px;")

        # ラジオボタングループ
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.structure_radio, 0)
        self.button_group.addButton(self.complete_radio, 1)

        type_layout.addWidget(self.structure_radio)
        type_layout.addWidget(structure_desc)
        type_layout.addSpacing(5)
        type_layout.addWidget(self.complete_radio)
        type_layout.addWidget(complete_desc)

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        layout.addSpacing(10)

        # 説明（オプション）
        desc_label = QLabel("説明（オプション）:")
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("例: 30シーン構成、品質タグ統一")
        self.desc_input.setMaximumHeight(80)
        layout.addWidget(desc_label)
        layout.addWidget(self.desc_input)

        layout.addSpacing(20)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("保存")
        save_button.setDefault(True)
        save_button.clicked.connect(self._on_save)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _on_save(self):
        """保存ボタン押下時の処理"""
        # 入力チェック
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                "入力エラー",
                "テンプレート名を入力してください。"
            )
            self.name_input.setFocus()
            return

        # 値を設定
        self.template_name = name
        self.template_description = self.desc_input.toPlainText().strip()

        if self.structure_radio.isChecked():
            self.template_type = "structure"
        else:
            self.template_type = "complete"

        self.logger.info(
            f"テンプレート保存設定: {self.template_name} ({self.template_type})"
        )

        self.accept()

    def get_template_info(self) -> tuple[str, str, str]:
        """テンプレート情報を取得

        Returns:
            (テンプレート名, 説明, タイプ)
        """
        return self.template_name, self.template_description, self.template_type
