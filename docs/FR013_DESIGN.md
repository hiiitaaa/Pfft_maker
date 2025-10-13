# FR-013: テンプレート機能 - 設計書

作成日: 2025-10-13
担当者: Claude

---

## 概要

プロジェクト構成をテンプレートとして保存し、再利用できる機能を実装します。

### 目的
- よく使うプロジェクト構成を再利用
- 新規プロジェクト作成の効率化
- プロジェクトの一貫性を保つ

---

## テンプレートの種類

### 1. 構成テンプレート（プレースホルダー方式）

**保存内容**:
- ✅ シーン数（例: 30シーン）
- ✅ ブロック構造（各シーンのブロック数とタイプ）
- ✅ 共通プロンプト設定
- ❌ プロンプト内容（空のまま）

**用途**: プロジェクトの構造だけを再利用したい場合

**特徴**: プレースホルダー（空のブロック）として保存され、ユーザーが内容を埋める

### 2. 完全テンプレート（コピー方式）

**保存内容**:
- ✅ シーン数
- ✅ ブロック構造
- ✅ 共通プロンプト設定
- ✅ プロンプト内容（すべて）

**用途**: よく使うプロジェクト構成をそのままコピーしたい場合

**特徴**: プロンプト内容も含めて完全にコピー、すぐに使える

---

## データモデル設計

### ProjectTemplateモデル

```python
@dataclass
class ProjectTemplate(SerializableMixin):
    """プロジェクトテンプレートモデル

    Attributes:
        id: テンプレートID
        name: テンプレート名
        description: 説明
        template_type: テンプレートタイプ（"structure" or "complete"）
        scene_count: シーン数
        scene_templates: シーンテンプレートのリスト
        common_prompts: 共通プロンプト設定
        created_date: 作成日時
        last_used: 最終使用日時
        usage_count: 使用回数
    """
    id: str
    name: str
    description: str = ""
    template_type: str = "structure"  # "structure" or "complete"
    scene_count: int = 1
    scene_templates: List['SceneTemplate'] = field(default_factory=list)
    common_prompts: List[Dict[str, Any]] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
```

### SceneTemplateモデル

```python
@dataclass
class SceneTemplate(SerializableMixin):
    """シーンテンプレートモデル

    Attributes:
        scene_name: シーン名（プレースホルダー可）
        block_templates: ブロックテンプレートのリスト
    """
    scene_name: str = ""
    block_templates: List['BlockTemplate'] = field(default_factory=list)
```

### BlockTemplateモデル

```python
@dataclass
class BlockTemplate(SerializableMixin):
    """ブロックテンプレートモデル

    Attributes:
        type: ブロックタイプ
        content: ブロック内容（構成テンプレートの場合は空）
    """
    type: str  # "fixed_text", "wildcard", "break"
    content: str = ""
```

---

## TemplateManagerクラス

```python
class TemplateManager:
    """テンプレート管理クラス

    templates.jsonファイルを読み書きし、
    テンプレートの保存・読み込み・削除を管理します。
    """

    def __init__(self, data_dir: Path):
        """初期化"""
        self.data_dir = data_dir
        self.templates_file = data_dir / "templates.json"
        self.templates: List[ProjectTemplate] = []
        self.logger = get_logger()

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
        template_id = self._get_next_id()

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

        self.logger.info(f"テンプレート保存: {name} ({template_type})")
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
        from models import Project, Scene, Block, BlockType, CommonPrompt
        from datetime import datetime

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
        template.last_used = datetime.now()
        template.usage_count += 1
        self.save()

        self.logger.info(f"テンプレートから作成: {template.name} -> {project_name}")
        return project
```

---

## UI設計

### 1. テンプレート保存ダイアログ

```
┌─ テンプレート保存 ───────────┐
│ テンプレート名:              │
│ [学園メイド基本構成______]   │
│                              │
│ テンプレートタイプ:          │
│ ◉ 構成テンプレート           │
│   （プロンプト内容は保存しない）│
│ ○ 完全テンプレート           │
│   （プロンプト内容も含めて保存）│
│                              │
│ 説明（オプション）:          │
│ ┌──────────────────────────┐ │
│ │30シーン構成、品質タグ統一 │ │
│ └──────────────────────────┘ │
│                              │
│      [キャンセル] [保存]     │
└──────────────────────────────┘
```

### 2. メインウィンドウ - テンプレートメニュー

```
メニューバー
├ ファイル
│  ├ 新規プロジェクト
│  ├ テンプレートから作成 ...  ← NEW
│  ├ プロジェクトを開く
│  ├ 保存
│  ├ 名前を付けて保存
│  ├ ─────────────────
│  ├ テンプレートとして保存 ...  ← NEW
│  └ ...
```

### 3. テンプレート選択ダイアログ

```
┌─ テンプレートから作成 ───────┐
│ 利用可能なテンプレート:      │
│ ┌──────────────────────────┐ │
│ │✨ 学園メイド基本構成      │ │
│ │   （構成テンプレート）    │ │
│ │   30シーン、10回使用      │ │
│ │                          │ │
│ │✨ CG集標準構成           │ │
│ │   （完全テンプレート）    │ │
│ │   20シーン、5回使用       │ │
│ └──────────────────────────┘ │
│                              │
│ プロジェクト名:              │
│ [新規プロジェクト______]     │
│                              │
│ [編集] [削除]                │
│                              │
│      [キャンセル] [作成]     │
└──────────────────────────────┘
```

---

## 実装優先順位

### Phase 1: 基本機能（必須）
1. ✅ ProjectTemplateモデル
2. ✅ TemplateManagerクラス
3. ✅ テンプレート保存ダイアログ
4. ✅ テンプレート選択ダイアログ
5. ✅ メニュー統合

### Phase 2: 詳細機能（推奨）
1. テンプレート編集機能
2. テンプレート削除機能
3. よく使うテンプレート表示

### Phase 3: 拡張機能（オプション）
1. テンプレートのインポート・エクスポート
2. テンプレートのプレビュー機能
3. テンプレートの共有機能

---

## データ保存形式

### templates.json

```json
{
  "version": "1.0",
  "last_updated": "2025-10-13T16:00:00",
  "templates": [
    {
      "id": "template_001",
      "name": "学園メイド基本構成",
      "description": "30シーン構成、品質タグ統一",
      "template_type": "structure",
      "scene_count": 30,
      "scene_templates": [
        {
          "scene_name": "",
          "block_templates": [
            {"type": "fixed_text", "content": ""},
            {"type": "break", "content": ""},
            {"type": "wildcard", "content": ""}
          ]
        }
      ],
      "common_prompts": [
        {
          "name": "品質タグ",
          "content": "masterpiece, best quality",
          "enabled": true,
          "position": "end",
          "insert_break_after": false
        }
      ],
      "created_date": "2025-10-13T15:00:00",
      "last_used": "2025-10-13T15:30:00",
      "usage_count": 3
    }
  ]
}
```

---

## まとめ

FR-013テンプレート機能の設計が完了しました。

### 次のステップ
1. ProjectTemplateモデル実装
2. TemplateManagerクラス実装
3. UI実装（保存・選択ダイアログ）
4. メニュー統合
5. テスト

この設計に基づいて実装を進めます。
