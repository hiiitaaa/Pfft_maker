# 問題7: CSVカラム定義の整理 - 解決記録

作成日: 2025-10-12
問題番号: 7
ステータス: ✅ 解決済み

---

## 問題の概要

**タイトル**: CSVの`line_number`カラムの意味が不明確

**問題内容**:
- `line_number`カラムの意味が曖昧（クリーン版での行番号？元ファイルの行番号？）
- 元ファイルが変更されると、`line_number`は無効になる
- CSVとファイルの対応が取れなくなる
- プロンプト照合に使うと誤動作の原因になる

**該当箇所**:
- requirements.md: FR-001（ワイルドカードファイル読み込み）
- requirements.md: セクション5.2（プロンプトライブラリCSV）
- technical_requirements.md: models/prompt.py
- technical_requirements.md: セクション4.1（prompts_library.csv）

---

## 問題の詳細

### 現状のCSVスキーマ（修正前）

```csv
id,source_file,line_number,original_number,label_ja,label_en,prompt,category,tags,created_date,last_used,label_source
```

### 問題点

**1. `line_number`の意味が不明確**
- クリーン版（番号削除後）での行番号なのか？
- 元ファイルの行番号なのか？
- 使用目的が不明

**2. 元ファイル変更時の問題**
```
元ファイル（旧）:
1: standing
2: sitting
3: lying down
...
14: clothed masturbation  ← line_number: 14

↓ 外部エディタで編集

元ファイル（新）:
1: standing
（2: sitting が削除された）
2: lying down
...
13: clothed masturbation  ← 行番号が13に変更

CSV上は line_number: 14 のまま → 不一致！
```

**3. プロンプト照合での誤動作リスク**
- `line_number`を使ってプロンプトを照合すると、ファイル変更後に誤った行を参照する
- 例: line_number:14で照合したら、本来の`clothed masturbation`ではなく、別のプロンプトを取得してしまう

---

## 採用した解決策

### 修正後のCSVスキーマ

```csv
id,source_file,original_line_number,original_number,label_ja,label_en,prompt,category,tags,created_date,last_used,label_source
```

### 変更内容

**1. カラム名のリネーム**
- `line_number` → `original_line_number`

**2. 役割の明確化**
- `original_line_number`: 元ファイルの行番号（**参考情報のみ**、元ファイル変更時は無効）
- `original_number`: `14→`の番号（**プロンプト照合に使用**）

### カラムの役割

| カラム | 役割 | 用途 | 備考 |
|-------|------|------|------|
| `original_line_number` | 元ファイルの行番号 | **参考情報** | 元ファイル変更時は無効になる |
| `original_number` | `14→`の番号 | **プロンプト照合** | ファイル変更後も有効（番号が変わらない限り） |
| `prompt` | プロンプト本文 | **プロンプト照合** | 内容の類似度で照合 |

---

## 実施した変更

### 1. requirements.md FR-001の更新

**修正前**:
```csv
id,source_file,line_number,original_number,label_ja,label_en,prompt,...
```

**修正後**:
```csv
id,source_file,original_line_number,original_number,label_ja,label_en,prompt,...
```

**追加した注意書き**:
> **注意**: `original_line_number`は参考情報であり、元ファイルが変更されると無効になります。プロンプト照合には`original_number`（`14→`の番号）や内容の類似度を使用してください。

---

### 2. requirements.md セクション5.2の更新

**カラム説明の更新**:
```markdown
- `original_line_number`: 元ファイルの行番号（**参考情報**、元ファイル変更時は無効）
- `original_number`: 元の番号（`14→`の14、プロンプト照合に使用）
```

---

### 3. technical_requirements.md models/prompt.pyの更新

**修正前**:
```python
@dataclass
class Prompt:
    """プロンプトモデル"""
    id: str
    source_file: str
    line_number: int
    original_number: int | None
    ...
```

**修正後**:
```python
@dataclass
class Prompt:
    """プロンプトモデル"""
    id: str
    source_file: str
    original_line_number: int  # 元ファイルの行番号（参考情報、元ファイル変更時は無効）
    original_number: int | None  # 元の番号（`14→`の14、プロンプト照合に使用）
    ...
```

---

### 4. technical_requirements.md セクション4.1の更新

**データ型の説明を更新**:
```markdown
- `original_line_number`: integer (元ファイルの行番号、参考情報)
- `original_number`: integer | null (元の番号`14→`の14、プロンプト照合に使用)
```

**追加した重要事項**:
> **重要**: `original_line_number`は**参考情報**であり、プロンプト照合には使用しません。照合には`original_number`（`14→`の番号）や内容の類似度を使用してください。

---

## プロンプト照合ロジック（参考）

ISSUES_AND_FIXES.md 問題8で提案されている照合ロジック:

```python
def match_prompt(old_prompt: Prompt, new_line: str) -> bool:
    """プロンプトの同一性判定（優先度順）"""

    # 1. 完全一致（最優先）
    if old_prompt.prompt == new_line:
        return True

    # 2. original_numberが一致（番号付き型の場合）
    # 例: "14→clothed masturbation" の14
    if old_prompt.original_number:
        new_match = re.match(r'^(\d+)→', new_line)
        if new_match and int(new_match.group(1)) == old_prompt.original_number:
            return True

    # 3. 編集距離が小さい（類似度90%以上）
    similarity = difflib.SequenceMatcher(None, old_prompt.prompt, new_line).ratio()
    if similarity > 0.9:
        return True

    return False
```

**重要**: この照合ロジックでは`original_line_number`は使用しません。

---

## 影響範囲

### 更新されたファイル
1. `requirements.md` (FR-001, セクション5.2)
2. `technical_requirements.md` (models/prompt.py, セクション4.1)

### 新規作成されたファイル
- `ISSUE_07_RESOLVED.md` （本ファイル）

### 影響を受ける機能
- FR-001: ワイルドカードファイル読み込み
- FR-005: ファイル更新チェック・手動同期
- データモデル: Prompt
- CSV読み込み・書き込み処理

---

## 実装ガイドライン

### WildcardParserでの実装

```python
# core/wildcard_parser.py
def parse_file(self, file_path: Path) -> List[Prompt]:
    """ファイルをパース"""
    prompts = []

    with file_path.open('r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue

        # パターンマッチング
        original_number, label, prompt = self.extract_label(line)

        prompts.append(Prompt(
            id=f"{file_path.stem}_{line_num}",
            source_file=str(file_path.relative_to(self.wildcard_dir)),
            original_line_number=line_num,  # 元ファイルの行番号（参考情報）
            original_number=original_number,  # `14→`の14（照合に使用）
            label_ja=label,
            label_en=prompt,
            prompt=prompt,
            ...
        ))

    return prompts
```

### ファイル更新時の照合ロジック

```python
# core/library_manager.py
def update_from_file_change(self, file_path: Path):
    """ファイル変更時の更新処理"""
    # 新しいプロンプトをパース
    new_prompts = self.parser.parse_file(file_path)

    # 既存のプロンプトと照合
    for new_prompt in new_prompts:
        # original_numberで照合（優先）
        old_prompt = self.find_by_original_number(new_prompt.original_number)

        if old_prompt:
            # IDを維持、ラベル・タグを保持
            new_prompt.id = old_prompt.id
            new_prompt.label_ja = old_prompt.label_ja
            new_prompt.tags = old_prompt.tags
        else:
            # プロンプト内容の類似度で照合
            old_prompt = self.find_by_similarity(new_prompt.prompt, threshold=0.9)
            if old_prompt:
                new_prompt.id = old_prompt.id
                new_prompt.label_ja = old_prompt.label_ja

        # CSVを更新
        self.update_prompt(new_prompt)
```

**重要**: `original_line_number`は照合には使用していません。

---

## 補足事項

### なぜ`line_number`ではダメなのか？

**1. 行番号は不安定**
- 元ファイルを編集すると行番号が変わる
- 行の追加・削除で全体の行番号がずれる

**2. 照合に使えない**
- 行番号だけでは、どのプロンプトか特定できない
- ファイル変更後は完全に無効になる

**3. 名前が曖昧**
- `line_number`という名前では、どの時点の行番号か不明
- 開発者が混乱する

### なぜ`original_line_number`に変更したのか？

**1. 役割の明確化**
- 「元ファイルの」行番号であることが明確
- 「参考情報」であることを強調

**2. 照合に使わないことを明示**
- 名前から「照合には使えない」ことがわかる
- `original_number`との違いが明確

**3. デバッグ時の利便性**
- 元ファイルの何行目か確認できる（デバッグ用）
- ユーザーが手動で元ファイルを確認する際に便利

### 将来的な拡張

もし将来、より高度な照合ロジックが必要になった場合、以下のような情報を追加できます：

```csv
id,source_file,original_line_number,original_number,prompt_hash,label_ja,...
```

- `prompt_hash`: プロンプトのSHA256ハッシュ（高速照合用）

ただし、Phase 1では`original_number`と内容の類似度で十分です。

---

## テスト項目

### 単体テスト
- [ ] WildcardParser.parse_file()が`original_line_number`を正しく設定することを確認
- [ ] Promptモデルで`original_line_number`が正しく保存されることを確認

### 統合テスト
- [ ] ファイル更新時、`original_number`での照合が優先されることを確認
- [ ] `original_line_number`が照合に使用されていないことを確認
- [ ] 元ファイルの行番号が変わっても、`original_number`で正しく照合できることを確認

### ファイル変更テスト
1. プロンプトライブラリを作成
2. 元ファイルで行を追加・削除（行番号が変わる）
3. ファイル更新チェック実行
4. `original_number`で正しく照合され、ラベル・タグが保持されることを確認

---

## 結論

問題7は`line_number` → `original_line_number`へのリネームで解決した。

**キーポイント**:
- ✅ カラム名が明確になった（「元ファイルの」行番号）
- ✅ 役割が明確になった（参考情報のみ）
- ✅ プロンプト照合は`original_number`や内容の類似度を使用
- ✅ ドキュメント全体で一貫性が確保された

**次のステップ**:
- 問題8（ファイル監視の照合ロジック改善）へ進む（オプション、Phase 2以降）
- 問題9（シーン削除時の番号管理）へ進む

---

**承認日**: 2025-10-12
**承認者**: ユーザー
