"""Pfft_maker メインエントリーポイント

アプリケーションの起動処理。
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from ui import MainWindow


def main():
    """メイン処理"""
    # Qtアプリケーション初期化
    app = QApplication(sys.argv)

    # アプリケーション情報設定
    app.setApplicationName("Pfft_maker")
    app.setOrganizationName("Pfft_maker Development Team")
    app.setApplicationVersion("0.1.0")

    # メインウィンドウ表示
    window = MainWindow()
    window.show()

    # イベントループ開始
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
