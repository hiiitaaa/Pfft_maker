# Pfft_maker 問題点・リスク分析と修正案

作成日: 2025-01-15
ステータス: 要対応

---

## 🚨 重大な問題（即座に修正必要）

### 問題1: ワイルドカードファイルとCSVの同期ロジックが不完全

**現状の矛盾**:
- 「既存ワイルドカードファイルのクリーン化」と書いてあるが、実際には外部編集を想定している（ファイル監視機能あり）
- 元ファイルを書き換えるのか？それとも読み取り専用で参照するのか？不明確

**問題点**:
```
元ファイル: E:\EasyReforge\Model\wildcards\tipo_play.txt
↓
Pfft_maker読み込み → CSV化
↓
外部でファイル編集
↓
ファイル監視が検知 → CSV再構築
↓
【問題】ユーザーが手動追加した日本語ラベルが失われる可能性
```

**修正案**:
1. **ワイルドカードファイルは読み取り専用** - 絶対に書き換えない
2. **Pfft_maker独自のラベル管理JSON** - `labels_override.json` で日本語ラベルを別管理
3. **ファイル同期時のマージロジック**:
   ```
   元ファイル変更検知
   ↓
   新しいプロンプトをパース
   ↓
   既存のlabels_override.jsonと照合
   - プロンプト内容で完全一致 → ラベル引き継ぎ
   - 一致しない → 新規エントリとして追加、古いエントリは「削除済み」マーク
   ↓
   CSV再構築
   ```

**実装例**:
```python
# data/labels_override.json
{
  "tipo_play.txt": {
    "clothed masturbation": {
      "label_ja": "服着たままオナニー",
      "tags": ["服", "オナニー"],
      "user_modified": true
    }
  }
}
```

---

### 問題2: ワイルドカード形式のパス表記が未定義

**現状の曖昧さ**:
- ファイル: `E:\EasyReforge\Model\wildcards\背景\学校.txt`
- 挿入される形式: `__背景/学校__` ? `__学校__` ? `__wildcards/背景/学校__` ?

**リスク**:
- Stable Diffusion WebUIが期待する形式と一致しない
- サブディレクトリの扱いが不明

**調査必要**:
Stable Diffusion WebUIの「Dynamic Prompts」拡張の正確な仕様を確認する必要がある。

**仮修正案**（仕様確認後に確定）:
```python
# core/wildcard_formatter.py
def format_wildcard_path(file_path: Path, wildcard_root: Path) -> str:
    """ワイルドカード形式に変換

    Args:
        file_path: E:\EasyReforge\Model\wildcards\背景\学校.txt
        wildcard_root: E:\EasyReforge\Model\wildcards\

    Returns:
        __背景/学校__ (拡張子なし、Unixスタイル区切り)
    """
    relative_path = file_path.relative_to(wildcard_root)
    stem = relative_path.with_suffix('')  # 拡張子削除
    unix_path = str(stem).replace('\\', '/')  # Unixスタイル
    return f"__{unix_path}__"
```

---

### 問題3: BREAKの出力形式が不明確

**現状**:
プロンプトビルダーで「カンマ区切りで結合」とあるが、BREAKの前後のカンマ処理が不明。

**パターン1**: `clothed masturbation, BREAK, __posing/arm__`
**パターン2**: `clothed masturbation BREAK __posing/arm__`
**パターン3**: `clothed masturbation, BREAK\n__posing/arm__` (改行あり)

**正解を確認する必要がある**。

**仮修正案**（Stable Diffusion仕様確認後に確定）:
```python
def build_scene_prompt(self, scene: Scene) -> str:
    """シーンの最終プロンプトを構築"""
    parts = []

    for block in scene.blocks:
        if block.type == BlockType.BREAK:
            parts.append("BREAK")  # カンマなし
        else:
            parts.append(block.content)

    # BREAKは独立、それ以外はカンマ区切り
    result = []
    for i, part in enumerate(parts):
        if part == "BREAK":
            # 前のカンマを削除
            if result and result[-1].endswith(','):
                result[-1] = result[-1].rstrip(',')
            result.append(" BREAK ")
        else:
            result.append(part + ", ")

    return ''.join(result).rstrip(', ')
```

---

### 問題4: Windowsでのファイルパーミッション（600）が無効

**現状**:
`self.KEY_FILE.chmod(0o600)` とあるが、Windowsでは効果がない。

**Windows正しい実装**:
```python
import win32security
import ntsecuritycon as con

def set_file_security_windows(file_path: Path):
    """Windows ACLでファイル保護"""
    # 現在のユーザーのみアクセス許可
    user, domain, type = win32security.LookupAccountName("", win32api.GetUserName())
    sd = win32security.SECURITY_DESCRIPTOR()
    dacl = win32security.ACL()

    # 現在のユーザーにフルコントロール
    dacl.AddAccessAllowedAce(
        win32security.ACL_REVISION,
        con.FILE_ALL_ACCESS,
        user
    )

    sd.SetSecurityDescriptorDacl(1, dacl, 0)
    win32security.SetFileSecurity(
        str(file_path),
        win32security.DACL_SECURITY_INFORMATION,
        sd
    )
```

**または、より簡単な方法**:
```python
import os
import stat

def set_file_readonly_windows(file_path: Path):
    """Windows: 読み取り専用 + 隠しファイル化"""
    # 隠しファイル + システムファイル属性
    os.system(f'attrib +h +s "{file_path}"')
    # 読み取り専用
    file_path.chmod(stat.S_IREAD)
```

**修正案**: technical_requirements.mdのセキュリティセクションを更新

---

### 問題5: PyInstallerのUPX圧縮がアンチウイルスに誤検知される

**現状**:
`upx=True` と設定されているが、**Windows Defenderが高確率で誤検知**する。

**実際の事例**:
- UPX圧縮されたexeは「Trojan:Win32/Wacatac」として検出される
- ユーザーが実行できない
- 配布時に大問題

**修正案**:
```python
# build.spec
exe = EXE(
    ...
    upx=False,  # ❌ UPX無効化（必須）
    ...
)
```

**サイズ削減の代替案**:
- PyInstaller の `--exclude-module` で不要なモジュール除外
- `excludes=['tkinter', 'matplotlib', 'numpy']` など

---

## ⚠️ 重要な問題（設計変更推奨）

### 問題6: 共通プロンプトの挿入位置ロジックが曖昧

**現状の矛盾**:
- 設定画面: 「挿入位置: [BREAKの後 ▼]」
- シーン編集UI: 共通プロンプトブロックを自由に移動できる（[↑][↓]ボタン）

**どちらが正しい？**

**修正案A: 自動挿入（固定位置）**
```
シーンブロック
↓
[ユーザーのブロック]
[BREAK]
[共通プロンプト: LoRA] ← 自動挿入（移動不可🔒）
[BREAK]
[共通プロンプト: 品質タグ] ← 自動挿入（移動不可🔒）
```

**修正案B: 手動管理（自由配置）**
```
共通プロンプトは「テンプレート」として保存し、
新規シーン作成時に自動挿入するが、その後は通常ブロックとして扱う
→ ユーザーが自由に移動・削除可能
```

**推奨**: 修正案Bの方が柔軟性が高い

---

### 問題7: CSVのline_numberカラムの意味が不明確

**現状**:
- `line_number`: クリーン版での行番号？元ファイルの行番号？
- `original_number`: 元の番号（`14→` の14）

**混乱ポイント**:
- 元ファイルが変更されたら、line_numberは無効になる
- CSVとファイルの対応が取れなくなる

**修正案**:
```csv
id,source_file,original_line_number,original_number,label_ja,prompt,...
```

- `original_line_number`: 元ファイルの行番号（参考情報、変更されたら無効）
- `original_number`: `14→` の番号（ある場合のみ）

**重要**: line_numberは「参考情報」であり、プロンプト照合には使わない

---

### 問題8: ファイル監視の日本語ラベル保持ロジックが不完全

**現状**:
「プロンプト内容で照合（完全一致 or 部分一致）」とあるが、曖昧。

**問題ケース**:
```
元ファイル（旧）: clothed masturbation
元ファイル（新）: clothed masturbation, embarrassed  ← 編集された

完全一致？ → ❌ 一致しない
部分一致？ → ✅ 一致する（が、別のプロンプトも一致する可能性）
```

**修正案**:
```python
# 照合ロジック（優先度順）
def match_prompt(old_prompt: Prompt, new_line: str) -> bool:
    """プロンプトの同一性判定"""
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

**重要**: ユーザーに警告を表示
```
⚠ ファイルが変更されました
以下のプロンプトのラベルを引き継げませんでした：
- tipo_play:14 (旧: clothed masturbation)
  新しいプロンプト候補:
  1. clothed masturbation, embarrassed [推奨]
  2. （新規エントリとして追加）
```

---

### 問題9: シーン削除時の番号管理が不明確

**現状**: シーン3を削除した場合の動作が未定義

**パターンA: 番号付け直し**
```
削除前: [1:保健室] [2:教室] [3:屋上] [4:プール]
削除後: [1:保健室] [2:教室] [3:プール]  ← 番号がずれる
```
**問題**: 出力履歴との整合性が取れない

**パターンB: 欠番**
```
削除前: [1:保健室] [2:教室] [3:屋上] [4:プール]
削除後: [1:保健室] [2:教室] [4:プール]  ← 3が欠番
```
**問題**: 見た目が悪い

**修正案（推奨）**: パターンAで実装、出力履歴は `scene_name` で管理
```json
{
  "output_history": [
    {
      "date": "2025-01-15",
      "scenes": [
        {"scene_id": 1, "scene_name": "保健室"},
        {"scene_id": 2, "scene_name": "教室"},
        {"scene_id": 3, "scene_name": "屋上"}  // 削除済み
      ]
    }
  ]
}
```

---

### 問題10: テンプレート機能の「個別プロンプト内容」オプションの実用性

**現状**:
「☐ 個別プロンプト内容（オプション）」のチェックを外すと、ブロック構造だけ保存される。

**問題**:
- ブロック構造だけだと、空のブロックが並ぶ
- 実用性が低い

**修正案**:
テンプレートの用途を明確化:
1. **構成テンプレート**: シーン数、ブロック数だけ（プレースホルダー）
2. **完全テンプレート**: プロンプト内容も含む（コピー）

```
【構成テンプレート】
シーン1: [空の固定ブロック] → [BREAK] → [空のワイルドカードブロック]
→ ユーザーが埋める

【完全テンプレート】
シーン1: [clothed masturbation] → [BREAK] → [__posing/arm__]
→ そのまま使える、微調整のみ
```

---

### 問題11: 出力オプション「完成済みシーンのみ」の判定基準が不明確

**現状**: 完成の定義がない

**修正案**:
```python
# models/scene.py
def is_completed(self) -> bool:
    """完成済みかチェック"""
    # 最低1個のプロンプトブロックが必要
    prompt_blocks = [b for b in self.blocks
                    if b.type in [BlockType.FIXED_TEXT, BlockType.WILDCARD]]
    return len(prompt_blocks) > 0

# または、ユーザーが手動でマーク
@dataclass
class Scene:
    ...
    is_marked_completed: bool = False  # ユーザーが✓マーク
```

**UI**:
```
シーン編集パネル
[シーン: 1:保健室 ▼]  [☑ 完成]  ← ユーザーがチェック
```

---

## 📊 中程度の問題（改善推奨）

### 問題12: AI自動生成のコスト見積もりが甘い

**現状**: 「推定コスト: $0.50-1.00」

**実際の計算**:
```
前提:
- 1,250プロンプト
- Claude Haiku: $0.25/1M input tokens, $1.25/1M output tokens
- プロンプトテンプレート: ~150 tokens/request
- 平均プロンプト長: ~50 tokens
- 出力: ~20 tokens (日本語ラベル)

計算:
Input: 1,250 * (150 + 50) = 250,000 tokens = $0.06
Output: 1,250 * 20 = 25,000 tokens = $0.03
合計: $0.09

→ 見積もりが10倍高い
```

**修正案**: 正確なコスト計算式を実装
```python
def estimate_cost(prompt_count: int, model: str = "haiku") -> float:
    """コスト見積もり"""
    COSTS = {
        "haiku": {"input": 0.25, "output": 1.25},  # per 1M tokens
        "sonnet": {"input": 3.0, "output": 15.0}
    }

    template_tokens = 150
    avg_prompt_tokens = 50
    output_tokens = 20

    input_total = prompt_count * (template_tokens + avg_prompt_tokens)
    output_total = prompt_count * output_tokens

    cost = (input_total / 1_000_000 * COSTS[model]["input"] +
            output_total / 1_000_000 * COSTS[model]["output"])

    return round(cost, 2)
```

---

### 問題13: 検索のパフォーマンス問題

**現状**: 「リアルタイム検索」で入力中に結果更新

**問題**:
- 2,000プロンプト × 5カラム = 10,000回の文字列比較
- 毎回文字入力で実行 → UIが重い

**修正案**: デバウンス処理
```python
# ui/library_panel.py
from PyQt6.QtCore import QTimer

class LibraryPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._execute_search)

        self.search_bar.textChanged.connect(self._on_search_input)

    def _on_search_input(self, text: str):
        """入力後300ms待機してから検索実行"""
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms後に実行

    def _execute_search(self):
        """実際の検索実行"""
        query = self.search_bar.text()
        results = self.search_engine.search(query)
        self.update_tree(results)
```

---

### 問題14: ワイルドカード展開候補表示の実装困難性

**現状**: プレビューで「ワイルドカード展開候補」を表示

**問題**:
```
シーンに3個のワイルドカードがある場合:
- __posing/arm__ (10候補)
- __posing/leg__ (8候補)
- __angle/camera__ (15候補)

全組み合わせ: 10 × 8 × 15 = 1,200パターン
→ 表示不可能
```

**修正案**: 個別ファイルの候補のみ表示
```
【ワイルドカード展開候補】
posing/arm:
 • arms crossed
 • arms up
 • arms behind back
 ...

posing/leg:
 • standing
 • sitting
 ...
```

---

### 問題15: タグ自動生成の単語分割ロジックが不明確

**現状**: 「単語分割で自動生成」

**問題**:
- `school_infirmary` → `school`, `infirmary` ?
- `clothed masturbation` → `clothed`, `masturbation` ?
- 日本語はどうする？（形態素解析は実装していない）

**修正案**:
```python
def generate_tags_auto(prompt: str) -> List[str]:
    """自動タグ生成（シンプル版）"""
    # 1. カンマ区切り
    parts = [p.strip() for p in prompt.split(',')]

    # 2. アンダースコア・スペース区切り
    tags = []
    for part in parts:
        words = re.split(r'[_\s]+', part)
        tags.extend(words)

    # 3. 重複削除・小文字化
    tags = list(set(w.lower() for w in tags if w))

    return tags[:10]  # 最大10タグ
```

---

### 問題16: プロジェクトの自動保存時の競合リスク

**現状**: 「編集後30秒で自動保存」

**問題**:
- ネットワークドライブに保存している場合、書き込み失敗
- ファイルロック機能がない

**修正案**:
```python
def auto_save(self):
    """自動保存（エラーハンドリング付き）"""
    try:
        # 一時ファイルに保存
        temp_path = self.project_path.with_suffix('.pfft.tmp')
        self._save_to_file(temp_path)

        # 成功したら本番ファイルに上書き
        temp_path.replace(self.project_path)

        logger.info("Auto-saved successfully")
    except Exception as e:
        logger.error(f"Auto-save failed: {e}")
        # ユーザーに通知バナー表示
        self.show_notification("自動保存に失敗しました。手動保存を推奨します。")
```

---

### 問題17: ライブラリの「最近使用」の更新タイミングが不明確

**現状**: CSVの`last_used`カラム

**問題**:
- いつ更新？ブロック挿入時？シーン保存時？
- CSVの頻繁な書き込みでパフォーマンス低下

**修正案**:
```python
# メモリ上でキャッシュ、アプリ終了時にまとめて書き込み
class LibraryManager:
    def __init__(self):
        self.usage_cache = {}  # {prompt_id: last_used_datetime}

    def on_prompt_used(self, prompt_id: str):
        """プロンプト使用時（メモリ更新のみ）"""
        self.usage_cache[prompt_id] = datetime.now()

    def save_usage_history(self):
        """アプリ終了時にCSVに書き込み"""
        for prompt_id, last_used in self.usage_cache.items():
            self.df.loc[self.df['id'] == prompt_id, 'last_used'] = last_used
        self.save_library(self.df)
```

---

### 問題18: 文字エンコーディング自動検出の精度問題

**現状**: chardetで自動検出

**問題**:
- 短いファイル（数行）だと誤判定
- 日本語の場合、Shift_JIS vs UTF-8の誤判定

**修正案**: フォールバックロジック
```python
def read_file_with_fallback(file_path: Path) -> str:
    """エンコーディング自動検出（フォールバック付き）"""
    # 試行順序
    encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932']

    for encoding in encodings:
        try:
            with file_path.open('r', encoding=encoding) as f:
                content = f.read()
            logger.info(f"Detected encoding: {encoding}")
            return content
        except UnicodeDecodeError:
            continue

    # 最終手段: chardet
    with file_path.open('rb') as f:
        raw = f.read()
    detected = chardet.detect(raw)
    encoding = detected['encoding'] or 'utf-8'

    return raw.decode(encoding, errors='replace')  # エラー時は置換
```

---

## 📝 軽微な問題（将来対応可）

### 問題19: シーン番号コメントの形式が未定義

**現状**: 「☐ シーン番号をコメントで追記」

**問題**: Stable Diffusion WebUIがコメントとして認識する形式が不明

**調査必要**: Prompts from file機能でコメントが使えるか？

**仮実装**:
```
# Scene 1: 保健室
clothed masturbation, school infirmary, ...
# Scene 2: 教室
deepthroat, classroom interior, ...
```

---

### 問題20: キーボードショートカットの競合

**現状**: `Ctrl + →` / `Ctrl + ←`

**問題**: PyQt6アプリ内では問題ないが、ユーザーの習慣と異なる可能性

**代替案**:
- `Ctrl + Tab` / `Ctrl + Shift + Tab` （タブ切り替えの標準）
- `Alt + →` / `Alt + ←`
- カスタマイズ可能にする

---

### 問題21: ブロックの複数選択の実装複雑性

**現状**: 「複数ブロック選択 → まとめて移動/削除」

**問題**: PyQt6での実装が複雑、Phase 1で必要？

**修正案**: Phase 2に延期、まずは単一選択で実装

---

### 問題22: プロジェクトバックアップディレクトリの場所が不明確

**現状**: `.backup/` ディレクトリ

**問題**: プロジェクトファイルと同じディレクトリ？アプリのデータディレクトリ？

**修正案**:
```
プロジェクトと同じディレクトリに作成:
E:\works\学園メイド\
├── 学園メイドCG集.pfft
└── .pfft_backup\
    ├── 学園メイドCG集_20250120_1430.pfft
    └── ...
```

---

### 問題23: CSVとJSONの混在による複雑性

**現状**:
- プロンプトライブラリ: CSV
- プロジェクト: JSON
- カテゴリ設定: JSON

**問題**: データ管理が複雑、同期の問題

**長期的修正案**: SQLite移行を検討（Phase 3以降）

---

### 問題24: パス区切り文字の統一性

**現状**: Windowsパス vs Unix風パス

**修正案**: 内部処理はすべて `pathlib.Path` 使用
```python
# NG
file_path = "E:\\EasyReforge\\Model\\wildcards\\tipo_play.txt"

# OK
file_path = Path("E:/EasyReforge/Model/wildcards/tipo_play.txt")
# または
file_path = Path("E:\\EasyReforge\\Model\\wildcards\\tipo_play.txt")

# pathlib が自動的に処理
```

---

### 問題25: ワイルドカードファイルのサブディレクトリ対応

**現状**: カテゴリ自動分類

**問題**: 深い階層（`背景/学校/教室/1-A.txt`）の扱いが不明確

**修正案**: 最大2階層までサポート、それ以上は「その他」カテゴリ
```python
def extract_category(file_path: Path, wildcard_root: Path) -> str:
    """カテゴリ抽出"""
    relative = file_path.relative_to(wildcard_root)
    parts = relative.parts[:-1]  # ファイル名を除く

    if len(parts) == 0:
        return "その他"
    elif len(parts) == 1:
        return parts[0]  # 例: "背景"
    else:
        return f"{parts[0]}/{parts[1]}"  # 例: "背景/学校"
```

---

## ✅ 優先度付き修正ロードマップ

### 最優先（Phase 1開始前に解決）
1. ✅ ワイルドカードファイルとCSVの同期ロジック明確化 → `labels_override.json`導入
2. ✅ ワイルドカード形式のパス表記定義 → Stable Diffusion仕様確認必要
3. ✅ BREAKの出力形式確認 → Stable Diffusion仕様確認必要
4. ✅ Windowsファイルパーミッション修正
5. ✅ UPX圧縮無効化

### 高優先（Phase 1実装時に解決）
6. 共通プロンプト挿入位置ロジック明確化
7. CSVカラム定義の整理（line_number → original_line_number）
8. ファイル監視の照合ロジック改善
9. シーン削除時の番号管理定義
10. 完成シーン判定基準の実装

### 中優先（Phase 2で対応）
11. 検索のデバウンス処理
12. ワイルドカード展開候補表示の簡略化
13. タグ自動生成ロジックの実装
14. 自動保存のエラーハンドリング
15. エンコーディング検出のフォールバック

### 低優先（Phase 3以降）
16. テンプレート機能の用途明確化
17. AIコスト見積もりの正確な実装
18. ライブラリ使用履歴のキャッシュ化
19. キーボードショートカットのカスタマイズ
20. SQLite移行検討

---

## 📋 次のアクション

1. **Stable Diffusion WebUI仕様確認**（最優先）
   - ワイルドカード形式の正確なパス表記
   - BREAKの正しい出力形式
   - Prompts from fileのコメント対応

2. **requirements.md / technical_requirements.md 更新**
   - 上記の修正内容を反映
   - 曖昧な記述を明確化

3. **Phase 1実装開始**
   - データモデル実装
   - ワイルドカードパーサー実装（修正版）

---

**このドキュメントを確認後、requirements.mdとtechnical_requirements.mdを更新します。**
