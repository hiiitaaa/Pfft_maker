# 問題18: エンコーディング検出のフォールバック - 解決記録

作成日: 2025-10-12
ステータス: ✅ 解決済み
優先度: 中
カテゴリ: ファイル読み込み・信頼性

---

## 📋 問題の詳細

### 問題タイトル
文字エンコーディング自動検出の精度問題

### 現状の仕様
- chardetライブラリで文字エンコーディングを自動検出
- ワイルドカードファイル読み込み時に使用

### 問題点
1. **短いファイルでの誤判定**
   - 数行しかないファイルでは、chardetが誤ったエンコーディングを推測する可能性
   - サンプルデータが少ないため、推測精度が低下

2. **日本語ファイルでの誤判定**
   - Shift_JIS vs UTF-8 の誤判定が発生しやすい
   - 特に日本語の短い文字列（1-2行）では高確率で誤判定

3. **chardetへの過度な依存**
   - 検出失敗時のフォールバックロジックがない
   - ユーザーのファイルが読み込めない場合がある

### 該当箇所
- `requirements.md`: FR-001（ワイルドカードファイル読み込み）
- `technical_requirements.md`: core/wildcard_parser.py の `detect_encoding()` メソッド

---

## 💡 採用した解決策

### フォールバックロジックの実装

**基本方針**: 優先エンコーディングを順に試行し、すべて失敗した場合のみchardetを使用する

**試行順序**:
1. `utf-8-sig` (UTF-8 BOM付き)
2. `utf-8` (UTF-8 BOMなし)
3. `shift_jis` (Shift-JIS)
4. `cp932` (Windows-31J、Shift_JISの拡張)
5. **最終手段**: chardetで検出

**エラー時の動作**:
- すべてのエンコーディングでデコード失敗した場合でも、`errors='replace'` で文字を置換して読み込む
- 完全にファイルが読み込めない状況を回避

---

## 🔧 実装内容

### 1. requirements.md FR-001の更新

**追加内容**:
```markdown
**処理**:
1. **初回起動時**: 元ディレクトリから `E:\tool\Pfft_maker\wildcards\` に全ファイルをコピー
2. **エンコーディング自動検出**（フォールバック付き）:
   - 優先エンコーディング試行順序: `utf-8-sig` → `utf-8` → `shift_jis` → `cp932`
   - すべて失敗した場合: chardetライブラリで検出
   - デコードエラー時: `errors='replace'`で文字を置換して読み込み
   - 理由: 短いファイルや日本語ファイルでchardetの誤判定を防ぐため
3. **ファイルクリーン化**:
   ...
```

**更新場所**: requirements.md:66-72

---

### 2. technical_requirements.md の更新

**追加内容**: `core/wildcard_parser.py` の `detect_encoding()` メソッド実装

```python
def detect_encoding(self, file_path: Path) -> str:
    """文字エンコーディングを検出（フォールバック付き）

    優先エンコーディングを順に試行し、すべて失敗した場合はchardetで検出する。

    Args:
        file_path: 対象ファイルパス

    Returns:
        検出されたエンコーディング名（例: 'utf-8', 'shift_jis'）

    Note:
        - 短いファイルや日本語ファイルでのchardet誤判定を防ぐため、
          一般的なエンコーディングを優先的に試行する
        - デコードエラー時は errors='replace' で読み込む
    """
    import logging
    logger = logging.getLogger(__name__)

    # 試行順序（優先度順）
    encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932']

    # バイナリ読み込み
    with file_path.open('rb') as f:
        raw = f.read()

    # 優先エンコーディングで順次試行
    for encoding in encodings:
        try:
            raw.decode(encoding)
            logger.info(f"Detected encoding: {encoding} for {file_path.name}")
            return encoding
        except UnicodeDecodeError:
            continue

    # すべて失敗した場合: chardetで検出
    detected = chardet.detect(raw)
    encoding = detected['encoding'] or 'utf-8'
    confidence = detected.get('confidence', 0)

    logger.warning(
        f"Fallback to chardet: {encoding} (confidence: {confidence:.2f}) "
        f"for {file_path.name}"
    )

    return encoding
```

**更新場所**: technical_requirements.md:346-391

---

## 📊 実装のポイント

### 1. 優先エンコーディングの選定理由

| エンコーディング | 選定理由 |
|----------------|---------|
| `utf-8-sig` | UTF-8 BOM付きファイルに対応、最近のエディタでの保存に多い |
| `utf-8` | 最も一般的なエンコーディング、国際標準 |
| `shift_jis` | 日本語レガシーファイルで使用される |
| `cp932` | Windows環境の日本語ファイル（Shift_JISの拡張） |

### 2. 順次試行のメリット

- **高速**: 一般的なエンコーディングから試行するため、ほとんどのファイルで最初の1-2回で成功
- **正確**: chardetの推測に頼らず、実際にデコード可能かテストする
- **安全**: すべて失敗した場合のフォールバック（chardet）も用意

### 3. ログ出力による可視化

```python
logger.info(f"Detected encoding: {encoding} for {file_path.name}")
# → 成功時: どのエンコーディングが使用されたか記録

logger.warning(f"Fallback to chardet: {encoding} (confidence: {confidence:.2f}) for {file_path.name}")
# → chardetフォールバック時: 検出されたエンコーディングと信頼度を記録
```

**メリット**:
- デバッグ時に問題ファイルを特定しやすい
- ユーザーが誤ったエンコーディングのファイルを使っている場合、ログから気づける

---

## 🧪 テスト項目

実装時に以下のテストケースを検証すること:

### 1. 正常系テスト

| テストケース | 期待結果 |
|------------|---------|
| UTF-8 BOM付きファイル | `utf-8-sig` を返す |
| UTF-8 BOMなしファイル | `utf-8` を返す |
| Shift_JISファイル | `shift_jis` を返す |
| CP932ファイル | `cp932` を返す |

### 2. エッジケーステスト

| テストケース | 期待結果 |
|------------|---------|
| 1行のみの短いファイル (UTF-8) | `utf-8` を返す（chardetに頼らず） |
| 1行のみの日本語ファイル (Shift_JIS) | `shift_jis` を返す |
| 空ファイル | `utf-8` を返す（デフォルト） |
| バイナリファイル（画像等） | chardetで検出、または `utf-8` デフォルト |

### 3. フォールバックテスト

| テストケース | 期待結果 |
|------------|---------|
| 不明なエンコーディング | chardetで検出、ログに警告を出力 |
| chardet検出失敗 | `utf-8` をデフォルトで返す |

---

## ✅ 解決確認

### 更新したファイル
- ✅ `requirements.md` FR-001: エンコーディング検出の仕様を追加
- ✅ `technical_requirements.md` core/wildcard_parser.py: `detect_encoding()` メソッド実装

### 記録したファイル
- ✅ `docs/archive/ISSUE_18_RESOLVED.md` (本ファイル)

### 次回実装時の注意点
1. **ログレベル**: INFO（成功）、WARNING（chardetフォールバック）を適切に設定
2. **パフォーマンス**: 順次試行は数回で終わるため、パフォーマンス影響は軽微
3. **エラーハンドリング**: `errors='replace'` でデコードエラー時も読み込み可能にする

---

## 📝 関連問題

**類似の問題**:
- なし

**依存関係**:
- 問題1（ワイルドカードファイルとCSVの同期）: エンコーディング検出はファイル読み込みの前提

---

## 💭 備考

### 設計思想の適用
この解決策は、ユーザーの設計思想「**柔軟性を重視**」に基づいています:
- 複数のエンコーディングに対応
- フォールバックロジックで様々なファイルを読み込める
- chardetの誤判定に頼らず、実際のデコードテストで判定

### 今後の拡張可能性
- **ユーザー指定エンコーディング**: 設定でデフォルトエンコーディングを指定可能にする
- **エンコーディングキャッシュ**: 一度検出したファイルのエンコーディングをキャッシュして高速化

---

**解決日**: 2025-10-12
**解決者**: Claude
