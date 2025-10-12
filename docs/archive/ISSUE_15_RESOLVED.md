# 問題15: タグ自動生成の単語分割ロジックが不明確 - 解決記録

作成日: 2025-10-12
問題番号: 15
ステータス: ✅ 解決済み

---

## 問題の概要

**タイトル**: タグ自動生成の単語分割ロジックが不明確

**問題内容**:
requirements.md FR-016に「単語分割で自動生成」と記述されているが、具体的なロジックが未定義だった。

**曖昧な点**:
- `school_infirmary` → どう分割？
- `clothed masturbation` → どう分割？
- 日本語はどうする？
- 括弧や記号はどう扱う？

**該当箇所**:
- requirements.md: FR-016（ラベル・タグ自動生成）
- technical_requirements.md: ai/label_generator.py

---

## 採用した解決策

### 基本方針

**3段階のタグ生成システム**を確立:
1. **自動抽出（必須）**: シンプルな単語分割、AI不要、常時動作
2. **AI生成（オプション）**: Claude API / LM Studioで高品質なタグを生成
3. **手動編集（常に可能）**: ユーザーが自由に追加・削除・編集

### 実装仕様

**タグ自動生成ロジック**:

```python
def generate_tags_auto(prompt: str) -> List[str]:
    """自動タグ生成（シンプル版）

    Args:
        prompt: "school_infirmary, beds with curtain dividers"

    Returns:
        ["school", "infirmary", "beds", "with", "curtain", "dividers"]
    """
    import re

    # 1. 小文字化
    text = prompt.lower()

    # 2. カンマ、アンダースコア、スペースで分割
    words = re.split(r'[,_\s]+', text)

    # 3. フィルタリング
    tags = [w.strip() for w in words
            if w.strip() and len(w.strip()) > 1 and w.strip().isalnum()]

    # 4. 重複削除（順序保持）
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    # 5. 最大10タグ
    return unique_tags[:10]
```

### 処理ルール

1. **小文字化**: すべて小文字に統一
2. **分割文字**: カンマ(`,`)、アンダースコア(`_`)、スペース(` `)
3. **フィルタリング**:
   - 空文字列を除去
   - 1文字の単語を除外（`a`, `i`, `s`など）
   - 英数字以外のみの文字列を除外
4. **重複削除**: 順序を保持しながら重複を削除
5. **上限**: 最大10タグまで

### 生成例

| プロンプト | 生成されるタグ |
|-----------|--------------|
| `school_infirmary` | `school`, `infirmary` |
| `clothed masturbation` | `clothed`, `masturbation` |
| `classroom interior, desks in rows` | `classroom`, `interior`, `desks`, `in`, `rows` |
| `({torogao\|ahegao}: 1.4)` | `torogao`, `ahegao`, `1`, `4` |

---

## 実施した変更

### 1. requirements.md FR-016の更新

**追加内容**:

- タグ自動生成の詳細仕様セクションを追加
- 生成ロジックの5ステップを明記
- 実装例（Pythonコード）を追加
- 生成例のテーブルを追加
- 日本語の扱いを明記
- 限界と対応策を記述

**変更箇所**: requirements.md:720-801行目

### 2. technical_requirements.md ai/label_generator.pyの更新

**追加内容**:

- `generate_tags_auto()` メソッドの完全な実装を追加
- `generate_label_dict_based()` メソッドを更新し、タグ生成ロジックを呼び出すように変更

**変更箇所**: technical_requirements.md:557-604行目

---

## 設計の詳細

### なぜシンプルな単語分割を採用したか？

**理由**:
1. **AI不要**: 常時動作可能、オフライン環境でも動作
2. **高速**: 正規表現のみで処理、パフォーマンス影響なし
3. **十分な実用性**: 基本的な英単語の分割には十分
4. **フォールバック**: AI生成が失敗した場合の最終手段として機能

### 日本語の扱い

**Phase 1での方針**:
- 日本語の形態素解析は実装しない
- AI生成（Claude API/LM Studio）で日本語タグを補完することを推奨
- 手動編集で日本語タグを追加可能

**理由**:
- 形態素解析ライブラリ（MeCab, janomeなど）は依存関係が増える
- exe化時のサイズ増加
- AI生成で十分カバー可能

### 限界と対応策

**認識している限界**:
- 複雑な表現（括弧、記号）は正確に分割できない
  - 例: `({torogao|ahegao}: 1.4)` → `torogao`, `ahegao`, `1`, `4` （数値が含まれる）
- 日本語は分割不可

**対応策**:
1. AI生成で補完（Claude API / LM Studio）
2. ユーザーの手動編集

---

## 影響範囲

### 更新されたファイル
1. `requirements.md` (FR-016) - タグ自動生成仕様を追加
2. `technical_requirements.md` (ai/label_generator.py) - 実装コードを追加

### 新規作成されたファイル
- `ISSUE_15_RESOLVED.md` （本ファイル）

### 影響を受ける機能
- FR-016: ラベル・タグ自動生成
- ai/label_generator.py: タグ生成ロジック
- ワイルドカードパーサー: タグ自動生成時に呼び出し

---

## 実装ガイドライン

### 実装タイミング

**Phase 1（MVP）で実装すべき機能**:
- ✅ `generate_tags_auto()` - シンプルな単語分割
- ⏳ ワイルドカードパーサーでの呼び出し
- ⏳ CSVへのタグ保存

**Phase 2で実装すべき機能**:
- ⏳ AI生成（Claude API）でのタグ補完
- ⏳ AI生成（LM Studio）でのタグ補完
- ⏳ UI上でのタグ編集機能

### 使用例

```python
# 使用例1: ワイルドカードパース時
from ai.label_generator import LabelGenerator

generator = LabelGenerator(api_manager)
tags = generator.generate_tags_auto("clothed masturbation, school infirmary")
# → ["clothed", "masturbation", "school", "infirmary"]

# CSVに保存
prompt.tags = tags
csv_handler.save(prompt)
```

```python
# 使用例2: AI生成との併用
tags_auto = generator.generate_tags_auto(prompt_text)
tags_ai = generator.generate_tags_claude(prompt_text)  # AI補完

# マージ（重複削除）
all_tags = list(set(tags_auto + tags_ai))[:10]
```

---

## テスト項目

### 単体テスト

```python
# tests/test_tag_generation.py
import pytest
from src.ai.label_generator import LabelGenerator

def test_generate_tags_simple():
    """シンプルな単語分割"""
    generator = LabelGenerator(None)
    tags = generator.generate_tags_auto("clothed masturbation")
    assert tags == ["clothed", "masturbation"]

def test_generate_tags_underscore():
    """アンダースコア分割"""
    generator = LabelGenerator(None)
    tags = generator.generate_tags_auto("school_infirmary")
    assert tags == ["school", "infirmary"]

def test_generate_tags_comma():
    """カンマ分割"""
    generator = LabelGenerator(None)
    tags = generator.generate_tags_auto("classroom interior, desks in rows")
    assert "classroom" in tags
    assert "interior" in tags
    assert "desks" in tags

def test_generate_tags_filter_single_char():
    """1文字除外"""
    generator = LabelGenerator(None)
    tags = generator.generate_tags_auto("a big room")
    assert "a" not in tags
    assert "big" in tags
    assert "room" in tags

def test_generate_tags_max_limit():
    """最大10タグ"""
    generator = LabelGenerator(None)
    long_prompt = ", ".join([f"word{i}" for i in range(20)])
    tags = generator.generate_tags_auto(long_prompt)
    assert len(tags) <= 10

def test_generate_tags_duplicate_removal():
    """重複削除"""
    generator = LabelGenerator(None)
    tags = generator.generate_tags_auto("school, school infirmary, school")
    assert tags.count("school") == 1
```

---

## まとめ

問題15は**シンプルな単語分割ロジック**を採用することで解決した。

**キーポイント**:
- ✅ AI不要、常時動作可能
- ✅ 高速で実用的
- ✅ AI生成・手動編集で補完可能
- ✅ 実装が簡単（約30行）
- ✅ Phase 1で十分な機能

**次のステップ**:
- 問題16（自動保存のエラーハンドリング）へ進む
- 問題18（エンコーディング検出のフォールバック）へ進む

---

**承認日**: 2025-10-12
**承認者**: ユーザー
