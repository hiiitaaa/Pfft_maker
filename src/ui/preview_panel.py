"""プレビューパネル

最終プロンプトのプレビューを表示するパネル。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QHBoxLayout, QFileDialog, QMessageBox,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QClipboard
from PyQt6.QtWidgets import QApplication
from pathlib import Path

from models import Scene, Project
from core.prompt_builder import PromptBuilder
from config.settings import Settings


class ScenePreviewWidget(QFrame):
    """個別シーンのプレビューウィジェット

    各シーンのプロンプトと削除ボタンを含む。
    """

    # シグナル定義
    delete_requested = pyqtSignal(int)  # scene_id

    def __init__(self, scene: Scene, prompt: str, parent=None):
        """初期化

        Args:
            scene: シーンオブジェクト
            prompt: プロンプトテキスト
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.scene = scene
        self.prompt = prompt

        self._create_ui()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # フレームスタイル設定
        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("""
            ScenePreviewWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                color: black;
            }
        """)

        # ヘッダー（シーン名 + 削除ボタン）
        header_layout = QHBoxLayout()

        scene_label = QLabel(f"🎬 {self.scene.scene_name}")
        scene_label.setStyleSheet("font-weight: bold; font-size: 11pt; color: black;")
        header_layout.addWidget(scene_label)

        header_layout.addStretch()

        # 削除ボタン
        delete_btn = QPushButton("✕ 削除")
        delete_btn.setFixedWidth(80)
        delete_btn.setStyleSheet("background-color: #ffdddd; color: #cc0000;")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.scene.scene_id))
        header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

        # プロンプト表示
        prompt_text = QTextEdit()
        prompt_text.setReadOnly(True)
        prompt_text.setPlainText(self.prompt)
        prompt_text.setMaximumHeight(150)
        prompt_text.setStyleSheet("""
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            color: black;
        """)
        layout.addWidget(prompt_text)

        # 文字数
        char_label = QLabel(f"文字数: {len(self.prompt)}")
        char_label.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(char_label)


class PreviewPanel(QWidget):
    """プレビューパネル

    最終プロンプトの表示とコピー機能を提供。
    """

    def __init__(self):
        """初期化"""
        super().__init__()

        self.current_scene: Scene | None = None
        self.current_project: Project | None = None
        self.settings = Settings()
        self.prompt_builder = PromptBuilder(self.settings)

        # プレビュー済みシーンを管理（scene_id -> (Scene, prompt)）
        self.preview_scenes: dict[int, tuple[Scene, str]] = {}

        # UI構築
        self._create_ui()

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # タイトル & ボタン
        header_layout = QHBoxLayout()
        title_label = QLabel("プレビュー")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # 全てクリアボタン
        clear_all_btn = QPushButton("🗑️ 全てクリア")
        clear_all_btn.setFixedWidth(120)
        clear_all_btn.clicked.connect(self._on_clear_all)
        header_layout.addWidget(clear_all_btn)

        layout.addLayout(header_layout)

        # シーンプレビュー表示エリア（スクロール可能）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # スクロールエリア内のコンテナ
        self.scenes_container = QWidget()
        self.scenes_layout = QVBoxLayout(self.scenes_container)
        self.scenes_layout.setSpacing(10)
        self.scenes_layout.setContentsMargins(0, 0, 0, 0)
        self.scenes_layout.addStretch()  # 下部の余白

        scroll_area.setWidget(self.scenes_container)
        layout.addWidget(scroll_area)

        # 統計情報
        self.stats_label = QLabel("シーン数: 0 | 合計文字数: 0")
        self.stats_label.setStyleSheet("color: gray; font-size: 10pt;")
        layout.addWidget(self.stats_label)

        # ボタン
        button_layout = QHBoxLayout()

        copy_btn = QPushButton("📋 コピー")
        copy_btn.clicked.connect(self._on_copy)
        button_layout.addWidget(copy_btn)

        export_btn = QPushButton("💾 ファイル出力")
        export_btn.clicked.connect(self._on_export_file)
        button_layout.addWidget(export_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

    def update_preview(self, scene: Scene):
        """プレビュー更新（単一シーン）

        Args:
            scene: シーンオブジェクト
        """
        self.current_scene = scene

        # プロンプト構築
        if scene.blocks:
            prompt = self.prompt_builder.build_scene_prompt(scene)
            # プレビュー済みシーンに追加/更新
            self.preview_scenes[scene.scene_id] = (scene, prompt)
        else:
            prompt = ""
            # ブロックが空の場合は削除
            self.preview_scenes.pop(scene.scene_id, None)

        # UI再構築
        self._rebuild_preview_ui()

    def _rebuild_preview_ui(self):
        """プレビューUIを再構築"""
        # 既存のウィジェットを全削除
        while self.scenes_layout.count() > 1:  # stretchは残す
            item = self.scenes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # シーンを順番に追加
        total_chars = 0
        for scene_id in sorted(self.preview_scenes.keys()):
            scene, prompt = self.preview_scenes[scene_id]

            # シーンプレビューウィジェットを作成
            scene_widget = ScenePreviewWidget(scene, prompt, self)
            scene_widget.delete_requested.connect(self._on_delete_scene)
            self.scenes_layout.insertWidget(self.scenes_layout.count() - 1, scene_widget)

            total_chars += len(prompt)

        # 統計情報を更新
        scene_count = len(self.preview_scenes)
        self.stats_label.setText(f"シーン数: {scene_count} | 合計文字数: {total_chars}")

    def _on_delete_scene(self, scene_id: int):
        """シーンをプレビューから削除

        Args:
            scene_id: 削除するシーンのID
        """
        if scene_id in self.preview_scenes:
            scene_name = self.preview_scenes[scene_id][0].scene_name

            # 確認ダイアログ
            reply = QMessageBox.question(
                self,
                "プレビューから削除",
                f"シーン「{scene_name}」をプレビューから削除しますか？\n\n"
                f"※ プロジェクト本体のシーンは削除されません。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # プレビューから削除
                del self.preview_scenes[scene_id]
                self._rebuild_preview_ui()

    def _on_clear_all(self):
        """全てのプレビューをクリア"""
        if not self.preview_scenes:
            QMessageBox.information(
                self,
                "クリア",
                "プレビューは既に空です。"
            )
            return

        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "全てクリア",
            f"全てのプレビュー（{len(self.preview_scenes)}シーン）をクリアしますか？\n\n"
            f"※ プロジェクト本体のシーンは削除されません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.preview_scenes.clear()
            self._rebuild_preview_ui()

    def update_all_scenes(self, project: Project):
        """全シーンのプレビューを表示（保存済みシーンのみ）

        Args:
            project: プロジェクトオブジェクト
        """
        self.current_project = project  # プロジェクトを保存

        if not project or not project.scenes:
            self.preview_scenes.clear()
            self._rebuild_preview_ui()
            return

        # 全シーンのプロンプトを構築してプレビューに追加
        for scene in project.scenes:
            # ブロックが空のシーンはスキップ（未保存シーン）
            if not scene.blocks:
                continue

            # シーンのプロンプト
            scene_prompt = self.prompt_builder.build_scene_prompt(scene)
            self.preview_scenes[scene.scene_id] = (scene, scene_prompt)

        # UI再構築
        self._rebuild_preview_ui()

    def _get_export_text(self) -> str:
        """出力用のテキストを取得（ヘッダーなし、1シーン1行）

        Returns:
            出力用のテキスト（各シーンが1行、改行区切り）
        """
        if not self.preview_scenes:
            return ""

        export_lines = []

        # プレビュー済みシーンを順番に出力
        for scene_id in sorted(self.preview_scenes.keys()):
            scene, prompt = self.preview_scenes[scene_id]
            export_lines.append(prompt)

        # シーンごとに改行で区切る
        return "\n".join(export_lines)

    def _on_copy(self):
        """プロンプトをクリップボードにコピー（ヘッダーなし、1シーン1行）"""
        export_text = self._get_export_text()

        if export_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(export_text)

            # コピーした行数をカウント
            line_count = len(export_text.split('\n'))

            # 成功メッセージを表示
            QMessageBox.information(
                self,
                "コピー完了",
                f"{line_count}シーンのプロンプトをクリップボードにコピーしました。\n\n"
                f"合計文字数: {len(export_text)}"
            )
        else:
            QMessageBox.warning(
                self,
                "コピーエラー",
                "コピーするプロンプトがありません。\n\n"
                "先にシーンを「🖼️ プレビューへ出力」ボタンでプレビューに表示してください。"
            )

    def _on_export_file(self):
        """ファイルに出力（ヘッダーなし、1シーン1行）"""
        export_text = self._get_export_text()

        if not export_text:
            QMessageBox.warning(
                self,
                "出力エラー",
                "出力するプロンプトがありません。\n\n"
                "先にシーンを「🖼️ プレビューへ出力」ボタンでプレビューに表示してください。"
            )
            return

        # ファイル保存ダイアログを表示
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "プロンプトをファイルに保存",
            str(Path.home() / "prompts.txt"),
            "テキストファイル (*.txt);;すべてのファイル (*.*)"
        )

        if not file_path:
            return

        try:
            # ファイルに書き込み
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(export_text)

            # 成功メッセージ
            line_count = len(export_text.split('\n'))
            QMessageBox.information(
                self,
                "出力完了",
                f"プロンプトをファイルに保存しました。\n\n"
                f"ファイル: {file_path}\n"
                f"シーン数: {line_count}\n"
                f"文字数: {len(export_text)}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "エラー",
                f"ファイルの保存に失敗しました:\n{e}"
            )
