"""テンプレート管理

プロジェクトテンプレートの保存・読み込み・管理を行います。
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from models import (
    Project, Scene, Block, BlockType,
    ProjectTemplate, SceneTemplate, BlockTemplate
)
from utils.logger import get_logger


class TemplateManager:
    """テンプレート管理クラス

    templates.jsonファイルを読み書きし、
    テンプレートの保存・読み込み・削除を管理します。
    """

    def __init__(self, data_dir: Path):
        """初期化

        Args:
            data_dir: データディレクトリのパス
        """
        self.data_dir = data_dir
        self.templates_file = data_dir / "templates.json"
        self.templates: List[ProjectTemplate] = []
        self.logger = get_logger()

        # テンプレートファイルが存在すれば読み込み
        if self.templates_file.exists():
            self.load()

    def save_template_from_project(
        self,
        project: Project,
        name: str,
        description: str,
        template_type: str
    ) -> ProjectTemplate:
        """プロジェクトからテンプレートを保存

        Args:
            project: プロジェクトオブジェクト
            name: テンプレート名
            description: 説明
            template_type: "structure" or "complete"

        Returns:
            作成されたProjectTemplateオブジェクト
        """
        # テンプレートIDを生成
        template_id = self._get_next_id()

        # シーンテンプレートを作成
        scene_templates = []
        for scene in project.scenes:
            # ブロックテンプレートを作成
            block_templates = []
            for block in scene.blocks:
                # 構成テンプレートの場合は内容を空にする
                content = "" if template_type == "structure" else block.content

                block_template = BlockTemplate(
                    type=block.type.value,
                    content=content
                )
                block_templates.append(block_template)

            # シーン名をプレースホルダーにするかそのまま保持
            scene_name = "" if template_type == "structure" else scene.scene_name

            scene_template = SceneTemplate(
                scene_name=scene_name,
                block_templates=block_templates
            )
            scene_templates.append(scene_template)

        # 共通プロンプト設定をコピー
        common_prompts = [cp.to_dict() for cp in project.common_prompts]

        # テンプレート作成
        template = ProjectTemplate(
            id=template_id,
            name=name,
            description=description,
            template_type=template_type,
            scene_count=len(project.scenes),
            scene_templates=scene_templates,
            common_prompts=common_prompts
        )

        self.templates.append(template)
        self.save()

        self.logger.info(f"テンプレート保存: {name} ({template_type}, {len(scene_templates)}シーン)")
        return template

    def create_project_from_template(
        self,
        template: ProjectTemplate,
        project_name: str
    ) -> Project:
        """テンプレートからプロジェクトを作成

        Args:
            template: テンプレートオブジェクト
            project_name: 新規プロジェクト名

        Returns:
            作成されたProjectオブジェクト
        """
        from models import CommonPrompt

        # プロジェクト作成
        project = Project(
            name=project_name,
            created_date=datetime.now(),
            last_modified=datetime.now(),
            description=f"テンプレート「{template.name}」から作成"
        )

        # 共通プロンプト設定を復元
        project.common_prompts = [
            CommonPrompt.from_dict(cp)
            for cp in template.common_prompts
        ]

        # シーンを作成
        for i, scene_template in enumerate(template.scene_templates, start=1):
            scene = Scene(
                scene_id=i,
                scene_name=scene_template.scene_name or f"シーン{i}",
                is_completed=False
            )

            # ブロックを作成
            for j, block_template in enumerate(scene_template.block_templates, start=1):
                block_type = BlockType(block_template.type)

                block = Block(
                    block_id=j,
                    type=block_type,
                    content=block_template.content
                )
                scene.add_block(block)

            project.add_scene(scene)

        # 使用履歴を記録
        template.increment_usage()
        self.save()

        self.logger.info(
            f"テンプレートから作成: {template.name} -> {project_name} "
            f"({len(project.scenes)}シーン)"
        )
        return project

    def get_all_templates(self) -> List[ProjectTemplate]:
        """全テンプレートを取得

        Returns:
            テンプレートのリスト
        """
        return self.templates

    def get_template_by_id(self, template_id: str) -> Optional[ProjectTemplate]:
        """IDでテンプレートを取得

        Args:
            template_id: テンプレートID

        Returns:
            テンプレートオブジェクト、見つからない場合None
        """
        for template in self.templates:
            if template.id == template_id:
                return template
        return None

    def delete_template(self, template_id: str) -> bool:
        """テンプレートを削除

        Args:
            template_id: テンプレートID

        Returns:
            削除に成功したかどうか
        """
        for i, template in enumerate(self.templates):
            if template.id == template_id:
                deleted_name = template.name
                del self.templates[i]
                self.save()
                self.logger.info(f"テンプレート削除: {deleted_name}")
                return True
        return False

    def save(self):
        """テンプレートをファイルに保存"""
        data = {
            'version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'templates': [t.to_dict() for t in self.templates]
        }

        # JSONファイルに書き込み
        with self.templates_file.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.debug(f"テンプレート保存: {len(self.templates)}件")

    def load(self):
        """テンプレートをファイルから読み込み"""
        try:
            with self.templates_file.open('r', encoding='utf-8') as f:
                data = json.load(f)

            # テンプレートを復元
            self.templates = [
                ProjectTemplate.from_dict(t)
                for t in data.get('templates', [])
            ]

            self.logger.info(f"テンプレート読み込み: {len(self.templates)}件")

        except Exception as e:
            self.logger.error(f"テンプレート読み込み失敗: {e}")
            self.templates = []

    def _get_next_id(self) -> str:
        """次のテンプレートIDを生成

        Returns:
            生成されたID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        counter = len(self.templates) + 1
        return f"template_{timestamp}_{counter:03d}"
