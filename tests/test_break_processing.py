"""BREAK処理のテスト

FR-018のBREAK処理ルールが正しく実装されているか確認します。
"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import Scene, Block, BlockType
from core.prompt_builder import PromptBuilder


def test_break_processing():
    """BREAK処理テスト

    FR-018のルール:
    - BREAK前: カンマあり（`prompt, BREAK`）
    - BREAK後: スペース区切り（`BREAK prompt`）
    """
    print("=== BREAK Processing Test ===\n")

    builder = PromptBuilder()

    # テストケース1: 通常のBREAK処理
    print("Test 1: 通常のBREAK処理")
    scene1 = Scene(scene_id=1, scene_name="テスト1", blocks=[
        Block(block_id=1, type=BlockType.FIXED_TEXT, content="clothed masturbation"),
        Block(block_id=2, type=BlockType.BREAK, content=""),
        Block(block_id=3, type=BlockType.WILDCARD, content="__posing/arm__"),
        Block(block_id=4, type=BlockType.BREAK, content=""),
        Block(block_id=5, type=BlockType.FIXED_TEXT, content="masterpiece, best quality"),
    ])

    prompt1 = builder.build_scene_prompt(scene1)
    expected1 = "clothed masturbation, BREAK __posing/arm__, BREAK masterpiece, best quality"

    print(f"  入力: clothed masturbation → BREAK → __posing/arm__ → BREAK → masterpiece, best quality")
    print(f"  期待: {expected1}")
    print(f"  結果: {prompt1}")
    print(f"  {'[PASS]' if prompt1 == expected1 else '[NG] FAIL'}\n")

    # テストケース2: 最初がBREAK
    print("Test 2: 最初がBREAK")
    scene2 = Scene(scene_id=2, scene_name="テスト2", blocks=[
        Block(block_id=1, type=BlockType.BREAK, content=""),
        Block(block_id=2, type=BlockType.FIXED_TEXT, content="school infirmary"),
        Block(block_id=3, type=BlockType.BREAK, content=""),
        Block(block_id=4, type=BlockType.FIXED_TEXT, content="best quality"),
    ])

    prompt2 = builder.build_scene_prompt(scene2)
    expected2 = ", BREAK school infirmary, BREAK best quality"

    print(f"  入力: BREAK → school infirmary → BREAK → best quality")
    print(f"  期待: {expected2}")
    print(f"  結果: {prompt2}")
    print(f"  {'[PASS]' if prompt2 == expected2 else '[FAIL]'}\n")

    # テストケース3: 最後がBREAK
    print("Test 3: 最後がBREAK")
    scene3 = Scene(scene_id=3, scene_name="テスト3", blocks=[
        Block(block_id=1, type=BlockType.FIXED_TEXT, content="exhibitionism"),
        Block(block_id=2, type=BlockType.BREAK, content=""),
        Block(block_id=3, type=BlockType.FIXED_TEXT, content="school rooftop"),
        Block(block_id=4, type=BlockType.BREAK, content=""),
    ])

    prompt3 = builder.build_scene_prompt(scene3)
    expected3 = "exhibitionism, BREAK school rooftop, BREAK"

    print(f"  入力: exhibitionism → BREAK → school rooftop → BREAK")
    print(f"  期待: {expected3}")
    print(f"  結果: {prompt3}")
    print(f"  {'[PASS]' if prompt3 == expected3 else '[FAIL]'}\n")

    # テストケース4: BREAKなし
    print("Test 4: BREAKなし（通常のカンマ区切り）")
    scene4 = Scene(scene_id=4, scene_name="テスト4", blocks=[
        Block(block_id=1, type=BlockType.FIXED_TEXT, content="standing"),
        Block(block_id=2, type=BlockType.FIXED_TEXT, content="spread legs"),
        Block(block_id=3, type=BlockType.WILDCARD, content="__背景/学校__"),
    ])

    prompt4 = builder.build_scene_prompt(scene4)
    expected4 = "standing, spread legs, __背景/学校__"

    print(f"  入力: standing → spread legs → __背景/学校__")
    print(f"  期待: {expected4}")
    print(f"  結果: {prompt4}")
    print(f"  {'[PASS]' if prompt4 == expected4 else '[FAIL]'}\n")

    # テストケース5: 複数のワイルドカード
    print("Test 5: 複数のワイルドカード")
    scene5 = Scene(scene_id=5, scene_name="テスト5", blocks=[
        Block(block_id=1, type=BlockType.WILDCARD, content="__tipo_play__"),
        Block(block_id=2, type=BlockType.BREAK, content=""),
        Block(block_id=3, type=BlockType.WILDCARD, content="__キャラ/SAYA__"),
        Block(block_id=4, type=BlockType.WILDCARD, content="__posing/arm__"),
        Block(block_id=5, type=BlockType.BREAK, content=""),
        Block(block_id=6, type=BlockType.FIXED_TEXT, content="amazing quality"),
    ])

    prompt5 = builder.build_scene_prompt(scene5)
    expected5 = "__tipo_play__, BREAK __キャラ/SAYA__, __posing/arm__, BREAK amazing quality"

    print(f"  入力: __tipo_play__ → BREAK → __キャラ/SAYA__ → __posing/arm__ → BREAK → amazing quality")
    print(f"  期待: {expected5}")
    print(f"  結果: {prompt5}")
    print(f"  {'[PASS]' if prompt5 == expected5 else '[FAIL]'}\n")

    # 結果サマリー
    results = [
        prompt1 == expected1,
        prompt2 == expected2,
        prompt3 == expected3,
        prompt4 == expected4,
        prompt5 == expected5,
    ]

    passed = sum(results)
    total = len(results)

    print("=" * 50)
    print(f"結果: {passed}/{total} テスト合格")
    print("=" * 50)

    return all(results)


if __name__ == "__main__":
    try:
        success = test_break_processing()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
