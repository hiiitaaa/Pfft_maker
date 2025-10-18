"""初回起動時のウェルカムダイアログ

ユーザーにワイルドカードフォルダの設定を促す
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt
from pathlib import Path

from config.settings import Settings


class WelcomeDialog(QDialog):
    """初回起動時のウェルカムダイアログ"""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.init_ui()

    def init_ui(self):
        """UI初期化"""
        self.setWindowTitle("Pfft_maker へようこそ")
        self.setModal(True)
        self.setMinimumWidth(600)

        layout = QVBoxLayout()

        # タイトル
        title = QLabel("Pfft_maker へようこそ！")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # 説明
        description = QLabel(
            "Pfft_maker は Stable Diffusion WebUI 用のプロンプト管理ツールです。\n\n"
            "初回セットアップとして、ワイルドカードフォルダの設定を行います。"
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addSpacing(20)

        # Stable Diffusion WebUI のワイルドカードフォルダ設定
        sd_group = QGroupBox("Stable Diffusion WebUI のワイルドカードフォルダ（任意）")
        sd_layout = QVBoxLayout()

        sd_info = QLabel(
            "既に Stable Diffusion WebUI を使用している場合、\n"
            "ワイルドカードフォルダを指定すると既存のファイルを読み込めます。\n"
            "（後から設定画面で変更できます）"
        )
        sd_info.setWordWrap(True)
        sd_layout.addWidget(sd_info)

        # パス入力
        path_layout = QHBoxLayout()
        self.sd_path_input = QLineEdit()
        self.sd_path_input.setPlaceholderText("例: C:\\stable-diffusion-webui\\extensions\\sd-dynamic-prompts\\wildcards")
        browse_btn = QPushButton("参照...")
        browse_btn.clicked.connect(self.browse_sd_folder)
        path_layout.addWidget(self.sd_path_input)
        path_layout.addWidget(browse_btn)
        sd_layout.addLayout(path_layout)

        # スキップチェックボックス
        self.skip_checkbox = QCheckBox("今はスキップする（後で設定）")
        self.skip_checkbox.setChecked(True)
        sd_layout.addWidget(self.skip_checkbox)

        sd_group.setLayout(sd_layout)
        layout.addWidget(sd_group)

        layout.addSpacing(10)

        # LoRAフォルダ設定
        lora_group = QGroupBox("LoRAフォルダ（任意）")
        lora_layout = QVBoxLayout()

        lora_info = QLabel(
            "LoRAファイルが保存されているフォルダを指定すると、\n"
            "LoRAをプロンプトライブラリから選択できます。\n"
            "（後から設定画面で変更できます）"
        )
        lora_info.setWordWrap(True)
        lora_layout.addWidget(lora_info)

        # パス入力
        lora_path_layout = QHBoxLayout()
        self.lora_path_input = QLineEdit()
        self.lora_path_input.setPlaceholderText("例: C:\\stable-diffusion-webui\\models\\Lora")
        lora_browse_btn = QPushButton("参照...")
        lora_browse_btn.clicked.connect(self.browse_lora_folder)
        lora_path_layout.addWidget(self.lora_path_input)
        lora_path_layout.addWidget(lora_browse_btn)
        lora_layout.addLayout(lora_path_layout)

        # スキップチェックボックス
        self.skip_lora_checkbox = QCheckBox("今はスキップする（後で設定）")
        self.skip_lora_checkbox.setChecked(True)
        lora_layout.addWidget(self.skip_lora_checkbox)

        lora_group.setLayout(lora_layout)
        layout.addWidget(lora_group)

        layout.addSpacing(20)

        # データ保存場所の説明
        data_group = QGroupBox("データ保存場所")
        data_layout = QVBoxLayout()

        user_data_root = Settings.get_user_data_root()
        data_info = QLabel(
            f"プロジェクトやシーンなどのユーザーデータは、\n"
            f"以下のフォルダに保存されます：\n\n"
            f"{user_data_root}\n\n"
            f"このフォルダは定期的にバックアップすることをお勧めします。"
        )
        data_info.setWordWrap(True)
        data_layout.addWidget(data_info)

        data_group.setLayout(data_layout)
        layout.addWidget(data_group)

        layout.addStretch()

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("開始")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept_settings)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def browse_sd_folder(self):
        """Stable Diffusion WebUI のワイルドカードフォルダを参照"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Stable Diffusion WebUI のワイルドカードフォルダを選択",
            str(Path.home())
        )
        if folder:
            self.sd_path_input.setText(folder)
            self.skip_checkbox.setChecked(False)

    def browse_lora_folder(self):
        """LoRAフォルダを参照"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "LoRAフォルダを選択",
            str(Path.home())
        )
        if folder:
            self.lora_path_input.setText(folder)
            self.skip_lora_checkbox.setChecked(False)

    def accept_settings(self):
        """設定を保存して閉じる"""
        # Stable Diffusion WebUI のワイルドカードフォルダ
        if not self.skip_checkbox.isChecked() and self.sd_path_input.text():
            sd_path = Path(self.sd_path_input.text())
            if sd_path.exists():
                self.settings.source_wildcard_dir = str(sd_path)
            else:
                # パスが存在しない場合は警告（でも続行）
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "警告",
                    f"指定されたフォルダが見つかりません：\n{sd_path}\n\n"
                    "後で設定画面から変更できます。"
                )

        # LoRAフォルダ
        if not self.skip_lora_checkbox.isChecked() and self.lora_path_input.text():
            lora_path = Path(self.lora_path_input.text())
            if lora_path.exists():
                self.settings.lora_directory = str(lora_path)
            else:
                # パスが存在しない場合は警告（でも続行）
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "警告",
                    f"指定されたフォルダが見つかりません：\n{lora_path}\n\n"
                    "後で設定画面から変更できます。"
                )

        # 設定を保存
        self.settings.save()

        self.accept()
