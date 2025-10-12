# 問題1: ワイルドカードファイルとCSVの同期ロジック - 解決済み

作成日: 2025-01-15
ステータス: ✅ 解決

---

## 確定した設計方針

### 基本方針: **独立コピー＋手動更新**

```
【元ファイル】読み取り専用
E:\EasyReforge\Model\wildcards\
├── tipo_play.txt
├── posing\
│   └── arm.txt
└── キャラ\
    └── SAYA.txt

【Pfft_maker管理】クリーン化＋編集可能
E:\tool\Pfft_maker\
├── wildcards\                    ← マスターデータ
│   ├── tipo_play.txt             ← 番号・ラベル削除済み
│   ├── posing\
│   │   └── arm.txt
│   └── キャラ\
│       └── SAYA.txt
├── data\
│   ├── prompts_library.csv       ← パース結果
│   └── labels_metadata.json      ← ユーザー設定
└── config\
    └── wildcard_source.json      ← 元ディレクトリパス記録
```

---

## 動作フロー

### 1. 初回起動時

```
起動
↓
設定確認: wildcard_source.json
↓
元ディレクトリパス: E:\EasyReforge\Model\wildcards\
↓
【処理】
1. 全ファイルをスキャン
2. E:\tool\Pfft_maker\wildcards\ にコピー
3. 各ファイルをクリーン化:
   - BOM除去
   - 番号削除: "14→clothed masturbation" → "clothed masturbation"
   - 空行削除
4. prompts_library.csv 生成
5. labels_metadata.json 初期化（空）
↓
完了
```

---

### 2. 起動時の更新チェック

```
起動
↓
元ディレクトリ E:\EasyReforge\Model\wildcards\ をスキャン
↓
更新日時・ファイル数を比較
↓
【変更あり】
┌────────────────────────────────────┐
│ ℹ 新しいワイルドカードがあります   │
│                                    │
│ 更新: 3ファイル                    │
│ 追加: 2ファイル                    │
│ 削除: 1ファイル                    │
│                                    │
│ [詳細を表示] [今すぐ更新] [後で]   │
└────────────────────────────────────┘

【変更なし】
通常起動
```

---

### 3. 手動更新

```
UIの [🔄更新] ボタンをクリック
↓
元ディレクトリをスキャン
↓
【処理】
1. 変更されたファイルを検出
2. E:\tool\Pfft_maker\wildcards\ に上書きコピー
3. クリーン化
4. prompts_library.csv 再構築
5. labels_metadata.json とマージ（ユーザー設定保持）
↓
完了通知: "✅ 5個のファイルを更新しました"
```

---

## ファイルクリーン化処理

### 変換例

**元ファイル（tipo_play.txt）**:
```
1→﻿({torogao|ahegao}: 1.4)
2→(school uniform:1.4)
14→clothed masturbation
25→(deepthroat, irrumatio, vomiting cum: 1.4)
```

**クリーン化後**:
```
({torogao|ahegao}: 1.4)
(school uniform:1.4)
clothed masturbation
(deepthroat, irrumatio, vomiting cum: 1.4)
```

### クリーン化ルール
1. ✅ BOM除去（`\ufeff`）
2. ✅ 番号削除（`14→` の部分）
3. ✅ 空行削除
4. ✅ UTF-8で保存
5. ❌ プロンプト内容は変更しない

---

## データ管理

### prompts_library.csv

```csv
id,source_file,line_number,original_number,prompt,auto_label,file_hash,created_date
tipo_play_001,tipo_play.txt,1,1,({torogao|ahegao}: 1.4),torogao ahegao,abc12345,2025-01-15
tipo_play_014,tipo_play.txt,14,14,clothed masturbation,clothed masturbation,abc12345,2025-01-15
posing_arm_001,posing/arm.txt,1,1,hand on lower abdomen,hand on lower abdomen,def67890,2025-01-15
```

**説明**:
- `id`: 一意識別子
- `original_number`: 元ファイルの番号（`14→` の14）
- `prompt`: クリーン化後のプロンプト
- `auto_label`: 自動生成ラベル（AI生成前のデフォルト）
- `file_hash`: ファイル変更検知用（SHA256先頭8文字）

---

### labels_metadata.json

```json
{
  "tipo_play_014": {
    "label_ja": "服着たままオナニー",
    "label_en": "clothed masturbation",
    "tags": ["服", "オナニー", "clothed", "masturbation"],
    "category": "行為",
    "notes": "",
    "user_modified": true,
    "last_modified": "2025-01-15T14:30:00"
  },
  "posing_arm_001": {
    "label_ja": "下腹部に手を当てる",
    "tags": ["ポーズ", "手"],
    "user_modified": true,
    "last_modified": "2025-01-15T15:00:00"
  }
}
```

**説明**:
- ユーザーが手動で付けたメタデータのみ保存
- ファイル更新時も保持される（IDで紐付け）

---

## 更新検知ロジック

### ファイル変更の判定

```python
def check_for_updates(source_dir: Path, local_dir: Path) -> Dict:
    """更新チェック"""
    changes = {
        'updated': [],  # 更新されたファイル
        'added': [],    # 新規追加
        'deleted': []   # 削除された
    }

    # 元ディレクトリのファイル一覧
    source_files = set(source_dir.rglob('*.txt'))

    # ローカルディレクトリのファイル一覧
    local_files = set(local_dir.rglob('*.txt'))

    for source_file in source_files:
        relative = source_file.relative_to(source_dir)
        local_file = local_dir / relative

        if not local_file.exists():
            # 新規追加
            changes['added'].append(relative)
        else:
            # 更新日時比較
            if source_file.stat().st_mtime > local_file.stat().st_mtime:
                changes['updated'].append(relative)

    # 削除検知
    for local_file in local_files:
        relative = local_file.relative_to(local_dir)
        source_file = source_dir / relative
        if not source_file.exists():
            changes['deleted'].append(relative)

    return changes
```

---

## ユーザーラベルの保持ロジック

### ファイル更新時の照合

```python
def update_and_preserve_labels(old_csv: pd.DataFrame,
                                new_prompts: List[Prompt],
                                metadata: Dict) -> pd.DataFrame:
    """ファイル更新時にユーザーラベルを保持"""

    for new_prompt in new_prompts:
        # original_numberで照合（最優先）
        match = old_csv[old_csv['original_number'] == new_prompt.original_number]

        if not match.empty:
            # 一致 → IDを引き継ぐ
            new_prompt.id = match.iloc[0]['id']
            # metadata も保持される（IDで紐付け）
        else:
            # プロンプト内容で類似度チェック（90%以上）
            # ... 類似判定ロジック
            pass

    return new_df
```

---

## SD再インストール時の対応

### 元ディレクトリが消えた場合

```
起動
↓
E:\EasyReforge\Model\wildcards\ が存在しない
↓
【警告ダイアログ】
┌────────────────────────────────────┐
│ ⚠ ワイルドカード元ディレクトリが   │
│   見つかりません                   │
│                                    │
│ E:\EasyReforge\Model\wildcards\    │
│                                    │
│ SD再インストール後は新しいパスを   │
│ 設定してください。                 │
│                                    │
│ ※ Pfft_maker内のデータは保持され   │
│    ています                        │
│                                    │
│ [パスを再設定] [このまま続行]      │
└────────────────────────────────────┘

【このまま続行】
→ E:\tool\Pfft_maker\wildcards\ のデータで動作
→ 更新機能は無効化

【パスを再設定】
→ 新しい元ディレクトリを選択
→ 再コピー・再同期
```

---

## メリット

✅ **SD再インストールの影響を受けない**
- Pfft_makerのデータは `E:\tool\Pfft_maker\` に独立保存

✅ **ユーザーのラベル・タグが失われない**
- `labels_metadata.json` で別管理

✅ **元ファイルを汚染しない**
- 読み取り専用、書き換えなし

✅ **ユーザーがコントロールできる**
- 手動更新、自動更新に驚かない

✅ **シンプルで安定**
- 複雑な同期ロジック不要

---

## デメリットと対策

❌ **元ファイル編集時の手動更新が必要**
→ 対策: 起動時に自動チェック＋通知

❌ **ディスク容量を2倍消費**
→ 対策: txtファイルは小さい（全体で数MB程度）、問題なし

---

## 実装チェックリスト

- [ ] 初回起動時のコピー処理
- [ ] ファイルクリーン化処理（番号削除）
- [ ] 起動時の更新チェック
- [ ] 手動更新ボタン実装
- [ ] prompts_library.csv 生成
- [ ] labels_metadata.json 管理
- [ ] SD再インストール時の警告ダイアログ
- [ ] 更新通知バナー

---

**これで問題1は完全に解決しました。次の問題に進めます。**
