"""ユーザーラベル保持ロジック

ワイルドカードファイル更新時に、ユーザーが設定した日本語ラベル・タグを保持します。
"""

from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

from models import Prompt
from utils.logger import get_logger


class LabelPreserver:
    """ユーザーラベル保持クラス

    ワイルドカードファイル更新時に、ユーザーが手動で設定した
    日本語ラベルやタグを保持し、新しいプロンプトに引き継ぎます。

    照合方法:
    1. original_number（14→ の14）で照合
    2. プロンプト内容の類似度90%以上で照合
    3. source_fileとプロンプト内容の完全一致で照合
    """

    # 類似度閾値（90%以上で同一とみなす）
    SIMILARITY_THRESHOLD = 0.9

    def __init__(self):
        """初期化"""
        self.logger = get_logger()

    def preserve_labels(
        self,
        old_prompts: List[Prompt],
        new_prompts: List[Prompt]
    ) -> List[Prompt]:
        """ユーザーラベルを保持

        古いプロンプトリストから、ユーザーが設定したラベル・タグを抽出し、
        新しいプロンプトリストに引き継ぎます。

        Args:
            old_prompts: 既存のプロンプトリスト
            new_prompts: 新しいプロンプトリスト

        Returns:
            ラベル・タグが引き継がれた新しいプロンプトリスト
        """
        self.logger.info(
            f"ラベル保持処理開始: 既存{len(old_prompts)}件 → 新規{len(new_prompts)}件"
        )

        # ユーザー設定があるプロンプトを抽出
        user_modified_prompts = [
            p for p in old_prompts
            if self._has_user_modifications(p)
        ]

        self.logger.info(f"ユーザー設定があるプロンプト: {len(user_modified_prompts)}件")

        # 照合用のインデックスを作成
        old_prompt_index = self._create_prompt_index(user_modified_prompts)

        preserved_count = 0
        not_found_count = 0

        # 新しいプロンプトに対して照合
        for new_prompt in new_prompts:
            matched_old_prompt = self._find_matching_prompt(
                new_prompt,
                old_prompt_index,
                user_modified_prompts
            )

            if matched_old_prompt:
                # ラベル・タグを引き継ぐ
                self._copy_user_data(matched_old_prompt, new_prompt)
                preserved_count += 1
                self.logger.debug(
                    f"ラベル保持: {new_prompt.source_file}:{new_prompt.original_line_number} "
                    f"← {matched_old_prompt.label_ja}"
                )
            else:
                # 照合失敗
                if self._has_user_modifications(new_prompt):
                    not_found_count += 1

        self.logger.info(
            f"ラベル保持完了: 保持={preserved_count}件, 未照合={not_found_count}件"
        )

        return new_prompts

    def _has_user_modifications(self, prompt: Prompt) -> bool:
        """ユーザーによる変更があるかチェック

        以下の条件をチェック:
        - label_sourceが'manual'または'ai_generated'
        - label_jaがpromptと異なる（自動抽出ではない）
        - tagsが空でない

        Args:
            prompt: プロンプトオブジェクト

        Returns:
            ユーザー変更がある場合True
        """
        # label_sourceがmanualまたはai_generated
        if prompt.label_source in ['manual', 'ai_generated']:
            return True

        # label_jaがpromptと異なる（自動抽出ではない）
        if prompt.label_ja and prompt.label_ja != prompt.prompt[:30]:
            return True

        # tagsが設定されている
        if prompt.tags:
            return True

        return False

    def _create_prompt_index(
        self,
        prompts: List[Prompt]
    ) -> Dict[str, List[Prompt]]:
        """プロンプトインデックスを作成

        照合を高速化するため、以下のキーでインデックス化:
        - source_file
        - original_number
        - prompt内容の最初の30文字

        Args:
            prompts: プロンプトリスト

        Returns:
            インデックス辞書
        """
        index = {
            'by_file': {},
            'by_number': {},
            'by_content': {}
        }

        for prompt in prompts:
            # ファイル別
            file_key = prompt.source_file
            if file_key not in index['by_file']:
                index['by_file'][file_key] = []
            index['by_file'][file_key].append(prompt)

            # 番号別（original_numberがある場合）
            if prompt.original_number is not None:
                number_key = f"{prompt.source_file}:{prompt.original_number}"
                index['by_number'][number_key] = prompt

            # 内容別（最初の30文字）
            content_key = prompt.prompt[:30].strip().lower()
            if content_key not in index['by_content']:
                index['by_content'][content_key] = []
            index['by_content'][content_key].append(prompt)

        return index

    def _find_matching_prompt(
        self,
        new_prompt: Prompt,
        old_index: Dict[str, any],
        old_prompts: List[Prompt]
    ) -> Optional[Prompt]:
        """マッチするプロンプトを検索

        優先順位:
        1. original_numberで照合（最高精度）
        2. プロンプト内容の類似度90%以上（高精度）
        3. source_fileとプロンプト内容の完全一致（中精度）

        Args:
            new_prompt: 新しいプロンプト
            old_index: 古いプロンプトのインデックス
            old_prompts: 古いプロンプトリスト

        Returns:
            マッチしたプロンプト、見つからない場合None
        """
        # 方法1: original_numberで照合
        if new_prompt.original_number is not None:
            number_key = f"{new_prompt.source_file}:{new_prompt.original_number}"
            if number_key in old_index['by_number']:
                matched = old_index['by_number'][number_key]
                self.logger.debug(
                    f"照合成功(original_number): {number_key}"
                )
                return matched

        # 方法2: 同じファイル内でプロンプト類似度が90%以上
        if new_prompt.source_file in old_index['by_file']:
            candidates = old_index['by_file'][new_prompt.source_file]

            for old_prompt in candidates:
                similarity = self._calculate_similarity(
                    new_prompt.prompt,
                    old_prompt.prompt
                )

                if similarity >= self.SIMILARITY_THRESHOLD:
                    self.logger.debug(
                        f"照合成功(類似度{similarity:.2%}): "
                        f"{new_prompt.source_file}:{new_prompt.original_line_number}"
                    )
                    return old_prompt

        # 方法3: 内容の最初の30文字で照合
        content_key = new_prompt.prompt[:30].strip().lower()
        if content_key in old_index['by_content']:
            candidates = old_index['by_content'][content_key]

            for old_prompt in candidates:
                if old_prompt.source_file == new_prompt.source_file:
                    self.logger.debug(
                        f"照合成功(内容一致): {content_key}"
                    )
                    return old_prompt

        # マッチなし
        return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """テキスト類似度を計算

        SequenceMatcherを使用して、2つのテキストの類似度を計算します。

        Args:
            text1: テキスト1
            text2: テキスト2

        Returns:
            類似度（0.0〜1.0）
        """
        return SequenceMatcher(None, text1, text2).ratio()

    def _copy_user_data(self, source: Prompt, target: Prompt):
        """ユーザーデータをコピー

        ソースプロンプトからターゲットプロンプトに、
        ユーザーが設定したデータをコピーします。

        Args:
            source: コピー元プロンプト
            target: コピー先プロンプト
        """
        # IDを維持
        target.id = source.id

        # ラベルをコピー
        if source.label_ja:
            target.label_ja = source.label_ja

        if source.label_en:
            target.label_en = source.label_en

        # タグをコピー
        if source.tags:
            target.tags = source.tags.copy()

        # カテゴリをコピー
        if source.category:
            target.category = source.category

        # ラベルソースをコピー
        if source.label_source:
            target.label_source = source.label_source

        # 最終使用日をコピー
        if source.last_used:
            target.last_used = source.last_used

    def get_preservation_stats(
        self,
        old_prompts: List[Prompt],
        new_prompts: List[Prompt]
    ) -> Dict[str, int]:
        """ラベル保持統計を取得

        Args:
            old_prompts: 既存のプロンプトリスト
            new_prompts: 新しいプロンプトリスト

        Returns:
            統計情報の辞書
        """
        user_modified_count = sum(
            1 for p in old_prompts
            if self._has_user_modifications(p)
        )

        preserved_count = sum(
            1 for p in new_prompts
            if self._has_user_modifications(p)
        )

        return {
            'total_old': len(old_prompts),
            'total_new': len(new_prompts),
            'user_modified': user_modified_count,
            'preserved': preserved_count,
            'lost': user_modified_count - preserved_count
        }
