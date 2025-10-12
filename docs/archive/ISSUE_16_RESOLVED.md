# 問題16: プロジェクトの自動保存時の競合リスク - 解決記録

作成日: 2025-10-12
問題番号: 16
ステータス: ✅ 解決済み

---

## 問題の概要

**タイトル**: プロジェクトの自動保存時の競合リスク

**問題内容**:
requirements.mdに「編集後30秒で自動保存」と記述されているが、エラーハンドリングが不明確だった。

**曖昧な点**:
- ネットワークドライブに保存している場合、書き込み失敗の可能性
- ファイルロック機能がない
- 保存失敗時の挙動が未定義
- 一時ファイルを使用していない（保存中のクラッシュでファイル破損の可能性）

**該当箇所**:
- requirements.md: FR-010（プロジェクト保存・読み込み）
- technical_requirements.md: core/project_manager.py

---

## 採用した解決策

### 基本方針

**一時ファイル方式 + エラーハンドリング + UI通知**を採用

### 実装仕様

**自動保存の処理フロー**:

```python
def auto_save(self):
    """自動保存（エラーハンドリング付き）"""
    try:
        # 1. 一時ファイルに保存
        temp_path = self.project_path.with_suffix('.pfft.tmp')
        self._save_to_file(temp_path)

        # 2. 成功したら本番ファイルに上書き（アトミック操作）
        temp_path.replace(self.project_path)

        logger.info("Auto-saved successfully")

    except PermissionError as e:
        logger.error(f"Auto-save failed (Permission denied): {e}")
        self._show_notification(
            "自動保存に失敗しました",
            "理由: ファイルへのアクセス権限がありません\n\n手動保存を推奨します。",
            error=True
        )

    except OSError as e:
        logger.error(f"Auto-save failed (OS error): {e}")
        self._show_notification(
            "自動保存に失敗しました",
            "理由: ネットワークドライブへの書き込みがタイムアウトしました\n\n手動保存を推奨します。",
            error=True
        )

    except Exception as e:
        logger.error(f"Auto-save failed (unexpected error): {e}")
        self._show_notification(
            "自動保存に失敗しました",
            "理由: 予期しないエラーが発生しました\n\n手動保存を推奨します。",
            error=True
        )
```

### 処理ルール

1. **一時ファイル保存**: `project_name.pfft.tmp` に保存
2. **アトミック上書き**: `Path.replace()` でアトミックに本番ファイルに上書き
3. **エラー分類**:
   - `PermissionError`: アクセス権限エラー
   - `OSError`: ネットワークエラー、ディスクフルなど
   - `Exception`: その他の予期しないエラー
4. **ログ記録**: すべてのエラーをログに記録
5. **UI通知**: エラー時は通知バナーを表示、ユーザーに手動保存を推奨

---

## 実施した変更

### 1. requirements.md FR-010の更新

**追加内容**:

- 自動保存にエラーハンドリングを明記
- 一時ファイル方式の仕様を追加
- エラー通知UIの仕様を追加
- プロジェクトフォルダ構成に `.pfft.tmp` を追加

**変更箇所**: requirements.md:440-479行目

**追加された仕様**:
```markdown
**保存方式**:
- **自動保存**: 編集後30秒で自動保存（エラーハンドリング付き）
  - 一時ファイル（`.pfft.tmp`）に保存後、成功したら本番ファイルに上書き
  - 保存失敗時は通知バナー表示、手動保存を推奨
  - ネットワークドライブ、書き込みエラー、ファイルロック等に対応

**自動保存のエラーハンドリング**:
1. 一時ファイル（`project_name.pfft.tmp`）に保存
2. 保存成功 → 本番ファイル（`project_name.pfft`）に上書き（アトミック操作）
3. 保存失敗 → エラーログ記録 + UI通知バナー表示
4. 通知内容: 「⚠ 自動保存に失敗しました。手動保存を推奨します。」
```

---

### 2. technical_requirements.md core/project_manager.pyの更新

**追加内容**:

- `auto_save()` メソッドの完全な実装コード
- エラーハンドリングロジック（3種類のエラー分類）
- `_save_to_file()` ヘルパーメソッド
- `_show_notification()` ヘルパーメソッド
- 詳細なDocstring（処理フロー、Example、Note、Raises）

**変更箇所**: technical_requirements.md:392-482行目

**実装の特徴**:
- **アトミック操作**: `Path.replace()` を使用（Windowsでも安全）
- **エラー分類**: PermissionError、OSError、Exceptionを個別ハンドリング
- **ログ記録**: すべての成功・失敗をログに記録
- **UI通知**: エラー時のみ通知バナー表示

---

## 設計の詳細

### なぜ一時ファイル方式を採用したか？

**理由**:
1. **ファイル破損防止**: 保存中のクラッシュでも本番ファイルは安全
2. **アトミック操作**: `Path.replace()` は上書きをアトミックに実行
3. **ネットワークドライブ対応**: 書き込み失敗時も本番ファイルに影響なし
4. **Pythonの標準機能**: 追加ライブラリ不要、クロスプラットフォーム対応

### エラー通知UIの設計

**通知バナー仕様**:
```
┌─────────────────────────────────────────┐
│ ⚠ 自動保存に失敗しました              │
│                                        │
│ 理由: ネットワークドライブへの書き込み│
│       がタイムアウトしました           │
│                                        │
│ [手動保存] [詳細を表示] [閉じる]      │
└─────────────────────────────────────────┘
```

**ボタンの動作**:
- **[手動保存]**: 即座に手動保存ダイアログを表示
- **[詳細を表示]**: エラーログを表示
- **[閉じる]**: 通知を閉じる

### アトミック操作の保証

**`Path.replace()` の動作**:
- Windows: `ReplaceFile()` API を使用、アトミックな上書き
- Unix/Linux/Mac: `rename()` システムコールを使用、アトミックな上書き

**メリット**:
- 上書き中にクラッシュしても、元のファイルか新しいファイルのどちらかが確実に存在
- ファイルが中途半端に壊れることがない

---

## 影響範囲

### 更新されたファイル
1. `requirements.md` (FR-010) - 自動保存仕様を強化
2. `technical_requirements.md` (core/project_manager.py) - 実装コードを追加

### 新規作成されたファイル
- `docs/archive/ISSUE_16_RESOLVED.md` （本ファイル）

### 影響を受ける機能
- FR-010: プロジェクト保存・読み込み
- core/project_manager.py: 自動保存ロジック
- UI: 通知バナー表示機能（新規実装必要）

---

## 実装ガイドライン

### 実装タイミング

**Phase 1（MVP）で実装すべき機能**:
- ✅ `auto_save()` メソッドの基本実装
- ✅ 一時ファイル方式
- ✅ エラーログ記録
- ⏳ UI通知バナー

**Phase 2で実装すべき機能**:
- ⏳ エラー詳細表示機能
- ⏳ 自動リトライ機能（オプション）

### 使用例

```python
# 使用例1: 自動保存タイマーの設定
from PyQt6.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project_manager = ProjectManager()

        # 30秒ごとに自動保存
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.project_manager.auto_save)
        self.auto_save_timer.start(30000)  # 30秒 = 30000ms

    def on_edit(self):
        """シーン編集時"""
        # 編集フラグを立てる
        self.project_manager.has_unsaved_changes = True
```

```python
# 使用例2: UI通知バナーの実装
class NotificationManager:
    """通知バナー管理"""

    def show_notification(self, title: str, message: str, error: bool = False):
        """通知バナーを表示"""
        banner = QMessageBox()
        banner.setIcon(QMessageBox.Icon.Warning if error else QMessageBox.Icon.Information)
        banner.setWindowTitle(title)
        banner.setText(message)
        banner.setStandardButtons(
            QMessageBox.StandardButton.Save |  # 手動保存
            QMessageBox.StandardButton.Help |  # 詳細を表示
            QMessageBox.StandardButton.Close   # 閉じる
        )
        banner.exec()
```

---

## テスト項目

### 単体テスト

```python
# tests/test_project_manager_autosave.py
import pytest
from pathlib import Path
from src.core.project_manager import ProjectManager

def test_auto_save_success(tmp_path):
    """正常な自動保存"""
    manager = ProjectManager()
    manager.project_path = tmp_path / "test.pfft"
    manager.current_project = Project(name="test")

    manager.auto_save()

    # 本番ファイルが存在
    assert manager.project_path.exists()
    # 一時ファイルは削除されている
    assert not (tmp_path / "test.pfft.tmp").exists()

def test_auto_save_permission_error(tmp_path, monkeypatch):
    """アクセス権限エラー"""
    manager = ProjectManager()
    manager.project_path = tmp_path / "test.pfft"
    manager.current_project = Project(name="test")

    # _save_to_file() をモック化してPermissionErrorを発生させる
    def mock_save_to_file(file_path):
        raise PermissionError("Permission denied")

    monkeypatch.setattr(manager, "_save_to_file", mock_save_to_file)

    # エラーハンドリングが動作することを確認
    manager.auto_save()  # 例外が発生しないことを確認

def test_auto_save_network_error(tmp_path, monkeypatch):
    """ネットワークエラー"""
    manager = ProjectManager()
    manager.project_path = Path("Z:/nonexistent/test.pfft")  # ネットワークドライブ
    manager.current_project = Project(name="test")

    # _save_to_file() をモック化してOSErrorを発生させる
    def mock_save_to_file(file_path):
        raise OSError("Network timeout")

    monkeypatch.setattr(manager, "_save_to_file", mock_save_to_file)

    # エラーハンドリングが動作することを確認
    manager.auto_save()  # 例外が発生しないことを確認

def test_auto_save_no_project_loaded():
    """プロジェクト未ロード時"""
    manager = ProjectManager()
    manager.project_path = None
    manager.current_project = None

    # エラーが発生しないことを確認
    manager.auto_save()  # 何もせずに終了
```

---

## まとめ

問題16は**一時ファイル方式 + エラーハンドリング + UI通知**を採用することで解決した。

**キーポイント**:
- ✅ 一時ファイル方式でファイル破損を防止
- ✅ `Path.replace()` でアトミックな上書き
- ✅ 3種類のエラー分類（PermissionError、OSError、Exception）
- ✅ エラーログ記録とUI通知
- ✅ ネットワークドライブ対応
- ✅ クロスプラットフォーム対応（Pythonの標準機能のみ）

**次のステップ**:
- 問題18（エンコーディング検出のフォールバック）へ進む
- 問題17（ライブラリ使用履歴のキャッシュ化）へ進む

---

**承認日**: 2025-10-12
**承認者**: ユーザー
