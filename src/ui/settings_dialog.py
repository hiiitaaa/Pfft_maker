"""設定ダイアログ

APIキー管理、アプリケーション設定を行うダイアログ。
FR-017: セキュアなAPIキー管理
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QPushButton, QMessageBox,
    QGroupBox, QCheckBox, QListWidget, QListWidgetItem,
    QTextEdit, QComboBox
)
from PyQt6.QtCore import Qt
from pathlib import Path

from ai import APIKeyManager
from config.settings import Settings
from models.common_prompt import CommonPrompt


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

        # 共通プロンプトタブ
        common_prompt_tab = self._create_common_prompt_tab()
        tabs.addTab(common_prompt_tab, "共通プロンプト")

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

    def _create_common_prompt_tab(self) -> QWidget:
        """共通プロンプトタブを作成

        Returns:
            共通プロンプトタブウィジェット
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 説明
        description = QLabel(
            "新規シーンに自動挿入されるプロンプトを設定します。\n"
            "品質タグやLoRAなどをON/OFFで切り替えられます。"
        )
        description.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(description)

        # 共通プロンプトリスト
        self.common_prompts_list = QListWidget()
        self.common_prompts_list.setMaximumHeight(300)
        layout.addWidget(self.common_prompts_list)

        # ボタン
        button_layout = QHBoxLayout()

        add_button = QPushButton("＋ 追加")
        add_button.clicked.connect(self._on_add_common_prompt)
        button_layout.addWidget(add_button)

        edit_button = QPushButton("編集")
        edit_button.clicked.connect(self._on_edit_common_prompt)
        button_layout.addWidget(edit_button)

        delete_button = QPushButton("削除")
        delete_button.clicked.connect(self._on_delete_common_prompt)
        button_layout.addWidget(delete_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 共通プロンプトリストを更新
        self._refresh_common_prompts_list()

        layout.addStretch()

        return tab

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

        # OpenAI API設定
        openai_group = QGroupBox("OpenAI API (ChatGPT)")
        openai_layout = QVBoxLayout()

        # APIキー入力
        openai_key_layout = QHBoxLayout()
        openai_key_layout.addWidget(QLabel("APIキー:"))

        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_input.setPlaceholderText("sk-proj-...")
        openai_key_layout.addWidget(self.openai_key_input)

        show_openai_key_button = QPushButton("表示")
        show_openai_key_button.setCheckable(True)
        show_openai_key_button.toggled.connect(self._on_show_openai_key_toggled)
        openai_key_layout.addWidget(show_openai_key_button)

        openai_layout.addLayout(openai_key_layout)

        # APIキーの状態表示
        self.openai_key_status_label = QLabel()
        self.openai_key_status_label.setStyleSheet("color: gray;")
        openai_layout.addWidget(self.openai_key_status_label)

        # ボタン
        openai_button_layout = QHBoxLayout()

        openai_test_button = QPushButton("接続テスト")
        openai_test_button.clicked.connect(self._on_test_openai_connection)
        openai_button_layout.addWidget(openai_test_button)

        openai_save_button = QPushButton("APIキーを保存")
        openai_save_button.clicked.connect(self._on_save_openai_key)
        openai_button_layout.addWidget(openai_save_button)

        openai_delete_button = QPushButton("APIキーを削除")
        openai_delete_button.clicked.connect(self._on_delete_openai_key)
        openai_button_layout.addWidget(openai_delete_button)

        openai_button_layout.addStretch()

        openai_layout.addLayout(openai_button_layout)

        openai_group.setLayout(openai_layout)
        layout.addWidget(openai_group)

        # AI機能の有効/無効
        ai_features_group = QGroupBox("AI機能")
        ai_features_layout = QVBoxLayout()

        self.use_claude_checkbox = QCheckBox("Claude APIを使用")
        self.use_claude_checkbox.setChecked(True)
        ai_features_layout.addWidget(self.use_claude_checkbox)

        self.use_openai_checkbox = QCheckBox("OpenAI APIを使用")
        self.use_openai_checkbox.setChecked(False)
        ai_features_layout.addWidget(self.use_openai_checkbox)

        self.use_lm_studio_checkbox = QCheckBox("LM Studioを使用")
        self.use_lm_studio_checkbox.setChecked(False)
        ai_features_layout.addWidget(self.use_lm_studio_checkbox)

        ai_features_group.setLayout(ai_features_layout)
        layout.addWidget(ai_features_group)

        # LM Studio設定
        lm_studio_group = QGroupBox("LM Studio 設定")
        lm_studio_layout = QVBoxLayout()

        # エンドポイント
        endpoint_layout = QHBoxLayout()
        endpoint_layout.addWidget(QLabel("エンドポイント:"))
        self.lm_studio_endpoint_input = QLineEdit()
        self.lm_studio_endpoint_input.setPlaceholderText("http://localhost:1234/v1")
        endpoint_layout.addWidget(self.lm_studio_endpoint_input)
        lm_studio_layout.addLayout(endpoint_layout)

        # モデル名
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("モデル名:"))
        self.lm_studio_model_input = QLineEdit()
        self.lm_studio_model_input.setPlaceholderText("local-model")
        model_layout.addWidget(self.lm_studio_model_input)
        lm_studio_layout.addLayout(model_layout)

        # 同時実行数
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("並列実行数:"))
        self.lm_studio_concurrent_input = QLineEdit()
        self.lm_studio_concurrent_input.setPlaceholderText("2")
        concurrent_layout.addWidget(self.lm_studio_concurrent_input)
        concurrent_layout.addWidget(QLabel("(推奨: 2〜3)"))
        concurrent_layout.addStretch()
        lm_studio_layout.addLayout(concurrent_layout)

        # 接続テストボタン
        lm_test_button = QPushButton("LM Studio 接続テスト")
        lm_test_button.clicked.connect(self._on_test_lm_studio_connection)
        lm_studio_layout.addWidget(lm_test_button)

        # 説明
        lm_info = QLabel(
            "💡 ヒント:\n"
            "• LM Studioを起動してモデルをロードしてください\n"
            "• RTX 4070 Ti Super 16GBなら並列2〜3が最適\n"
            "• 完全オフラインで動作（APIキー不要）"
        )
        lm_info.setStyleSheet("color: gray; font-size: 10pt;")
        lm_studio_layout.addWidget(lm_info)

        lm_studio_group.setLayout(lm_studio_layout)
        layout.addWidget(lm_studio_group)

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
        # Claude APIキーの状態を確認
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

        # OpenAI APIキーの状態を確認
        if self.api_key_manager.has_api_key("openai"):
            self.openai_key_status_label.setText("✅ APIキーが設定されています")
            self.openai_key_status_label.setStyleSheet("color: green;")
            # APIキーをマスク表示
            openai_key = self.api_key_manager.get_api_key("openai")
            if openai_key:
                masked_key = openai_key[:10] + "..." + openai_key[-4:] if len(openai_key) > 14 else "●" * len(openai_key)
                self.openai_key_input.setText(masked_key)
                self.openai_key_input.setReadOnly(True)
        else:
            self.openai_key_status_label.setText("❌ APIキーが設定されていません")
            self.openai_key_status_label.setStyleSheet("color: red;")

        # LM Studio設定を読み込み
        self.lm_studio_endpoint_input.setText(self.settings.lm_studio_endpoint)
        self.lm_studio_model_input.setText(self.settings.lm_studio_model)
        self.lm_studio_concurrent_input.setText(str(self.settings.lm_studio_max_concurrent))

    def _on_show_key_toggled(self, checked: bool):
        """Claude APIキー表示/非表示切り替え

        Args:
            checked: 表示するか
        """
        if checked:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _on_show_openai_key_toggled(self, checked: bool):
        """OpenAI APIキー表示/非表示切り替え

        Args:
            checked: 表示するか
        """
        if checked:
            self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)

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
        # APIキーが存在しない場合
        if not self.api_key_manager.has_api_key("claude"):
            QMessageBox.warning(
                self,
                "エラー",
                "削除するAPIキーがありません"
            )
            return

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
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

            # 状態表示を更新
            self._load_settings()

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            QMessageBox.critical(
                self,
                "エラー",
                f"APIキーの削除に失敗しました:\n{e}\n\n詳細:\n{error_detail}"
            )

    def _on_test_openai_connection(self):
        """OpenAI API接続テスト"""
        if not self.api_key_manager.has_api_key("openai"):
            QMessageBox.warning(
                self,
                "接続テスト",
                "APIキーが設定されていません。\n先に「APIキーを保存」してください。"
            )
            return

        # 接続テスト実行
        QMessageBox.information(self, "接続テスト", "接続テストを開始します...")

        success, message = self.api_key_manager.test_connection("openai")

        if success:
            QMessageBox.information(
                self,
                "接続テスト成功",
                f"✅ {message}\n\nOpenAI APIに正常に接続できました。"
            )
        else:
            QMessageBox.critical(
                self,
                "接続テスト失敗",
                f"❌ {message}\n\nAPIキーを確認してください。"
            )

    def _on_save_openai_key(self):
        """OpenAI APIキーを保存"""
        api_key = self.openai_key_input.text().strip()

        if not api_key:
            QMessageBox.warning(
                self,
                "エラー",
                "APIキーを入力してください"
            )
            return

        # マスク表示の場合は既存のキーがあるので何もしない
        if self.openai_key_input.isReadOnly():
            QMessageBox.information(
                self,
                "情報",
                "既にAPIキーが設定されています。\n変更する場合は、先に削除してください。"
            )
            return

        # APIキー検証（形式チェック）
        if not (api_key.startswith("sk-proj-") or api_key.startswith("sk-")):
            reply = QMessageBox.question(
                self,
                "確認",
                "OpenAI APIキーは通常 'sk-proj-' または 'sk-' で始まりますが、\n入力されたキーは異なる形式です。\n\nこのまま保存しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # APIキーを保存
        try:
            self.api_key_manager.save_api_key("openai", api_key)

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

    def _on_delete_openai_key(self):
        """OpenAI APIキーを削除"""
        # APIキーが存在しない場合
        if not self.api_key_manager.has_api_key("openai"):
            QMessageBox.warning(
                self,
                "エラー",
                "削除するAPIキーがありません"
            )
            return

        reply = QMessageBox.question(
            self,
            "確認",
            "APIキーを削除しますか？\n\nこの操作は取り消せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.api_key_manager.delete_api_key("openai")

            QMessageBox.information(
                self,
                "成功",
                "✅ APIキーを削除しました"
            )

            # 入力をクリア
            self.openai_key_input.clear()
            self.openai_key_input.setReadOnly(False)
            self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)

            # 状態表示を更新
            self._load_settings()

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            QMessageBox.critical(
                self,
                "エラー",
                f"APIキーの削除に失敗しました:\n{e}\n\n詳細:\n{error_detail}"
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

    def _on_test_lm_studio_connection(self):
        """LM Studio接続テスト"""
        endpoint = self.lm_studio_endpoint_input.text().strip()
        model = self.lm_studio_model_input.text().strip()

        if not endpoint:
            QMessageBox.warning(
                self,
                "エラー",
                "エンドポイントを入力してください"
            )
            return

        if not model:
            QMessageBox.warning(
                self,
                "エラー",
                "モデル名を入力してください"
            )
            return

        # 接続テスト実行
        QMessageBox.information(self, "接続テスト", "LM Studioへの接続テストを開始します...")

        try:
            import openai

            client = openai.OpenAI(
                base_url=endpoint,
                api_key="lm-studio"  # ダミーキー
            )

            # シンプルなテストリクエスト
            response = client.chat.completions.create(
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )

            QMessageBox.information(
                self,
                "接続テスト成功",
                f"✅ LM Studioに正常に接続できました。\n\nモデル: {model}\nエンドポイント: {endpoint}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "接続テスト失敗",
                f"❌ LM Studioへの接続に失敗しました:\n\n{str(e)}\n\nLM Studioが起動しているか、モデルがロードされているか確認してください。"
            )

    def _on_apply(self):
        """設定を適用"""
        # パス設定を保存
        self.settings.source_wildcard_dir = self.source_dir_input.text()
        self.settings.local_wildcard_dir = self.local_dir_input.text()

        # LM Studio設定を保存
        self.settings.lm_studio_endpoint = self.lm_studio_endpoint_input.text().strip() or self.settings.DEFAULT_LM_STUDIO_ENDPOINT
        self.settings.lm_studio_model = self.lm_studio_model_input.text().strip() or self.settings.DEFAULT_LM_STUDIO_MODEL

        try:
            concurrent = int(self.lm_studio_concurrent_input.text().strip())
            if concurrent < 1 or concurrent > 10:
                raise ValueError("1〜10の範囲で入力してください")
            self.settings.lm_studio_max_concurrent = concurrent
        except ValueError as e:
            QMessageBox.warning(
                self,
                "エラー",
                f"並列実行数が不正です: {e}"
            )
            return

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

    def _refresh_common_prompts_list(self):
        """共通プロンプトリストを更新"""
        self.common_prompts_list.clear()

        for i, cp in enumerate(self.settings.common_prompts):
            item = QListWidgetItem()

            # チェックボックス付きアイテム
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(5, 2, 5, 2)

            checkbox = QCheckBox(f"{cp.name} [{cp.position}]")
            checkbox.setChecked(cp.enabled)
            checkbox.stateChanged.connect(
                lambda state, index=i: self._on_common_prompt_toggled(index, state)
            )
            checkbox_layout.addWidget(checkbox)

            # 内容のプレビュー
            preview = cp.content[:50] + "..." if len(cp.content) > 50 else cp.content
            preview_label = QLabel(preview)
            preview_label.setStyleSheet("color: gray; font-size: 10pt;")
            checkbox_layout.addWidget(preview_label)

            checkbox_layout.addStretch()

            self.common_prompts_list.addItem(item)
            self.common_prompts_list.setItemWidget(item, checkbox_widget)
            item.setSizeHint(checkbox_widget.sizeHint())

    def _on_common_prompt_toggled(self, index: int, state: int):
        """共通プロンプトのON/OFF切り替え

        Args:
            index: プロンプトのインデックス
            state: チェック状態
        """
        self.settings.common_prompts[index].enabled = (state == Qt.CheckState.Checked.value)

    def _on_add_common_prompt(self):
        """共通プロンプト追加"""
        dialog = CommonPromptEditDialog(None, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_prompt = dialog.get_common_prompt()
            self.settings.common_prompts.append(new_prompt)
            self._refresh_common_prompts_list()

    def _on_edit_common_prompt(self):
        """共通プロンプト編集"""
        current_row = self.common_prompts_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "エラー", "編集する項目を選択してください")
            return

        current_prompt = self.settings.common_prompts[current_row]
        dialog = CommonPromptEditDialog(current_prompt, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_prompt = dialog.get_common_prompt()
            self.settings.common_prompts[current_row] = updated_prompt
            self._refresh_common_prompts_list()

    def _on_delete_common_prompt(self):
        """共通プロンプト削除"""
        current_row = self.common_prompts_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "エラー", "削除する項目を選択してください")
            return

        reply = QMessageBox.question(
            self,
            "確認",
            f"'{self.settings.common_prompts[current_row].name}' を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.settings.common_prompts[current_row]
            self._refresh_common_prompts_list()


class CommonPromptEditDialog(QDialog):
    """共通プロンプト編集ダイアログ"""

    def __init__(self, common_prompt: CommonPrompt = None, parent=None):
        """初期化

        Args:
            common_prompt: 編集する共通プロンプト（Noneの場合は新規作成）
            parent: 親ウィジェット
        """
        super().__init__(parent)

        self.common_prompt = common_prompt
        self.is_new = (common_prompt is None)

        # ウィンドウ設定
        self.setWindowTitle("共通プロンプト編集" if not self.is_new else "共通プロンプト追加")
        self.resize(500, 400)

        # UI構築
        self._create_ui()

        # データロード
        if not self.is_new:
            self._load_data()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)

        # 名前
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名前:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例: 品質タグ")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # 内容
        layout.addWidget(QLabel("内容:"))
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("例: masterpiece, best quality, amazing quality")
        layout.addWidget(self.content_input)

        # 挿入位置
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("挿入位置:"))
        self.position_combo = QComboBox()
        self.position_combo.addItems(["先頭 (start)", "末尾 (end)"])
        position_layout.addWidget(self.position_combo)
        position_layout.addStretch()
        layout.addLayout(position_layout)

        # BREAK挿入
        self.break_checkbox = QCheckBox("後にBREAKを挿入")
        layout.addWidget(self.break_checkbox)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self._on_ok)
        button_layout.addWidget(ok_button)

        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def _load_data(self):
        """データをロード"""
        if self.common_prompt:
            self.name_input.setText(self.common_prompt.name)
            self.content_input.setPlainText(self.common_prompt.content)
            self.position_combo.setCurrentIndex(
                0 if self.common_prompt.position == "start" else 1
            )
            self.break_checkbox.setChecked(self.common_prompt.insert_break_after)

    def _on_ok(self):
        """OKボタン"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "エラー", "名前を入力してください")
            return

        content = self.content_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "エラー", "内容を入力してください")
            return

        self.accept()

    def get_common_prompt(self) -> CommonPrompt:
        """共通プロンプトを取得

        Returns:
            編集後の共通プロンプト
        """
        position = "start" if self.position_combo.currentIndex() == 0 else "end"

        return CommonPrompt(
            name=self.name_input.text().strip(),
            content=self.content_input.toPlainText().strip(),
            enabled=True if self.is_new else self.common_prompt.enabled,
            position=position,
            insert_break_after=self.break_checkbox.isChecked()
        )
