"""自作プロンプト管理

custom_prompts.jsonファイルを読み書きし、
自作プロンプトの保存・検索・削除を管理します。
"""

import re
import json
from pathlib import Path
from typing import List, Optional

from models.custom_prompt import CustomPrompt
from utils.logger import get_logger


class CustomPromptManager:
    """自作プロンプト管理クラス

    custom_prompts.jsonファイルを読み書きし、
    自作プロンプトの保存・検索・削除を管理します。
    """

    def __init__(self, data_dir: Path):
        """初期化

        Args:
            data_dir: データディレクトリパス
        """
        self.data_dir = data_dir
        self.custom_prompts_file = data_dir / "custom_prompts.json"
        self.prompts: List[CustomPrompt] = []
        self.logger = get_logger()

        # ファイルが存在する場合は読み込み
        if self.custom_prompts_file.exists():
            self.load()

    def load(self) -> List[CustomPrompt]:
        """JSONファイルから読み込み

        Returns:
            自作プロンプトリスト
        """
        try:
            with self.custom_prompts_file.open('r', encoding='utf-8') as f:
                data = json.load(f)

            self.prompts = [
                CustomPrompt.from_dict(item)
                for item in data.get("custom_prompts", [])
            ]

            self.logger.info(f"自作プロンプト読み込み: {len(self.prompts)}件")
            return self.prompts

        except Exception as e:
            self.logger.error(f"自作プロンプト読み込みエラー: {e}", exc_info=True)
            return []

    def save(self):
        """JSONファイルに保存"""
        try:
            from datetime import datetime

            data = {
                "custom_prompts": [p.to_dict() for p in self.prompts],
                "version": "1.0",
                "last_updated": datetime.now().isoformat()
            }

            # データディレクトリが存在しない場合は作成
            self.data_dir.mkdir(parents=True, exist_ok=True)

            # 一時ファイルに書き込み（安全な保存）
            temp_file = self.custom_prompts_file.with_suffix('.json.tmp')
            with temp_file.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 成功したら本番ファイルに上書き
            temp_file.replace(self.custom_prompts_file)

            self.logger.info(f"自作プロンプト保存: {len(self.prompts)}件")

        except Exception as e:
            self.logger.error(f"自作プロンプト保存エラー: {e}", exc_info=True)
            raise

    def add_prompt(
        self,
        prompt: str,
        label_ja: str,
        category: str = "自作",
        tags: Optional[List[str]] = None,
        label_en: str = "",
        notes: str = ""
    ) -> CustomPrompt:
        """プロンプトを追加

        Args:
            prompt: プロンプト本体
            label_ja: 日本語ラベル
            category: カテゴリ
            tags: タグリスト
            label_en: 英語ラベル
            notes: メモ

        Returns:
            作成されたCustomPromptオブジェクト
        """
        # ID生成（custom_001, custom_002, ...）
        next_id = self._get_next_id()

        # タグ自動生成（空の場合）
        if not tags:
            tags = self._generate_tags(prompt)

        custom_prompt = CustomPrompt(
            id=next_id,
            prompt=prompt,
            label_ja=label_ja,
            label_en=label_en,
            category=category,
            tags=tags,
            notes=notes
        )

        self.prompts.append(custom_prompt)
        self.save()

        self.logger.info(f"自作プロンプト追加: {next_id} - {label_ja}")
        return custom_prompt

    def update_prompt(
        self,
        prompt_id: str,
        prompt: Optional[str] = None,
        label_ja: Optional[str] = None,
        label_en: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> bool:
        """プロンプトを更新

        Args:
            prompt_id: プロンプトID
            prompt: プロンプト本体
            label_ja: 日本語ラベル
            label_en: 英語ラベル
            category: カテゴリ
            tags: タグリスト
            notes: メモ

        Returns:
            更新成功の場合True
        """
        custom_prompt = self.get_prompt_by_id(prompt_id)
        if not custom_prompt:
            return False

        # 指定された値のみ更新
        if prompt is not None:
            custom_prompt.prompt = prompt
        if label_ja is not None:
            custom_prompt.label_ja = label_ja
        if label_en is not None:
            custom_prompt.label_en = label_en
        if category is not None:
            custom_prompt.category = category
        if tags is not None:
            custom_prompt.tags = tags
        if notes is not None:
            custom_prompt.notes = notes

        self.save()
        self.logger.info(f"自作プロンプト更新: {prompt_id}")
        return True

    def remove_prompt(self, prompt_id: str) -> bool:
        """プロンプトを削除

        Args:
            prompt_id: プロンプトID

        Returns:
            削除成功の場合True
        """
        before_count = len(self.prompts)
        self.prompts = [p for p in self.prompts if p.id != prompt_id]
        after_count = len(self.prompts)

        if before_count > after_count:
            self.save()
            self.logger.info(f"自作プロンプト削除: {prompt_id}")
            return True

        return False

    def get_prompt_by_id(self, prompt_id: str) -> Optional[CustomPrompt]:
        """IDでプロンプトを取得

        Args:
            prompt_id: プロンプトID

        Returns:
            プロンプトオブジェクト、見つからない場合None
        """
        for prompt in self.prompts:
            if prompt.id == prompt_id:
                return prompt
        return None

    def record_usage(self, prompt_id: str, project_name: str):
        """使用履歴を記録

        Args:
            prompt_id: プロンプトID
            project_name: プロジェクト名
        """
        prompt = self.get_prompt_by_id(prompt_id)
        if prompt:
            prompt.record_usage(project_name)
            self.save()
            self.logger.debug(f"使用履歴記録: {prompt_id} in {project_name}")

    def search(self, query: str) -> List[CustomPrompt]:
        """プロンプトを検索

        Args:
            query: 検索クエリ

        Returns:
            マッチしたプロンプトリスト
        """
        if not query:
            return self.prompts

        return [p for p in self.prompts if p.matches_search(query)]

    def filter_by_category(self, category: str) -> List[CustomPrompt]:
        """カテゴリでフィルタ

        Args:
            category: カテゴリ名

        Returns:
            フィルタされたプロンプトリスト
        """
        return [p for p in self.prompts if p.category == category]

    def get_categories(self) -> List[str]:
        """カテゴリ一覧を取得

        Returns:
            カテゴリ名のリスト
        """
        categories = set(p.category for p in self.prompts)
        return sorted(categories)

    def get_most_used(self, limit: int = 10) -> List[CustomPrompt]:
        """よく使うプロンプトを取得

        Args:
            limit: 取得件数

        Returns:
            使用頻度順のプロンプトリスト
        """
        sorted_prompts = sorted(
            self.prompts,
            key=lambda p: p.usage_count,
            reverse=True
        )
        return sorted_prompts[:limit]

    def get_recent_prompts(self, limit: int = 10) -> List[CustomPrompt]:
        """最近使用したプロンプトを取得

        Args:
            limit: 取得件数

        Returns:
            最終使用日時順のプロンプトリスト
        """
        # last_usedがあるものだけ取得してソート
        used_prompts = [p for p in self.prompts if p.last_used]
        sorted_prompts = sorted(
            used_prompts,
            key=lambda p: p.last_used,
            reverse=True
        )
        return sorted_prompts[:limit]

    def _get_next_id(self) -> str:
        """次のIDを生成

        Returns:
            custom_001形式のID
        """
        if not self.prompts:
            return "custom_001"

        # 既存IDから最大番号を取得
        max_num = 0
        for prompt in self.prompts:
            if prompt.id.startswith("custom_"):
                try:
                    num = int(prompt.id.split("_")[1])
                    max_num = max(max_num, num)
                except (IndexError, ValueError):
                    pass

        return f"custom_{max_num + 1:03d}"

    def _generate_tags(self, prompt: str) -> List[str]:
        """タグを自動生成

        Args:
            prompt: プロンプト本体

        Returns:
            タグリスト
        """
        # シンプルな単語分割
        words = re.split(r'[,_\s]+', prompt.lower())

        # フィルタリング
        tags = [
            w.strip() for w in words
            if w.strip() and len(w.strip()) > 1 and w.strip().isalnum()
        ]

        # 重複削除（順序保持）
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags[:10]
