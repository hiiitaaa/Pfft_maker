"""ライブラリマネージャーのテスト

ワイルドカードファイルの読み込みと保存をテストします。
"""

import sys
from pathlib import Path
import shutil

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.library_manager import LibraryManager
from config.settings import Settings


def create_test_wildcards():
    """テスト用のワイルドカードファイルを作成"""
    test_dir = Path(__file__).parent / "test_wildcards"

    # ディレクトリをクリーン
    if test_dir.exists():
        shutil.rmtree(test_dir)

    test_dir.mkdir()

    # パターン1: 番号+テーブル型
    (test_dir / "test1.txt").write_text(
        "1→| 教室 | classroom interior, desks in rows |\n"
        "2→| 保健室 | school infirmary, beds with curtain |\n",
        encoding="utf-8"
    )

    # パターン2: テーブル型
    (test_dir / "test2.txt").write_text(
        "| 屋上 | school rooftop, fence, blue sky |\n"
        "| プール | swimming pool, water, tiles |\n",
        encoding="utf-8"
    )

    # パターン3: 番号付き型
    (test_dir / "test3.txt").write_text(
        "14→clothed masturbation\n"
        "25→(deepthroat, irrumatio)\n",
        encoding="utf-8"
    )

    # パターン4: シンプル型
    posing_dir = test_dir / "posing"
    posing_dir.mkdir(exist_ok=True)
    (posing_dir / "arm.txt").write_text(
        "arms crossed\n"
        "arms up\n"
        "arms behind back\n",
        encoding="utf-8"
    )

    print(f"[OK] Created test wildcard files in {test_dir}")
    return test_dir


def test_library_manager():
    """ライブラリマネージャーのテスト"""
    print("=== Library Manager Test ===\n")

    # テスト用ワイルドカードファイル作成
    test_wildcards_dir = create_test_wildcards()

    # テスト用設定
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)

    settings = Settings()
    settings.source_wildcard_dir = str(test_wildcards_dir)
    settings.local_wildcard_dir = str(test_data_dir / "wildcards")
    settings.data_dir = str(test_data_dir)
    settings.save()

    # ライブラリマネージャー作成
    manager = LibraryManager(settings)

    # 進捗コールバック
    def on_progress(current, total, message):
        print(f"Progress: [{current}/{total}] {message}")

    # ライブラリ再構築
    print("\n--- Rebuilding library ---")
    success = manager.rebuild_library(force_copy=True, progress_callback=on_progress)

    if not success:
        print("[ERROR] Failed to rebuild library")
        return False

    # プロンプト取得
    prompts = manager.get_prompts()
    print(f"\n[OK] Library built: {len(prompts)} prompts")

    # プロンプト内容を表示
    print("\n--- Prompts ---")
    for prompt in prompts[:10]:  # 最初の10件のみ表示
        print(f"  {prompt.id}: {prompt.label_ja or prompt.prompt[:30]} ({prompt.category})")

    # CSV保存テスト
    print("\n--- Testing CSV save/load ---")
    csv_path = settings.get_library_csv_path()
    print(f"CSV path: {csv_path}")

    # CSV読み込み
    loaded_prompts = manager.load_from_csv()
    print(f"[OK] Loaded {len(loaded_prompts)} prompts from CSV")

    # 検証
    if len(prompts) == len(loaded_prompts):
        print("[OK] Prompt count matches")
    else:
        print(f"[ERROR] Prompt count mismatch: {len(prompts)} != {len(loaded_prompts)}")
        return False

    print("\n" + "=" * 50)
    print("[SUCCESS] All tests passed!")
    print("=" * 50)

    # クリーンアップ
    print("\n--- Cleanup ---")
    if test_wildcards_dir.exists():
        shutil.rmtree(test_wildcards_dir)
        print(f"[OK] Removed {test_wildcards_dir}")

    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)
        print(f"[OK] Removed {test_data_dir}")

    return True


if __name__ == "__main__":
    try:
        success = test_library_manager()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
