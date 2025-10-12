"""プロンプトビルダー

シーンから最終プロンプトを構築します。
"""

import re
from typing import List

from ..models import Scene, Project, BlockType


class PromptBuilder:
    """プロンプトビルダー

    シーンのブロックリストから1行のプロンプトを構築。
    """

    def build_scene_prompt(self, scene: Scene) -> str:
        """シーンの最終プロンプトを構築

        Args:
            scene: シーンオブジェクト

        Returns:
            1行のプロンプト文字列（カンマ区切り）

        Example:
            >>> scene = Scene(scene_id=1, scene_name="保健室", blocks=[...])
            >>> builder = PromptBuilder()
            >>> builder.build_scene_prompt(scene)
            "clothed masturbation, BREAK, __posing/arm__, BREAK, masterpiece"
        """
        parts = []

        for block in scene.blocks:
            if block.type == BlockType.BREAK:
                parts.append("BREAK")
            else:
                # プロンプト内容をそのまま追加
                parts.append(block.content.strip())

        # カンマ + スペース区切りで結合
        prompt = ", ".join(parts)

        # 連続カンマを削除（念のため）
        prompt = re.sub(r',\s*,', ', ', prompt)

        return prompt

    def build_all_prompts(
        self,
        project: Project,
        include_comment: bool = False,
        completed_only: bool = False
    ) -> List[str]:
        """全シーンのプロンプトを構築

        Args:
            project: プロジェクトオブジェクト
            include_comment: シーン番号コメントを含めるか
            completed_only: 完成シーンのみを含めるか

        Returns:
            プロンプトの行リスト
        """
        lines = []

        for scene in project.scenes:
            # 完成シーンのみフィルタ
            if completed_only and not scene.is_completed:
                continue

            # コメント追加（オプション）
            if include_comment:
                lines.append(f"# Scene {scene.scene_id}: {scene.scene_name}")

            # プロンプト追加
            prompt = self.build_scene_prompt(scene)
            lines.append(prompt)

        return lines

    def validate_blocks(self, scene: Scene) -> tuple[bool, str]:
        """ブロックのバリデーション

        Args:
            scene: シーンオブジェクト

        Returns:
            (有効かどうか, エラーメッセージ)
        """
        blocks = scene.blocks

        # 空チェック
        if not blocks:
            return False, "ブロックが1つもありません"

        # 連続BREAKチェック
        for i in range(len(blocks) - 1):
            if (blocks[i].type == BlockType.BREAK and
                blocks[i + 1].type == BlockType.BREAK):
                return False, "連続したBREAKは使用できません"

        return True, ""

    def export_to_file(
        self,
        project: Project,
        output_path: str,
        include_comment: bool = False,
        completed_only: bool = False
    ):
        """プロンプトをファイルに出力

        Args:
            project: プロジェクトオブジェクト
            output_path: 出力ファイルパス
            include_comment: シーン番号コメントを含めるか
            completed_only: 完成シーンのみを含めるか
        """
        from pathlib import Path

        lines = self.build_all_prompts(project, include_comment, completed_only)

        # ファイルに書き込み
        output_file = Path(output_path)
        output_file.write_text("\n".join(lines), encoding="utf-8")
