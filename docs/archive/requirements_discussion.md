# Pfft_maker 要件定義検討メモ

> このファイルは要件定義を決めるための検討内容をまとめたものです。
> 最終的な要件定義書・技術要件定義書は別途作成します。

最終更新日: 2025-01-15（詳細仕様追記 第2版）

---

## 1. プロジェクト概要

### 1.1 ツール名
**Pfft_maker**

### 1.2 目的
Stable Diffusion WebUIの「Prompts from file or textbox」機能を効率的に使用するためのプロンプト管理・生成ツール

### 1.3 背景
- CG集制作においてプロンプト管理が煩雑
- ワイルドカードファイルから目的のプロンプトを探す手間が非効率
- 使用したプロンプトの記録・再利用が困難
- 日本語ラベルが本番プロンプトに混入してしまう

### 1.4 解決する課題
1. **プロンプト探索の非効率性**: 複数のワイルドカードファイルを開いて探す手間
2. **並べ替え作業**: ストーリー順に手動でコピペして組み立てる作業
3. **記録・管理の欠如**: どのプロンプトを使ったか記録がなく、再度探す必要がある
4. **日本語ラベルの混入**: `| 教室 |` など自分用メモが本番プロンプトに含まれる

---

## 2. ユーザーワークフロー

### 2.1 CG集制作の流れ
1. **作品ストーリー決定**
2. **キャラクターデザイン** → ワイルドカード化 (`キャラ/SAYA.txt`)
3. **服装設定** → ワイルドカード化 (`服装/`)
4. **背景設定** → ワイルドカード化 (`背景/学校.txt`)
5. **行為・シーン設定** → ワイルドカード化 (`tipo_play.txt`)
6. **ストーリー順にプロンプト組み立て**
7. **Stable Diffusionで画像生成**

### 2.2 プロンプト構成例

```
crotch_grab,fondling,over_clothes,fingering,embarrassed,surprised_expression,
tensei_shitara_dai_nana_oji_datta_no_de:_kimama_ni_majutsu_o_kiwamemasu,official_art,kokuzawa_yosuke style,
__posing/arm__,__posing/leg__,
BREAK
__キャラ/SAYA__,
maid costume, black dress with white lace trim,maid_headdress,white frilled apron,classic domestic uniform style,
BREAK
<lora:futoshi_v1:0.7> futoshi,male,faceless_man,fat_man,bald_head,white_coat,
BREAK
__angle/angle__,__angle/camera__,
medical_room,white_walls,bright_lighting,clean_environment,examination_table,sterile_atmosphere,daylight_from_window,soft_shadows,realistic_shading,detailed_background,professional_setting,peaceful_mood,storytelling_scene,
motion_outline,speed_lines,motion_lines,motion_blur,
masterpiece, best quality, amazing quality,portrait,newest,ultra-detailed,absurdres,detailed_background,general
```

**構成要素:**
- **固定テキスト**: 自作プロンプト、ワイルドカードから選択したプロンプト（展開済み）
- **ワイルドカード**: `__ファイル名__` 形式（ランダム展開用）
- **BREAK**: プロンプトブロック区切り

---

## 3. ワイルドカードファイルの構造

### 3.1 参照元ディレクトリ
```
E:\EasyReforge\Model\wildcards\
```

### 3.2 ファイル形式

#### シンプル型
```
standing
standing,spread legs
sitting
```

#### テーブル型（日本語ラベル付き）
```
| 電車 | commuter train interior, school students in uniforms, morning rush hour... |
| 教室 | classroom interior, desks in rows, chalkboard or whiteboard... |
| 保健室 | school infirmary, beds with curtain dividers... |
```

#### 番号付き型
```
14→clothed masturbation
25→(deepthroat, irrumatio, vomiting cum, cum in nose, monoglove, cum on clothes: 1.4)
```

### 3.3 カテゴリ構成
- `キャラ/` (ARISA.txt, SAYA.txt, テスト花子.txt など)
- `背景/` (学校.txt, ビーチ.txt, 異世界.txt など)
- `服装/`, `表情/`, `髪型/`, `姿勢/`
- `posing/` (arm, leg)
- `angle/` (angle, camera)
- `色/`
- その他: `tipo_play.txt`, `tipo_1girl.txt`, `tipo_location.txt` など

### 3.4 ワイルドカードの動作
- `__キャラ/SAYA__` → Stable Diffusion実行時に `SAYA.txt` から1行ランダム選択して展開
- Dynamic Prompts拡張が自動処理
- ファイルが1行のみの場合も同様に処理される（実質固定）

---

## 4. 機能要件（検討中）

### 4.1 プロンプトソース管理

#### ワイルドカードファイル読み込み
- **対象**: `E:\EasyReforge\Model\wildcards\` 配下の全.txtファイル
- **処理**:
  1. ディレクトリ再帰スキャン
  2. ファイル形式自動判別（シンプル型/テーブル型/番号付き型）
  3. インデックス化

**データ構造例:**
```json
{
  "file": "tipo_play.txt",
  "category": "行為",
  "lines": [
    {
      "id": "tipo_play_14",
      "number": 14,
      "label": "clothed masturbation",
      "prompt": "clothed masturbation",
      "source_type": "wildcard"
    }
  ]
}
```

#### 自作プロンプト登録・保存
- **保存場所**: `E:\tool\Pfft_maker\custom_prompts\`
- **機能**:
  - シーン編集中に作成したプロンプトをライブラリに保存
  - 日本語ラベル、カテゴリ、タグを付与
  - 使用履歴の記録

**データ構造例:**
```json
{
  "custom_prompts": [
    {
      "id": "custom_001",
      "prompt": "crotch_grab,fondling,over_clothes,fingering,embarrassed",
      "label": "服の上から愛撫",
      "category": "行為",
      "tags": [
        "愛撫", "服装付き", "恥ずかしがり",
        "crotch_grab", "fondling", "over_clothes", "fingering", "embarrassed"
      ],
      "created_date": "2025-01-15",
      "usage_count": 3,
      "used_in_projects": ["学園メイドCG集", "OL物語"]
    }
  ]
}
```

**タグ登録方法:**
1. **自動抽出**: プロンプト内の単語を自動タグ化
2. **手動追加**: ユーザーが日本語タグを追加
3. **最終タグ = 自動 + 手動**

#### 日本語ラベル付け
- **自動抽出**:
  - テーブル型: `| 教室 |` → 「教室」
  - 番号付き型: `14→clothed masturbation` → 「clothed masturbation」
  - ファイル名: `tipo_play.txt` → 「tipo_play」
- **手動追加/編集**: UI上でラベル編集可能
- **ラベル管理ファイル**:
```json
{
  "label_overrides": {
    "tipo_play_14": "服着たままオナニー",
    "bg_school_12": "保健室"
  }
}
```

#### カテゴリ分類
- **自動カテゴリ**: フォルダ構造から推測
  - `背景/学校.txt` → 「背景」
  - `キャラ/SAYA.txt` → 「キャラ」
- **カスタムカテゴリ**:
```json
{
  "categories": [
    {
      "name": "行為",
      "files": ["tipo_play.txt", "tipo_1girl.txt"],
      "color": "#ff6b6b"
    },
    {
      "name": "背景",
      "files": ["背景/学校.txt", "背景/ビーチ.txt"],
      "color": "#4ecdc4"
    },
    {
      "name": "キャラ",
      "files": ["キャラ/SAYA.txt", "キャラ/ARISA.txt"],
      "color": "#45b7d1"
    },
    {
      "name": "ポージング",
      "files": ["posing/arm.txt", "posing/leg.txt", "姿勢.txt"],
      "color": "#f9ca24"
    },
    {
      "name": "アングル",
      "files": ["angle/angle.txt", "angle/camera.txt"],
      "color": "#6c5ce7"
    }
  ]
}
```

### 4.2 シーン編集機能

#### プロンプト挿入方法
1. **固定テキスト挿入**
   - ワイルドカードファイルから特定の1行を選択 → 展開して挿入
   - 手動入力
   - 自作プロンプトライブラリから選択

2. **ワイルドカード形式挿入**
   - ファイル全体をランダム化 → `__posing/arm__` 形式で挿入

#### ブロックタイプ
1. **固定テキストブロック**
   - 内容: 任意のテキスト
   - ソース: 自作 or ライブラリ参照

2. **ワイルドカードブロック**
   - 内容: `__ファイル名__` 形式
   - ソース: ワイルドカードファイル

3. **BREAKブロック**
   - 内容: `BREAK`

#### 編集操作
- ドラッグ&ドロップで並び替え
- [↑][↓]ボタンで順序変更
- [削除]で削除
- [複製]で同じブロックをコピー
- 複数ブロック選択 → まとめて移動/削除

#### リアルタイムプレビュー
- 最終プロンプト表示
- ワイルドカード展開候補表示（可能であれば）
- 文字数チェック
- クリップボードコピー

### 4.3 プロジェクト管理
- CG集単位で保存
- シーン一覧管理
- 使用プロンプト履歴

**プロジェクトデータ構造:**
```json
{
  "project_name": "学園メイドCG集",
  "created_date": "2025-01-15",
  "scenes": [
    {
      "scene_id": 1,
      "scene_name": "保健室",
      "blocks": [
        {
          "block_name": "行為",
          "type": "fixed_text",
          "content": "clothed masturbation"
        },
        {
          "block_name": "ポージング",
          "type": "wildcard",
          "content": "__posing/arm__,__posing/leg__"
        },
        {
          "type": "break"
        }
      ],
      "final_prompt": "..."
    }
  ]
}
```

### 4.4 出力機能
- **Prompts from file形式** (output.txt)
  - 1行1プロンプト
  - 日本語ラベル自動除去
  - クリーンなプロンプトのみ

- **管理用CSV** (オプション)
```csv
scene_id,scene_name,prompt,sources
1,保健室,"clothed masturbation, school infirmary...","tipo_play:14, 背景/学校:12, キャラ/SAYA:1"
```

---

## 5. UI設計

### 5.1 画面構成（3カラムレイアウト）

**解像度**: FULLHD (1920x1080)

```
┌─ Pfft_maker ─ プロジェクト: 学園メイドCG集 ──────────────────────────────────┐
│ メニューバー・ツールバー (高さ: 60px)                    [保存] [出力] [設定] │
├───────────────────────────────────────────────────────────────────────────┤
│                        作業エリア (高さ: 920px)                             │
│ ┌─ライブラリ────┐ ┌─シーン編集────┐ ┌─プレビュー────────┐            │
│ │               │ │                │ │                    │            │
│ │   600px       │ │    750px       │ │      550px         │            │
│ │               │ │                │ │                    │            │
│ │  高さ:        │ │  高さ:         │ │  高さ:             │            │
│ │  820px        │ │  820px         │ │  820px             │            │
│ │               │ │                │ │                    │            │
│ └───────────────┘ └────────────────┘ └────────────────────┘            │
├─ シーン一覧タブ (高さ: 60px) ────────────────────────────────────────────┤
│ [1:保健室] [2:教室] [3:屋上] [4:プール] ... [+新規シーン]                  │
└───────────────────────────────────────────────────────────────────────────┘
```

### 5.2 詳細レイアウト

#### 左カラム：ライブラリ (600px)
```
┌─ライブラリ─────────────┐
│🔍 検索: [__________]    │
│📁 カテゴリ: [全て ▼]    │
│                         │
│📂 行為                  │
│  14. clothed mast... [+]│
│  25. deepthroat... [+]  │
│                         │
│📂 背景                  │
│  📁 学校                │
│    9. classroom... [+]  │
│    12. school inf.. [+] │
│  📁 ビーチ              │
│                         │
│📂 キャラ                │
│  SAYA.txt          [+]  │
│  ARISA.txt         [+]  │
│                         │
│📂 ポージング            │
│  posing/arm        [+]  │
│  posing/leg        [+]  │
│                         │
│📂 自作プロンプト        │
│  服の上から愛撫    [+]  │
└─────────────────────────┘
```
- 検索バー: 60px
- カテゴリフィルタ: 40px
- ツリー表示: 720px（スクロール可）
- フォントサイズ: 14px

#### 中央カラム：シーン編集 (750px)
```
┌─シーン編集──────────────┐
│シーン: [1:保健室 ▼]     │
│                         │
│[ブロック1]─────────────│
││タイプ: [固定 ▼]       ││
││カテゴリ: [行為 ▼]     ││
││crotch_grab,fondling,  ││
││over_clothes,fingering ││
││[挿入][削][↑][↓]      ││
│└───────────────────────┘│
│                         │
│[ブロック2: BREAK]       │
│                         │
│[ブロック3]─────────────│
││タイプ: [ワイルド ▼]   ││
││__posing/arm__,        ││
││__posing/leg__         ││
││[挿入][削][↑][↓]      ││
│└───────────────────────┘│
│                         │
│[+ブロック] [+BREAK]     │
└─────────────────────────┘
```
- ヘッダー: 50px
- ブロック編集エリア: 670px
- フッター: 100px

#### 右カラム：プレビュー (550px)
```
┌─プレビュー──────────────┐
│最終プロンプト:           │
│                         │
│crotch_grab,fondling,    │
│over_clothes,fingering   │
│BREAK                    │
│__posing/arm__,          │
│__posing/leg__           │
│BREAK                    │
│__キャラ/SAYA__          │
│BREAK                    │
│medical_room,white_walls │
│                         │
│文字数: 245 / 推奨: ~500 │
│                         │
│[コピー] [テスト生成]    │
│                         │
│【ワイルドカード展開候補】│
│posing/arm:              │
│ ・arms crossed          │
│ ・arms up               │
│ ・arms behind back      │
└─────────────────────────┘
```
- プレビューエリア: 500px
- 統計・ボタン: 160px
- フォントサイズ: 13px（等幅）

### 5.3 ワークフロー
1. **左：ライブラリから探す** → 検索・フィルタリング
2. **中央：シーンに組み立て** → ドラッグ or [挿入]ボタン
3. **右：リアルタイム確認** → 最終プロンプト表示、コピー

---

## 6. 技術検討事項（未決定）

### 6.1 実装技術スタック
- プログラミング言語: Python、JavaScript、その他
- GUI フレームワーク: tkinter、PyQt、Electron、その他
- データ保存形式: JSON、SQLite、その他

### 6.2 課題・検討点
1. **ワイルドカード更新時の同期**
   - 元ファイル変更時、インデックス再構築が必要

2. **テーブル型パース**
   - `| 教室 | ...` の抽出ロジックの複雑さ

3. **大量データ処理**
   - tipo_play.txt 90行など、UI表示パフォーマンス

4. **BREAK挿入ルール**
   - 自動挿入？手動挿入？デフォルト動作の決定

5. **ワイルドカード展開プレビュー**
   - 全候補を表示する実装の可否

6. **ファイル監視**
   - ワイルドカードファイル更新の自動検知

---

## 7. 次回以降の作業項目

### Phase 1: 要件定義の確定
- [ ] 技術スタックの決定
- [ ] 詳細機能仕様の確定
- [ ] UI/UXの最終調整

### Phase 2: 要件定義書作成
- [ ] `requirements.md` - 機能要件定義書
- [ ] `technical_requirements.md` - 技術要件定義書
- [ ] `CLAUDE.md` - 開発ガイド

### Phase 3: 設計・実装
- [ ] データモデル設計
- [ ] UI モックアップ作成
- [ ] プロトタイプ開発

---

## 8. 参考情報

### Stable Diffusion WebUI関連
- **Prompts from file or textbox**: AUTOMATIC1111の標準スクリプト、1行1プロンプト形式
- **Dynamic Prompts拡張**: ワイルドカード機能を提供、`__filename__` 形式を実行時に展開
- **ワイルドカード配置**: `extensions/sd-dynamic-prompts/wildcards/`

### 既存ワイルドカード構造
- 参照元: `E:\EasyReforge\Model\wildcards\`
- 複数の形式が混在（シンプル/テーブル/番号付き）
- 日本語ラベルは自分用メモ（出力時は削除必要）

---

## 付録: 用語集

- **ワイルドカード**: Dynamic Prompts拡張の機能。`__filename__` 形式で記述し、実行時にファイル内容からランダムに1行選択
- **BREAK**: プロンプトブロックの区切り。Stable Diffusionで異なる重み付けを行うために使用
- **Prompts from file or textbox**: AUTOMATIC1111の標準スクリプト。テキストファイルまたはテキストボックスから複数のプロンプトを読み込み、バッチ生成する機能
- **CG集**: 複数のCG画像をまとめた作品集

---

## 9. 詳細仕様（確定版）

### 9.1 ワイルドカードパーサー詳細仕様

#### 移行方針
**既存ワイルドカードファイルのクリーン化とCSV管理への移行**

- **現状**: 番号付き型・テーブル型が混在（`14→clothed masturbation`, `| 教室 | ...`）
- **目標**:
  - ワイルドカード.txtファイル → クリーンなプロンプトのみ（番号・日本語削除）
  - Pfft_maker内部 → CSV形式で日本語ラベル付き管理

#### パースパターン（優先度順）

```python
# パターン1: 番号+テーブル型
# 例: 9→| 教室 | `classroom interior...` |
PATTERN_1 = r'^(\d+)→\s*\|\s*([^|]+?)\s*\|\s*`?([^|`]+?)`?\s*\|'

# パターン2: テーブル型
# 例: | 教室 | classroom interior... |
PATTERN_2 = r'^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'

# パターン3: 番号付き型
# 例: 14→clothed masturbation
PATTERN_3 = r'^(\d+)→(.+)'

# パターン4: シンプル型
# 例: clothed masturbation
# → 上記に該当しない場合、行全体
```

#### 処理フロー

```
1. ワイルドカードディレクトリをスキャン (E:\EasyReforge\Model\wildcards\)
   ↓
2. 各ファイルを読み込み
   - BOM（\uFEFF）除去
   - 空行スキップ
   - パターンマッチング
   ↓
3. 抽出処理
   - 番号（あれば）
   - 日本語ラベル（あれば）
   - プロンプト本体
   ↓
4. CSVに保存（prompts_library.csv）
   ↓
5. クリーン版txtファイル生成（オプション、バックアップ付き）
```

#### CSV構造（確定版）

```csv
id,source_file,line_number,original_number,label_ja,label_en,prompt,category,tags,created_date,last_used
tipo_play_1,tipo_play.txt,1,14,服着たままオナニー,clothed masturbation,clothed masturbation,行為,"clothed,masturbation",2025-01-15,
bg_school_1,背景/学校.txt,1,9,教室,classroom,"classroom interior, desks in rows...",背景,"school,classroom",2025-01-15,
```

**カラム説明:**
- `id`: 一意識別子（ファイル名_連番）
- `source_file`: 元ファイルパス
- `line_number`: クリーン版での行番号
- `original_number`: 元の番号（あれば）
- `label_ja`: 日本語ラベル（自動抽出 or 手動入力）
- `label_en`: 英語ラベル（プロンプトの先頭部分 or 手動入力）
- `prompt`: プロンプト本体
- `category`: カテゴリ
- `tags`: タグ（カンマ区切り）
- `created_date`: 作成日
- `last_used`: 最終使用日

#### ファイルクリーニング

**オプション設定:**
- **バックアップ作成**: 元ファイルを `.bak` で保存
- **即座に書き換え**: 確認なしで実行
- **プレビューモード**: 変更内容を表示のみ

---

### 9.2 ライブラリUI仕様（確定版）

#### 通常表示（600px）

```
┌─ライブラリ────────────┐
│ 📂 カテゴリ一覧        │
│                       │
│ 📂 行為 (105)    [→] │← クリックで詳細表示
│ 📂 背景 (62)     [→] │
│ 📂 キャラ (4)    [→] │
│ 📂 ポージング(25)[→] │
│ 📂 アングル (15) [→] │
│ 📂 自作 (12)     [→] │
│                       │
│ ──────────────────    │
│ 最近使用:             │
│ • clothed mast... [+] │
│ • school infir... [+] │
│ • SAYA           [+] │
└───────────────────────┘
```

#### 詳細表示（600px、同じエリア内で切替）

```
┌─ライブラリ：行為──────────────┐
│ ◀ カテゴリ一覧                │
│ 🔍 [検索...]  📁[tipo_play ▼] │
│───────────────────────────────│
│ 📁 tipo_play.txt (90)    [+]  │← ファイル全体選択
│                               │   → __tipo_play__
│   ├ 1. ({torogao|aheg... [+] │← 個別選択
│   ├ 14. clothed mast... [+]  │   → 固定テキスト
│   ├ 25. deepthroat...   [+]  │
│   ├ 49. doggystyle,     [+]  │
│   └ ...                       │
│                               │
│ 📁 tipo_1girl.txt (15)   [+]  │
│   ├ 1. standing         [+]  │
│   └ ...                       │
└───────────────────────────────┘
```

**視覚的な区別:**
- **ファイル行**: 📁アイコン + 太字 + [+]ボタン
- **プロンプト行**: インデント + 通常フォント + [+]ボタン

---

### 9.3 プロンプト挿入ロジック（確定版）

#### 挿入方法の区別

**1. ファイル名の [+] をクリック**
- ワイルドカード形式で挿入
- 例: `__tipo_play__`
- Stable Diffusion実行時にランダム展開

**2. 個別プロンプトの [+] をクリック**
- 固定テキストとして挿入
- 例: `clothed masturbation`
- 常にこのプロンプトが使用される

**3. ダブルクリック（最速操作）**
- プロンプトをダブルクリック → 固定テキストとして即挿入

**4. チェックボックス選択（複数選択）**
- 複数チェック → [挿入]ボタン
- 選択した順番でシーンに挿入

#### シーン編集エリアでの表示

```
┌─シーン編集────────────────┐
│ [ブロック1] 📌固定         │← アイコンで明示
│ clothed masturbation      │
│ [削][↑][↓]              │
│                           │
│ [ブロック2] 🎲ワイルド     │← アイコンで明示
│ __posing/arm__            │
│ [削][↑][↓]              │
│                           │
│ [ブロック3: BREAK]        │
└───────────────────────────┘
```

**アイコン凡例:**
- 📌 固定テキスト
- 🎲 ワイルドカード（ランダム）

---

### 9.4 BREAK仕様（確定版）

#### 挿入方法
- **手動挿入**: [+BREAK]ボタンをクリック

#### バリデーションルール
- ❌ 連続BREAK不可（BREAK → BREAK）
- ✅ 最初にBREAK可
- ✅ 最後にBREAK可

#### UI動作

```
┌─シーン編集────────────────┐
│ [ブロック1] 📌            │
│ clothed masturbation      │
│ [削][↑][↓]              │
│                           │
│ [+ブロック] [+BREAK] ←有効│
│                           │
│ [BREAK]                   │← BREAK追加後
│ [削][↑][↓]              │
│                           │
│ [+ブロック] [+BREAK] ←無効│← 連続BREAK防止
└───────────────────────────┘
```

**バリデーションロジック:**
- 直前のブロックがBREAK → [+BREAK]ボタン無効化（グレーアウト）
- 直前が通常ブロック → [+BREAK]ボタン有効

---

### 9.5 プロジェクトファイル管理（確定版）

#### ファイル形式
**JSON形式（汎用性重視）**

#### プロジェクトファイル構造

```json
{
  "project_info": {
    "name": "学園メイドCG集",
    "created_date": "2025-01-15",
    "last_modified": "2025-01-20",
    "description": "保健室を舞台にしたメイド物"
  },
  "scenes": [
    {
      "scene_id": 1,
      "scene_name": "保健室での診察",
      "created_date": "2025-01-15",
      "blocks": [
        {
          "block_id": 1,
          "type": "fixed_text",
          "content": "clothed masturbation",
          "source": {
            "file": "tipo_play.txt",
            "line_number": 14,
            "label": "服着たままオナニー"
          }
        },
        {
          "block_id": 2,
          "type": "break"
        },
        {
          "block_id": 3,
          "type": "wildcard",
          "content": "__posing/arm__",
          "source": {
            "file": "posing/arm.txt"
          }
        }
      ],
      "final_prompt": "clothed masturbation\nBREAK\n__posing/arm__\nBREAK\n..."
    }
  ],
  "metadata": {
    "total_scenes": 10,
    "output_history": [
      {
        "date": "2025-01-20",
        "output_file": "output_20250120.txt"
      }
    ]
  }
}
```

#### 保存方式

**自動保存 + 手動保存の組み合わせ**
- 編集後30秒で自動保存（一時ファイル `.pfft.autosave`）
- [保存]ボタンで確定保存
- 終了時に未保存確認ダイアログ表示

#### バックアップ戦略

**自動バックアップ（世代管理）**
```
プロジェクトフォルダ構成:
学園メイドCG集.pfft
.backup/
  ├ 学園メイドCG集_20250120_1430.pfft
  ├ 学園メイドCG集_20250120_1210.pfft
  ├ 学園メイドCG集_20250119_1545.pfft
  └ ...（最大5世代保持）
```

**バックアップタイミング:**
- 手動保存時に自動で世代バックアップ作成
- 6世代目以降は古いものから削除

---

### 9.6 ワイルドカードファイル監視・同期（確定版）

#### 監視方式

**リアルタイム監視 + 手動リロードの併用**
1. **リアルタイム監視**: ファイルシステム変更を自動検知
2. **手動リロード**: [🔄更新]ボタンでいつでも再読み込み

#### 更新検知時の動作

**通知バナー表示**
```
┌────────────────────────────────────┐
│ ⚠ ワイルドカードファイルが更新され │
│   ました                           │
│   [更新する] [無視] [詳細を表示]   │
└────────────────────────────────────┘
```

**[更新する]クリック時:**
1. ファイルを全行再読み込み
2. CSV再構築
3. ライブラリ表示を更新

#### 競合時の処理（ファイル優先原則）

**基本方針: ファイルの現状が正解**

1. 古いCSVデータは破棄
2. ファイルを全行再読み込み → CSV再生成
3. ユーザーが手動追加した日本語ラベルは可能な限り保持
   - プロンプト内容で照合（完全一致 or 部分一致）
   - 一致すればラベルを引き継ぎ
   - 一致しなければ新規ラベル自動生成

**削除行の扱い:**
- 使用中プロジェクトで参照されている場合: 「削除済み」マーク
- 未使用の場合: CSVから削除

#### 動作フロー例

```
1. tipo_play.txt が外部編集で変更される
   ↓
2. ファイル監視が検知 → 通知バナー表示
   ↓
3. [更新する]クリック
   ↓
4. ファイル再読み込み開始
   - BOM除去
   - パターンマッチング
   - プロンプト抽出
   ↓
5. 既存CSVとの照合
   - プロンプト内容で照合
   - 一致: 日本語ラベル引き継ぎ
   - 不一致: 新規エントリ作成
   ↓
6. CSV更新完了 → ライブラリ再表示
   ↓
7. 完了通知「ライブラリを更新しました」
```

---

### 9.7 検索機能仕様（確定版）

#### 検索方式
**シンプル全文検索**

#### 検索対象
- `label_ja`（日本語ラベル）
- `label_en`（英語ラベル）
- `prompt`（プロンプト本文）
- `tags`（タグ）
- `source_file`（ファイル名）

#### 検索仕様
- **検索方法**: 部分一致
- **リアルタイム**: 入力中に結果更新
- **大文字小文字**: 区別なし
- **複数キーワード**: スペース区切りでAND検索（オプション）

#### UI実装

```
┌─ライブラリ：行為──────────────┐
│ ◀ カテゴリ一覧                │
│ 🔍 [検索...______] [×]        │← リアルタイム検索
│───────────────────────────────│
│ 📁 tipo_play.txt (90)    [+]  │
│   ├ 14. clothed mast...  [+]  │
│   ├ 25. deepthroat...    [+]  │
│                               │
│ 📁 背景/学校.txt (24)    [+]  │
│   ├ 12. school infir...  [+]  │
│       (保健室) ← マッチ表示   │
└───────────────────────────────┘
```

**メリット:**
- 実装が簡単
- 辞書不要、メンテ不要
- 日本語でも英語でもヒット
- ユーザーは何も考えず検索するだけ

---

### 9.8 Prompts from file機能の正しい理解と出力形式（確定版）

#### 重要な前提

**Prompts from file or textbox機能:**
- 改行区切りで複数プロンプトを読み込み
- 1行 = 1プロンプト = 1枚の画像生成
- 順番に処理される

#### Pfft_makerの出力形式

**1シーン = 1行 = 1画像**

```
シーン1: clothed masturbation, school infirmary, __キャラ/SAYA__, BREAK, __posing/arm__, BREAK, masterpiece, best quality
シーン2: deepthroat, irrumatio, classroom interior, __キャラ/SAYA__, BREAK, __posing/leg__, BREAK, masterpiece, best quality
シーン3: exhibitionism, school rooftop, __キャラ/SAYA__, BREAK, standing, spread legs, BREAK, masterpiece, best quality
...
シーン30: final scene prompt...
```

**output.txt（30シーン = 30行 = 30枚生成）:**
```
clothed masturbation, school infirmary, beds with curtain dividers, __キャラ/SAYA__, BREAK, __posing/arm__, BREAK, masterpiece, best quality
deepthroat, irrumatio, classroom interior, desks in rows, __キャラ/SAYA__, BREAK, __posing/leg__, BREAK, masterpiece, best quality
exhibitionism, school rooftop, chain-link fence, __キャラ/SAYA__, BREAK, standing, spread legs, BREAK, masterpiece, best quality
handjob, nurse office, medical equipment, __キャラ/SAYA__, BREAK, __posing/arm__, BREAK, masterpiece, best quality
...
(30行)
```

#### BREAKの扱い

- **BREAK**は文字列として1行内に含まれる
- プロンプトブロックの区切りとして機能
- 最終的に改行なしで1行にまとめられる

---

### 9.9 30シーン管理UI（確定版）

#### UI全体構成

```
┌─ Pfft_maker ─ プロジェクト: 学園メイドCG集 ──────────────────────────────────┐
│ [ファイル] [編集] [表示]                    [保存] [全シーン出力] [設定]     │
├───────────────────────────────────────────────────────────────────────────┤
│ ┌─ライブラリ──┐ ┌─シーン編集────┐ ┌─プレビュー────────────────┐      │
│ │             │ │シーン3: 屋上   │ │【現在のシーン】            │      │
│ │ 600px       │ │               │ │exhibitionism, school...    │      │
│ │             │ │[ブロック1]📌  │ │BREAK, standing, spread...  │      │
│ │📂 行為      │ ││exhibitionism ││ │BREAK, masterpiece...       │      │
│ ││14.clothed  │ ││[削][↑][↓]   ││ │                            │      │
│ │             │ │               │ │文字数: 145 / ~500          │      │
│ │📂 背景      │ │[BREAK]        │ │                            │      │
│ ││12.保健室   │ │               │ │[コピー] [このシーンを出力] │      │
│ │             │ │[ブロック2]📌  │ │─────────────────────────  │      │
│ │             │ ││school rooftop││ │【全シーン一覧】(30シーン)  │      │
│ │             │ ││[削][↑][↓]   ││ │1. clothed mast, school...  │      │
│ │             │ │               │ │2. deepthroat, classroom... │      │
│ │             │ │[+ブロック]    │ │3. exhibitionism, roof... ★│      │
│ │             │ │[+BREAK]       │ │4. handjob, nurse...        │      │
│ │             │ │               │ │...                         │      │
│ │             │ │               │ │30. final scene...          │      │
│ └─────────────┘ └───────────────┘ └────────────────────────────┘      │
├─ シーン一覧タブ ──────────────────────────────────────────────────────────┤
│ [1:保健室✓] [2:教室✓] [3:屋上★] [4:プール] ... [30:最終] [+新規シーン]    │
└───────────────────────────────────────────────────────────────────────────┘
```

#### プレビューエリア（2分割）

```
┌─プレビュー────────────────────┐
│【現在編集中のシーン（1行）】  │
│exhibitionism, school rooftop, │
│chain-link fence, __キャラ/...,│
│BREAK, standing, spread legs,  │
│BREAK, masterpiece, best...    │
│                               │
│文字数: 145 / ~500             │
│[コピー] [このシーンを出力]    │
│                               │
│───────────────────────────── │
│【全シーン一覧】               │
│(スクロール可、30シーン表示)   │
│                               │
│ 1. clothed masturbation... ✓  │
│ 2. deepthroat, irrumatio... ✓ │
│ 3. exhibitionism, school... ★ │← 編集中
│ 4. handjob, nurse office...   │
│ ...                           │
│ 30. final scene...            │
│                               │
│ 完成: 2/30シーン              │
└───────────────────────────────┘
```

#### シーン切り替え方法

**方法A: タブクリック**
- 下部のシーン一覧タブをクリック

**方法B: キーボードショートカット**
- `Ctrl + →`: 次のシーンへ
- `Ctrl + ←`: 前のシーンへ
- `Ctrl + G`: シーン番号指定ジャンプ

**方法C: プレビューから**
- プレビューの全シーン一覧でクリック

---

### 9.10 共通プロンプト機能（確定版）

#### カテゴリ追加

ライブラリに以下のカテゴリを追加:
- **品質タグ**: `masterpiece, best quality` など
- **LoRA**: `<lora:xxx:0.7>` など

#### プロジェクト設定

```
┌─ プロジェクト設定 ─────────────────────┐
│ プロジェクト: 学園メイドCG集           │
│                                        │
│【共通プロンプト】                      │
│ 全シーンに自動適用されます             │
│                                        │
│ 品質タグ:                              │
│ [masterpiece, best quality... ▼]       │
│ ☑ 全シーンの末尾に自動追加             │
│                                        │
│ LoRA:                                  │
│ [<lora:futoshi_v1:0.7>... ▼]          │
│ ☑ 全シーンに自動追加                   │
│ 挿入位置: [BREAKの後 ▼]               │
│                                        │
│ スタイル指定:                          │
│ [official_art, anime... ▼]             │
│ ☑ 全シーンに自動追加                   │
│                                        │
│          [キャンセル] [保存]           │
└────────────────────────────────────────┘
```

#### シーン編集での表示

```
┌─シーン編集────────────────┐
│ [ブロック1] 📌固定        │
│ clothed masturbation      │
│ [編集][削][↑][↓]        │
│                           │
│ [BREAK]                   │
│                           │
│ [ブロック2] 📌固定        │
│ school infirmary          │
│ [編集][削][↑][↓]        │
│                           │
│ [BREAK]                   │
│                           │
│ [ブロック3] 📌共通 🔒     │← 共通設定（自動）
│ <lora:futoshi_v1:0.7>    │
│ [個別編集可]              │
│                           │
│ [BREAK]                   │
│                           │
│ [ブロック4] 📌共通 🔒     │← 共通設定（自動）
│ masterpiece, best quality │
│ [個別編集可]              │
└───────────────────────────┘
```

---

### 9.11 テンプレート機能（確定版）

#### テンプレート保存

```
┌─ テンプレート保存 ─────────────────┐
│ テンプレート名:                    │
│ [学園メイド基本構成______]         │
│                                    │
│ 説明（オプション）:                │
│ ┌────────────────────────────────┐ │
│ │30シーン構成                    │ │
│ │キャラ: SAYA固定                │ │
│ │品質: masterpiece統一           │ │
│ └────────────────────────────────┘ │
│                                    │
│ 保存する内容:                      │
│ ☑ シーン構成（30シーン）           │
│ ☑ 使用ブロック構造                 │
│ ☑ 共通プロンプト（品質タグ等）     │
│ ☐ 個別プロンプト内容               │
│                                    │
│          [キャンセル] [保存]       │
└────────────────────────────────────┘
```

#### テンプレートから新規作成

```
┌─ テンプレート選択 ─────────────────┐
│ 保存済みテンプレート:              │
│                                    │
│ ○ 学園メイド基本構成               │
│   30シーン、SAYA固定               │
│   作成日: 2025-01-15               │
│                                    │
│ ○ OL物語構成                       │
│   25シーン、オフィス背景中心       │
│   作成日: 2025-01-10               │
│                                    │
│ 新規プロジェクト名:                │
│ [新作CG集______]                   │
│                                    │
│      [キャンセル] [作成]           │
└────────────────────────────────────┘
```

---

### 9.12 マニュアル編集操作（確定版）

#### 新規ブロックの手動追加

```
┌─ 手動入力 ─────────────────────────┐
│ プロンプトを入力:                  │
│ ┌──────────────────────────────┐  │
│ │crotch_grab, fondling,        │  │
│ │over_clothes, finger...       │  │
│ └──────────────────────────────┘  │
│                                    │
│ ブロックタイプ:                    │
│ ◉ 固定テキスト                     │
│ ○ ワイルドカード                   │
│                                    │
│ ☑ ライブラリに保存                 │
│   日本語ラベル: [愛撫__]  [AI提案]│
│   カテゴリ: [行為 ▼]               │
│   タグ: [愛撫,crotch_grab] [自動]  │
│                                    │
│     [キャンセル] [追加]            │
└────────────────────────────────────┘
```

#### 既存ブロックの編集

**インライン編集（ダブルクリック）:**
- ブロックをダブルクリック → 直接編集モード
- Enter or [保存]で確定
- Escでキャンセル

**右クリックメニュー:**
```
┌─────────────────────┐
│ ブロックを編集      │
│ ─────────────────── │
│ 複製                │
│ 削除                │
│ ─────────────────── │
│ 上に移動            │
│ 下に移動            │
│ ─────────────────── │
│ ライブラリに保存    │
└─────────────────────┘
```

---

### 9.13 AI自動生成（ラベル・タグ）（確定版）

#### ラベル・タグ生成フロー

```
ワイルドカード読み込み
   ↓
【ステップ1: 自動抽出】
├ テーブル型: | 教室 | → label_ja: "教室"
├ 番号付き型: 14→clothed... → label_en: "clothed masturbation"
└ タグ: 単語分割で自動生成
   ↓
【ステップ2: AI自動生成（オプション）】
label_ja が空欄のプロンプトに対して
├ Claude API / LM Studio に一括送信
├ 日本語ラベル生成
└ タグ補完
   ↓
【ステップ3: 手動編集】
ユーザーが必要に応じて修正
```

#### AI設定（3段階フォールバック）

```
┌─ AI設定 ───────────────────────────────┐
│【ラベル・タグ自動生成】                │
│                                        │
│ 1. ◉ Claude API（優先）               │
│    APIキー: [●●●●●●●●●●] [変更]      │
│    状態: ✅ 認証成功                   │
│                                        │
│ 2. ◉ LM Studio（フォールバック）      │
│    URL: [http://localhost:1234___]     │
│    状態: ✅ 接続成功                   │
│                                        │
│ 3. ◉ 辞書ベース（最終手段）            │
│    常に有効                            │
│                                        │
│ 優先順位: Claude → LM Studio → 辞書   │
│                                        │
│ 完全オフライン動作:                    │
│ ☐ オンラインAPIを使用しない            │
│                                        │
│          [キャンセル] [保存]           │
└────────────────────────────────────────┘
```

#### 初回起動時のAI生成

```
┌─ 初回セットアップ ─────────────────────┐
│ ワイルドカード読み込み完了             │
│                                        │
│ 検出: 2,450プロンプト                  │
│ ├ 日本語ラベル付き: 1,200 (49%)        │
│ └ ラベルなし: 1,250 (51%)              │
│                                        │
│【AI自動生成（推奨）】                  │
│ 使用するAI: Claude API (Haiku)         │
│                                        │
│ 推定時間: 約5-10分                     │
│ 推定コスト: $0.09-0.10                 │
│ (1,250プロンプト × 約200トークン)      │
│                                        │
│ [後で] [自動生成開始]                  │
└────────────────────────────────────────┘
```

#### CSV最終形（label_sourceカラム追加）

```csv
id,source_file,label_ja,label_en,prompt,tags,label_source
tipo_play_14,tipo_play.txt,服着たままオナニー,clothed masturbation,clothed masturbation,"clothed,masturbation,服,オナニー",auto_extract
beach_1,ビーチ.txt,トロピカルビーチ,tropical beach,"tropical beach, white sand...","beach,tropical,ビーチ,リゾート,海",ai_generated
custom_001,手動入力,服の上から愛撫,fondling over clothes,"crotch_grab,fondling...","愛撫,服,crotch_grab,fondling",manual
```

**label_source値:**
- `auto_extract`: テーブル型から自動抽出
- `ai_generated`: AI生成（Claude / LM Studio）
- `manual`: ユーザー手動入力
- `auto_word_split`: 単語分割のみ

---

### 9.14 セキュアなAPIキー管理（確定版）

#### 暗号化方式

**3層セキュリティ:**
1. **暗号化**: Fernet（AES128ベース）
2. **マスターキー**: OSキーチェーンに保存（Windows資格情報マネージャー等）
3. **ファイルパーミッション**: 読み取り専用（600）

```python
from cryptography.fernet import Fernet
import keyring

class SecureAPIKeyManager:
    APP_NAME = "Pfft_maker"

    def __init__(self):
        self._api_key_cache = None

    def get_api_key(self):
        """必要な時に自動で復号化"""
        if not self._api_key_cache:
            self._api_key_cache = self._decrypt_from_file()
        return self._api_key_cache

    def on_app_close(self):
        """アプリ終了時にメモリクリア"""
        self._api_key_cache = None
```

#### API設定画面

```
┌─ Claude API設定 ───────────────────────┐
│                                        │
│ APIキー:                               │
│ [●●●●●●●●●●●●●●●●●●●●] [表示] [変更]│
│                                        │
│ 状態: ✅ 認証成功                      │
│ 使用モデル: [Haiku ▼]                 │
│                                        │
│ 🔒 セキュリティ:                      │
│ • 暗号化してファイルに保存             │
│ • OSが安全に管理                       │
│ • 他ユーザーからアクセス不可           │
│                                        │
│ [接続テスト] [削除]                    │
│                                        │
│          [キャンセル] [保存]           │
└────────────────────────────────────────┘
```

#### セキュリティチェックリスト

✅ APIキーは暗号化保存（Fernet AES128）
✅ マスターキーはOSキーチェーン管理
✅ ファイルパーミッション制限（600）
✅ アプリ終了時にメモリクリア
✅ ログにAPIキーを出力しない
✅ 設定ファイルは.gitignore
✅ UI上ではマスク表示

---

### 9.15 出力機能（確定版）

#### 出力設定UI

```
┌─ 出力設定 ─────────────────────────────┐
│ 出力対象: 全30シーン                   │
│                                        │
│ 出力先:                                │
│ ◉ ファイル                             │
│   ファイル名: [学園メイド_prompts.txt] │
│   保存先: [E:\works\学園メイド\___]    │
│           [参照...]                    │
│                                        │
│ ○ クリップボード                       │
│                                        │
│ オプション:                            │
│ ☑ 完成済みシーンのみ                   │
│ ☐ シーン番号をコメントで追記           │
│                                        │
│          [キャンセル] [出力]           │
└────────────────────────────────────────┘
```

#### 出力形式

**ファイル出力（学園メイド_prompts.txt）:**
```
clothed masturbation, school infirmary, __キャラ/SAYA__, BREAK, __posing/arm__, BREAK, masterpiece, best quality
deepthroat, classroom interior, __キャラ/SAYA__, BREAK, __posing/leg__, BREAK, masterpiece, best quality
exhibitionism, school rooftop, __キャラ/SAYA__, BREAK, standing, spread legs, BREAK, masterpiece, best quality
...
(30行 = Stable Diffusionで30枚生成)
```

**クリップボード出力:**
- 同じ内容がクリップボードにコピー
- すぐにPrompts from file or textboxに貼り付け可能

#### プロジェクトファイル内の出力履歴

```json
{
  "metadata": {
    "output_history": [
      {
        "date": "2025-01-15 14:30",
        "output_file": "学園メイド_prompts.txt",
        "output_path": "E:\\works\\学園メイド\\",
        "scenes_count": 30,
        "output_type": "file"
      },
      {
        "date": "2025-01-15 16:45",
        "output_type": "clipboard",
        "scenes_count": 25
      }
    ]
  }
}
```

---

## 10. 更新された次回作業項目

### Phase 1: 残りの仕様確定
- [x] 検索機能の詳細設計 ✅
- [ ] 技術スタックの決定（Python/JavaScript等）
- [x] 出力形式の最終確認 ✅
- [x] 30シーン管理UI ✅
- [x] 共通プロンプト機能 ✅
- [x] テンプレート機能 ✅
- [x] AI自動生成機能 ✅
- [x] APIキー管理 ✅

### Phase 2: 要件定義書作成
- [ ] `requirements.md` - 機能要件定義書
- [ ] `technical_requirements.md` - 技術要件定義書
- [ ] `CLAUDE.md` - 開発ガイド

### Phase 3: 設計・実装
- [ ] データモデル詳細設計
- [ ] UI モックアップ作成
- [ ] プロトタイプ開発

---

## 11. 確定事項サマリー

### コア機能（確定）
✅ ワイルドカードパーサー（4パターン対応）
✅ CSV管理への移行方針（日本語ラベル・タグ管理）
✅ ライブラリUI（2ステップ選択、+ボタンで明確な区別）
✅ 固定テキスト/ワイルドカード挿入の明確な区別
✅ BREAK仕様（手動挿入、連続不可）
✅ プロジェクトファイル管理（JSON形式、自動保存、世代バックアップ）
✅ ファイル監視・同期（リアルタイム+手動、ファイル優先原則）
✅ 検索機能（シンプル全文検索、リアルタイム）
✅ 30シーン管理UI（1シーン=1行=1画像）
✅ 共通プロンプト機能（品質タグ、LoRA）
✅ テンプレート機能（構成の保存・再利用）
✅ マニュアル編集（手動入力、インライン編集、右クリックメニュー）
✅ AI自動生成（Claude API / LM Studio / 辞書ベース）
✅ セキュアなAPIキー管理（暗号化、OSキーチェーン）
✅ 出力機能（ファイル/クリップボード、ファイル名・保存先指定）

### 未確定事項
❓ 技術スタック（言語・フレームワーク） - 最重要
❓ UI実装詳細（PyQt6 / Electron / その他）
❓ パフォーマンス最適化戦略
