"""Pfft_maker 起動スクリプト

プロジェクトルートから実行するための起動スクリプト。
"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# メイン処理をインポートして実行
from main import main

if __name__ == "__main__":
    main()
