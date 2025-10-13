"""更新通知バナー

ワイルドカードファイルの更新を通知するバナーUI。
"""

from typing import Optional, Dict, List
from pathlib import Path
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPalette, QColor


class UpdateNotificationBanner(QFrame):
    """更新通知バナー

    ワイルドカードファイルの更新を検出したときに表示される通知バナー。

    Signals:
        sync_requested: 同期ボタンがクリックされた
        dismissed: バナーが閉じられた
    """

    # シグナル定義
    sync_requested = pyqtSignal()
    dismissed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        """初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self._updates = None
        self._setup_ui()
        self._apply_style()

        # デフォルトで非表示
        self.hide()

    def _setup_ui(self):
        """UI構築"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # アイコン（📢）
        icon_label = QLabel("📢")
        icon_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(icon_label)

        # メッセージエリア
        message_layout = QVBoxLayout()
        message_layout.setSpacing(4)

        self.title_label = QLabel("ライブラリに更新があります")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        message_layout.addWidget(self.title_label)

        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("font-size: 11px; color: #555;")
        message_layout.addWidget(self.detail_label)

        layout.addLayout(message_layout)

        # スペーサー
        layout.addStretch()

        # ボタンエリア
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        # 今すぐ同期ボタン
        self.sync_button = QPushButton("今すぐ同期")
        self.sync_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 16px;
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
        self.sync_button.clicked.connect(self._on_sync_clicked)
        button_layout.addWidget(self.sync_button)

        # 後でボタン
        self.later_button = QPushButton("後で")
        self.later_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #555;
                border: 1px solid #999;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        self.later_button.clicked.connect(self._on_later_clicked)
        button_layout.addWidget(self.later_button)

        # 閉じるボタン（×）
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #000;
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 12px;
            }
        """)
        self.close_button.clicked.connect(self._on_close_clicked)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        # フレームプロパティ
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)

    def _apply_style(self):
        """スタイル適用"""
        self.setStyleSheet("""
            UpdateNotificationBanner {
                background-color: #FFF9C4;
                border: 1px solid #FBC02D;
                border-radius: 6px;
            }
        """)

    def show_update(self, updates: Dict[str, List[Path]]):
        """更新情報を表示

        Args:
            updates: 更新情報辞書
                - "added": 追加ファイルリスト
                - "modified": 変更ファイルリスト
                - "deleted": 削除ファイルリスト
        """
        self._updates = updates

        # 詳細メッセージ作成
        details = []

        added_count = len(updates.get("added", []))
        if added_count > 0:
            details.append(f"追加: {added_count}ファイル")

        modified_count = len(updates.get("modified", []))
        if modified_count > 0:
            details.append(f"更新: {modified_count}ファイル")

        deleted_count = len(updates.get("deleted", []))
        if deleted_count > 0:
            details.append(f"削除: {deleted_count}ファイル")

        detail_text = "、".join(details)
        self.detail_label.setText(detail_text)

        # バナー表示
        self.show()

    def _on_sync_clicked(self):
        """同期ボタンクリック"""
        self.sync_requested.emit()
        self.hide()

    def _on_later_clicked(self):
        """後でボタンクリック"""
        self.dismissed.emit()
        self.hide()

    def _on_close_clicked(self):
        """閉じるボタンクリック"""
        self.dismissed.emit()
        self.hide()
