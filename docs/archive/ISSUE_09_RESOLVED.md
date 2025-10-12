# 問題9: シーン削除時の番号管理の定義 - 解決記録

作成日: 2025-10-12
問題番号: 9
ステータス: ✅ 解決済み

---

## 問題の概要

**タイトル**: シーン削除時の番号管理が不明確

**問題内容**:
シーンを削除した際の番号管理方法が未定義で、実装時に混乱を招く可能性がありました。

**該当箇所**:
- requirements.md: FR-011（30シーン管理）
- technical_requirements.md: core/project_manager.py

---

## 検討した選択肢

### パターンA: 番号付け直し（採用）

**概要**: シーンを削除すると、以降のシーン番号が自動的に詰まる

**動作例**:
```
削除前: [1:保健室] [2:教室] [3:屋上] [4:プール]
シーン3削除
削除後: [1:保健室] [2:教室] [3:プール]  ← 番号が詰まる
```

**メリット**:
- ✅ UI上は常に連番で表示され、ユーザーが混乱しない
- ✅ 実装がシンプル（配列のインデックスとして扱える）
- ✅ 見た目が綺麗

**デメリット**:
- 出力履歴との整合性問題 → `scene_name`で管理することで解決

---

### パターンB: 欠番（不採用）

**概要**: シーンを削除しても、番号を詰めずに欠番として扱う

**動作例**:
```
削除前: [1:保健室] [2:教室] [3:屋上] [4:プール]
シーン3削除
削除後: [1:保健室] [2:教室] [4:プール]  ← 3が欠番
```

**デメリット**:
- ❌ 見た目が不自然
- ❌ 30シーン全体での欠番管理が複雑
- ❌ UIの実装が煩雑になる

---

## 採用した解決策

**パターンA（番号付け直し方式）を採用**

**理由**:
1. UIがシンプルで、常に連番表示
2. 実装が容易（配列のインデックスとして扱える）
3. ユーザーの柔軟性を重視する設計思想に合致
4. 出力履歴の問題は `scene_name` による管理で解決可能

---

## 実施した変更

### 1. requirements.md FR-011の更新

**追加内容**:

```markdown
**シーン削除時の動作**:
- **番号付け直し方式**: シーンを削除すると、以降のシーン番号が自動的に詰まる
- **例**:
  ```
  削除前: [1:保健室] [2:教室] [3:屋上] [4:プール]
  シーン3削除
  削除後: [1:保健室] [2:教室] [3:プール]  ← 番号が詰まる
  ```
- **出力履歴の管理**: シーン番号ではなく `scene_name` で履歴を管理することで整合性を保つ
- **メリット**: UI上は常に連番で表示され、ユーザーが混乱しない

**出力履歴の記録形式**:
```json
{
  "output_history": [
    {
      "date": "2025-01-15 14:30",
      "output_file": "学園メイド_prompts.txt",
      "scenes": [
        {"scene_name": "保健室", "prompt_preview": "clothed masturbation..."},
        {"scene_name": "教室", "prompt_preview": "deepthroat..."},
        {"scene_name": "屋上", "prompt_preview": "exhibitionism..."}
      ]
    }
  ]
}
```
```

---

### 2. technical_requirements.md project_manager.pyの更新

**追加メソッド**:

```python
def delete_scene(self, project: Project, scene_id: int):
    """シーンを削除（番号付け直し方式）

    Args:
        project: プロジェクトオブジェクト
        scene_id: 削除するシーンのID（1から始まる番号）

    Note:
        削除後、以降のシーンのscene_idを自動的に詰める
        例: シーン3削除 → [1,2,4,5] → [1,2,3,4]
    """
    # シーンを削除
    project.scenes = [s for s in project.scenes if s.scene_id != scene_id]

    # 以降のシーンの番号を詰める
    for i, scene in enumerate(project.scenes, start=1):
        scene.scene_id = i
```

---

## 実装への影響

### データモデル（models/scene.py）

**変更不要**: `scene_id`は既存のフィールドをそのまま使用

```python
@dataclass
class Scene:
    """シーンモデル"""
    scene_id: int  # 1から始まる連番（削除時に自動で詰まる）
    scene_name: str
    is_completed: bool = False
    blocks: List['Block'] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
```

---

### プロジェクトファイル（FR-010）

**出力履歴の管理方法を変更**:

**従来（シーン番号で管理）**:
```json
{
  "output_history": [
    {
      "date": "2025-01-15",
      "scenes": [1, 2, 3]  // シーン番号のみ → 削除後に無効
    }
  ]
}
```

**新方式（シーン名で管理）**:
```json
{
  "output_history": [
    {
      "date": "2025-01-15",
      "output_file": "学園メイド_prompts.txt",
      "scenes": [
        {"scene_name": "保健室", "prompt_preview": "clothed..."},
        {"scene_name": "教室", "prompt_preview": "deepthroat..."},
        {"scene_name": "屋上", "prompt_preview": "exhibitionism..."}
      ]
    }
  ]
}
```

**メリット**:
- シーン番号が変わっても、シーン名で履歴を追跡可能
- プロンプトのプレビューも記録され、後から確認しやすい

---

### UI（ui/scene_editor_panel.py）

**シーン削除ボタンの実装**:

```python
class SceneEditorPanel(QWidget):
    """シーン編集パネル"""

    def on_delete_scene_clicked(self):
        """シーン削除ボタンがクリックされたとき"""
        current_scene_id = self.get_current_scene_id()

        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "シーン削除",
            f"シーン{current_scene_id}を削除しますか？\n"
            "以降のシーン番号は自動的に詰まります。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # シーン削除
            self.project_manager.delete_scene(self.project, current_scene_id)

            # UI更新
            self.refresh_scene_list()

            # 完了通知
            QMessageBox.information(
                self,
                "削除完了",
                f"シーン{current_scene_id}を削除しました。\n"
                "シーン番号を自動的に詰めました。"
            )
```

---

## 影響範囲

### 更新されたファイル
1. `requirements.md` (FR-011)
2. `technical_requirements.md` (core/project_manager.py)

### 新規作成されたファイル
- `ISSUE_09_RESOLVED.md` （本ファイル）

### 影響を受ける機能
- FR-011: 30シーン管理
- FR-010: プロジェクト保存・読み込み（出力履歴の形式変更）
- UI: シーン編集パネル、シーン一覧タブ

---

## テスト項目

### 単体テスト
- [ ] ProjectManager.delete_scene()が正しくシーンを削除することを確認
- [ ] 削除後、以降のシーン番号が詰まることを確認
- [ ] シーン1を削除した場合、正しく動作することを確認
- [ ] 最後のシーンを削除した場合、正しく動作することを確認

### 統合テスト
- [ ] シーン削除→プロジェクト保存→読み込みで整合性が保たれることを確認
- [ ] 出力履歴が`scene_name`で正しく記録されることを確認
- [ ] シーン削除後、出力履歴を参照しても問題ないことを確認

### UI/UXテスト
- [ ] シーン削除ボタンをクリックした際、確認ダイアログが表示されることを確認
- [ ] 削除後、UI上のシーン番号が正しく更新されることを確認
- [ ] シーン一覧タブが正しく更新されることを確認

---

## 補足事項

### なぜ番号付け直し方式を採用したのか？

**1. UIの一貫性**
- 常に連番で表示されるため、ユーザーが混乱しない
- 「シーン3」と表示されているのに、内部的にはシーン4だった...という事態を防ぐ

**2. 実装の簡潔性**
- 配列のインデックスとしてそのまま扱える
- 欠番管理のための複雑なロジックが不要

**3. 柔軟性重視の設計思想に合致**
- ユーザーは自由にシーンを追加・削除できる
- 番号を気にせず、シーン名で管理できる

### 出力履歴の整合性問題をどう解決したか？

**問題**:
```
初回出力: シーン1,2,3を出力
シーン2削除
2回目出力: シーン1,2を出力（元のシーン1,3）
→ 履歴上は同じ「シーン2」だが、内容が異なる！
```

**解決策**:
```json
{
  "output_history": [
    {
      "date": "2025-01-15 14:30",
      "scenes": [
        {"scene_name": "保健室"},  // ← シーン名で管理
        {"scene_name": "教室"},
        {"scene_name": "屋上"}
      ]
    }
  ]
}
```

シーン名で履歴を管理することで、シーン番号が変わっても追跡可能になる。

### 将来的な拡張可能性

もし将来的に「シーンの並び替え」機能が必要になった場合、同じロジックで対応可能:

```python
def reorder_scenes(self, project: Project, new_order: List[int]):
    """シーンを並び替え"""
    # 新しい順序でシーンをソート
    project.scenes.sort(key=lambda s: new_order.index(s.scene_id))

    # シーン番号を付け直し
    for i, scene in enumerate(project.scenes, start=1):
        scene.scene_id = i
```

---

## 結論

問題9は**番号付け直し方式**を採用することで解決した。

**キーポイント**:
- ✅ UIがシンプルで、常に連番表示
- ✅ 実装が容易
- ✅ 出力履歴は`scene_name`で管理
- ✅ 柔軟性重視の設計思想に合致

**次のステップ**:
- 問題8（ファイル監視の照合ロジック改善）は**オプション**なので、Phase 2以降に延期
- 問題10（テンプレート機能の実用性検討）へ進む

---

**承認日**: 2025-10-12
**承認者**: ユーザー
