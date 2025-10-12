# Pfft_maker 現在の進捗

作成日: 2025-10-12
最終更新: 2025-10-12

---

## 📊 全体進捗

| フェーズ | 状態 | 進捗 |
|---------|------|------|
| Phase 1: 技術調査 | ✅ 完了 | 100% |
| Phase 2: ドキュメント整備 | ✅ 完了 | 100% |
| Phase 3: 問題解決（25個） | ✅ 完了 | 100% (25/25) |
| Phase 4: 実装準備 | ⏳ 準備完了 | 0% |

**全体進捗**: Phase 3完了（100%）

---

## ✅ Phase 3: 解決済みの問題（25個）

### 重大な問題（5個）
1. ✅ ワイルドカードファイル同期 → 独立コピー方式
2. ✅ ワイルドカード形式 → `__folder/file__`
3. ✅ BREAK仕様 → `prompt, BREAK, prompt`
4. ✅ Windows ACL → pywin32実装
5. ✅ UPX圧縮誤検知 → `upx=False`

### 重要な問題（6個）
6. ✅ 共通プロンプト → 初期テンプレート方式
7. ✅ CSVカラム定義 → `original_line_number`明確化
8. ✅ ファイル監視照合 → `original_number`優先
9. ✅ シーン削除 → 番号付け直し方式
10. ✅ テンプレート機能 → 構成/完全の2種類
11. ✅ 完成シーン判定 → 手動マーク方式

### 中優先度の問題（7個）
12. ✅ AIコスト見積もり → 正確な計算式
13. ✅ 検索デバウンス → 300ms待機
14. ✅ ワイルドカード展開候補 → 個別ファイル表示
15. ✅ タグ自動生成 → シンプルな単語分割
16. ✅ 自動保存エラーハンドリング → 一時ファイル方式
17. ✅ ライブラリ使用履歴のキャッシュ化 → メモリキャッシュ方式
18. ✅ エンコーディング検出 → フォールバック方式

### 低優先度の問題（7個）
19. ✅ シーン番号コメント形式 → オプション実装
20. ✅ キーボードショートカット → Ctrl/Alt+矢印
21. ✅ ブロック複数選択 → Phase 2延期
22. ✅ バックアップディレクトリの場所 → `.pfft_backup/`
23. ✅ CSVとJSONの混在 → 現行維持（Phase 3でSQLite検討）
24. ✅ パス区切り文字の統一 → `pathlib.Path`
25. ✅ サブディレクトリ対応 → 最大2階層

---

## 🎉 すべての問題を解決！

**Phase 3完了**:
- 全25問題の解決完了
- technical_requirements.md Section 12追加（約600行）
- 実装準備完了

---

## 🎯 次回の作業

**次のタスク**: Phase 4（実装開始）

**実施内容**:
1. ディレクトリ構造作成（src/, resources/, tests/）
2. データモデル実装（models/）
3. ワイルドカードパーサー実装（core/wildcard_parser.py）
4. 基本UI実装（ui/main_window.py）

**詳細**: `NEXT_TASK.md` を参照
**開発ガイド**: `docs/archive/CLAUDE.md` を参照

---

## 📂 ドキュメント構成

### ルートディレクトリ
- `requirements.md` - 機能要件定義書 v1.1 ✅
- `technical_requirements.md` - 技術要件定義書 v1.1 ✅
- `ISSUES_AND_FIXES.md` - 全25問題のリスト ✅
- `NEXT_TASK.md` - 次回タスクの詳細 ✅
- `CURRENT_PROGRESS.md` - 現在の進捗（本ファイル） ✅
- `PROGRESS_SUMMARY.md` - 全セッションの詳細記録 ✅
- `SESSION_HANDOFF.md` - セッション引き継ぎメモ ✅

### docs/archive/
- `CLAUDE.md` - 開発ガイド v1.1
- `requirements_discussion.md` - 要件検討メモ（元資料）
- `SPECIFICATIONS_CONFIRMED.md` - 確定仕様（問題2,3解決）
- `ISSUE_01_RESOLVED.md` - 問題1解決記録
- `ISSUE_04_05_RESOLVED.md` - 問題4,5解決記録
- `ISSUE_06_RESOLVED.md` - 問題6解決記録
- `ISSUE_07_RESOLVED.md` - 問題7解決記録
- `ISSUE_09_RESOLVED.md` - 問題9解決記録
- `ISSUE_10_RESOLVED.md` - 問題10解決記録
- `ISSUE_11_RESOLVED.md` - 問題11解決記録
- `ISSUE_12_RESOLVED.md` - 問題12解決記録
- `ISSUE_13_RESOLVED.md` - 問題13解決記録
- `ISSUE_14_RESOLVED.md` - 問題14解決記録
- `ISSUE_15_RESOLVED.md` - 問題15解決記録

---

## 💡 重要な設計思想

ユーザーの設計思想: **柔軟性を重視**

**適用例**:
- ✅ 共通プロンプト: 初期テンプレート、その後自由編集可能（問題6）
- ✅ 完成シーン: 手動マーク方式（問題11）
- ✅ タグ生成: 自動+AI+手動の3段階（問題15）

**今後の問題解決でも、この設計思想を適用する**

---

## 🔄 最近の変更（2025-10-12）

### ファイル構成の最適化
- **目的**: コンテキスト使用量の削減
- **実施内容**:
  - `docs/archive/` ディレクトリを作成
  - 解決済み問題ファイル（15個）をアーカイブに移動
  - 参照頻度の低いドキュメント（3個）をアーカイブに移動
  - 軽量版ファイル（NEXT_TASK.md, CURRENT_PROGRESS.md）を作成

### 移動したファイル
- ISSUE_*_RESOLVED.md（15個） → docs/archive/
- CLAUDE.md → docs/archive/
- requirements_discussion.md → docs/archive/
- SPECIFICATIONS_CONFIRMED.md → docs/archive/

### 新規作成したファイル
- `NEXT_TASK.md` - 次回タスクの詳細（軽量版）
- `CURRENT_PROGRESS.md` - 現在の進捗（軽量版、本ファイル）

---

**次回開始時**: `NEXT_TASK.md` を確認してください
