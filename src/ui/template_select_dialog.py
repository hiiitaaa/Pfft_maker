"""テンプレート選択ダイアログ

テンプレートから新規プロジェクトを作成するUIを提供します。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

from models import ProjectTemplate
from utils.logger import get_logger


class TemplateListItem(QWidget):
    """テンプレートリストアイテム

    テンプレート情報を見やすく表示するカスタムウィジェット。
    """

    def __init__(self, template: ProjectTemplate, parent=None):
        """初期化

        Args:
            template: テンプレートオブジェクト
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.template = template
        self._init_ui()

    def _init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # テンプレート名
        name_label = QLabel(f"✨ {self.template.name}")
        name_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(name_label)

        # タイプ
        type_text = "構成テンプレート" if self.template.template_type == "structure" else "完全テンプレート"
        type_label = QLabel(f"   （{type_text}）")
        type_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(type_label)

        # シーン数と使用回数
        info_text = f"   {self.template.scene_count}シーン"
        if self.template.usage_count > 0:
            info_text += f"、{self.template.usage_count}回使用"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(info_label)

        # 説明
        if self.template.description:
            desc_label = QLabel(f"   {self.template.description}")
            desc_label.setStyleSheet("color: #555; font-size: 9pt;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        self.setLayout(layout)


class TemplateSelectDialog(QDialog):
    """テンプレート選択ダイアログ

    利用可能なテンプレートから選択し、新規プロジェクトを作成します。
    """

    template_deleted = pyqtSignal(str)  # テンプレート削除時のシグナル

    def __init__(self, templates: list[ProjectTemplate], parent=None):
        """初期化

        Args:
            templates: テンプレートのリスト
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.logger = get_logger()
        self.templates = templates
        self.selected_template: ProjectTemplate | None = None
        self.project_name = ""

        self._init_ui()
        self._load_templates()

    def _init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("テンプレートから作成")
        self.setMinimumSize(500, 450)

        layout = QVBoxLayout()

        # タイトル
        title_label = QLabel("利用可能なテンプレート:")
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)

        # テンプレートリスト
        self.template_list = QListWidget()
        self.template_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.template_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.template_list)

        layout.addSpacing(10)

        # プロジェクト名入力
        name_label = QLabel("プロジェクト名:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例: 新規プロジェクト")
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        layout.addSpacing(10)

        # 下部ボタン
        button_layout = QHBoxLayout()

        self.edit_button = QPushButton("編集")
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self._on_edit)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("削除")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._on_delete)
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch()

        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        self.create_button = QPushButton("作成")
        self.create_button.setDefault(True)
        self.create_button.setEnabled(False)
        self.create_button.clicked.connect(self._on_create)
        button_layout.addWidget(self.create_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_templates(self):
        """テンプレートリストを読み込み"""
        self.template_list.clear()

        if not self.templates:
            # テンプレートがない場合
            item = QListWidgetItem("テンプレートがありません")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.template_list.addItem(item)
            return

        # テンプレートを表示
        for template in self.templates:
            item = QListWidgetItem(self.template_list)
            widget = TemplateListItem(template)
            item.setSizeHint(widget.sizeHint())
            self.template_list.addItem(item)
            self.template_list.setItemWidget(item, widget)

    def _on_selection_changed(self):
        """選択変更時の処理"""
        items = self.template_list.selectedItems()
        has_selection = len(items) > 0

        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.create_button.setEnabled(has_selection)

        if has_selection:
            # 選択されたテンプレートを取得
            index = self.template_list.row(items[0])
            self.selected_template = self.templates[index]

            # デフォルトのプロジェクト名を設定
            if not self.name_input.text():
                self.name_input.setText(f"{self.selected_template.name}_プロジェクト")

    def _on_edit(self):
        """編集ボタン押下時の処理"""
        # Phase 2で実装予定
        QMessageBox.information(
            self,
            "未実装",
            "テンプレート編集機能は今後実装予定です。"
        )

    def _on_delete(self):
        """削除ボタン押下時の処理"""
        if not self.selected_template:
            return

        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "テンプレート削除",
            f"テンプレート「{self.selected_template.name}」を削除しますか？\n\n"
            "この操作は取り消せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 削除シグナルを発行
            self.template_deleted.emit(self.selected_template.id)

            # リストから削除
            self.templates = [t for t in self.templates if t.id != self.selected_template.id]
            self._load_templates()

            self.logger.info(f"テンプレート削除: {self.selected_template.name}")
            self.selected_template = None

    def _on_create(self):
        """作成ボタン押下時の処理"""
        # 入力チェック
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                "入力エラー",
                "プロジェクト名を入力してください。"
            )
            self.name_input.setFocus()
            return

        if not self.selected_template:
            QMessageBox.warning(
                self,
                "選択エラー",
                "テンプレートを選択してください。"
            )
            return

        self.project_name = name
        self.logger.info(
            f"テンプレート選択: {self.selected_template.name} -> {self.project_name}"
        )
        self.accept()

    def get_selected_template(self) -> ProjectTemplate | None:
        """選択されたテンプレートを取得

        Returns:
            選択されたテンプレート、未選択の場合None
        """
        return self.selected_template

    def get_project_name(self) -> str:
        """プロジェクト名を取得

        Returns:
            入力されたプロジェクト名
        """
        return self.project_name
