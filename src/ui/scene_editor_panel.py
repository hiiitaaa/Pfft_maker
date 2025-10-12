"""シーンエディタパネル

シーンの編集（ブロック追加・削除・移動）を行うパネル。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..models import Project, Scene, Block, BlockType, Prompt


class SceneEditorPanel(QWidget):
    """シーンエディタパネル

    シーンごとのブロック編集機能を提供。

    Signals:
        scene_changed: シーンが変更された時（Sceneオブジェクト）
    """

    # シグナル定義
    scene_changed = pyqtSignal(object)  # Scene

    def __init__(self):
        """初期化"""
        super().__init__()

        self.project: Project | None = None
        self.current_scene: Scene | None = None

        # UI構築
        self._create_ui()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # タイトル
        title_label = QLabel("シーン編集")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # シーンタブ
        self.scene_tabs = QTabWidget()
        self.scene_tabs.currentChanged.connect(self._on_scene_changed)
        layout.addWidget(self.scene_tabs)

        # シーン情報
        info_layout = QHBoxLayout()

        self.scene_name_edit = QLineEdit()
        self.scene_name_edit.setPlaceholderText("シーン名")
        self.scene_name_edit.textChanged.connect(self._on_scene_name_changed)
        info_layout.addWidget(QLabel("シーン名:"))
        info_layout.addWidget(self.scene_name_edit)

        self.completed_checkbox = QCheckBox("完成")
        self.completed_checkbox.stateChanged.connect(self._on_completed_changed)
        info_layout.addWidget(self.completed_checkbox)

        layout.addLayout(info_layout)

        # ブロックリスト
        self.block_list = QListWidget()
        self.block_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(QLabel("ブロック:"))
        layout.addWidget(self.block_list)

        # ボタン
        button_layout = QHBoxLayout()

        add_break_btn = QPushButton("+ BREAK")
        add_break_btn.clicked.connect(self._on_add_break)
        button_layout.addWidget(add_break_btn)

        move_up_btn = QPushButton("↑ 上へ")
        move_up_btn.clicked.connect(self._on_move_up)
        button_layout.addWidget(move_up_btn)

        move_down_btn = QPushButton("↓ 下へ")
        move_down_btn.clicked.connect(self._on_move_down)
        button_layout.addWidget(move_down_btn)

        delete_btn = QPushButton("削除")
        delete_btn.clicked.connect(self._on_delete_block)
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        # シーン管理ボタン
        scene_button_layout = QHBoxLayout()

        add_scene_btn = QPushButton("+ シーン追加")
        add_scene_btn.clicked.connect(self._on_add_scene)
        scene_button_layout.addWidget(add_scene_btn)

        delete_scene_btn = QPushButton("シーン削除")
        delete_scene_btn.clicked.connect(self._on_delete_scene)
        scene_button_layout.addWidget(delete_scene_btn)

        layout.addLayout(scene_button_layout)

    def set_project(self, project: Project):
        """プロジェクトを設定

        Args:
            project: プロジェクトオブジェクト
        """
        self.project = project

        # タブをクリア
        self.scene_tabs.clear()

        # シーンがない場合、デフォルトシーンを作成
        if not project.scenes:
            scene = Scene(
                scene_id=1,
                scene_name="シーン1",
                is_completed=False
            )
            project.add_scene(scene)

        # シーンタブを作成
        for scene in project.scenes:
            self.scene_tabs.addTab(QWidget(), f"シーン{scene.scene_id}")

        # 最初のシーンを選択
        self.scene_tabs.setCurrentIndex(0)
        self._load_scene(0)

    def _load_scene(self, index: int):
        """シーンを読み込み

        Args:
            index: シーンインデックス
        """
        if not self.project or index < 0 or index >= len(self.project.scenes):
            return

        self.current_scene = self.project.scenes[index]

        # シーン情報を表示
        self.scene_name_edit.setText(self.current_scene.scene_name)
        self.completed_checkbox.setChecked(self.current_scene.is_completed)

        # ブロックリストを更新
        self._update_block_list()

        # プレビュー更新
        self.scene_changed.emit(self.current_scene)

    def _update_block_list(self):
        """ブロックリスト更新"""
        self.block_list.clear()

        if not self.current_scene:
            return

        for block in self.current_scene.blocks:
            if block.type == BlockType.BREAK:
                item_text = "--- BREAK ---"
            elif block.type == BlockType.WILDCARD:
                item_text = f"🎲 {block.content}"
            else:
                item_text = f"📌 {block.content[:50]}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, block.block_id)
            self.block_list.addItem(item)

    def insert_prompt_block(self, prompt: Prompt):
        """プロンプトブロックを挿入

        Args:
            prompt: プロンプトオブジェクト
        """
        if not self.current_scene:
            return

        # ワイルドカードパス生成（簡易版）
        wildcard_path = f"__{prompt.source_file.replace('.txt', '')}__"

        # ブロック作成
        block = Block(
            block_id=self.current_scene.get_next_block_id(),
            type=BlockType.WILDCARD,
            content=wildcard_path,
            source={"prompt_id": prompt.id}
        )

        self.current_scene.add_block(block)
        self._update_block_list()
        self.scene_changed.emit(self.current_scene)

    def _on_scene_changed(self, index: int):
        """シーンタブ変更時

        Args:
            index: 新しいシーンインデックス
        """
        self._load_scene(index)

    def _on_scene_name_changed(self, text: str):
        """シーン名変更時

        Args:
            text: 新しいシーン名
        """
        if self.current_scene:
            self.current_scene.scene_name = text
            # タブ名も更新
            current_index = self.scene_tabs.currentIndex()
            self.scene_tabs.setTabText(current_index, f"シーン{self.current_scene.scene_id}")

    def _on_completed_changed(self, state: int):
        """完成チェックボックス変更時

        Args:
            state: チェック状態
        """
        if self.current_scene:
            self.current_scene.is_completed = (state == Qt.CheckState.Checked.value)

    def _on_add_break(self):
        """BREAK追加"""
        if not self.current_scene:
            return

        block = Block(
            block_id=self.current_scene.get_next_block_id(),
            type=BlockType.BREAK,
            content=""
        )

        self.current_scene.add_block(block)
        self._update_block_list()
        self.scene_changed.emit(self.current_scene)

    def _on_move_up(self):
        """ブロックを上へ移動"""
        current_item = self.block_list.currentItem()
        if not current_item or not self.current_scene:
            return

        block_id = current_item.data(Qt.ItemDataRole.UserRole)
        self.current_scene.move_block(block_id, -1)
        self._update_block_list()
        self.scene_changed.emit(self.current_scene)

    def _on_move_down(self):
        """ブロックを下へ移動"""
        current_item = self.block_list.currentItem()
        if not current_item or not self.current_scene:
            return

        block_id = current_item.data(Qt.ItemDataRole.UserRole)
        self.current_scene.move_block(block_id, 1)
        self._update_block_list()
        self.scene_changed.emit(self.current_scene)

    def _on_delete_block(self):
        """ブロック削除"""
        current_item = self.block_list.currentItem()
        if not current_item or not self.current_scene:
            return

        block_id = current_item.data(Qt.ItemDataRole.UserRole)
        self.current_scene.remove_block(block_id)
        self._update_block_list()
        self.scene_changed.emit(self.current_scene)

    def _on_add_scene(self):
        """シーン追加"""
        if not self.project:
            return

        scene = Scene(
            scene_id=self.project.get_next_scene_id(),
            scene_name=f"シーン{self.project.get_next_scene_id()}",
            is_completed=False
        )

        self.project.add_scene(scene)

        # タブ追加
        self.scene_tabs.addTab(QWidget(), f"シーン{scene.scene_id}")
        self.scene_tabs.setCurrentIndex(len(self.project.scenes) - 1)

    def _on_delete_scene(self):
        """シーン削除"""
        if not self.project or not self.current_scene:
            return

        # 最後のシーンは削除不可
        if len(self.project.scenes) <= 1:
            return

        scene_id = self.current_scene.scene_id
        current_index = self.scene_tabs.currentIndex()

        # シーン削除
        self.project.remove_scene(scene_id)

        # タブ削除
        self.scene_tabs.removeTab(current_index)

        # 前のシーンを選択
        if current_index > 0:
            self.scene_tabs.setCurrentIndex(current_index - 1)

    def next_scene(self):
        """次のシーンへ"""
        current = self.scene_tabs.currentIndex()
        if current < self.scene_tabs.count() - 1:
            self.scene_tabs.setCurrentIndex(current + 1)

    def previous_scene(self):
        """前のシーンへ"""
        current = self.scene_tabs.currentIndex()
        if current > 0:
            self.scene_tabs.setCurrentIndex(current - 1)
