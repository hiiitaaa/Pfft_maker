"""設定ダイアログ

APIキー管理、アプリケーション設定を行うダイアログ。
FR-017: セキュアなAPIキー管理
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox,
    QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt
from pathlib import Path

from ai import APIKeyManager
from config.settings import Settings


class SettingsDialog(QDialog):
    """設定ダイアログ

    APIキー管理、パス設定、AI機能の有効/無効を設定。
    """

    def __init__(self, parent=None):
        """初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.settings = Settings()
        self.api_key_manager = APIKeyManager(self.settings.get_data_dir())

        # ウィンドウ設定
        self.setWindowTitle("設定")
        self.resize(600, 500)

        # UI構築
        self._create_ui()
        self._load_settings()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)

        # タブウィジェット
        tabs = QTabWidget()

        # AI設定タブ
        ai_tab = self._create_ai_tab()
        tabs.addTab(ai_tab, "AI設定")

        # パス設定タブ
        path_tab = self._create_path_tab()
        tabs.addTab(path_tab, "パス設定")

        layout.addWidget(tabs)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self._on_ok)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        apply_button = QPushButton("適用")
        apply_button.clicked.connect(self._on_apply)
        button_layout.addWidget(apply_button)

        layout.addLayout(button_layout)

    def _create_ai_tab(self) -> QWidget:
        """AI設定タブを作成

        Returns:
            AIタブウィジェット
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Claude API設定
        claude_group = QGroupBox("Claude API")
        claude_layout = QVBoxLayout()

        # APIキー入力
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("APIキー:"))

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-ant-...")
        key_layout.addWidget(self.api_key_input)

        show_key_button = QPushButton("表示")
        show_key_button.setCheckable(True)
        show_key_button.toggled.connect(self._on_show_key_toggled)
        key_layout.addWidget(show_key_button)

        claude_layout.addLayout(key_layout)

        # APIキーの状態表示
        self.api_key_status_label = QLabel()
        self.api_key_status_label.setStyleSheet("color: gray;")
        claude_layout.addWidget(self.api_key_status_label)

        # ボタン
        button_layout = QHBoxLayout()

        test_button = QPushButton("接続テスト")
        test_button.clicked.connect(self._on_test_connection)
        button_layout.addWidget(test_button)

        save_button = QPushButton("APIキーを保存")
        save_button.clicked.connect(self._on_save_api_key)
        button_layout.addWidget(save_button)

        delete_button = QPushButton("APIキーを削除")
        delete_button.clicked.connect(self._on_delete_api_key)
        button_layout.addWidget(delete_button)

        button_layout.addStretch()

        claude_layout.addLayout(button_layout)

        # セキュリティ情報
        security_info = QLabel(
            "🔒 セキュリティ:\n"
            "• 暗号化してファイルに保存\n"
            "• OSが安全に管理\n"
            "• 他ユーザーからアクセス不可"
        )
        security_info.setStyleSheet("color: gray; font-size: 10pt;")
        claude_layout.addWidget(security_info)

        claude_group.setLayout(claude_layout)
        layout.addWidget(claude_group)

        # AI機能の有効/無効
        ai_features_group = QGroupBox("AI機能")
        ai_features_layout = QVBoxLayout()

        self.use_claude_checkbox = QCheckBox("Claude APIを使用")
        self.use_claude_checkbox.setChecked(True)
        ai_features_layout.addWidget(self.use_claude_checkbox)

        self.use_lm_studio_checkbox = QCheckBox("LM Studioを使用（未実装）")
        self.use_lm_studio_checkbox.setEnabled(False)
        ai_features_layout.addWidget(self.use_lm_studio_checkbox)

        ai_features_group.setLayout(ai_features_layout)
        layout.addWidget(ai_features_group)

        layout.addStretch()

        return tab

    def _create_path_tab(self) -> QWidget:
        """パス設定タブを作成

        Returns:
            パスタブウィジェット
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # ワイルドカードディレクトリ設定
        wildcard_group = QGroupBox("ワイルドカードディレクトリ")
        wildcard_layout = QVBoxLayout()

        # 元ディレクトリ
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("元ディレクトリ:"))

        self.source_dir_input = QLineEdit()
        self.source_dir_input.setText(self.settings.source_wildcard_dir)
        source_layout.addWidget(self.source_dir_input)

        source_browse_button = QPushButton("参照...")
        source_browse_button.clicked.connect(lambda: self._browse_directory(self.source_dir_input))
        source_layout.addWidget(source_browse_button)

        wildcard_layout.addLayout(source_layout)

        # ローカルディレクトリ
        local_layout = QHBoxLayout()
        local_layout.addWidget(QLabel("ローカルディレクトリ:"))

        self.local_dir_input = QLineEdit()
        self.local_dir_input.setText(self.settings.local_wildcard_dir)
        local_layout.addWidget(self.local_dir_input)

        local_browse_button = QPushButton("参照...")
        local_browse_button.clicked.connect(lambda: self._browse_directory(self.local_dir_input))
        local_layout.addWidget(local_browse_button)

        wildcard_layout.addLayout(local_layout)

        wildcard_group.setLayout(wildcard_layout)
        layout.addWidget(wildcard_group)

        layout.addStretch()

        return tab

    def _load_settings(self):
        """設定を読み込み"""
        # APIキーの状態を確認
        if self.api_key_manager.has_api_key("claude"):
            self.api_key_status_label.setText("✅ APIキーが設定されています")
            self.api_key_status_label.setStyleSheet("color: green;")
            # APIキーをマスク表示
            api_key = self.api_key_manager.get_api_key("claude")
            if api_key:
                masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "●" * len(api_key)
                self.api_key_input.setText(masked_key)
                self.api_key_input.setReadOnly(True)
        else:
            self.api_key_status_label.setText("❌ APIキーが設定されていません")
            self.api_key_status_label.setStyleSheet("color: red;")

    def _on_show_key_toggled(self, checked: bool):
        """APIキー表示/非表示切り替え

        Args:
            checked: 表示するか
        """
        if checked:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _on_test_connection(self):
        """接続テスト"""
        if not self.api_key_manager.has_api_key("claude"):
            QMessageBox.warning(
                self,
                "接続テスト",
                "APIキーが設定されていません。\n先に「APIキーを保存」してください。"
            )
            return

        # 接続テスト実行
        QMessageBox.information(self, "接続テスト", "接続テストを開始します...")

        success, message = self.api_key_manager.test_connection("claude")

        if success:
            QMessageBox.information(
                self,
                "接続テスト成功",
                f"✅ {message}\n\nClaude APIに正常に接続できました。"
            )
        else:
            QMessageBox.critical(
                self,
                "接続テスト失敗",
                f"❌ {message}\n\nAPIキーを確認してください。"
            )

    def _on_save_api_key(self):
        """APIキーを保存"""
        api_key = self.api_key_input.text().strip()

        if not api_key:
            QMessageBox.warning(
                self,
                "エラー",
                "APIキーを入力してください"
            )
            return

        # マスク表示の場合は既存のキーがあるので何もしない
        if self.api_key_input.isReadOnly():
            QMessageBox.information(
                self,
                "情報",
                "既にAPIキーが設定されています。\n変更する場合は、先に削除してください。"
            )
            return

        # APIキー検証（形式チェック）
        if not api_key.startswith("sk-ant-"):
            reply = QMessageBox.question(
                self,
                "確認",
                "Claude APIキーは通常 'sk-ant-' で始まりますが、\n入力されたキーは異なる形式です。\n\nこのまま保存しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # APIキーを保存
        try:
            self.api_key_manager.save_api_key("claude", api_key)

            QMessageBox.information(
                self,
                "成功",
                "✅ APIキーを保存しました"
            )

            # 表示を更新
            self._load_settings()

        except Exception as e:
            QMessageBox.critical(
                self,
                "エラー",
                f"APIキーの保存に失敗しました:\n{e}"
            )

    def _on_delete_api_key(self):
        """APIキーを削除"""
        reply = QMessageBox.question(
            self,
            "確認",
            "APIキーを削除しますか？\n\nこの操作は取り消せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.api_key_manager.delete_api_key("claude")

            QMessageBox.information(
                self,
                "成功",
                "✅ APIキーを削除しました"
            )

            # 入力をクリア
            self.api_key_input.clear()
            self.api_key_input.setReadOnly(False)
            self._load_settings()

        except Exception as e:
            QMessageBox.critical(
                self,
                "エラー",
                f"APIキーの削除に失敗しました:\n{e}"
            )

    def _browse_directory(self, line_edit: QLineEdit):
        """ディレクトリ参照ダイアログ

        Args:
            line_edit: 選択したパスを設定するLineEdit
        """
        from PyQt6.QtWidgets import QFileDialog

        directory = QFileDialog.getExistingDirectory(
            self,
            "ディレクトリを選択",
            line_edit.text()
        )

        if directory:
            line_edit.setText(directory)

    def _on_apply(self):
        """設定を適用"""
        # パス設定を保存
        self.settings.source_wildcard_dir = self.source_dir_input.text()
        self.settings.local_wildcard_dir = self.local_dir_input.text()
        self.settings.save()

        QMessageBox.information(
            self,
            "成功",
            "設定を適用しました"
        )

    def _on_ok(self):
        """OKボタン"""
        self._on_apply()
        self.accept()
