"""ブロック編集ダイアログ

ブロックの内容を直接編集するUIを提供します。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt

from models import BlockType


class BlockEditDialog(QDialog):
    """ブロック編集ダイアログ

    ブロックの内容を編集・貼り付けできるダイアログ。
    """

    def __init__(self, block_type: BlockType = BlockType.FIXED_TEXT,
                 content: str = "", parent=None):
        """初期化

        Args:
            block_type: ブロックタイプ
            content: 初期内容
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.block_type = block_type
        self.content = content

        self._init_ui()

    def _init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("ブロック編集")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        # ブロックタイプ選択
        type_layout = QHBoxLayout()
        type_label = QLabel("ブロックタイプ:")
        self.type_combo = QComboBox()
        self.type_combo.addItem("固定テキスト", BlockType.FIXED_TEXT)
        self.type_combo.addItem("ワイルドカード", BlockType.WILDCARD)
        self.type_combo.addItem("BREAK", BlockType.BREAK)

        # 現在のタイプを選択
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.block_type:
                self.type_combo.setCurrentIndex(i)
                break

        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()

        layout.addLayout(type_layout)

        # 説明ラベル
        self.description_label = QLabel()
        self.description_label.setStyleSheet("color: gray; font-size: 10pt;")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        # コンテンツ編集エリア
        content_label = QLabel("内容:")
        layout.addWidget(content_label)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText(
            "プロンプトテキストを入力または貼り付けてください...\n\n"
            "例:\n"
            "1girl, solo, standing, looking at viewer\n"
            "または\n"
            "__character/girl__, __pose/standing__"
        )
        self.content_edit.setText(self.content)
        layout.addWidget(self.content_edit)

        # ヒント
        hint_label = QLabel(
            "💡 ヒント: Ctrl+V で既存のプロンプトを貼り付けられます"
        )
        hint_label.setStyleSheet("color: #1976D2; font-size: 9pt; padding: 5px;")
        layout.addWidget(hint_label)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("保存")
        save_button.setDefault(True)
        save_button.clicked.connect(self._on_save)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # 初期説明を設定
        self._update_description()

    def _on_type_changed(self, index: int):
        """タイプ変更時の処理"""
        self.block_type = self.type_combo.itemData(index)
        self._update_description()

        # BREAKの場合は内容をクリア
        if self.block_type == BlockType.BREAK:
            self.content_edit.setEnabled(False)
            self.content_edit.clear()
        else:
            self.content_edit.setEnabled(True)

    def _update_description(self):
        """説明を更新"""
        descriptions = {
            BlockType.FIXED_TEXT: "固定テキスト: そのまま出力されます。複数行可能。",
            BlockType.WILDCARD: "ワイルドカード: __path/to/file__ 形式で記述。ランダムに1つ選択されます。",
            BlockType.BREAK: "BREAK: Stable Diffusion WebUIの区切り記号。75トークンで分割されます。"
        }
        self.description_label.setText(descriptions.get(self.block_type, ""))

    def _on_save(self):
        """保存ボタンクリック時の処理"""
        content = self.content_edit.toPlainText().strip()

        # BREAKは内容不要
        if self.block_type == BlockType.BREAK:
            self.content = ""
            self.accept()
            return

        # 内容チェック
        if not content:
            QMessageBox.warning(
                self,
                "入力エラー",
                "内容を入力してください。"
            )
            self.content_edit.setFocus()
            return

        self.content = content
        self.accept()

    def get_block_info(self) -> tuple:
        """ブロック情報を取得

        Returns:
            (block_type, content)
        """
        return self.block_type, self.content
