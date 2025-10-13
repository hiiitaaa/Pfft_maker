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
        logger.info("Qtアプリケーション初期化完了")

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
