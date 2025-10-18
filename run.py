"""Pfft_maker 起動スクリプト

プロジェクトルートから実行するための起動スクリプト。
"""

import sys
import os
from pathlib import Path

# Windows環境でのUTF-8対応（コンソール出力用）
if sys.platform == "win32":
    # Python 3.7以降: UTF-8モードを有効化
    if hasattr(sys, "set_int_max_str_digits"):  # Python 3.11+
        os.environ["PYTHONUTF8"] = "1"
    # コンソールのコードページをUTF-8に設定
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)  # UTF-8
        kernel32.SetConsoleOutputCP(65001)  # UTF-8

        # 開発時のみコンソールウィンドウを最小化（EXE化時は不要）
        if not getattr(sys, 'frozen', False):
            SW_MINIMIZE = 6
            console_window = kernel32.GetConsoleWindow()
            if console_window:
                user32 = ctypes.windll.user32
                user32.ShowWindow(console_window, SW_MINIMIZE)
    except:
        pass

# srcディレクトリをパスに追加
if getattr(sys, 'frozen', False):
    # PyInstallerでEXE化されている場合
    application_path = Path(sys.executable).parent
else:
    # 開発環境
    application_path = Path(__file__).parent

src_path = application_path / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(application_path))

# メイン処理をインポートして実行
from main import main

if __name__ == "__main__":
    main()
