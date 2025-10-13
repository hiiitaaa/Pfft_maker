"""コスト見積もりテスト"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ai.cost_estimator import CostEstimator
from models import Prompt

# テストデータ作成
test_prompts = []

# 典型的なプロンプト例
examples = [
    "school infirmary, beds with curtain dividers, medical equipment",
    "classroom interior, desks in rows, chalkboard, windows",
    "clothed masturbation, embarrassed expression",
    "sitting, spread legs, blushing",
    "standing, arms crossed, looking away",
]

# 100件のプロンプトをシミュレート
for i in range(100):
    prompt = Prompt(
        id=f'test_{i}',
        source_file='test.txt',
        original_line_number=i,
        original_number=None,
        label_ja='',  # 空のラベル
        label_en='',
        prompt=examples[i % len(examples)],
        category='test',
        tags=[],
        label_source='auto_extract'
    )
    test_prompts.append(prompt)

# コスト見積もり
print("="*60)
print("Claude API コスト見積もりテスト")
print("="*60)
print()

# Haiku (安価モデル)
print("【Claude 3 Haiku を使用】")
estimator_haiku = CostEstimator(model="claude-3-haiku-20240307")
cost, count, details = estimator_haiku.estimate_label_generation_cost(test_prompts)
print(estimator_haiku.format_cost_summary(details))
print()

# Sonnet (高性能モデル)
print("【Claude 3 Sonnet を使用（比較参考）】")
estimator_sonnet = CostEstimator(model="claude-3-sonnet-20240229")
cost, count, details = estimator_sonnet.estimate_label_generation_cost(test_prompts)
print(estimator_sonnet.format_cost_summary(details))
print()

# 実際のプロジェクト規模での見積もり
print("="*60)
print("実プロジェクトでの想定コスト")
print("="*60)
print()

scenarios = [
    (1000, "小規模プロジェクト（1,000プロンプト）"),
    (5000, "中規模プロジェクト（5,000プロンプト）"),
    (10000, "大規模プロジェクト（10,000プロンプト）"),
]

estimator = CostEstimator(model="claude-3-haiku-20240307")

for count, scenario in scenarios:
    prompts = test_prompts * (count // 100)
    cost, _, details = estimator.estimate_label_generation_cost(prompts)
    cost_jpy = cost * 150
    print(f"{scenario}:")
    print(f"  推定コスト: ${cost:.4f} USD (約¥{cost_jpy:.2f} JPY)")
    print()
