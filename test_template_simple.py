"""テンプレート機能の簡易テスト"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models import Project, Scene, Block, BlockType, ProjectTemplate
from core.template_manager import TemplateManager


def main():
    print("\n" + "="*60)
    print("  FR-013: Template Feature Test")
    print("="*60 + "\n")

    # Test directory
    test_dir = Path(__file__).parent / "test_data" / "templates_test"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create TemplateManager
    manager = TemplateManager(test_dir)
    print(f"[1/5] TemplateManager created: {test_dir}")

    # Create test project
    project = Project.create_new("Test Project", "For testing")
    for i in range(1, 4):
        scene = Scene(scene_id=i, scene_name=f"Scene {i}")
        scene.add_block(Block(block_id=1, type=BlockType.FIXED_TEXT, content="test"))
        scene.add_block(Block(block_id=2, type=BlockType.BREAK, content=""))
        project.add_scene(scene)
    print(f"[2/5] Test project created: {len(project.scenes)} scenes")

    # Save as structure template
    template1 = manager.save_template_from_project(
        project, "Structure Template", "No content", "structure"
    )
    print(f"[3/5] Structure template saved: {template1.name}")

    # Save as complete template
    template2 = manager.save_template_from_project(
        project, "Complete Template", "With content", "complete"
    )
    print(f"[4/5] Complete template saved: {template2.name}")

    # Load templates
    templates = manager.get_all_templates()
    print(f"[5/5] Templates loaded: {len(templates)} templates")

    for t in templates:
        print(f"  - {t.name} ({t.template_type}, {t.scene_count} scenes)")

    # Create project from structure template
    new_project1 = manager.create_project_from_template(template1, "From Structure")
    assert new_project1.scenes[0].blocks[0].content == "", "Structure template should have empty content"
    print(f"\n[TEST] Structure template: PASS")

    # Create project from complete template
    new_project2 = manager.create_project_from_template(template2, "From Complete")
    assert new_project2.scenes[0].blocks[0].content == "test", "Complete template should have content"
    print(f"[TEST] Complete template: PASS")

    # Usage count
    assert template1.usage_count == 1, "Usage count should be 1"
    print(f"[TEST] Usage count: PASS")

    print("\n" + "="*60)
    print("  ALL TESTS PASSED!")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
