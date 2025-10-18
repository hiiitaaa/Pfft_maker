"""Pfft_maker メインエントリーポイント

アプリケーションの起動処理。
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox

from ui import MainWindow
from utils.logger import get_logger


def main():
    """メイン処理"""
    # ロガー初期化
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("Pfft_maker アプリケーション起動")
    logger.info(f"Python: {sys.version}")
    logger.info(f"作業ディレクトリ: {Path.cwd()}")
    logger.info("=" * 60)

    try:
        # Qtアプリケーション初期化
        logger.info("Qtアプリケーションを初期化中...")
        app = QApplication(sys.argv)

        # アプリケーション情報設定
        app.setApplicationName("Pfft_maker")
        app.setOrganizationName("Pfft_maker Development Team")
        app.setApplicationVersion("0.1.0")

        # 日本語フォント設定（文字化け対策）
        from PyQt6.QtGui import QFont
        font = QFont("Yu Gothic UI", 9)  # Windows 10/11の標準日本語フォント
        app.setFont(font)

        logger.info("Qtアプリケーション初期化完了")

        # 初回起動チェック
        from config.settings import Settings
        settings = Settings()
        is_first_run = not settings.config_path.exists()

        if is_first_run:
            logger.info("初回起動を検出: ウェルカムダイアログを表示")
            from ui.welcome_dialog import WelcomeDialog
            welcome = WelcomeDialog(settings)
            if welcome.exec() != WelcomeDialog.DialogCode.Accepted:
                logger.info("ユーザーがセットアップをキャンセルしました")
                sys.exit(0)
            logger.info("初回セットアップ完了")
        else:
            # 起動時の自動バックアップ（初回起動以外）
            try:
                from core.backup_manager import BackupManager
                backup_manager = BackupManager(
                    settings.get_data_dir(),
                    Settings.get_default_backup_dir()
                )
                if backup_manager.auto_backup_on_startup():
                    logger.info("起動時の自動バックアップを作成しました")
            except Exception as e:
                logger.warning(f"自動バックアップに失敗しましたが、アプリは続行します: {e}")

        # メインウィンドウ表示
        logger.info("メインウィンドウを作成中...")
        window = MainWindow()
        window.show()
        logger.info("メインウィンドウ表示完了")

        # イベントループ開始
        logger.info("イベントループを開始します")
        exit_code = app.exec()
        logger.info(f"アプリケーション終了 (終了コード: {exit_code})")
        sys.exit(exit_code)

    except Exception as e:
        logger.exception("アプリケーション起動中に予期しないエラーが発生しました")

        # ユーザーにエラーを通知
        try:
            QMessageBox.critical(
                None,
                "起動エラー",
                f"アプリケーションの起動中にエラーが発生しました:\n\n{e}\n\n"
                f"詳細はログファイルを確認してください。\n"
                f"ログ: {Path('logs').absolute()}"
            )
        except:
            # QApplication初期化前にエラーが発生した場合
            print(f"[CRITICAL] {e}")

        sys.exit(1)


if __name__ == "__main__":
    main()
