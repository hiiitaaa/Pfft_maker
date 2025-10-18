"""一括編集ダイアログ

複数のシーンに対してプロンプトの置換・追加・削除を一括で行うダイアログ。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTextEdit, QCheckBox, QGroupBox,
    QRadioButton, QButtonGroup, QSpinBox, QDialogButtonBox,
    QMessageBox
)
from PyQt6.QtCore import Qt
from typing import List
from models import Scene


class BatchEditDialog(QDialog):
    """一括編集ダイアログ

    複数シーンに対してプロンプトの一括編集を行います。
    """

    def __init__(self, scenes: List[Scene], current_scene_index: int, parent=None):
        """初期化

        Args:
            scenes: 編集対象のシーンリスト
            current_scene_index: 現在選択中のシーンインデックス
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.scenes = scenes
        self.current_scene_index = current_scene_index

        self.setWindowTitle("一括編集")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._create_ui()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # タイトル
        title_label = QLabel("複数シーンのプロンプトを一括編集")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # 操作タイプ選択
        operation_group = QGroupBox("操作タイプ")
        operation_layout = QVBoxLayout()

        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "プロンプト置換",
            "プロンプト追加",
            "プロンプト削除"
        ])
        self.operation_combo.currentIndexChanged.connect(self._on_operation_changed)
        operation_layout.addWidget(self.operation_combo)

        operation_group.setLayout(operation_layout)
        layout.addWidget(operation_group)

        # 対象シーン選択
        target_group = QGroupBox("対象シーン")
        target_layout = QVBoxLayout()

        self.target_button_group = QButtonGroup()

        self.all_scenes_radio = QRadioButton(f"全シーン ({len(self.scenes)}シーン)")
        self.all_scenes_radio.setChecked(True)
        self.target_button_group.addButton(self.all_scenes_radio, 0)
        target_layout.addWidget(self.all_scenes_radio)

        self.current_scene_radio = QRadioButton(f"現在のシーン (シーン{self.current_scene_index + 1})")
        self.target_button_group.addButton(self.current_scene_radio, 1)
        target_layout.addWidget(self.current_scene_radio)

        # 範囲指定
        range_layout = QHBoxLayout()
        self.range_radio = QRadioButton("範囲指定:")
        self.target_button_group.addButton(self.range_radio, 2)
        range_layout.addWidget(self.range_radio)

        range_layout.addWidget(QLabel("シーン"))
        self.start_spin = QSpinBox()
        self.start_spin.setMinimum(1)
        self.start_spin.setMaximum(len(self.scenes))
        self.start_spin.setValue(1)
        range_layout.addWidget(self.start_spin)

        range_layout.addWidget(QLabel("～"))
        self.end_spin = QSpinBox()
        self.end_spin.setMinimum(1)
        self.end_spin.setMaximum(len(self.scenes))
        self.end_spin.setValue(len(self.scenes))
        range_layout.addWidget(self.end_spin)

        range_layout.addStretch()
        target_layout.addLayout(range_layout)

        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        # 置換設定（デフォルト表示）
        self.replace_group = QGroupBox("置換設定")
        replace_layout = QVBoxLayout()

        replace_layout.addWidget(QLabel("検索するプロンプト:"))
        self.search_text = QLineEdit()
        self.search_text.setPlaceholderText("例: __キャラ/SAYA__")
        replace_layout.addWidget(self.search_text)

        replace_layout.addWidget(QLabel("置換後のプロンプト:"))
        self.replace_text = QLineEdit()
        self.replace_text.setPlaceholderText("例: __キャラ/ARISA__")
        replace_layout.addWidget(self.replace_text)

        self.case_sensitive_check = QCheckBox("大文字小文字を区別する")
        replace_layout.addWidget(self.case_sensitive_check)

        self.replace_group.setLayout(replace_layout)
        layout.addWidget(self.replace_group)

        # 追加設定（初期非表示）
        self.add_group = QGroupBox("追加設定")
        add_layout = QVBoxLayout()

        add_layout.addWidget(QLabel("追加するプロンプト:"))
        self.add_text = QTextEdit()
        self.add_text.setPlaceholderText("追加するプロンプトを入力\n例: __キャラ/MIKU__, red dress")
        self.add_text.setMaximumHeight(100)
        add_layout.addWidget(self.add_text)

        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("追加位置:"))

        self.position_combo = QComboBox()
        self.position_combo.addItems(["最初", "最後"])
        position_layout.addWidget(self.position_combo)
        position_layout.addStretch()

        add_layout.addLayout(position_layout)

        self.add_group.setLayout(add_layout)
        self.add_group.setVisible(False)
        layout.addWidget(self.add_group)

        # 削除設定（初期非表示）
        self.delete_group = QGroupBox("削除設定")
        delete_layout = QVBoxLayout()

        delete_layout.addWidget(QLabel("削除するプロンプト:"))
        self.delete_text = QLineEdit()
        self.delete_text.setPlaceholderText("例: __キャラ/SAYA__")
        delete_layout.addWidget(self.delete_text)

        self.delete_case_sensitive_check = QCheckBox("大文字小文字を区別する")
        delete_layout.addWidget(self.delete_case_sensitive_check)

        self.delete_group.setLayout(delete_layout)
        self.delete_group.setVisible(False)
        layout.addWidget(self.delete_group)

        # プレビュー
        preview_label = QLabel("影響を受けるシーン数: 計算前")
        preview_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(preview_label)

        layout.addStretch()

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_operation_changed(self, index: int):
        """操作タイプ変更時

        Args:
            index: 選択されたインデックス
        """
        # 全て非表示にしてから選択されたものだけ表示
        self.replace_group.setVisible(index == 0)
        self.add_group.setVisible(index == 1)
        self.delete_group.setVisible(index == 2)

    def _get_target_scenes(self) -> List[Scene]:
        """対象シーンを取得

        Returns:
            対象シーンのリスト
        """
        target_id = self.target_button_group.checkedId()

        if target_id == 0:
            # 全シーン
            return self.scenes
        elif target_id == 1:
            # 現在のシーン
            return [self.scenes[self.current_scene_index]]
        else:
            # 範囲指定
            start = self.start_spin.value() - 1
            end = self.end_spin.value()
            return self.scenes[start:end]

    def _on_accept(self):
        """OKボタン押下時"""
        operation_type = self.operation_combo.currentIndex()

        # 入力チェック
        if operation_type == 0:  # 置換
            if not self.search_text.text().strip():
                QMessageBox.warning(
                    self,
                    "入力エラー",
                    "検索するプロンプトを入力してください。"
                )
                return
            if not self.replace_text.text().strip():
                QMessageBox.warning(
                    self,
                    "入力エラー",
                    "置換後のプロンプトを入力してください。"
                )
                return

        elif operation_type == 1:  # 追加
            if not self.add_text.toPlainText().strip():
                QMessageBox.warning(
                    self,
                    "入力エラー",
                    "追加するプロンプトを入力してください。"
                )
                return

        elif operation_type == 2:  # 削除
            if not self.delete_text.text().strip():
                QMessageBox.warning(
                    self,
                    "入力エラー",
                    "削除するプロンプトを入力してください。"
                )
                return

        # 対象シーン取得
        target_scenes = self._get_target_scenes()

        if not target_scenes:
            QMessageBox.warning(
                self,
                "エラー",
                "対象シーンがありません。"
            )
            return

        # 確認ダイアログ
        operation_name = self.operation_combo.currentText()
        message = f"{operation_name}を実行します。\n\n対象シーン数: {len(target_scenes)}シーン\n\nよろしいですか？"

        reply = QMessageBox.question(
            self,
            "確認",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.accept()

    def get_edit_info(self):
        """編集情報を取得

        Returns:
            タプル: (操作タイプ, 対象シーン, パラメータ)
                操作タイプ: 0=置換, 1=追加, 2=削除
                対象シーン: Sceneオブジェクトのリスト
                パラメータ: 操作に応じた辞書
        """
        operation_type = self.operation_combo.currentIndex()
        target_scenes = self._get_target_scenes()

        if operation_type == 0:  # 置換
            params = {
                'search': self.search_text.text().strip(),
                'replace': self.replace_text.text().strip(),
                'case_sensitive': self.case_sensitive_check.isChecked()
            }
        elif operation_type == 1:  # 追加
            params = {
                'text': self.add_text.toPlainText().strip(),
                'position': 'start' if self.position_combo.currentIndex() == 0 else 'end'
            }
        else:  # 削除
            params = {
                'text': self.delete_text.text().strip(),
                'case_sensitive': self.delete_case_sensitive_check.isChecked()
            }

        return operation_type, target_scenes, params
