# Pfft_maker 確定仕様（調査完了版）

作成日: 2025-01-15
ステータス: ✅ 確定

---

## 🎯 調査により確定した仕様

### 1. ワイルドカード形式（問題2 解決）

#### ✅ 確定した形式
```
__フォルダ名/ファイル名__
```

#### 実例
```
__posing/arm__
__angle/camera__
__スクリプト/nsfw_sex_spresdlegs/aftersex__
__キャラ/SAYA__
__背景/学校__
```

#### ルール
- ✅ 拡張子（.txt）は**不要**
- ✅ ディレクトリ区切りは `/`（Unixスタイル）
- ✅ ルートディレクトリの場合: `__tipo_play__`
- ✅ サブディレクトリの場合: `__posing/arm__`
- ✅ 深い階層も対応: `__スクリプト/nsfw_sex_spresdlegs/aftersex__`

#### 実装コード（確定版）
```python
# core/wildcard_formatter.py
from pathlib import Path

def format_wildcard_path(file_path: Path, wildcard_root: Path) -> str:
    """ワイルドカード形式に変換

    Args:
        file_path: E:\EasyReforge\Model\wildcards\posing\arm.txt
        wildcard_root: E:\EasyReforge\Model\wildcards

    Returns:
        __posing/arm__
    """
    # 相対パスを取得
    relative_path = file_path.relative_to(wildcard_root)

    # 拡張子を削除
    stem_path = relative_path.with_suffix('')

    # Unixスタイルのパスに変換（バックスラッシュ → スラッシュ）
    unix_path = str(stem_path).replace('\\', '/')

    # ワイルドカード形式
    return f"__{unix_path}__"


# テストケース
# Input:  E:\EasyReforge\Model\wildcards\posing\arm.txt
# Output: __posing/arm__

# Input:  E:\EasyReforge\Model\wildcards\tipo_play.txt
# Output: __tipo_play__

# Input:  E:\EasyReforge\Model\wildcards\スクリプト\nsfw_sex_spresdlegs\aftersex.txt
# Output: __スクリプト/nsfw_sex_spresdlegs/aftersex__
```

---

### 2. BREAK仕様（問題3 解決）

#### ✅ 確定した仕様
- **必ず大文字**: `BREAK`（小文字不可）
- **独立したキーワード**: カンマ区切りのプロンプトリストの1要素として扱う
- **用途**: 75トークンチャンクの境界を強制、前の文脈の影響を区切る

#### 正しい使い方
```
clothed masturbation, school infirmary, BREAK, __posing/arm__, BREAK, masterpiece, best quality
```

**構造**:
```
[prompt1], [prompt2], [BREAK], [prompt3], [BREAK], [prompt4]
```

#### 間違った使い方
```
❌ clothed masturbation BREAK school infirmary     (カンマなし)
❌ clothed masturbation\nBREAK\nschool infirmary  (改行区切り)
❌ clothed masturbation, break, school infirmary   (小文字)
```

#### 実装コード（確定版）
```python
# core/prompt_builder.py
from typing import List
from models.block import Block, BlockType

def build_scene_prompt(blocks: List[Block]) -> str:
    """シーンの最終プロンプトを構築

    Args:
        blocks: ブロックリスト

    Returns:
        1行のプロンプト文字列

    Example:
        Input: [
            Block(type=FIXED_TEXT, content="clothed masturbation"),
            Block(type=BREAK),
            Block(type=WILDCARD, content="__posing/arm__"),
            Block(type=BREAK),
            Block(type=FIXED_TEXT, content="masterpiece, best quality")
        ]
        Output: "clothed masturbation, BREAK, __posing/arm__, BREAK, masterpiece, best quality"
    """
    parts = []

    for block in blocks:
        if block.type == BlockType.BREAK:
            parts.append("BREAK")
        else:
            # プロンプト内容をそのまま追加
            parts.append(block.content.strip())

    # カンマ + スペース区切りで結合
    prompt = ", ".join(parts)

    # 念のため連続カンマを削除
    import re
    prompt = re.sub(r',\s*,', ', ', prompt)

    return prompt
```

---

### 3. Prompts from file形式（確定）

#### ✅ 確定した仕様
- **1行 = 1プロンプト = 1枚の画像生成**
- **改行区切り**
- **BREAKは同じ行内に含まれる**

#### 出力例（output.txt）
```
clothed masturbation, school infirmary, __キャラ/SAYA__, BREAK, __posing/arm__, BREAK, masterpiece, best quality
deepthroat, classroom interior, __キャラ/SAYA__, BREAK, __posing/leg__, BREAK, masterpiece, best quality
exhibitionism, school rooftop, __キャラ/SAYA__, BREAK, standing, spread legs, BREAK, masterpiece, best quality
handjob, nurse office, __キャラ/SAYA__, BREAK, __posing/arm__, BREAK, masterpiece, best quality
```

**30シーン = 30行 = Stable Diffusionで30枚生成**

#### 実装コード（確定版）
```python
# core/exporter.py
from typing import List
from models.project import Project
from core.prompt_builder import build_scene_prompt

def export_prompts_from_file(project: Project, output_path: Path,
                             completed_only: bool = False) -> int:
    """Prompts from file形式でエクスポート

    Args:
        project: プロジェクト
        output_path: 出力先ファイルパス
        completed_only: 完成済みシーンのみ出力

    Returns:
        出力したシーン数
    """
    lines = []

    for scene in project.scenes:
        # 完成済みチェック
        if completed_only and not scene.is_completed():
            continue

        # 最終プロンプト構築
        prompt = build_scene_prompt(scene.blocks)

        lines.append(prompt)

    # ファイル出力（改行区切り）
    output_path.write_text("\n".join(lines), encoding='utf-8')

    return len(lines)
```

---

### 4. ワイルドカードファイル仕様（確定）

#### ✅ 確認できた形式
- **番号付き型のみ**: `行番号→プロンプト`
- **BOM付きUTF-8**: `\ufeff` で開始
- **改行区切り**: 1行1プロンプト

#### 実例
```
1→﻿({torogao|ahegao}: 1.4)
2→(school uniform:1.4)
14→clothed masturbation
25→(deepthroat, irrumatio, vomiting cum, cum in nose, monoglove, cum on clothes: 1.4)
```

#### パース処理（確定版）
```python
# core/wildcard_parser.py
import re
from pathlib import Path

class WildcardParser:
    # パターン1: 番号+テーブル型（現時点で未使用）
    PATTERN_1 = r'^(\d+)→\s*\|\s*([^|]+?)\s*\|\s*`?([^|`]+?)`?\s*\|'

    # パターン2: テーブル型（現時点で未使用）
    PATTERN_2 = r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'

    # パターン3: 番号付き型（主に使用）
    PATTERN_3 = r'^(\d+)→(.+)'

    # パターン4: シンプル型（該当しない場合）

    def parse_line(self, line: str, line_number: int) -> dict:
        """行をパース

        Args:
            line: "14→clothed masturbation"
            line_number: 行番号（ファイル内での位置）

        Returns:
            {
                'original_number': 14,
                'prompt': 'clothed masturbation',
                'label': 'clothed masturbation'
            }
        """
        # BOM除去
        line = line.lstrip('\ufeff').strip()

        if not line:  # 空行スキップ
            return None

        # パターン3: 番号付き型
        match = re.match(self.PATTERN_3, line)
        if match:
            original_number = int(match.group(1))
            prompt = match.group(2).strip()
            return {
                'original_number': original_number,
                'prompt': prompt,
                'label': prompt  # デフォルトラベルはプロンプトと同じ
            }

        # パターン4: シンプル型
        return {
            'original_number': None,
            'prompt': line,
            'label': line
        }
```

---

### 5. ディレクトリ構造（実環境）

#### ✅ 実際のディレクトリ構成
```
E:\EasyReforge\Model\wildcards\
├── tipo_play.txt
├── tipo_1girl.txt
├── play.txt
├── 姿勢.txt
├── キッチン.txt
├── 数字.txt
├── angle\
│   ├── camera.txt
│   └── angle.txt
├── posing\
│   ├── arm.txt
│   ├── leg.txt
│   └── face.txt
├── キャラ\
│   ├── SAYA.txt
│   ├── ARISA.txt
│   └── Coharu.txt
├── 背景\
│   ├── 学校.txt
│   ├── ビーチ.txt
│   └── office.txt
├── 服装\
│   └── ...
├── 表情\
│   └── ...
└── スクリプト\
    └── nsfw_sex_spresdlegs\
        ├── aftersex.txt
        ├── missionary.txt
        └── ...
```

#### カテゴリ自動分類ロジック（確定版）
```python
# core/category_classifier.py
from pathlib import Path

def extract_category(file_path: Path, wildcard_root: Path) -> str:
    """ファイルパスからカテゴリを抽出

    Args:
        file_path: E:\EasyReforge\Model\wildcards\posing\arm.txt
        wildcard_root: E:\EasyReforge\Model\wildcards

    Returns:
        "posing" または "ポージング"（日本語名があればマッピング）
    """
    relative = file_path.relative_to(wildcard_root)
    parts = relative.parts[:-1]  # ファイル名を除く

    if len(parts) == 0:
        # ルートディレクトリ
        return "その他"
    elif len(parts) == 1:
        # 1階層: "posing" → "ポージング"
        category = parts[0]
        return CATEGORY_MAPPING.get(category, category)
    else:
        # 2階層以上: "スクリプト/nsfw_sex_spresdlegs"
        return f"{parts[0]}/{parts[1]}"


# カテゴリマッピング（日本語化）
CATEGORY_MAPPING = {
    "angle": "アングル",
    "posing": "ポージング",
    "キャラ": "キャラ",
    "背景": "背景",
    "服装": "服装",
    "表情": "表情",
    "髪型": "髪型",
    "色": "色",
    "スクリプト": "スクリプト",
}
```

---

## 📋 修正が必要なドキュメント

以下のドキュメントを更新する必要があります：

### 1. requirements.md
- **FR-001**: ワイルドカード形式の正確な記述
- **FR-006**: BREAK仕様の確定版
- **FR-018**: 出力形式の明確化

### 2. technical_requirements.md
- **3.3.2**: `WildcardParser`のパターン定義
- **3.3.2**: `PromptBuilder`のBREAK処理ロジック
- **データベース設計**: CSV構造の確定

### 3. CLAUDE.md
- **7.1**: ワイルドカードパーサーの実装例を修正
- **7.2**: プロンプトビルダーの実装例を修正

---

## ✅ 解決済み問題

### 問題2: ワイルドカード形式のパス表記 → ✅ 解決
- 確定: `__folder/file__`（拡張子なし、スラッシュ区切り）

### 問題3: BREAKの出力形式 → ✅ 解決
- 確定: カンマ区切りで `BREAK` を独立配置
- 例: `prompt1, BREAK, prompt2`

---

## 📝 次のアクション

1. ✅ ワイルドカード形式確定
2. ✅ BREAK仕様確定
3. ✅ Prompts from file形式確定
4. ⏳ requirements.md更新
5. ⏳ technical_requirements.md更新
6. ⏳ CLAUDE.md更新
7. ⏳ 残りの問題（1, 4, 5...）を解決

---

**これで最重要問題が解決しました。残りの問題に進みましょう。**
