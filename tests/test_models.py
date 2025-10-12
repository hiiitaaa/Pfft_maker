"""データモデルのテスト

基本的な動作確認を行います。
"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models import Block, BlockType, Scene, Project


def test_block_creation():
    """ブロック作成のテスト"""
    print("=== ブロック作成テスト ===")

    # 固定テキストブロック
    block1 = Block(
        block_id=1,
        type=BlockType.FIXED_TEXT,
        content="clothed masturbation"
    )
    print(f"ブロック1: {block1.content} (type: {block1.type.value})")

    # ワイルドカードブロック
    block2 = Block(
        block_id=2,
        type=BlockType.WILDCARD,
        content="__posing/arm__"
    )
    print(f"ブロック2: {block2.content} (wildcard: {block2.is_wildcard_block()})")

    # BREAKブロック
    block3 = Block(
        block_id=3,
        type=BlockType.BREAK,
        content=""
    )
    print(f"ブロック3: BREAK")

    print("[OK] ブロック作成テスト成功\n")
    return [block1, block2, block3]


def test_scene_operations(blocks):
    """シーン操作のテスト"""
    print("=== シーン操作テスト ===")

    # シーン作成
    scene = Scene(scene_id=1, scene_name="保健室")

    # ブロック追加
    for block in blocks:
        scene.add_block(block)

    print(f"シーン名: {scene.scene_name}")
    print(f"ブロック数: {len(scene.blocks)}")

    # バリデーション
    is_valid, error_msg = scene.validate()
    print(f"バリデーション: {'[OK]' if is_valid else f'[NG] {error_msg}'}")

    # JSON変換
    scene_dict = scene.to_dict()
    print(f"JSON変換: {len(scene_dict)} keys")

    # 復元
    scene_restored = Scene.from_dict(scene_dict)
    print(f"復元成功: {scene_restored.scene_name}")

    print("[OK] シーン操作テスト成功\n")
    return scene


def test_project_operations(scene):
    """プロジェクト操作のテスト"""
    print("=== プロジェクト操作テスト ===")

    # プロジェクト作成
    project = Project.create_new("テストプロジェクト", "動作確認用")

    # シーン追加
    project.add_scene(scene)

    print(f"プロジェクト名: {project.name}")
    print(f"シーン数: {len(project.scenes)}")

    # バリデーション
    is_valid, error_msg = project.validate()
    print(f"バリデーション: {'[OK]' if is_valid else f'[NG] {error_msg}'}")

    # JSON変換
    project_dict = project.to_dict()
    print(f"JSON変換: {len(project_dict)} keys")

    # 復元
    project_restored = Project.from_dict(project_dict)
    print(f"復元成功: {project_restored.name}")
    print(f"復元シーン数: {len(project_restored.scenes)}")

    print("[OK] プロジェクト操作テスト成功\n")
    return project


def test_json_persistence(project):
    """JSON永続化のテスト"""
    print("=== JSON永続化テスト ===")

    # JSON保存
    json_str = project.to_json()
    print(f"JSON文字列長: {len(json_str)} chars")
    print(f"JSON preview:\n{json_str[:200]}...\n")

    # ファイル保存
    test_file = Path(__file__).parent / "test_project.json"
    test_file.write_text(json_str, encoding="utf-8")
    print(f"ファイル保存: {test_file}")

    # ファイル読み込み
    loaded_json = test_file.read_text(encoding="utf-8")
    import json
    loaded_dict = json.loads(loaded_json)

    # 復元
    project_loaded = Project.from_dict(loaded_dict)
    print(f"復元成功: {project_loaded.name}")

    # クリーンアップ
    test_file.unlink()
    print("[OK] JSON永続化テスト成功\n")


def main():
    """メイン処理"""
    print("=== Pfft_maker データモデル テスト ===\n")

    try:
        # テスト実行
        blocks = test_block_creation()
        scene = test_scene_operations(blocks)
        project = test_project_operations(scene)
        test_json_persistence(project)

        print("=" * 50)
        print("[OK] すべてのテストが成功しました！")
        print("=" * 50)

    except Exception as e:
        print(f"\n[NG] テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
