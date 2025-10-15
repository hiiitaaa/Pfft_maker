"""メインウィンドウ

Pfft_makerのメインUIウィンドウ。
3カラムレイアウト（ライブラリ、エディタ、プレビュー）。
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox,
    QMenuBar, QMenu, QFileDialog, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence

from .library_panel import LibraryPanel
from .scene_editor_panel import SceneEditorPanel
from .preview_panel import PreviewPanel
from .update_notification_banner import UpdateNotificationBanner
from models import Project
from config.settings import Settings
from core.file_sync_manager import FileSyncManager
from core.template_manager import TemplateManager
from utils.logger import get_logger


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

        # ロガー
        self.logger = get_logger()

        # プロジェクト
        self.current_project: Project | None = None
        self.project_path: Path | None = None

        # 設定
        self.settings = Settings()

        # テンプレートマネージャー
        data_dir = Path.cwd() / "data"
        data_dir.mkdir(exist_ok=True)
        self.template_manager = TemplateManager(data_dir)

        # 起動時チェック完了フラグ
        self._startup_check_done = False

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

        # メインレイアウト（縦）
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 更新通知バナー
        self.update_banner = UpdateNotificationBanner()
        main_layout.addWidget(self.update_banner)

        # 3カラムコンテナ
        columns_container = QWidget()
        columns_layout = QHBoxLayout(columns_container)
        columns_layout.setSpacing(0)
        columns_layout.setContentsMargins(0, 0, 0, 0)

        # 左: ライブラリパネル (600px)
        self.library_panel = LibraryPanel()
        self.library_panel.setFixedWidth(600)

        # 中央: シーンエディタパネル (750px)
        self.scene_editor = SceneEditorPanel()
        self.scene_editor.setFixedWidth(750)

        # 右: プレビューパネル (550px)
        self.preview_panel = PreviewPanel()
        self.preview_panel.setFixedWidth(550)

        columns_layout.addWidget(self.library_panel)
        columns_layout.addWidget(self.scene_editor)
        columns_layout.addWidget(self.preview_panel)

        main_layout.addWidget(columns_container)

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

        # テンプレートから作成
        new_from_template_action = QAction("テンプレートから作成(&T)...", self)
        new_from_template_action.triggered.connect(self._on_new_from_template)
        file_menu.addAction(new_from_template_action)

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

        # テンプレートとして保存
        save_as_template_action = QAction("テンプレートとして保存(&M)...", self)
        save_as_template_action.triggered.connect(self._on_save_as_template)
        file_menu.addAction(save_as_template_action)

        # 作品として保存
        save_as_project_lib_action = QAction("作品として保存(&P)...", self)
        save_as_project_lib_action.triggered.connect(self._on_save_as_project_library)
        file_menu.addAction(save_as_project_lib_action)

        file_menu.addSeparator()

        # プロンプト出力
        export_action = QAction("プロンプト出力(&E)...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._on_export_prompts)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # 終了
        exit_action = QAction("終了(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ツールメニュー
        tools_menu = menubar.addMenu("ツール(&T)")

        # シーン一括保存（提案3: バッチ保存）
        batch_save_action = QAction("シーンを一括保存(&B)...", self)
        batch_save_action.setShortcut(QKeySequence("Ctrl+Shift+B"))
        batch_save_action.triggered.connect(self._on_batch_save_scenes)
        tools_menu.addAction(batch_save_action)

        tools_menu.addSeparator()

        # 設定
        settings_action = QAction("設定(&S)...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._on_settings)
        tools_menu.addAction(settings_action)

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
        # ライブラリ → エディタ（固定テキスト）
        self.library_panel.prompt_selected.connect(
            self.scene_editor.insert_prompt_as_fixed_text
        )

        # ライブラリ → エディタ（ワイルドカード）
        self.library_panel.wildcard_selected.connect(
            self.scene_editor.insert_wildcard_block
        )

        # エディタ → プレビュー（全シーン表示）
        self.scene_editor.scene_changed.connect(
            self._on_scene_changed_update_all_preview
        )

        # エディタ → ライブラリパネル（シーンライブラリ更新）
        self.scene_editor.scene_library_updated.connect(
            self.library_panel.reload_scene_library
        )

        # ライブラリ → エディタ（シーン挿入）
        self.library_panel.scene_selected.connect(
            self._on_scene_library_item_selected
        )

        # ライブラリ → プロジェクト（作品全体挿入）
        self.library_panel.project_selected.connect(
            self._on_project_library_item_selected
        )

        # ライブラリ → プロジェクト（作品内個別シーン挿入）
        self.library_panel.project_scene_selected.connect(
            self._on_project_library_scene_selected
        )

        # エディタ → 作品保存
        self.scene_editor.save_project_requested.connect(
            self._on_save_as_project_library
        )

        # プロジェクト変更
        self.project_changed.connect(self._on_project_changed)

        # 更新通知バナー
        self.update_banner.sync_requested.connect(self._on_banner_sync_requested)
        self.update_banner.dismissed.connect(self._on_banner_dismissed)

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

    def _on_scene_changed_update_all_preview(self, scene):
        """シーン変更時にプレビューを全シーン表示で更新

        Args:
            scene: 変更されたシーン（使用しない）
        """
        if self.current_project:
            self.preview_panel.update_all_scenes(self.current_project)

    def _on_export_prompts(self):
        """プロンプト出力"""
        from .output_dialog import OutputDialog

        if not self.current_project or not self.current_project.scenes:
            QMessageBox.warning(
                self,
                "エラー",
                "出力するシーンがありません"
            )
            return

        # 出力ダイアログ表示
        dialog = OutputDialog(self.current_project, self)
        dialog.exec()

    def _on_settings(self):
        """設定ダイアログ表示"""
        from .settings_dialog import SettingsDialog

        dialog = SettingsDialog(self)
        dialog.exec()

    def _on_new_from_template(self):
        """テンプレートから新規プロジェクト作成"""
        from .template_select_dialog import TemplateSelectDialog

        # 保存確認
        if not self._confirm_save():
            return

        # テンプレート選択ダイアログ
        templates = self.template_manager.get_all_templates()

        if not templates:
            QMessageBox.information(
                self,
                "テンプレートなし",
                "利用可能なテンプレートがありません。\n\n"
                "先にプロジェクトを「テンプレートとして保存」してください。"
            )
            return

        dialog = TemplateSelectDialog(templates, self)
        dialog.template_deleted.connect(self._on_template_deleted)

        if dialog.exec() == TemplateSelectDialog.DialogCode.Accepted:
            template = dialog.get_selected_template()
            project_name = dialog.get_project_name()

            if template:
                try:
                    # テンプレートからプロジェクト作成
                    self.current_project = self.template_manager.create_project_from_template(
                        template, project_name
                    )
                    self.project_path = None
                    self.scene_editor.set_project(self.current_project)
                    self._update_title()
                    self.status_bar.showMessage(
                        f"テンプレート「{template.name}」からプロジェクトを作成しました"
                    )
                except Exception as e:
                    self.logger.error(f"テンプレートからの作成失敗: {e}", exc_info=True)
                    QMessageBox.critical(
                        self,
                        "エラー",
                        f"テンプレートからの作成に失敗しました:\n{e}"
                    )

    def _on_save_as_template(self):
        """テンプレートとして保存"""
        from .template_save_dialog import TemplateSaveDialog

        if not self.current_project or not self.current_project.scenes:
            QMessageBox.warning(
                self,
                "エラー",
                "保存するシーンがありません"
            )
            return

        # テンプレート保存ダイアログ
        dialog = TemplateSaveDialog(self)

        if dialog.exec() == TemplateSaveDialog.DialogCode.Accepted:
            name, description, template_type = dialog.get_template_info()

            try:
                # テンプレート保存
                template = self.template_manager.save_template_from_project(
                    self.current_project,
                    name,
                    description,
                    template_type
                )

                QMessageBox.information(
                    self,
                    "保存完了",
                    f"テンプレート「{template.name}」を保存しました。\n\n"
                    f"タイプ: {template_type}\n"
                    f"シーン数: {template.scene_count}"
                )
                self.status_bar.showMessage(f"テンプレートを保存しました: {name}")

            except Exception as e:
                self.logger.error(f"テンプレート保存失敗: {e}", exc_info=True)
                QMessageBox.critical(
                    self,
                    "エラー",
                    f"テンプレートの保存に失敗しました:\n{e}"
                )

    def _on_template_deleted(self, template_id: str):
        """テンプレート削除ハンドラ"""
        try:
            self.template_manager.delete_template(template_id)
            self.logger.info(f"テンプレート削除: {template_id}")
        except Exception as e:
            self.logger.error(f"テンプレート削除失敗: {e}", exc_info=True)

    def _on_scene_library_item_selected(self, scene_item):
        """シーンライブラリアイテムが選択された時

        Args:
            scene_item: SceneLibraryItemオブジェクト
        """
        from models.scene_library import SceneLibraryItem

        if not isinstance(scene_item, SceneLibraryItem):
            return

        if not self.current_project:
            QMessageBox.warning(
                self,
                "エラー",
                "プロジェクトが開かれていません"
            )
            return

        try:
            # 新しいシーンIDを取得
            scene_id = self.current_project.get_next_scene_id()

            # プロジェクト名を取得
            project_name = self.current_project.name if self.current_project else "不明"

            # ライブラリからシーンを作成
            scene = self.scene_editor.scene_library_manager.create_scene_from_library(
                item=scene_item,
                project_name=project_name,
                scene_id=scene_id
            )

            # プロジェクトに追加
            self.current_project.add_scene(scene)

            # シーンエディタを更新
            self.scene_editor.set_project(self.current_project)

            # ステータスバーに通知
            self.status_bar.showMessage(f"シーン「{scene_item.name}」を挿入しました")

        except Exception as e:
            self.logger.error(f"シーン挿入エラー: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "エラー",
                f"シーンの挿入に失敗しました:\n{e}"
            )

    def _on_save_as_project_library(self):
        """作品として保存（作品ライブラリ）"""
        from .project_save_dialog import ProjectSaveDialog

        if not self.current_project:
            QMessageBox.warning(
                self,
                "エラー",
                "プロジェクトが開かれていません"
            )
            return

        if not self.current_project.scenes:
            QMessageBox.warning(
                self,
                "エラー",
                "保存するシーンがありません"
            )
            return

        # 作品保存ダイアログを表示
        dialog = ProjectSaveDialog(
            project=self.current_project,
            project_library_manager=self.library_panel.project_library_manager,
            parent=self
        )

        if dialog.exec() == ProjectSaveDialog.DialogCode.Accepted:
            saved_item = dialog.get_saved_item()
            if saved_item:
                self.status_bar.showMessage(
                    f"作品「{saved_item.name}」をライブラリに保存しました "
                    f"({saved_item.get_scene_count()}シーン)"
                )
                # ライブラリパネルを更新
                self.library_panel.reload_project_library()

    def _on_project_library_item_selected(self, project_item):
        """作品ライブラリアイテムが選択された時（全シーン一括挿入）

        Args:
            project_item: ProjectLibraryItemオブジェクト
        """
        from models.project_library import ProjectLibraryItem

        if not isinstance(project_item, ProjectLibraryItem):
            return

        if not self.current_project:
            QMessageBox.warning(
                self,
                "エラー",
                "プロジェクトが開かれていません"
            )
            return

        try:
            # 挿入確認
            scene_count = project_item.get_scene_count()
            reply = QMessageBox.question(
                self,
                "作品全体を挿入",
                f"作品「{project_item.name}」の全シーン（{scene_count}シーン）を\n"
                f"現在のプロジェクトの末尾に挿入しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # 新しいシーンの開始ID
            start_scene_id = self.current_project.get_next_scene_id()

            # プロジェクト名を取得
            project_name = self.current_project.name if self.current_project else "不明"

            # ライブラリから複数のシーンを作成
            scenes = self.library_panel.project_library_manager.create_scenes_from_library(
                item=project_item,
                project_name=project_name,
                start_scene_id=start_scene_id
            )

            # 全シーンをプロジェクトに追加
            for scene in scenes:
                self.current_project.add_scene(scene)

            # シーンエディタを更新
            self.scene_editor.set_project(self.current_project)

            # ライブラリパネルを更新（使用履歴反映）
            self.library_panel.reload_project_library()

            # ステータスバーに通知
            self.status_bar.showMessage(
                f"作品「{project_item.name}」の{len(scenes)}シーンを挿入しました"
            )

        except Exception as e:
            self.logger.error(f"作品挿入エラー: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "エラー",
                f"作品の挿入に失敗しました:\n{e}"
            )

    def _on_project_library_scene_selected(self, project_item, scene_index: int):
        """作品ライブラリ内の個別シーンが選択された時

        Args:
            project_item: ProjectLibraryItemオブジェクト
            scene_index: シーンのインデックス
        """
        from models.project_library import ProjectLibraryItem

        if not isinstance(project_item, ProjectLibraryItem):
            return

        if not self.current_project:
            QMessageBox.warning(
                self,
                "エラー",
                "プロジェクトが開かれていません"
            )
            return

        try:
            # 新しいシーンID
            scene_id = self.current_project.get_next_scene_id()

            # プロジェクト名を取得
            project_name = self.current_project.name if self.current_project else "不明"

            # ライブラリから単一のシーンを作成
            scene = self.library_panel.project_library_manager.get_single_scene_from_library(
                item=project_item,
                scene_index=scene_index,
                project_name=project_name,
                scene_id=scene_id
            )

            # プロジェクトに追加
            self.current_project.add_scene(scene)

            # シーンエディタを更新
            self.scene_editor.set_project(self.current_project)

            # ライブラリパネルを更新（使用履歴反映）
            self.library_panel.reload_project_library()

            # ステータスバーに通知
            scene_name = project_item.scenes[scene_index].name
            self.status_bar.showMessage(
                f"作品「{project_item.name}」からシーン「{scene_name}」を挿入しました"
            )

        except Exception as e:
            self.logger.error(f"シーン挿入エラー: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "エラー",
                f"シーンの挿入に失敗しました:\n{e}"
            )

    def _on_batch_save_scenes(self):
        """シーン一括保存（提案3: バッチ保存）"""
        from .batch_scene_save_dialog import BatchSceneSaveDialog

        if not self.current_project:
            QMessageBox.warning(
                self,
                "エラー",
                "プロジェクトが開かれていません"
            )
            return

        # 完成済みシーンを取得
        completed_scenes = [s for s in self.current_project.scenes if s.is_completed]

        if not completed_scenes:
            QMessageBox.information(
                self,
                "シーンなし",
                "完成したシーンがありません。\n\n"
                "シーンに「✅ 完成」チェックを入れてください。"
            )
            return

        # バッチ保存ダイアログを表示
        dialog = BatchSceneSaveDialog(
            scenes=completed_scenes,
            scene_library_manager=self.scene_editor.scene_library_manager,
            parent=self
        )

        if dialog.exec() == BatchSceneSaveDialog.DialogCode.Accepted:
            saved_count = dialog.get_saved_count()
            self.status_bar.showMessage(f"{saved_count}個のシーンをライブラリに保存しました")
            # ライブラリパネルを更新
            self.library_panel.reload_scene_library()

    def _on_about(self):
        """バージョン情報"""
        QMessageBox.about(
            self,
            "Pfft_makerについて",
            "Pfft_maker v0.1.0\n\n"
            "Stable Diffusion WebUI用プロンプト管理ツール\n\n"
            "Phase 5 完了 - テンプレート機能実装"
        )

    def showEvent(self, event):
        """ウィンドウ表示時"""
        super().showEvent(event)

        # 起動時チェック（一度だけ実行）
        if not self._startup_check_done:
            self._startup_check_done = True
            self._check_library_updates()

    def _check_library_updates(self):
        """ライブラリ更新チェック"""
        try:
            self.logger.info("起動時のライブラリ更新チェックを開始")

            # FileSyncManagerで更新チェック
            sync_manager = FileSyncManager(self.settings)

            if not sync_manager.has_updates():
                self.logger.info("更新はありません")
                return

            # 更新情報を取得
            updates = sync_manager.check_updates()
            summary = sync_manager.get_update_summary()

            self.logger.info(f"更新を検出:\n{summary}")

            # バナー表示
            self.update_banner.show_update(updates)

            # ステータスバーにも通知
            self.status_bar.showMessage("ライブラリに更新があります")

        except Exception as e:
            self.logger.error(f"更新チェック中にエラーが発生: {e}", exc_info=True)

    def _on_banner_sync_requested(self):
        """バナーから同期リクエスト"""
        self.logger.info("バナーから同期がリクエストされました")

        # ライブラリパネルの同期機能を呼び出す
        self.library_panel._on_sync_files()

    def _on_banner_dismissed(self):
        """バナーが閉じられた"""
        self.logger.info("更新通知バナーが閉じられました")
        self.status_bar.showMessage("準備完了")

    def closeEvent(self, event):
        """ウィンドウクローズ時"""
        if self._confirm_save():
            event.accept()
        else:
            event.ignore()
