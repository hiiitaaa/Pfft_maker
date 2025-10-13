"""APIコスト見積もりモジュール

Claude APIの使用コストを事前に見積もります。
"""

from typing import List, Tuple
from models import Prompt


class CostEstimator:
    """APIコスト見積もりクラス

    Claude API (2024年料金):
    - Claude 3 Haiku: 入力 $0.25/MTok, 出力 $1.25/MTok
    - Claude 3 Sonnet: 入力 $3.00/MTok, 出力 $15.00/MTok
    """

    # 料金表（USD per 1M tokens）
    PRICING = {
        "claude-3-haiku-20240307": {
            "input": 0.25,   # $0.25 per 1M input tokens
            "output": 1.25,  # $1.25 per 1M output tokens
        },
        "claude-3-sonnet-20240229": {
            "input": 3.00,   # $3.00 per 1M input tokens
            "output": 15.00, # $15.00 per 1M output tokens
        },
    }

    # システムプロンプトの推定トークン数
    SYSTEM_PROMPT_TOKENS = 200  # 約200トークン

    # 出力トークン数（max_tokens設定）
    OUTPUT_TOKENS_PER_REQUEST = 50

    def __init__(self, model: str = "claude-3-haiku-20240307"):
        """初期化

        Args:
            model: 使用するモデル名
        """
        self.model = model
        self.pricing = self.PRICING.get(model, self.PRICING["claude-3-haiku-20240307"])

    def estimate_tokens(self, text: str) -> int:
        """テキストのトークン数を推定

        簡易推定式: 英語 = 文字数 / 4, 日本語は考慮しない

        Args:
            text: テキスト

        Returns:
            推定トークン数
        """
        # 簡易推定（正確にはtiktokenを使用すべきだが、依存を最小化するため簡易式を使用）
        return len(text) // 4

    def estimate_label_generation_cost(
        self,
        prompts: List[Prompt]
    ) -> Tuple[float, int, dict]:
        """ラベル生成コストを見積もり

        Args:
            prompts: Promptオブジェクトのリスト

        Returns:
            (総コスト(USD), プロンプト数, 詳細辞書)
        """
        count = len(prompts)

        if count == 0:
            return 0.0, 0, {
                "input_tokens": 0,
                "output_tokens": 0,
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
                "count": 0,
            }

        # 入力トークン数の推定
        total_input_tokens = 0
        for prompt in prompts:
            # システムプロンプト + ユーザープロンプト
            prompt_tokens = self.estimate_tokens(prompt.prompt)
            total_input_tokens += self.SYSTEM_PROMPT_TOKENS + prompt_tokens + 20  # 20はフォーマット用

        # 出力トークン数の推定
        total_output_tokens = count * self.OUTPUT_TOKENS_PER_REQUEST

        # コスト計算
        input_cost = (total_input_tokens / 1_000_000) * self.pricing["input"]
        output_cost = (total_output_tokens / 1_000_000) * self.pricing["output"]
        total_cost = input_cost + output_cost

        details = {
            "model": self.model,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "count": count,
            "cost_per_prompt": total_cost / count if count > 0 else 0.0,
        }

        return total_cost, count, details

    def format_cost_summary(self, details: dict) -> str:
        """コスト詳細をフォーマット

        Args:
            details: estimate_label_generation_cost()の戻り値の詳細辞書

        Returns:
            フォーマットされたコストサマリー
        """
        if details["count"] == 0:
            return "見積もり対象のプロンプトがありません"

        # 日本円換算（1 USD = 150 JPY と仮定）
        usd_to_jpy = 150
        total_cost_jpy = details["total_cost"] * usd_to_jpy
        cost_per_prompt_jpy = details["cost_per_prompt"] * usd_to_jpy

        summary = f"""【APIコスト見積もり】

モデル: {details['model'].replace('claude-3-', 'Claude 3 ').replace('-20240307', '').replace('-20240229', '')}

プロンプト数: {details['count']:,}件

推定トークン数:
  入力: {details['input_tokens']:,} tokens
  出力: {details['output_tokens']:,} tokens
  合計: {details['input_tokens'] + details['output_tokens']:,} tokens

推定コスト (USD):
  入力: ${details['input_cost']:.4f}
  出力: ${details['output_cost']:.4f}
  合計: ${details['total_cost']:.4f}

推定コスト (JPY): 約¥{total_cost_jpy:.2f}

1プロンプトあたり:
  USD: ${details['cost_per_prompt']:.6f}
  JPY: 約¥{cost_per_prompt_jpy:.4f}

※ 為替レート: 1 USD = {usd_to_jpy} JPY で計算
※ この見積もりは概算です。実際のコストは異なる場合があります。
"""

        return summary

    def is_cost_acceptable(self, total_cost: float, threshold: float = 1.0) -> Tuple[bool, str]:
        """コストが許容範囲かチェック

        Args:
            total_cost: 総コスト (USD)
            threshold: 閾値 (USD)

        Returns:
            (許容範囲内か, メッセージ)
        """
        if total_cost <= threshold:
            return True, f"推定コスト ${total_cost:.4f} は許容範囲内です（閾値: ${threshold}）"
        else:
            return False, f"⚠ 推定コスト ${total_cost:.4f} が閾値 ${threshold} を超えています"
