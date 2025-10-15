"""シーンエディタパネル

シーンの編集（ブロック追加・削除・移動）を行うパネル。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QLineEdit, QCheckBox, QMessageBox, QDialog, QDialogButtonBox,
    QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path

from models import Project, Scene, Block, BlockType, Prompt
from config.settings import Settings
from core.custom_prompt_manager import CustomPromptManager
from core.scene_library_manager import SceneLibraryManager


class SceneEditorPanel(QWidget):
    """シーンエディタパネル

    シーンごとのブロック編集機能を提供。

    Signals:
        scene_changed: シーンが変更された時（Sceneオブジェクト）
    """

    # シグナル定義
    scene_changed = pyqtSignal(object)  # Scene
    scene_library_updated = pyqtSignal()  # シーンライブラリが更新された
    save_project_requested = pyqtSignal()  # 作品保存が要求された

    def __init__(self):
        """初期化"""
        super().__init__()

        self.project: Project | None = None
        self.current_scene: Scene | None = None

        # 自作プロンプト管理
        settings = Settings()
        self.custom_prompt_manager = CustomPromptManager(settings.get_data_dir())

        # シーンライブラリ管理
        self.scene_library_manager = SceneLibraryManager(settings.get_data_dir())

        # UI構築
        self._create_ui()

    def _create_ui(self):
        """UI構築（新設計：テキストエディタ中心）"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # タイトルとシーン操作ボタンを横並びに
        title_layout = QHBoxLayout()

        title_label = QLabel("シーン編集")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # シーン操作ボタン群
        add_scene_btn = QPushButton("+ シーン追加")
        add_scene_btn.clicked.connect(self._on_add_scene)
        title_layout.addWidget(add_scene_btn)

        duplicate_scene_btn = QPushButton("📋 複製")
        duplicate_scene_btn.clicked.connect(self._on_duplicate_scene)
        duplicate_scene_btn.setToolTip("現在のシーンを複製")
        title_layout.addWidget(duplicate_scene_btn)

        delete_scene_btn = QPushButton("削除")
        delete_scene_btn.clicked.connect(self._on_delete_scene)
        title_layout.addWidget(delete_scene_btn)

        self.insert_scene_btn = QPushButton("シーン読み込み")
        self.insert_scene_btn.clicked.connect(self._on_load_scene_from_library)
        self.insert_scene_btn.setToolTip("ライブラリから保存済みシーンをプロンプト編集エリアに読み込み")
        title_layout.addWidget(self.insert_scene_btn)

        layout.addLayout(title_layout)

        # 作品名入力
        project_name_layout = QHBoxLayout()
        project_name_layout.addWidget(QLabel("作品名:"))

        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("作品の名前を入力")
        self.project_name_edit.textChanged.connect(self._on_project_name_changed)
        project_name_layout.addWidget(self.project_name_edit)

        # 💾 作品を保存ボタン
        self.save_project_btn = QPushButton("💾 作品を保存")
        self.save_project_btn.clicked.connect(self._on_save_project_to_library)
        self.save_project_btn.setToolTip("作品全体を保存（全シーンまとめて保存・後で読み込み可能）")
        self.save_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        project_name_layout.addWidget(self.save_project_btn)

        layout.addLayout(project_name_layout)

        # シーンタブ
        self.scene_tabs = QTabWidget()
        self.scene_tabs.setMovable(True)  # ドラッグ&ドロップで順番変更可能
        self.scene_tabs.setTabsClosable(False)  # 閉じるボタンは非表示
        self.scene_tabs.currentChanged.connect(self._on_scene_changed)
        # タブの順序変更をプロジェクトに反映
        self.scene_tabs.tabBar().tabMoved.connect(self._on_tab_moved)
        layout.addWidget(self.scene_tabs)

        # シーン情報 + ライブラリ保存ボタン
        info_layout = QHBoxLayout()

        info_layout.addWidget(QLabel("シーン名:"))

        self.scene_name_edit = QLineEdit()
        self.scene_name_edit.setPlaceholderText("シーン名")
        self.scene_name_edit.textChanged.connect(self._on_scene_name_changed)
        info_layout.addWidget(self.scene_name_edit)

        info_layout.addStretch()

        # 📚 ライブラリ保存ボタン
        self.save_scene_btn = QPushButton("📚 シーンをテンプレート保存")
        self.save_scene_btn.clicked.connect(self._on_save_scene_to_library)
        self.save_scene_btn.setToolTip("このシーン単体をテンプレートとして保存（後で再利用可能）")
        self.save_scene_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
        """)
        info_layout.addWidget(self.save_scene_btn)

        layout.addLayout(info_layout)

        # 💾 シーンに保存ボタン（重要！）
        save_button_layout = QHBoxLayout()
        save_button_layout.addStretch()

        self.save_to_scene_btn = QPushButton("💾 シーンに保存")
        self.save_to_scene_btn.clicked.connect(self._on_save_editor_to_scene)
        self.save_to_scene_btn.setToolTip("エディタの内容をシーンに保存")
        self.save_to_scene_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        save_button_layout.addWidget(self.save_to_scene_btn)
        save_button_layout.addStretch()

        layout.addLayout(save_button_layout)

        # プロンプトエディタ（常に表示）
        editor_label = QLabel("プロンプト編集:")
        editor_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(editor_label)

        self.prompt_text_edit = QTextEdit()
        self.prompt_text_edit.setPlaceholderText(
            "プロンプトをここに入力・編集してください。\n"
            "ライブラリからクリックでカーソル位置に挿入できます。\n\n"
            "例:\n"
            "1girl, school uniform, kiss,\n"
            "BREAK,\n"
            "standing, corridor,\n"
            "BREAK,\n"
            "masterpiece, best quality\n\n"
            "編集後は上の「💾 シーンに保存」ボタンをクリックしてください。"
        )
        layout.addWidget(self.prompt_text_edit)

        # 🖼️ シーンを保存（プレビューへ表示）ボタン
        preview_button_layout = QHBoxLayout()
        preview_button_layout.addStretch()

        self.save_to_preview_btn = QPushButton("🖼️ シーンを保存（プレビューへ表示）")
        self.save_to_preview_btn.clicked.connect(self._on_save_to_preview)
        self.save_to_preview_btn.setToolTip("シーンをプレビューに表示します。全シーン保存後に出力・コピーできます。")
        self.save_to_preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
        """)
        preview_button_layout.addWidget(self.save_to_preview_btn)
        preview_button_layout.addStretch()

        layout.addLayout(preview_button_layout)

    def set_project(self, project: Project):
        """プロジェクトを設定

        Args:
            project: プロジェクトオブジェクト
        """
        self.project = project

        # 作品名を表示
        self.project_name_edit.setText(project.name if project.name else "")

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

        # シーンタブを作成（ユーザー入力のシーン名を表示）
        for scene in project.scenes:
            display_name = scene.scene_name if scene.scene_name else f"シーン{scene.scene_id}"

            # シーンタブのコンテンツ：保存済みプロンプト表示エリア
            scene_content = QTextEdit()
            scene_content.setReadOnly(True)
            scene_content.setPlaceholderText("（未保存）\n\n下部の「プロンプト編集」エリアで編集し、\n「💾 シーンに保存」をクリックしてください。")
            scene_content.setStyleSheet("background-color: #f5f5f5; color: #333;")

            # シーンに保存済みプロンプトがあれば表示
            if scene.blocks:
                from core.prompt_builder import PromptBuilder
                builder = PromptBuilder()
                saved_prompt = builder.build_scene_prompt(scene, apply_common_prompts=False)
                scene_content.setPlainText(saved_prompt)

            self.scene_tabs.addTab(scene_content, display_name)

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

        # シーンの内容をテキストエディタに表示
        self._sync_blocks_to_text()

        # 注: プレビューは「シーンを保存」ボタンで手動更新

    def _update_block_list(self):
        """ブロックリスト更新"""
        self.block_list.clear()

        if not self.current_scene:
            return

        for block in self.current_scene.blocks:
            if block.type == BlockType.BREAK:
                item_text = "[BREAK]"
            elif block.type == BlockType.WILDCARD:
                item_text = f"[W] {block.content}"
            else:
                item_text = f"[F] {block.content[:50]}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, block.block_id)
            self.block_list.addItem(item)

    def insert_prompt_as_fixed_text(self, prompt: Prompt):
        """プロンプトをカーソル位置に挿入（新設計）

        Args:
            prompt: プロンプトオブジェクト
        """
        if not self.current_scene:
            return

        # テキストエディタのカーソル位置にプロンプトを挿入
        cursor = self.prompt_text_edit.textCursor()
        cursor.insertText(prompt.prompt)

        # カーソル位置を更新して、続けて入力できるようにする
        self.prompt_text_edit.setTextCursor(cursor)
        self.prompt_text_edit.setFocus()

    def insert_wildcard_block(self, wildcard_path: str):
        """ワイルドカードをカーソル位置に挿入（新設計）

        Args:
            wildcard_path: ワイルドカードパス（例: __posing/arm__）
        """
        if not self.current_scene:
            return

        # テキストエディタのカーソル位置にワイルドカードを挿入
        cursor = self.prompt_text_edit.textCursor()
        cursor.insertText(wildcard_path)

        # カーソル位置を更新して、続けて入力できるようにする
        self.prompt_text_edit.setTextCursor(cursor)
        self.prompt_text_edit.setFocus()

    def _on_scene_changed(self, index: int):
        """シーンタブ変更時

        Args:
            index: 新しいシーンインデックス
        """
        self._load_scene(index)

    def _on_project_name_changed(self, text: str):
        """作品名変更時

        Args:
            text: 新しい作品名
        """
        if self.project:
            self.project.name = text

    def _on_scene_name_changed(self, text: str):
        """シーン名変更時

        Args:
            text: 新しいシーン名
        """
        if self.current_scene:
            self.current_scene.scene_name = text
            # タブ名も更新（ユーザー入力のシーン名を表示）
            current_index = self.scene_tabs.currentIndex()
            display_name = text if text.strip() else f"シーン{self.current_scene.scene_id}"
            self.scene_tabs.setTabText(current_index, display_name)

    def _on_save_editor_to_scene(self):
        """エディタの内容をシーンに保存（新設計の核心メソッド）"""
        from utils.logger import get_logger
        logger = get_logger()

        if not self.current_scene:
            QMessageBox.warning(
                self,
                "エラー",
                "シーンが選択されていません。"
            )
            return

        logger.info(f"[シーン保存開始] シーンID: {self.current_scene.scene_id}, 名前: {self.current_scene.scene_name}")
        logger.info(f"[シーン保存開始] 保存前のブロック数: {len(self.current_scene.blocks)}")

        # テキストエディタの内容を取得
        prompt_text = self.prompt_text_edit.toPlainText().strip()
        logger.info(f"[シーン保存] エディタのテキスト長: {len(prompt_text)}")

        if not prompt_text:
            # 空の場合は確認
            reply = QMessageBox.question(
                self,
                "確認",
                "エディタが空です。シーンのブロックを全て削除しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.current_scene.blocks.clear()
                logger.info("[シーン保存] ブロックを全削除")
                self.scene_changed.emit(self.current_scene)
                QMessageBox.information(self, "保存完了", "シーンを空にしました。")
            return

        # 既存のブロックをクリア
        old_block_count = len(self.current_scene.blocks)
        self.current_scene.blocks.clear()
        logger.info(f"[シーン保存] ブロッククリア完了（削除数: {old_block_count}）")

        # テキストをパースしてブロックに変換
        import re
        segments = re.split(r',\s*BREAK\s*,?|BREAK', prompt_text, flags=re.IGNORECASE)

        for i, segment in enumerate(segments):
            segment = segment.strip().strip(',').strip()

            if not segment:
                continue

            # ワイルドカード形式かチェック
            is_wildcard = segment.startswith('__') and segment.endswith('__')

            if is_wildcard:
                block = Block(
                    block_id=self.current_scene.get_next_block_id(),
                    type=BlockType.WILDCARD,
                    content=segment
                )
            else:
                block = Block(
                    block_id=self.current_scene.get_next_block_id(),
                    type=BlockType.FIXED_TEXT,
                    content=segment
                )

            self.current_scene.add_block(block)

            # 最後のセグメント以外はBREAKを追加
            if i < len(segments) - 1 and segment:
                break_block = Block(
                    block_id=self.current_scene.get_next_block_id(),
                    type=BlockType.BREAK,
                    content=""
                )
                self.current_scene.add_block(break_block)

        logger.info(f"[シーン保存] ブロック作成完了（作成数: {len(self.current_scene.blocks)}）")

        # エディタの内容を保存されたブロックから再生成（表示を更新）
        self._sync_blocks_to_text()
        logger.info("[シーン保存] エディタ再同期完了")

        # シーンタブのコンテンツを更新（保存済みプロンプトを表示）
        current_tab_index = self.scene_tabs.currentIndex()
        scene_content_widget = self.scene_tabs.widget(current_tab_index)
        if isinstance(scene_content_widget, QTextEdit):
            from core.prompt_builder import PromptBuilder
            builder = PromptBuilder()
            saved_prompt = builder.build_scene_prompt(self.current_scene, apply_common_prompts=False)
            scene_content_widget.setPlainText(saved_prompt)
            logger.info("[シーン保存] シーンタブのコンテンツ更新完了")

        # 注: プレビューは「シーンを保存」ボタンで手動更新

        # 成功メッセージ（小さなトースト風に）
        logger.info(f"[シーン保存完了] シーンID: {self.current_scene.scene_id}, ブロック数: {len(self.current_scene.blocks)}")

        # プロジェクトのシーンリストも確認
        if self.project:
            for i, scene in enumerate(self.project.scenes):
                if scene.scene_id == self.current_scene.scene_id:
                    logger.info(f"[シーン保存確認] プロジェクト内シーン[{i}] ブロック数: {len(scene.blocks)}")
                    break

        QMessageBox.information(
            self,
            "保存完了",
            f"シーン「{self.current_scene.scene_name}」に保存しました。"
        )

    def _on_save_to_preview(self):
        """シーンを保存してプレビューに表示"""
        from utils.logger import get_logger
        logger = get_logger()

        if not self.current_scene:
            QMessageBox.warning(
                self,
                "エラー",
                "シーンが選択されていません。"
            )
            return

        # ブロック数チェック
        if not self.current_scene.blocks:
            QMessageBox.warning(
                self,
                "エラー",
                "シーンが空です。\n先に「💾 シーンに保存」ボタンでシーンを保存してください。"
            )
            return

        # プレビューに表示
        self.scene_changed.emit(self.current_scene)
        logger.info(f"[プレビュー表示] シーンID: {self.current_scene.scene_id}, 名前: {self.current_scene.scene_name}")

        # 成功メッセージ
        QMessageBox.information(
            self,
            "プレビュー表示",
            f"シーン「{self.current_scene.scene_name}」をプレビューに表示しました。\n\n"
            f"プレビューパネルで確認してください。"
        )

    def _on_block_double_clicked(self, item: QListWidgetItem):
        """ブロックダブルクリック時の処理

        Args:
            item: クリックされたアイテム
        """
        if not self.current_scene:
            return

        block_id = item.data(Qt.ItemDataRole.UserRole)

        # ブロックを検索
        block = None
        for b in self.current_scene.blocks:
            if b.block_id == block_id:
                block = b
                break

        if not block:
            return

        # ブロック編集ダイアログを表示
        from .block_edit_dialog import BlockEditDialog

        dialog = BlockEditDialog(block.type, block.content, self)

        if dialog.exec():
            # 編集内容を反映
            block_type, content = dialog.get_block_info()
            block.type = block_type
            block.content = content

            # リスト更新
            self._update_block_list()
            self.scene_changed.emit(self.current_scene)

    def _on_add_block_manual(self):
        """手動でブロックを追加"""
        if not self.current_scene:
            return

        # ブロック編集ダイアログを表示（新規作成モード）
        from .block_edit_dialog import BlockEditDialog

        dialog = BlockEditDialog(BlockType.FIXED_TEXT, "", self)

        if dialog.exec():
            # 新しいブロックを作成
            block_type, content = dialog.get_block_info()

            block = Block(
                block_id=self.current_scene.get_next_block_id(),
                type=block_type,
                content=content
            )

            self.current_scene.add_block(block)
            self._update_block_list()
            self.scene_changed.emit(self.current_scene)

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

        scene_id = self.project.get_next_scene_id()
        scene = Scene(
            scene_id=scene_id,
            scene_name=f"シーン{scene_id}",
            is_completed=False
        )

        # 共通プロンプトを自動挿入
        self._insert_common_prompts(scene)

        self.project.add_scene(scene)

        # タブ追加（シーン名を表示）
        display_name = scene.scene_name if scene.scene_name else f"シーン{scene.scene_id}"

        # シーンタブのコンテンツ：保存済みプロンプト表示エリア
        scene_content = QTextEdit()
        scene_content.setReadOnly(True)
        scene_content.setPlaceholderText("（未保存）\n\n下部の「プロンプト編集」エリアで編集し、\n「💾 シーンに保存」をクリックしてください。")
        scene_content.setStyleSheet("background-color: #f5f5f5; color: #333;")

        self.scene_tabs.addTab(scene_content, display_name)
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

    def _on_duplicate_scene(self):
        """シーン複製"""
        if not self.project or not self.current_scene:
            return

        # 元のシーン名を保存（メッセージ用）
        original_scene_name = self.current_scene.scene_name

        # 新しいシーンIDを取得
        scene_id = self.project.get_next_scene_id()

        # 現在のシーンを複製
        duplicated_scene = Scene(
            scene_id=scene_id,
            scene_name=f"{self.current_scene.scene_name} (コピー)",
            is_completed=False  # 複製したシーンは未完成とする
        )

        # ブロックを全てコピー
        for original_block in self.current_scene.blocks:
            # ブロックを深くコピー
            new_block = Block(
                block_id=duplicated_scene.get_next_block_id(),
                type=original_block.type,
                content=original_block.content,
                source=original_block.source.copy() if original_block.source else None,
                is_common=original_block.is_common
            )
            duplicated_scene.add_block(new_block)

        # プロジェクトに追加
        self.project.add_scene(duplicated_scene)

        # タブ追加（シーン名を表示）
        display_name = duplicated_scene.scene_name if duplicated_scene.scene_name else f"シーン{duplicated_scene.scene_id}"

        # シーンタブのコンテンツ：保存済みプロンプト表示エリア
        scene_content = QTextEdit()
        scene_content.setReadOnly(True)
        scene_content.setPlaceholderText("（未保存）\n\n下部の「プロンプト編集」エリアで編集し、\n「💾 シーンに保存」をクリックしてください。")
        scene_content.setStyleSheet("background-color: #f5f5f5; color: #333;")

        # 複製元のプロンプトを表示
        if duplicated_scene.blocks:
            from core.prompt_builder import PromptBuilder
            builder = PromptBuilder()
            saved_prompt = builder.build_scene_prompt(duplicated_scene, apply_common_prompts=False)
            scene_content.setPlainText(saved_prompt)

        self.scene_tabs.addTab(scene_content, display_name)

        # 新しいシーン（複製）を選択
        self.scene_tabs.setCurrentIndex(len(self.project.scenes) - 1)

        # 成功メッセージ
        QMessageBox.information(
            self,
            "複製完了",
            f"シーン「{original_scene_name}」を複製しました。\n\n"
            f"新しいシーン: {duplicated_scene.scene_name}"
        )

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

    def _insert_common_prompts(self, scene: Scene):
        """共通プロンプトを自動挿入

        Args:
            scene: シーンオブジェクト
        """
        if not self.project or not self.project.common_prompts:
            return

        # 有効な共通プロンプトを取得
        enabled_prompts = [cp for cp in self.project.common_prompts if cp.enabled]

        # 挿入位置別にグループ化
        start_prompts = [cp for cp in enabled_prompts if cp.position == "start"]
        end_prompts = [cp for cp in enabled_prompts if cp.position == "end"]

        # 先頭に挿入（逆順）
        for cp in reversed(start_prompts):
            block = Block(
                block_id=scene.get_next_block_id(),
                type=BlockType.FIXED_TEXT,
                content=cp.content,
                is_common=True
            )
            scene.blocks.insert(0, block)

            # BREAK挿入
            if cp.insert_break_after:
                break_block = Block(
                    block_id=scene.get_next_block_id(),
                    type=BlockType.BREAK,
                    content=""
                )
                scene.blocks.insert(1, break_block)

        # 末尾に挿入
        for cp in end_prompts:
            block = Block(
                block_id=scene.get_next_block_id(),
                type=BlockType.FIXED_TEXT,
                content=cp.content,
                is_common=True
            )
            scene.add_block(block)

            # BREAK挿入
            if cp.insert_break_after:
                break_block = Block(
                    block_id=scene.get_next_block_id(),
                    type=BlockType.BREAK,
                    content=""
                )
                scene.add_block(break_block)

    def _on_save_to_library(self):
        """ライブラリに保存ボタンクリック"""
        # 選択されているブロックを取得
        current_item = self.block_list.currentItem()
        if not current_item or not self.current_scene:
            QMessageBox.warning(
                self,
                "エラー",
                "保存するブロックを選択してください。"
            )
            return

        block_id = current_item.data(Qt.ItemDataRole.UserRole)

        # ブロックを検索
        block = None
        for b in self.current_scene.blocks:
            if b.block_id == block_id:
                block = b
                break

        if not block:
            return

        # BREAKブロックとワイルドカードブロックは保存不可
        if block.type == BlockType.BREAK:
            QMessageBox.warning(
                self,
                "保存不可",
                "BREAKブロックは保存できません。"
            )
            return

        if block.type == BlockType.WILDCARD:
            QMessageBox.warning(
                self,
                "保存不可",
                "ワイルドカードブロックは保存できません。\n固定テキストブロックのみ保存可能です。"
            )
            return

        # 固定テキストブロックのみ保存可能
        if block.type != BlockType.FIXED_TEXT:
            QMessageBox.warning(
                self,
                "保存不可",
                "このブロックは保存できません。"
            )
            return

        # 保存ダイアログを表示
        from .custom_prompt_dialog import CustomPromptDialog

        dialog = CustomPromptDialog(
            custom_prompt_manager=self.custom_prompt_manager,
            prompt_text=block.content,
            parent=self
        )

        if dialog.exec():
            # 保存成功
            saved_prompt = dialog.get_saved_prompt()
            if saved_prompt:
                # 使用履歴を記録（プロジェクト名を取得）
                project_name = self.project.name if self.project else "不明"
                self.custom_prompt_manager.record_usage(saved_prompt.id, project_name)

    def _on_save_scene_to_library(self):
        """シーンをライブラリに保存"""
        from utils.logger import get_logger
        logger = get_logger()

        if not self.current_scene:
            QMessageBox.warning(
                self,
                "エラー",
                "保存するシーンがありません。"
            )
            return

        logger.info(f"[ライブラリ保存開始] シーンID: {self.current_scene.scene_id}, 名前: {self.current_scene.scene_name}")
        logger.info(f"[ライブラリ保存開始] ブロック数: {len(self.current_scene.blocks)}")

        # ブロックの内容を詳細にログ出力
        for i, block in enumerate(self.current_scene.blocks):
            content_preview = block.content[:50] if len(block.content) > 50 else block.content
            logger.info(f"[ライブラリ保存] ブロック[{i}]: type={block.type.value}, content={content_preview}")

        # ブロック数チェック
        if not self.current_scene.blocks:
            logger.warning("[ライブラリ保存] ブロックが空です")
            QMessageBox.warning(
                self,
                "エラー",
                "ブロックが1つもありません。\nシーンにブロックを追加してから保存してください。"
            )
            return

        # 保存ダイアログを表示
        from .scene_save_dialog import SceneSaveDialog

        dialog = SceneSaveDialog(
            scene=self.current_scene,
            scene_library_manager=self.scene_library_manager,
            parent=self
        )

        if dialog.exec():
            # 保存成功
            saved_item = dialog.get_saved_item()
            if saved_item:
                QMessageBox.information(
                    self,
                    "保存完了",
                    f"シーン「{saved_item.name}」をライブラリに保存しました。"
                )
                # ライブラリパネルの更新を通知
                self.scene_library_updated.emit()

    def _on_load_scene_from_library(self):
        """ライブラリからシーンをプロンプト編集エリアに読み込み"""
        if not self.current_scene:
            QMessageBox.warning(
                self,
                "エラー",
                "シーンが選択されていません。"
            )
            return

        # ライブラリが空でないか確認
        items = self.scene_library_manager.get_all_items()
        if not items:
            QMessageBox.information(
                self,
                "ライブラリが空です",
                "シーンライブラリにシーンがありません。\n\n"
                "先にシーンを「📚 ライブラリ保存」で保存してください。"
            )
            return

        # 確認メッセージ
        current_text = self.prompt_text_edit.toPlainText().strip()
        if current_text:
            reply = QMessageBox.question(
                self,
                "確認",
                "プロンプト編集エリアの内容を上書きしますか？\n\n"
                "現在の内容は失われます。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # 選択ダイアログを表示
        from .scene_select_dialog import SceneSelectDialog

        dialog = SceneSelectDialog(
            scene_library_manager=self.scene_library_manager,
            parent=self
        )

        if dialog.exec() == SceneSelectDialog.DialogCode.Accepted:
            selected_item = dialog.get_selected_item()
            if selected_item:
                try:
                    # ライブラリからシーンを作成（一時的に）
                    temp_scene = self.scene_library_manager.create_scene_from_library(
                        item=selected_item,
                        project_name=self.project.name if self.project else "不明",
                        scene_id=999  # 一時ID
                    )

                    # シーンのプロンプトをプロンプト編集エリアに表示
                    if temp_scene.blocks:
                        from core.prompt_builder import PromptBuilder
                        builder = PromptBuilder()
                        loaded_prompt = builder.build_scene_prompt(temp_scene, apply_common_prompts=False)
                        self.prompt_text_edit.setPlainText(loaded_prompt)

                        QMessageBox.information(
                            self,
                            "読み込み完了",
                            f"シーン「{selected_item.name}」をプロンプト編集エリアに読み込みました。\n\n"
                            f"編集後、「💾 シーンに保存」ボタンで保存してください。"
                        )
                    else:
                        QMessageBox.warning(
                            self,
                            "エラー",
                            "選択したシーンにブロックがありません。"
                        )

                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "エラー",
                        f"シーンの読み込みに失敗しました:\n{e}"
                    )

    def _on_save_project_to_library(self):
        """作品を保存（作品ライブラリ）"""
        # MainWindowに通知（MainWindowで実際の保存処理を行う）
        self.save_project_requested.emit()

    def _on_paste_and_split_prompt(self):
        """プロンプトを貼り付けて自動的にブロックに分割"""
        if not self.current_scene:
            return

        # カスタムダイアログを作成
        dialog = QDialog(self)
        dialog.setWindowTitle("プロンプトから作成")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout(dialog)

        # 説明ラベル
        info_label = QLabel(
            "プロンプトを貼り付けてください。\n"
            "「BREAK」で自動的に分割されます。\n\n"
            "例: 1girl, school uniform, BREAK, standing, corridor, BREAK, masterpiece"
        )
        layout.addWidget(info_label)

        # テキスト入力エリア
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("プロンプトをここに貼り付け...")
        layout.addWidget(text_edit)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # ダイアログ表示
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # 入力されたテキストを取得
        prompt_text = text_edit.toPlainText().strip()

        if not prompt_text:
            QMessageBox.warning(
                self,
                "入力エラー",
                "プロンプトを入力してください。"
            )
            return

        # プロンプトを分割
        self._split_and_add_blocks(prompt_text)

    def _split_and_add_blocks(self, prompt_text: str):
        """プロンプトを分割してブロックに追加

        Args:
            prompt_text: 分割するプロンプト
        """
        if not self.current_scene:
            return

        # 既存のブロック数を記録
        original_block_count = len(self.current_scene.blocks)

        # BREAKで分割（大文字小文字を区別しない）
        import re
        segments = re.split(r',\s*BREAK\s*,?|BREAK', prompt_text, flags=re.IGNORECASE)

        added_blocks = 0

        for i, segment in enumerate(segments):
            segment = segment.strip().strip(',').strip()

            if not segment:
                continue

            # ワイルドカード形式かチェック
            is_wildcard = segment.startswith('__') and segment.endswith('__')

            if is_wildcard:
                # ワイルドカードブロック
                block = Block(
                    block_id=self.current_scene.get_next_block_id(),
                    type=BlockType.WILDCARD,
                    content=segment
                )
            else:
                # 固定テキストブロック
                block = Block(
                    block_id=self.current_scene.get_next_block_id(),
                    type=BlockType.FIXED_TEXT,
                    content=segment
                )

            self.current_scene.add_block(block)
            added_blocks += 1

            # 最後のセグメント以外はBREAKを追加
            if i < len(segments) - 1 and segment:
                break_block = Block(
                    block_id=self.current_scene.get_next_block_id(),
                    type=BlockType.BREAK,
                    content=""
                )
                self.current_scene.add_block(break_block)

        # UI更新
        self._update_block_list()
        self.scene_changed.emit(self.current_scene)

        # 完了メッセージ
        QMessageBox.information(
            self,
            "分割完了",
            f"{added_blocks}個のブロックを追加しました。"
        )

    def _on_switch_to_block_mode(self):
        """ブロックモードに切り替え"""
        # テキストモードからブロックモードに切り替える前に、テキストを保存
        if not self.block_mode_btn.isChecked():
            self._sync_text_to_blocks()

        self.block_mode_btn.setChecked(True)
        self.text_mode_btn.setChecked(False)
        self.block_mode_widget.show()
        self.text_mode_widget.hide()

        # ブロックリストを更新
        self._update_block_list()

    def _on_switch_to_text_mode(self):
        """テキストモードに切り替え"""
        self.block_mode_btn.setChecked(False)
        self.text_mode_btn.setChecked(True)
        self.block_mode_widget.hide()
        self.text_mode_widget.show()

        # ブロックからテキストを生成
        self._sync_blocks_to_text()

    def _sync_blocks_to_text(self):
        """ブロックからテキストエリアに同期"""
        from utils.logger import get_logger
        logger = get_logger()

        if not self.current_scene:
            return

        logger.info(f"[ブロック→テキスト同期] シーンID: {self.current_scene.scene_id}, ブロック数: {len(self.current_scene.blocks)}")

        # ブロックからプロンプトテキストを生成
        from core.prompt_builder import PromptBuilder
        builder = PromptBuilder()

        # BREAKを保持したまま1行のプロンプトを構築
        prompt = builder.build_scene_prompt(self.current_scene, apply_common_prompts=False)
        logger.info(f"[ブロック→テキスト同期] 生成されたプロンプト長: {len(prompt)}")

        # テキストエリアに設定（一時的にシグナルをブロック）
        self.prompt_text_edit.blockSignals(True)
        self.prompt_text_edit.setPlainText(prompt)
        self.prompt_text_edit.blockSignals(False)
        logger.info("[ブロック→テキスト同期] エディタ設定完了")

    def _sync_text_to_blocks(self):
        """テキストエリアからブロックに同期"""
        if not self.current_scene:
            return

        prompt_text = self.prompt_text_edit.toPlainText().strip()

        if not prompt_text:
            # 空の場合は全ブロック削除
            self.current_scene.blocks.clear()
            return

        # 既存のブロックをクリア
        self.current_scene.blocks.clear()

        # テキストをパースしてブロックに変換
        self._split_and_add_blocks(prompt_text)

    def _on_text_mode_changed(self):
        """テキストモードでの編集時"""
        # リアルタイムでプレビューを更新
        if not self.current_scene:
            return

        # 一時的にブロックに同期してプレビュー更新
        prompt_text = self.prompt_text_edit.toPlainText().strip()

        if prompt_text:
            # プレビュー用の一時シーンを作成
            from models import Scene
            temp_scene = Scene(
                scene_id=self.current_scene.scene_id,
                scene_name=self.current_scene.scene_name,
                is_completed=self.current_scene.is_completed
            )

            # テキストをパースして一時シーンにブロックを追加
            import re
            segments = re.split(r',\s*BREAK\s*,?|BREAK', prompt_text, flags=re.IGNORECASE)

            for i, segment in enumerate(segments):
                segment = segment.strip().strip(',').strip()

                if not segment:
                    continue

                # ワイルドカード形式かチェック
                is_wildcard = segment.startswith('__') and segment.endswith('__')

                if is_wildcard:
                    block = Block(
                        block_id=temp_scene.get_next_block_id(),
                        type=BlockType.WILDCARD,
                        content=segment
                    )
                else:
                    block = Block(
                        block_id=temp_scene.get_next_block_id(),
                        type=BlockType.FIXED_TEXT,
                        content=segment
                    )

                temp_scene.add_block(block)

                # 最後のセグメント以外はBREAKを追加
                if i < len(segments) - 1 and segment:
                    break_block = Block(
                        block_id=temp_scene.get_next_block_id(),
                        type=BlockType.BREAK,
                        content=""
                    )
                    temp_scene.add_block(break_block)

            # プレビュー更新
            self.scene_changed.emit(temp_scene)
        else:
            self.scene_changed.emit(self.current_scene)

    def _on_tab_moved(self, from_index: int, to_index: int):
        """タブ移動時の処理

        Args:
            from_index: 移動元のインデックス
            to_index: 移動先のインデックス
        """
        if not self.project or not self.project.scenes:
            return

        # プロジェクト内のシーンの順序も同期
        moved_scene = self.project.scenes.pop(from_index)
        self.project.scenes.insert(to_index, moved_scene)

