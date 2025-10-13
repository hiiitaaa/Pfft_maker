"""ラベル自動生成モジュール

Claude APIまたはLM Studioを使用してプロンプトに日本語ラベルを自動生成します。
FR-016: ラベル・タグ自動生成
"""

import re
from typing import List, Optional, Tuple
from datetime import datetime

from models import Prompt


class LabelGenerator:
    """ラベル自動生成クラス

    3段階フォールバック方式:
    1. Claude API（優先）- 高精度、要APIキー
    2. LM Studio（フォールバック）- ローカルLLM、オフライン可能
    3. 辞書ベース（最終手段）- 単語分割のみ、常に有効
    """

    def __init__(self, api_key_manager=None, use_claude: bool = True, use_lm_studio: bool = False):
        """初期化

        Args:
            api_key_manager: APIKeyManagerインスタンス（オプション）
            use_claude: Claude APIを使用するか
            use_lm_studio: LM Studioを使用するか
        """
        self.api_key_manager = api_key_manager
        self.use_claude = use_claude
        self.use_lm_studio = use_lm_studio

    def generate_labels_batch(
        self,
        prompts: List[Prompt],
        progress_callback=None
    ) -> Tuple[int, int, List[str]]:
        """プロンプトリストに対して一括でラベルを生成

        Args:
            prompts: Promptオブジェクトのリスト
            progress_callback: 進捗コールバック関数(current, total, message)

        Returns:
            (成功数, 失敗数, エラーメッセージリスト)
        """
        success_count = 0
        failure_count = 0
        errors = []

        # label_jaが空のプロンプトのみを対象
        target_prompts = [p for p in prompts if not p.label_ja or p.label_ja == p.prompt]
        total = len(target_prompts)

        if total == 0:
            return 0, 0, ["ラベル生成が必要なプロンプトがありません"]

        for i, prompt in enumerate(target_prompts):
            if progress_callback:
                progress_callback(i + 1, total, f"ラベル生成中: {prompt.prompt[:30]}...")

            try:
                # ラベル生成
                label_ja = self.generate_label(prompt.prompt)

                if label_ja:
                    prompt.label_ja = label_ja
                    prompt.label_source = self._get_label_source()
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append(f"ラベル生成失敗: {prompt.prompt[:30]}...")

            except Exception as e:
                failure_count += 1
                errors.append(f"エラー: {prompt.prompt[:30]}... - {str(e)}")

        return success_count, failure_count, errors

    def generate_label(self, prompt: str) -> Optional[str]:
        """プロンプトから日本語ラベルを生成

        Args:
            prompt: プロンプト文字列

        Returns:
            日本語ラベル、生成失敗時はNone
        """
        # ステップ1: Claude API（優先）
        if self.use_claude and self.api_key_manager:
            label = self._generate_with_claude(prompt)
            if label:
                return label

        # ステップ2: LM Studio（フォールバック）
        if self.use_lm_studio:
            label = self._generate_with_lm_studio(prompt)
            if label:
                return label

        # ステップ3: 辞書ベース（最終手段）
        return self._generate_with_dictionary(prompt)

    def _generate_with_claude(self, prompt: str) -> Optional[str]:
        """Claude APIで日本語ラベルを生成

        Args:
            prompt: プロンプト文字列

        Returns:
            日本語ラベル、失敗時はNone
        """
        try:
            import anthropic

            api_key = self.api_key_manager.get_api_key("claude")
            if not api_key:
                return None

            client = anthropic.Anthropic(api_key=api_key)

            # プロンプト作成
            system_prompt = """あなたはStable Diffusion用のプロンプトに日本語ラベルを付けるアシスタントです。
以下のルールに従って、簡潔で分かりやすい日本語ラベルを生成してください：

1. 最も重要な要素を3-5文字程度で表現
2. 平易な日本語を使用（カタカナ混在OK）
3. ラベルのみを出力（説明不要）

例：
- "clothed masturbation" → "服着たままオナニー"
- "school infirmary, beds with curtain dividers" → "保健室"
- "classroom interior, desks in rows" → "教室"
- "sitting, spread legs" → "座り開脚"
"""

            message = client.messages.create(
                model="claude-3-haiku-20240307",  # コスト効率の良いHaikuを使用
                max_tokens=50,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"プロンプト: {prompt}\n\n日本語ラベル:"}
                ]
            )

            # レスポンス抽出
            label = message.content[0].text.strip()

            # サニタイズ（改行や余分な文字を削除）
            label = re.sub(r'[\n\r]', '', label)
            label = label.strip('"').strip("'").strip()

            return label if label else None

        except Exception as e:
            print(f"[Warning] Claude API error: {e}")
            return None

    def _generate_with_lm_studio(self, prompt: str) -> Optional[str]:
        """LM Studioで日本語ラベルを生成

        Args:
            prompt: プロンプト文字列

        Returns:
            日本語ラベル、失敗時はNone
        """
        # TODO: LM Studio連携実装（Phase 5.2）
        # OpenAI互換APIを使用してローカルLLMに接続
        return None

    def _generate_with_dictionary(self, prompt: str) -> Optional[str]:
        """辞書ベースでラベルを生成

        プロンプトの先頭部分を抽出してラベルとする。

        Args:
            prompt: プロンプト文字列

        Returns:
            ラベル（プロンプトの先頭30文字）
        """
        # プロンプトの先頭部分を抽出（最大30文字）
        label = prompt.strip()
        if len(label) > 30:
            label = label[:30] + "..."
        return label

    def _get_label_source(self) -> str:
        """現在使用している生成方法を返す

        Returns:
            "ai_generated" または "manual"
        """
        if self.use_claude and self.api_key_manager:
            return "ai_generated"
        elif self.use_lm_studio:
            return "ai_generated"
        else:
            return "auto_extract"


def generate_tags_auto(prompt: str) -> List[str]:
    """自動タグ生成（シンプルな単語分割）

    FR-016仕様に準拠した単語分割ロジック。

    Args:
        prompt: プロンプト文字列

    Returns:
        タグのリスト（最大10個）

    Examples:
        >>> generate_tags_auto("school_infirmary")
        ['school', 'infirmary']

        >>> generate_tags_auto("clothed masturbation")
        ['clothed', 'masturbation']

        >>> generate_tags_auto("classroom interior, desks in rows")
        ['classroom', 'interior', 'desks', 'in', 'rows']
    """
    # 1. 小文字化
    text = prompt.lower()

    # 2. カンマ、アンダースコア、スペースで分割
    words = re.split(r'[,_\s]+', text)

    # 3. フィルタリング
    tags = [
        w.strip() for w in words
        if w.strip() and len(w.strip()) > 1 and w.strip().isalnum()
    ]

    # 4. 重複削除（順序保持）
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    # 5. 最大10タグ
    return unique_tags[:10]
