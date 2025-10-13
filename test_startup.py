"""起動テスト用スクリプト

GUIを起動せずにインポートのみテストする。
"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("Testing imports...")

try:
    from models import Project, Scene, Block, Prompt
    print("[OK] models imported")

    from core.wildcard_parser import WildcardParser
    print("[OK] core.wildcard_parser imported")

    from core.prompt_builder import PromptBuilder
    print("[OK] core.prompt_builder imported")

    from ui import MainWindow
    print("[OK] ui.MainWindow imported")

    print("\n" + "="*50)
    print("[SUCCESS] All imports successful!")
    print("Application is ready to run.")
    print("="*50)

except Exception as e:
    print(f"\n[ERROR] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
