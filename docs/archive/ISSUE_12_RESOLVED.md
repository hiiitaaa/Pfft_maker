# 問題12: AIコスト見積もり修正 - 解決記録

作成日: 2025-10-12
問題番号: 12
ステータス: ✅ 解決済み

---

## 問題の概要

**タイトル**: AI自動生成のコスト見積もりが実際より高い

**問題内容**:
requirements_discussion.mdに記載されているAI自動生成のコスト見積もり「$0.50-1.00」が、実際の計算値「~$0.09」と比べて約10倍高い。

**該当箇所**:
- requirements_discussion.md: 9.13（AI自動生成）

---

## 問題の詳細

### 現状の見積もり（修正前）

```
推定コスト: $0.50-1.00
```

### 問題点

**実際の計算**:
```
前提:
- 対象プロンプト: 1,250個（ラベルなし）
- 使用モデル: Claude Haiku
- 料金: Input $0.25/1M tokens, Output $1.25/1M tokens
- プロンプトテンプレート: ~150 tokens/request
- 平均プロンプト長: ~50 tokens
- 出力（日本語ラベル）: ~20 tokens

計算:
Input: 1,250 × (150 + 50) = 250,000 tokens = $0.0625
Output: 1,250 × 20 = 25,000 tokens = $0.03125
合計: $0.09375 ≒ $0.09-0.10

→ 見積もりが約10倍高い！
```

**影響**:
- ユーザーが実際より高いコストを想定してしまう
- AI自動生成の利用を躊躇する可能性
- 不正確な情報の提示

---

## 採用した解決策

**正確なコスト見積もりに修正**

### 修正後の見積もり

```
推定コスト: $0.09-0.10
(1,250プロンプト × 約200トークン)
```

### 計算根拠

**詳細な計算式**:
```
Claude Haiku料金:
- Input: $0.25 per 1M tokens
- Output: $1.25 per 1M tokens

1プロンプトあたりのトークン数:
- システムプロンプト（テンプレート）: 150 tokens
- プロンプト本文（平均）: 50 tokens
- 出力（日本語ラベル）: 20 tokens

1,250プロンプトの場合:
Input tokens  = 1,250 × (150 + 50) = 250,000 tokens
Output tokens = 1,250 × 20 = 25,000 tokens

コスト:
Input cost  = 250,000 / 1,000,000 × $0.25 = $0.0625
Output cost = 25,000 / 1,000,000 × $1.25 = $0.03125
Total       = $0.09375 ≒ $0.09-0.10
```

---

## 実施した変更

### requirements_discussion.md セクション9.13の更新

**修正前**:
```markdown
│【AI自動生成（推奨）】                  │
│ 使用するAI: Claude API                 │
│                                        │
│ 推定時間: 約5-10分                     │
│ 推定コスト: $0.50-1.00                 │
│                                        │
│ [後で] [自動生成開始]                  │
```

**修正後**:
```markdown
│【AI自動生成（推奨）】                  │
│ 使用するAI: Claude API (Haiku)         │
│                                        │
│ 推定時間: 約5-10分                     │
│ 推定コスト: $0.09-0.10                 │
│ (1,250プロンプト × 約200トークン)      │
│                                        │
│ [後で] [自動生成開始]                  │
```

**変更点**:
1. コスト見積もりを「$0.50-1.00」→「$0.09-0.10」に修正
2. モデル名を明記（Claude API → Claude API (Haiku)）
3. 計算根拠を追記（1,250プロンプト × 約200トークン）

---

## 実装への影響

### コスト計算関数の実装（推奨）

**technical_requirements.mdに追加すべき仕様**:

```python
# core/ai_cost_estimator.py

from typing import Literal

class AICostEstimator:
    """AI自動生成のコスト見積もり"""

    # Claude料金（per 1M tokens）
    COSTS = {
        "haiku": {"input": 0.25, "output": 1.25},
        "sonnet": {"input": 3.0, "output": 15.0}
    }

    # 想定トークン数
    TEMPLATE_TOKENS = 150  # システムプロンプト
    AVG_PROMPT_TOKENS = 50  # プロンプト本文（平均）
    OUTPUT_TOKENS = 20  # 日本語ラベル出力

    @classmethod
    def estimate_cost(
        cls,
        prompt_count: int,
        model: Literal["haiku", "sonnet"] = "haiku"
    ) -> float:
        """コスト見積もり

        Args:
            prompt_count: 処理するプロンプト数
            model: 使用するモデル（"haiku" or "sonnet"）

        Returns:
            推定コスト（USD）

        Example:
            >>> AICostEstimator.estimate_cost(1250, "haiku")
            0.09
            >>> AICostEstimator.estimate_cost(1250, "sonnet")
            1.13
        """
        # Input tokens総数
        input_total = prompt_count * (cls.TEMPLATE_TOKENS + cls.AVG_PROMPT_TOKENS)

        # Output tokens総数
        output_total = prompt_count * cls.OUTPUT_TOKENS

        # コスト計算
        input_cost = (input_total / 1_000_000) * cls.COSTS[model]["input"]
        output_cost = (output_total / 1_000_000) * cls.COSTS[model]["output"]

        total_cost = input_cost + output_cost

        return round(total_cost, 2)

    @classmethod
    def format_cost(cls, cost: float) -> str:
        """コストを見やすくフォーマット

        Args:
            cost: コスト（USD）

        Returns:
            フォーマットされたコスト文字列

        Example:
            >>> AICostEstimator.format_cost(0.09)
            '$0.09'
            >>> AICostEstimator.format_cost(1.13)
            '$1.13'
        """
        return f"${cost:.2f}"
```

### UI実装例

```python
# ui/ai_generation_dialog.py

class AIGenerationDialog(QDialog):
    """AI自動生成ダイアログ"""

    def update_cost_estimate(self):
        """コスト見積もりを更新"""
        prompt_count = self.get_unlabeled_prompt_count()
        selected_model = self.model_combo.currentText()  # "haiku" or "sonnet"

        # コスト計算
        estimated_cost = AICostEstimator.estimate_cost(
            prompt_count,
            selected_model
        )

        # UI表示
        self.cost_label.setText(
            f"推定コスト: {AICostEstimator.format_cost(estimated_cost)}"
        )

        # 警告表示（高額な場合）
        if estimated_cost > 1.0:
            self.warning_label.setText(
                "⚠ コストが$1.00を超えます。モデルをHaikuに変更することを推奨します。"
            )
            self.warning_label.show()
        else:
            self.warning_label.hide()
```

---

## 影響範囲

### 更新されたファイル
1. `requirements_discussion.md` (セクション9.13)

### 新規作成されたファイル
- `ISSUE_12_RESOLVED.md` （本ファイル）

### 影響を受ける機能
- AI自動生成機能のコスト表示
- ユーザー向けドキュメント

### 今後の実装が必要な機能
- `core/ai_cost_estimator.py` （コスト計算クラス）
- `ui/ai_generation_dialog.py` （ダイアログでのコスト表示）

---

## 補足事項

### なぜ見積もりが10倍も高かったのか？

**推測される原因**:
- プロンプト1つあたりのトークン数を過大評価していた可能性
- 1,250プロンプト全体を1リクエストで処理すると誤解していた可能性
- バッチ処理のオーバーヘッドを過剰に見積もっていた可能性

### 正確な見積もりの重要性

**1. ユーザーの意思決定への影響**:
- 不正確に高いコスト → AI機能を使わない判断
- 正確なコスト → 気軽に試せる、利用促進

**2. プロジェクトの信頼性**:
- 正確な情報提供 → ユーザーの信頼獲得
- 不正確な情報 → 信頼性低下

### Sonnetを使用した場合のコスト

**参考: Claude Sonnetでの見積もり**:
```
Sonnet料金:
- Input: $3.0 per 1M tokens
- Output: $15.0 per 1M tokens

1,250プロンプトの場合:
Input cost  = 250,000 / 1,000,000 × $3.0 = $0.75
Output cost = 25,000 / 1,000,000 × $15.0 = $0.375
Total       = $1.125 ≒ $1.10-1.15
```

**結論**: Sonnetでも約$1.10と、当初の見積もり「$0.50-1.00」よりやや高い程度。

---

## モデル選択ガイドライン

### Haiku vs Sonnet

| モデル | コスト | 精度 | 推奨ケース |
|--------|--------|------|-----------|
| Haiku | $0.09 | 十分 | 通常のラベル生成（推奨） |
| Sonnet | $1.13 | 高い | 複雑なプロンプトのラベル生成 |

**推奨**:
- デフォルトはHaiku
- 特殊なケース（複雑なプロンプト、精度重視）のみSonnet

---

## テスト項目

### 単体テスト
- [ ] `AICostEstimator.estimate_cost()`が正しくコストを計算することを確認
- [ ] Haikuモデルで1,250プロンプトのコストが$0.09になることを確認
- [ ] Sonnetモデルで1,250プロンプトのコストが$1.13になることを確認
- [ ] `format_cost()`が正しくフォーマットすることを確認

### 統合テスト
- [ ] AI生成ダイアログでコスト見積もりが正しく表示されることを確認
- [ ] プロンプト数が変更された際、コストが動的に更新されることを確認
- [ ] モデルを切り替えた際、コストが正しく再計算されることを確認

### UI/UXテスト
- [ ] コスト表示が見やすいことを確認
- [ ] 高額な場合に警告が表示されることを確認
- [ ] ユーザーがコスト情報を基に適切な判断ができることを確認

---

## 結論

問題12は**コスト見積もりの修正**で解決した。

**キーポイント**:
- ✅ コスト見積もりを「$0.50-1.00」→「$0.09-0.10」に修正（約1/10）
- ✅ 正確な計算根拠を明記（1,250プロンプト × 約200トークン）
- ✅ モデル名を明確化（Claude API → Claude API (Haiku)）
- ✅ 実装用のコスト計算クラスの仕様を提案

**次のステップ**:
- 問題13（検索のデバウンス処理実装）へ進む
- 問題14（ワイルドカード展開候補表示の簡略化）へ進む

---

**承認日**: 2025-10-12
**承認者**: ユーザー
