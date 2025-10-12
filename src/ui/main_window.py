"""メインウィンドウ

Pfft_makerのメインUIウィンドウ。
3カラムレイアウト（ライブラリ、エディタ、プレビュー）。
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QMessageBox,
    QMenuBar, QMenu, QFileDialog, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence

from .library_panel import LibraryPanel
from .scene_editor_panel import SceneEditorPanel
from .preview_panel import PreviewPanel
from ..models import Project


class MainWindow(QMainWindow):
    """メインウィンドウ

    3カラムレイアウトでプロンプト編集を効率化。

    Attributes:
        current_project: 現在のプロジェクト
        library_panel: ライブラリパネル（左）
        scene_editor: シーンエディタパネル（中央）
        preview_panel: プレビューパネル（右）
    """

    # シグナル定義
    project_changed = pyqtSignal()

    def __init__(self):
        """初期化"""
        super().__init__()

        # プロジェクト
        self.current_project: Project | None = None
        self.project_path: Path | None = None

        # ウィンドウ設定
        self.setWindowTitle("Pfft_maker")
        self.resize(1920, 1080)

        # UI構築
        self._create_ui()
        self._create_menu_bar()
        self._create_status_bar()
        self._create_shortcuts()
        self._connect_signals()

        # 新規プロジェクト作成
        self._create_new_project()

    def _create_ui(self):
        """UI構築"""
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 3カラムレイアウト
        layout = QHBoxLayout(central_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # 左: ライブラリパネル (600px)
        self.library_panel = LibraryPanel()
        self.library_panel.setFixedWidth(600)

        # 中央: シーンエディタパネル (750px)
        self.scene_editor = SceneEditorPanel()
        self.scene_editor.setFixedWidth(750)

        # 右: プレビューパネル (550px)
        self.preview_panel = PreviewPanel()
        self.preview_panel.setFixedWidth(550)

        layout.addWidget(self.library_panel)
        layout.addWidget(self.scene_editor)
        layout.addWidget(self.preview_panel)

    def _create_menu_bar(self):
        """メニューバー作成"""
        menubar = self.menuBar()

        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")

        # 新規プロジェクト
        new_action = QAction("新規プロジェクト(&N)", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_action)

        # プロジェクトを開く
        open_action = QAction("プロジェクトを開く(&O)...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open_project)
        file_menu.addAction(open_action)

        # 保存
        save_action = QAction("保存(&S)", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save_project)
        file_menu.addAction(save_action)

        # 名前を付けて保存
        save_as_action = QAction("名前を付けて保存(&A)...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._on_save_project_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # 終了
        exit_action = QAction("終了(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")

        # バージョン情報
        about_action = QAction("バージョン情報(&A)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _create_status_bar(self):
        """ステータスバー作成"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了")

    def _create_shortcuts(self):
        """キーボードショートカット作成"""
        # シーン移動（Ctrl + 矢印）
        next_scene = QAction(self)
        next_scene.setShortcut(QKeySequence("Ctrl+Right"))
        next_scene.triggered.connect(self.scene_editor.next_scene)
        self.addAction(next_scene)

        prev_scene = QAction(self)
        prev_scene.setShortcut(QKeySequence("Ctrl+Left"))
        prev_scene.triggered.connect(self.scene_editor.previous_scene)
        self.addAction(prev_scene)

    def _connect_signals(self):
        """シグナル・スロット接続"""
        # ライブラリ → エディタ
        self.library_panel.prompt_selected.connect(
            self.scene_editor.insert_prompt_block
        )

        # エディタ → プレビュー
        self.scene_editor.scene_changed.connect(
            self.preview_panel.update_preview
        )

        # プロジェクト変更
        self.project_changed.connect(self._on_project_changed)

    def _create_new_project(self):
        """新規プロジェクト作成"""
        self.current_project = Project.create_new("無題のプロジェクト", "")
        self.project_path = None
        self.scene_editor.set_project(self.current_project)
        self._update_title()
        self.status_bar.showMessage("新規プロジェクトを作成しました")

    def _on_new_project(self):
        """新規プロジェクト作成（メニュー）"""
        # 保存確認
        if not self._confirm_save():
            return

        self._create_new_project()

    def _on_open_project(self):
        """プロジェクトを開く"""
        # 保存確認
        if not self._confirm_save():
            return

        # ファイル選択
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "プロジェクトを開く",
            "",
            "Pfftプロジェクト (*.pfft)"
        )

        if not file_path:
            return

        # プロジェクト読み込み
        try:
            import json
            project_dict = json.loads(Path(file_path).read_text(encoding="utf-8"))
            self.current_project = Project.from_dict(project_dict)
            self.project_path = Path(file_path)
            self.scene_editor.set_project(self.current_project)
            self._update_title()
            self.status_bar.showMessage(f"プロジェクトを開きました: {file_path}")
        except Exception as e:
            QMessageBox.critical(
                self,
                "エラー",
                f"プロジェクトの読み込みに失敗しました:\n{e}"
            )

    def _on_save_project(self):
        """プロジェクトを保存"""
        if self.project_path:
            self._save_to_file(self.project_path)
        else:
            self._on_save_project_as()

    def _on_save_project_as(self):
        """名前を付けて保存"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "名前を付けて保存",
            "",
            "Pfftプロジェクト (*.pfft)"
        )

        if not file_path:
            return

        # 拡張子確認
        if not file_path.endswith('.pfft'):
            file_path += '.pfft'

        self.project_path = Path(file_path)
        self._save_to_file(self.project_path)

    def _save_to_file(self, file_path: Path):
        """ファイルに保存"""
        try:
            json_str = self.current_project.to_json()
            file_path.write_text(json_str, encoding="utf-8")
            self._update_title()
            self.status_bar.showMessage(f"保存しました: {file_path}")
        except Exception as e:
            QMessageBox.critical(
                self,
                "エラー",
                f"プロジェクトの保存に失敗しました:\n{e}"
            )

    def _confirm_save(self) -> bool:
        """保存確認

        Returns:
            処理を続行する場合True
        """
        # TODO: 変更検出を実装
        return True

    def _update_title(self):
        """タイトル更新"""
        if self.project_path:
            title = f"Pfft_maker - {self.project_path.name}"
        else:
            title = f"Pfft_maker - {self.current_project.name}"
        self.setWindowTitle(title)

    def _on_project_changed(self):
        """プロジェクト変更時"""
        self._update_title()

    def _on_about(self):
        """バージョン情報"""
        QMessageBox.about(
            self,
            "Pfft_makerについて",
            "Pfft_maker v0.1.0\n\n"
            "Stable Diffusion WebUI用プロンプト管理ツール\n\n"
            "Phase 4.2 - UI実装完了"
        )

    def closeEvent(self, event):
        """ウィンドウクローズ時"""
        if self._confirm_save():
            event.accept()
        else:
            event.ignore()
