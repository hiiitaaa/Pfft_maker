"""テンプレート機能のテスト

FR-013: テンプレート機能の動作確認用スクリプト
"""

from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models import Project, Scene, Block, BlockType, CommonPrompt, ProjectTemplate
from core.template_manager import TemplateManager
from utils.logger import get_logger


def test_template_models():
    """テンプレートモデルのテスト"""
    print("\n=== テンプレートモデルのテスト ===\n")

    # ProjectTemplate作成
    template = ProjectTemplate.create_new(
        name="テストテンプレート",
        description="テスト用のテンプレート",
        template_type="structure"
    )

    print(f"OK ProjectTemplate作成: {template.name}")
    print(f"  ID: {template.id}")
    print(f"  タイプ: {template.template_type}")

    # 辞書に変換
    template_dict = template.to_dict()
    print(f"OK 辞書に変換: {len(template_dict)} keys")

    # 辞書から復元
    restored = ProjectTemplate.from_dict(template_dict)
    print(f"OK 辞書から復元: {restored.name}")

    assert restored.name == template.name, "復元後の名前が一致しない"
    assert restored.template_type == template.template_type, "復元後のタイプが一致しない"

    print("\n[SUCCESS] テンプレートモデルのテストが完了しました\n")


def test_template_manager():
    """TemplateManagerのテスト"""
    print("\n=== TemplateManagerのテスト ===\n")

    # 一時ディレクトリ
    test_dir = Path(__file__).parent / "test_data" / "templates"
    test_dir.mkdir(parents=True, exist_ok=True)

    # TemplateManager作成
    manager = TemplateManager(test_dir)
    print(f"✓ TemplateManager作成: {test_dir}")

    # テストプロジェクト作成
    project = Project.create_new("テストプロジェクト", "テスト用")

    # シーン追加
    for i in range(1, 4):
        scene = Scene(
            scene_id=i,
            scene_name=f"テストシーン{i}",
            is_completed=False
        )

        # ブロック追加
        scene.add_block(Block(
            block_id=1,
            type=BlockType.FIXED_TEXT,
            content="test prompt"
        ))
        scene.add_block(Block(
            block_id=2,
            type=BlockType.BREAK,
            content=""
        ))
        scene.add_block(Block(
            block_id=3,
            type=BlockType.WILDCARD,
            content="__test__"
        ))

        project.add_scene(scene)

    print(f"✓ テストプロジェクト作成: {len(project.scenes)}シーン")

    # 構成テンプレートとして保存
    template1 = manager.save_template_from_project(
        project,
        "構成テンプレート",
        "プロンプト内容なし",
        "structure"
    )
    print(f"✓ 構成テンプレート保存: {template1.name}")

    # 完全テンプレートとして保存
    template2 = manager.save_template_from_project(
        project,
        "完全テンプレート",
        "プロンプト内容あり",
        "complete"
    )
    print(f"✓ 完全テンプレート保存: {template2.name}")

    # テンプレート一覧取得
    all_templates = manager.get_all_templates()
    print(f"✓ テンプレート一覧取得: {len(all_templates)}件")

    for t in all_templates:
        print(f"  - {t.name} ({t.template_type}, {t.scene_count}シーン)")

    # 構成テンプレートからプロジェクト作成
    new_project1 = manager.create_project_from_template(
        template1,
        "構成から作成したプロジェクト"
    )
    print(f"✓ 構成テンプレートから作成: {new_project1.name}")
    print(f"  シーン数: {len(new_project1.scenes)}")
    print(f"  シーン1のブロック数: {len(new_project1.scenes[0].blocks)}")
    print(f"  シーン1のブロック1の内容: '{new_project1.scenes[0].blocks[0].content}'")

    # 完全テンプレートからプロジェクト作成
    new_project2 = manager.create_project_from_template(
        template2,
        "完全から作成したプロジェクト"
    )
    print(f"✓ 完全テンプレートから作成: {new_project2.name}")
    print(f"  シーン数: {len(new_project2.scenes)}")
    print(f"  シーン1のブロック1の内容: '{new_project2.scenes[0].blocks[0].content}'")

    # 検証
    assert len(new_project1.scenes) == len(project.scenes), "シーン数が一致しない"
    assert new_project1.scenes[0].blocks[0].content == "", "構成テンプレートの内容が空でない"
    assert new_project2.scenes[0].blocks[0].content == "test prompt", "完全テンプレートの内容が一致しない"

    # 使用回数の確認
    print(f"✓ テンプレート使用回数: {template1.usage_count}")
    assert template1.usage_count == 1, "使用回数が更新されていない"

    # テンプレート削除
    success = manager.delete_template(template1.id)
    print(f"✓ テンプレート削除: {success}")

    remaining = manager.get_all_templates()
    print(f"✓ 残りのテンプレート: {len(remaining)}件")

    assert len(remaining) == 1, "削除後のテンプレート数が正しくない"

    print("\n✅ TemplateManagerのテストが完了しました\n")


def test_template_save_load():
    """テンプレートの保存・読み込みテスト"""
    print("\n=== テンプレート保存・読み込みテスト ===\n")

    test_dir = Path(__file__).parent / "test_data" / "templates2"
    test_dir.mkdir(parents=True, exist_ok=True)

    # マネージャー作成
    manager1 = TemplateManager(test_dir)

    # プロジェクト作成
    project = Project.create_new("保存テスト", "")
    scene = Scene(scene_id=1, scene_name="シーン1")
    scene.add_block(Block(block_id=1, type=BlockType.FIXED_TEXT, content="test"))
    project.add_scene(scene)

    # テンプレート保存
    template = manager1.save_template_from_project(
        project, "保存テスト", "説明", "structure"
    )
    print(f"✓ テンプレート保存: {template.name}")

    # 新しいマネージャーで読み込み
    manager2 = TemplateManager(test_dir)
    loaded_templates = manager2.get_all_templates()

    print(f"✓ テンプレート読み込み: {len(loaded_templates)}件")

    assert len(loaded_templates) == 1, "読み込んだテンプレート数が正しくない"
    assert loaded_templates[0].name == template.name, "読み込んだテンプレート名が一致しない"

    print("\n✅ 保存・読み込みテストが完了しました\n")


def main():
    """メインテスト実行"""
    print("\n" + "="*60)
    print("  FR-013: テンプレート機能のテスト")
    print("="*60)

    # ロガー取得
    logger = get_logger()

    try:
        # テスト実行
        test_template_models()
        test_template_manager()
        test_template_save_load()

        print("\n" + "="*60)
        print("  ✅ すべてのテストが成功しました！")
        print("="*60 + "\n")

        return True

    except Exception as e:
        logger.error(f"テスト失敗: {e}", exc_info=True)
        print("\n" + "="*60)
        print(f"  ❌ テストが失敗しました: {e}")
        print("="*60 + "\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
