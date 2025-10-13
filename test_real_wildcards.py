"""実際のワイルドカードファイルでテスト

GUIを起動せずにライブラリマネージャーをテストします。
"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.library_manager import LibraryManager
from config.settings import Settings


def main():
    """メイン処理"""
    print("=== Real Wildcard Files Test ===\n")

    # 設定読み込み
    settings = Settings()

    print(f"Source directory: {settings.source_wildcard_dir}")
    print(f"Local directory: {settings.local_wildcard_dir}")
    print(f"Data directory: {settings.data_dir}\n")

    # 元ディレクトリの存在確認
    source_dir = settings.get_source_dir()
    if not source_dir.exists():
        print(f"[ERROR] Source directory not found: {source_dir}")
        print("\nPlease check the path in settings.")
        return False

    # ファイル数を確認
    txt_files = list(source_dir.glob("**/*.txt"))
    print(f"Found {len(txt_files)} txt files in source directory\n")

    # ライブラリマネージャー作成
    manager = LibraryManager(settings)

    # 進捗コールバック
    def on_progress(current, total, message):
        if total > 0:
            percent = int((current / total) * 100)
            print(f"[{percent:3d}%] {message}")
        else:
            print(f"       {message}")

    # ライブラリ再構築（強制コピー）
    print("--- Rebuilding library (this may take a while) ---\n")
    success = manager.rebuild_library(force_copy=True, progress_callback=on_progress)

    if not success:
        print("\n[ERROR] Failed to rebuild library")
        return False

    # プロンプト取得
    prompts = manager.get_prompts()
    print(f"\n[OK] Library built: {len(prompts)} prompts")

    # カテゴリ別集計
    categories = {}
    for prompt in prompts:
        category = prompt.category or "その他"
        categories[category] = categories.get(category, 0) + 1

    print("\n--- Categories ---")
    for category, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {category}: {count} prompts")

    # サンプル表示（各カテゴリから1件ずつ）
    print("\n--- Sample prompts (first 10) ---")
    shown_categories = set()
    sample_count = 0
    for prompt in prompts:
        if sample_count >= 10:
            break
        category = prompt.category or "その他"
        if category not in shown_categories:
            shown_categories.add(category)
            label = prompt.label_ja or prompt.prompt[:50]
            print(f"  [{category}] {label}")
            print(f"      ID: {prompt.id}")
            print(f"      File: {prompt.source_file}")
            print(f"      Prompt: {prompt.prompt[:80]}...")
            print()
            sample_count += 1

    # CSV保存確認
    csv_path = settings.get_library_csv_path()
    if csv_path.exists():
        print(f"[OK] CSV saved: {csv_path}")
        print(f"     File size: {csv_path.stat().st_size / 1024:.1f} KB")

    print("\n" + "=" * 50)
    print("[SUCCESS] Test completed!")
    print("=" * 50)

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
