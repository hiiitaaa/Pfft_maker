"""LoRAパーサー

LoRAフォルダをスキャンしてプロンプトライブラリを構築します。
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Callable

from models import Prompt, generate_id


class LoraParser:
    """LoRAパーサー

    .safetensorsファイルをスキャンし、メタデータ（.civitai.info, .json）を読み込んで
    Promptオブジェクトを生成します。
    """

    DEFAULT_WEIGHT = 0.8  # デフォルトのLoRA重み

    def __init__(self):
        """初期化"""
        self.prompts: List[Prompt] = []

    def scan_directory(
        self,
        lora_dir: Path,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Prompt]:
        """LoRAディレクトリを再帰的にスキャン

        Args:
            lora_dir: LoRAディレクトリ
            progress_callback: 進捗コールバック関数（オプション）
                              progress_callback(current, total, message)

        Returns:
            Promptオブジェクトのリスト
        """
        self.prompts.clear()

        if not lora_dir.exists():
            if progress_callback:
                progress_callback(0, 0, f"[Error] LoRA directory not found: {lora_dir}")
            return []

        # .safetensorsファイルを再帰的に検索
        safetensors_files = list(lora_dir.rglob("*.safetensors"))
        total_files = len(safetensors_files)

        for i, safetensors_file in enumerate(safetensors_files):
            # ファイルをパース
            prompt = self.parse_lora_file(safetensors_file, lora_dir)
            if prompt:
                self.prompts.append(prompt)

            # 進捗通知
            if progress_callback:
                relative_path = safetensors_file.relative_to(lora_dir)
                progress_callback(i + 1, total_files, f"Parsing: {relative_path}")

        return self.prompts

    def parse_lora_file(self, safetensors_path: Path, base_dir: Path) -> Optional[Prompt]:
        """LoRAファイルをパース

        Args:
            safetensors_path: .safetensorsファイルのパス
            base_dir: LoRAベースディレクトリ

        Returns:
            Promptオブジェクト（パース失敗時はNone）
        """
        # ファイル名（拡張子なし）
        file_name = safetensors_path.stem

        # 相対パス（Unix形式に統一）
        relative_path = safetensors_path.relative_to(base_dir)
        source_file = str(relative_path).replace('\\', '/')

        # カテゴリ抽出（親ディレクトリ名）
        parent_dir = safetensors_path.parent.name
        category = f"LoRA/{parent_dir}" if parent_dir != base_dir.name else "LoRA"

        # メタデータ読み込み
        metadata = self._load_metadata(safetensors_path)

        # プロンプト生成
        weight = metadata.get('default_weight', self.DEFAULT_WEIGHT)
        trigger_words = metadata.get('trigger_words', '')
        prompt_text = self._build_lora_prompt(file_name, weight, trigger_words)

        # ラベル生成
        label_ja = metadata.get('model_name', file_name)
        label_en = metadata.get('model_name_en', '')

        # Promptオブジェクト生成
        prompt_id = generate_id("lora", file_name, 1)

        prompt = Prompt(
            id=prompt_id,
            source_file=source_file,
            original_line_number=None,
            original_number=None,
            label_ja=label_ja,
            label_en=label_en,
            prompt=prompt_text,
            category=category,
            tags=metadata.get('tags', []),
            label_source="auto_extract",
            lora_metadata=json.dumps(metadata, ensure_ascii=False) if metadata else None
        )

        return prompt

    def _load_metadata(self, safetensors_path: Path) -> dict:
        """メタデータファイルを読み込み

        優先順位:
        1. .civitai.info
        2. .json

        Args:
            safetensors_path: .safetensorsファイルのパス

        Returns:
            統合されたメタデータ辞書
        """
        metadata = {}

        # 1. .civitai.info を読み込み
        civitai_path = safetensors_path.with_suffix('.civitai.info')
        if civitai_path.exists():
            try:
                with civitai_path.open('r', encoding='utf-8') as f:
                    civitai_data = json.load(f)

                    # trainedWords を trigger_words に変換
                    if 'trainedWords' in civitai_data and civitai_data['trainedWords']:
                        metadata['trigger_words'] = civitai_data['trainedWords'][0]

                    # baseModel
                    if 'baseModel' in civitai_data:
                        metadata['base_model'] = civitai_data['baseModel']

                    # tags
                    if 'model' in civitai_data and 'tags' in civitai_data['model']:
                        metadata['tags'] = civitai_data['model']['tags']

                    # model name
                    if 'model' in civitai_data and 'name' in civitai_data['model']:
                        metadata['model_name'] = civitai_data['model']['name']

                    # modelId, versionId
                    if 'modelId' in civitai_data:
                        metadata['civitai_model_id'] = civitai_data['modelId']
                    if 'id' in civitai_data:
                        metadata['civitai_version_id'] = civitai_data['id']
            except Exception as e:
                print(f"[Warning] Failed to load {civitai_path}: {e}")

        # 2. .json を読み込み（civitai.infoの情報を補完）
        json_path = safetensors_path.with_suffix('.json')
        if json_path.exists():
            try:
                with json_path.open('r', encoding='utf-8') as f:
                    json_data = json.load(f)

                    # activation text（civitai.infoがない場合のみ）
                    if 'activation text' in json_data and not metadata.get('trigger_words'):
                        metadata['trigger_words'] = json_data['activation text']

                    # preferred weight
                    if 'preferred weight' in json_data:
                        weight = json_data['preferred weight']
                        # 0の場合はデフォルト値を使用
                        if weight > 0:
                            metadata['default_weight'] = weight
            except Exception as e:
                print(f"[Warning] Failed to load {json_path}: {e}")

        # デフォルト値を設定
        if 'default_weight' not in metadata:
            metadata['default_weight'] = self.DEFAULT_WEIGHT

        if 'tags' not in metadata:
            metadata['tags'] = []

        return metadata

    def _build_lora_prompt(self, file_name: str, weight: float, trigger_words: str) -> str:
        """LoRAプロンプトを生成

        Args:
            file_name: LoRAファイル名（拡張子なし）
            weight: 重み
            trigger_words: トリガーワード

        Returns:
            LoRAプロンプト文字列
            例: "<lora:medicalexamination_Illust_v1:0.8>, medical examination, stethoscope"
        """
        lora_tag = f"<lora:{file_name}:{weight}>"

        if trigger_words:
            # カンマの後のスペースは不要（ユーザー確認済み）
            return f"{lora_tag}, {trigger_words}"
        else:
            return lora_tag
