"""プロンプトビルダー

シーンから最終プロンプトを構築します。
"""

import re
from typing import List, Optional

from models import Scene, Project, BlockType


class PromptBuilder:
    """プロンプトビルダー

    シーンのブロックリストから1行のプロンプトを構築。
    共通プロンプト（品質タグ、LoRAなど）の自動挿入にも対応。
    """

    def __init__(self, settings=None):
        """初期化

        Args:
            settings: 設定オブジェクト（Noneの場合は共通プロンプト挿入なし）
        """
        self.settings = settings

    def build_scene_prompt(self, scene: Scene, apply_common_prompts: bool = True) -> str:
        """シーンの最終プロンプトを構築

        Args:
            scene: シーンオブジェクト
            apply_common_prompts: 共通プロンプトを適用するか

        Returns:
            1行のプロンプト文字列

        Example:
            >>> scene = Scene(scene_id=1, scene_name="保健室", blocks=[...])
            >>> builder = PromptBuilder()
            >>> builder.build_scene_prompt(scene)
            "clothed masturbation, BREAK __posing/arm__, BREAK masterpiece"

        BREAK処理ルール (FR-018):
            - BREAK前: カンマあり（`prompt, BREAK`）
            - BREAK後: スペース区切り（`BREAK prompt`）
            - 連続カンマ・スペースは自動削除
        """
        if not scene.blocks:
            return ""

        result = []

        # 先頭の共通プロンプト
        if apply_common_prompts and self.settings:
            start_prompts = self.settings.get_common_prompts_by_position("start")
            for cp in start_prompts:
                result.append(cp.content)
                if cp.insert_break_after:
                    result.append(", BREAK")
                result.append(", ")

        for i, block in enumerate(scene.blocks):
            if block.type == BlockType.BREAK:
                result.append(", BREAK")
            else:
                # 改行を除去（1シーン = 1行にするため）
                content = block.content.strip()
                content = re.sub(r'[\r\n]+', ' ', content)  # 改行をスペースに置換
                content = re.sub(r'\s+', ' ', content).strip()  # 連続スペースを1つに

                if i == 0 and not result:
                    # 最初のブロック（共通プロンプトがない場合）
                    result.append(content)
                elif i == 0:
                    # 最初のブロック（共通プロンプトがある場合）
                    result.append(content)
                elif scene.blocks[i - 1].type == BlockType.BREAK:
                    # BREAK直後: スペース区切り
                    result.append(" " + content)
                else:
                    # 通常: カンマ+スペース区切り
                    result.append(", " + content)

        # 末尾の共通プロンプト
        if apply_common_prompts and self.settings:
            end_prompts = self.settings.get_common_prompts_by_position("end")
            for cp in end_prompts:
                result.append(", ")
                if cp.insert_break_after:
                    result.append("BREAK ")
                result.append(cp.content)

        prompt = "".join(result)

        # クリーンアップ
        prompt = re.sub(r',\s*,', ', ', prompt)  # 連続カンマ削除
        prompt = re.sub(r'\s+', ' ', prompt)     # 連続スペース削除
        prompt = prompt.strip().rstrip(',')      # 先頭・末尾の空白とカンマ削除

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
