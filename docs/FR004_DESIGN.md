# FR-004: 自作プロンプトライブラリ - 設計書

作成日: 2025-10-13
担当者: Claude

---

## 概要

シーン編集中に作成したプロンプトをライブラリに保存し、再利用できる機能を実装します。

### 目的
- シーン編集中に作成した優良なプロンプトを保存
- プロジェクト間でプロンプトを再利用
- 使用履歴を記録し、よく使うプロンプトを把握

---

## データモデル設計

### 1. CustomPromptモデル

```python
@dataclass
class CustomPrompt(SerializableMixin):
    """自作プロンプトモデル

    ユーザーが作成・保存したプロンプトを管理します。

    Attributes:
        id: 一意識別子（custom_001, custom_002, ...）
        prompt: プロンプト本体
        label_ja: 日本語ラベル
        label_en: 英語ラベル（オプション）
        category: カテゴリ（既存カテゴリ or 新規）
        tags: タグリスト
        created_date: 作成日時
        last_used: 最終使用日時
        usage_count: 使用回数
        used_in_projects: 使用したプロジェクト名のリスト
        notes: メモ（オプション）
    """
    id: str
    prompt: str
    label_ja: str
    label_en: str = ""
    category: str = "自作"
    tags: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    used_in_projects: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return {
            "id": self.id,
            "prompt": self.prompt,
            "label_ja": self.label_ja,
            "label_en": self.label_en,
            "category": self.category,
            "tags": self.tags,
            "created_date": self.created_date.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "used_in_projects": self.used_in_projects,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomPrompt':
        """辞書から復元"""
        data = cls._deserialize_datetime(data, cls)
        return cls(**data)

    def record_usage(self, project_name: str):
        """使用履歴を記録

        Args:
            project_name: プロジェクト名
        """
        self.last_used = datetime.now()
        self.usage_count += 1
        if project_name not in self.used_in_projects:
            self.used_in_projects.append(project_name)
```

### 2. CustomPromptManagerクラス

```python
class CustomPromptManager:
    """自作プロンプト管理クラス

    custom_prompts.jsonファイルを読み書きし、
    自作プロンプトの保存・検索・削除を管理します。
    """

    def __init__(self, data_dir: Path):
        """初期化

        Args:
            data_dir: データディレクトリパス
        """
        self.data_dir = data_dir
        self.custom_prompts_file = data_dir / "custom_prompts.json"
        self.prompts: List[CustomPrompt] = []
        self.logger = get_logger()

        # ファイルが存在する場合は読み込み
        if self.custom_prompts_file.exists():
            self.load()

    def load(self) -> List[CustomPrompt]:
        """JSONファイルから読み込み

        Returns:
            自作プロンプトリスト
        """
        try:
            with self.custom_prompts_file.open('r', encoding='utf-8') as f:
                data = json.load(f)

            self.prompts = [
                CustomPrompt.from_dict(item)
                for item in data.get("custom_prompts", [])
            ]

            self.logger.info(f"自作プロンプト読み込み: {len(self.prompts)}件")
            return self.prompts

        except Exception as e:
            self.logger.error(f"自作プロンプト読み込みエラー: {e}", exc_info=True)
            return []

    def save(self):
        """JSONファイルに保存"""
        try:
            data = {
                "custom_prompts": [p.to_dict() for p in self.prompts],
                "version": "1.0",
                "last_updated": datetime.now().isoformat()
            }

            # 一時ファイルに書き込み（安全な保存）
            temp_file = self.custom_prompts_file.with_suffix('.json.tmp')
            with temp_file.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 成功したら本番ファイルに上書き
            temp_file.replace(self.custom_prompts_file)

            self.logger.info(f"自作プロンプト保存: {len(self.prompts)}件")

        except Exception as e:
            self.logger.error(f"自作プロンプト保存エラー: {e}", exc_info=True)
            raise

    def add_prompt(
        self,
        prompt: str,
        label_ja: str,
        category: str = "自作",
        tags: Optional[List[str]] = None
    ) -> CustomPrompt:
        """プロンプトを追加

        Args:
            prompt: プロンプト本体
            label_ja: 日本語ラベル
            category: カテゴリ
            tags: タグリスト

        Returns:
            作成されたCustomPromptオブジェクト
        """
        # ID生成（custom_001, custom_002, ...）
        next_id = self._get_next_id()

        # タグ自動生成（空の場合）
        if not tags:
            tags = self._generate_tags(prompt)

        custom_prompt = CustomPrompt(
            id=next_id,
            prompt=prompt,
            label_ja=label_ja,
            category=category,
            tags=tags
        )

        self.prompts.append(custom_prompt)
        self.save()

        self.logger.info(f"自作プロンプト追加: {next_id} - {label_ja}")
        return custom_prompt

    def remove_prompt(self, prompt_id: str) -> bool:
        """プロンプトを削除

        Args:
            prompt_id: プロンプトID

        Returns:
            削除成功の場合True
        """
        before_count = len(self.prompts)
        self.prompts = [p for p in self.prompts if p.id != prompt_id]
        after_count = len(self.prompts)

        if before_count > after_count:
            self.save()
            self.logger.info(f"自作プロンプト削除: {prompt_id}")
            return True

        return False

    def get_prompt_by_id(self, prompt_id: str) -> Optional[CustomPrompt]:
        """IDでプロンプトを取得

        Args:
            prompt_id: プロンプトID

        Returns:
            プロンプトオブジェクト、見つからない場合None
        """
        for prompt in self.prompts:
            if prompt.id == prompt_id:
                return prompt
        return None

    def record_usage(self, prompt_id: str, project_name: str):
        """使用履歴を記録

        Args:
            prompt_id: プロンプトID
            project_name: プロジェクト名
        """
        prompt = self.get_prompt_by_id(prompt_id)
        if prompt:
            prompt.record_usage(project_name)
            self.save()
            self.logger.debug(f"使用履歴記録: {prompt_id} in {project_name}")

    def search(self, query: str) -> List[CustomPrompt]:
        """プロンプトを検索

        Args:
            query: 検索クエリ

        Returns:
            マッチしたプロンプトリスト
        """
        query_lower = query.lower()

        results = [
            p for p in self.prompts
            if query_lower in p.label_ja.lower()
            or query_lower in p.label_en.lower()
            or query_lower in p.prompt.lower()
            or any(query_lower in tag.lower() for tag in p.tags)
        ]

        return results

    def filter_by_category(self, category: str) -> List[CustomPrompt]:
        """カテゴリでフィルタ

        Args:
            category: カテゴリ名

        Returns:
            フィルタされたプロンプトリスト
        """
        return [p for p in self.prompts if p.category == category]

    def get_categories(self) -> List[str]:
        """カテゴリ一覧を取得

        Returns:
            カテゴリ名のリスト
        """
        categories = set(p.category for p in self.prompts)
        return sorted(categories)

    def get_most_used(self, limit: int = 10) -> List[CustomPrompt]:
        """よく使うプロンプトを取得

        Args:
            limit: 取得件数

        Returns:
            使用頻度順のプロンプトリスト
        """
        sorted_prompts = sorted(
            self.prompts,
            key=lambda p: p.usage_count,
            reverse=True
        )
        return sorted_prompts[:limit]

    def _get_next_id(self) -> str:
        """次のIDを生成

        Returns:
            custom_001形式のID
        """
        if not self.prompts:
            return "custom_001"

        # 既存IDから最大番号を取得
        max_num = 0
        for prompt in self.prompts:
            if prompt.id.startswith("custom_"):
                try:
                    num = int(prompt.id.split("_")[1])
                    max_num = max(max_num, num)
                except (IndexError, ValueError):
                    pass

        return f"custom_{max_num + 1:03d}"

    def _generate_tags(self, prompt: str) -> List[str]:
        """タグを自動生成

        Args:
            prompt: プロンプト本体

        Returns:
            タグリスト
        """
        # シンプルな単語分割
        words = re.split(r'[,_\s]+', prompt.lower())

        # フィルタリング
        tags = [
            w.strip() for w in words
            if w.strip() and len(w.strip()) > 1 and w.strip().isalnum()
        ]

        # 重複削除
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags[:10]
```

---

## データ保存形式

### custom_prompts.json

```json
{
  "version": "1.0",
  "last_updated": "2025-10-13T15:30:00",
  "custom_prompts": [
    {
      "id": "custom_001",
      "prompt": "crotch_grab,fondling,over_clothes,fingering,embarrassed",
      "label_ja": "服の上から愛撫",
      "label_en": "touching over clothes",
      "category": "行為",
      "tags": ["愛撫", "服装付き", "恥ずかしがり", "crotch", "grab", "fondling"],
      "created_date": "2025-10-13T14:00:00",
      "last_used": "2025-10-13T15:30:00",
      "usage_count": 3,
      "used_in_projects": ["学園メイドCG集", "OL物語"],
      "notes": ""
    },
    {
      "id": "custom_002",
      "prompt": "school nurse room, infirmary bed, curtain",
      "label_ja": "保健室（カスタム）",
      "label_en": "custom infirmary",
      "category": "背景",
      "tags": ["保健室", "school", "nurse", "room", "infirmary"],
      "created_date": "2025-10-13T14:10:00",
      "last_used": "2025-10-13T14:30:00",
      "usage_count": 1,
      "used_in_projects": ["学園メイドCG集"],
      "notes": "保健室の基本構成"
    }
  ]
}
```

---

## UI設計

### 1. シーンエディタパネルへの追加

#### 「ライブラリに保存」ボタン

```
┌─シーン編集────────────────┐
│シーン: [1:保健室 ▼]       │
│                           │
│[ブロック1] 📌固定         │
│ clothed masturbation      │
│ [編集][削][↑][↓][💾保存]│ ← 新規ボタン
│                           │
│[BREAK]                    │
│                           │
│[+ブロック] [+BREAK]       │
└───────────────────────────┘
```

#### 保存ダイアログ

```
┌─ライブラリに保存──────────┐
│                           │
│プロンプト:                │
│┌─────────────────────────┐│
││clothed masturbation     ││
│└─────────────────────────┘│
│                           │
│日本語ラベル: *必須        │
│[服着たままオナニー______] │
│                           │
│英語ラベル:                │
│[clothed masturbation___] │
│                           │
│カテゴリ:                  │
│[行為 ▼]                   │
│                           │
│タグ: (カンマ区切り)       │
│[愛撫,服装付き,clothed__] │
│                           │
│メモ:                      │
│┌─────────────────────────┐│
││特によく使うプロンプト    ││
│└─────────────────────────┘│
│                           │
│    [キャンセル] [保存]    │
└───────────────────────────┘
```

### 2. ライブラリパネルへの表示

#### カテゴリ一覧に「自作」追加

```
┌─ライブラリ────────────┐
│ 📂 カテゴリ一覧        │
│                       │
│ 📂 行為 (105)    [→] │
│ 📂 背景 (62)     [→] │
│ 📂 キャラ (4)    [→] │
│ 📂 ポージング(25)[→] │
│ 📂 アングル (15) [→] │
│ 📂 自作 (12)     [→] │ ← 新規
│                       │
│ ──────────────────    │
│ 最近使用:             │
│ • 服の上から愛... [+] │← 自作プロンプト
│ • clothed mast... [+] │
│ • school infir... [+] │
└───────────────────────┘
```

#### 詳細表示（自作カテゴリ選択時）

```
┌─ライブラリ：自作──────────┐
│ ◀ カテゴリ一覧            │
│ 🔍 [検索...]              │
│───────────────────────────│
│ ✨ custom_001        [+]  │← 自作プロンプト
│    服の上から愛撫          │
│    (使用: 3回)            │
│    [編集] [削除]          │
│                           │
│ ✨ custom_002        [+]  │
│    保健室（カスタム）      │
│    (使用: 1回)            │
│    [編集] [削除]          │
│                           │
│ [よく使うプロンプト]       │
│ • 服の上から愛撫 (3回)    │
│ • 保健室（カスタム）(1回) │
└───────────────────────────┘
```

---

## 動作フロー

### 1. プロンプト保存

```
シーンエディタでブロック編集中
  ↓
[💾保存] ボタンクリック
  ↓
保存ダイアログ表示
  - プロンプト内容を自動入力
  - タグを自動生成
  ↓
ユーザーがラベル・カテゴリ入力
  ↓
[保存] クリック
  ↓
CustomPromptManagerに保存
  ↓
custom_prompts.jsonに永続化
  ↓
ライブラリパネルに表示
```

### 2. プロンプト使用

```
ライブラリパネル
  ↓
「自作」カテゴリ選択
  ↓
プロンプトをダブルクリック or [+]クリック
  ↓
シーンエディタに固定テキストとして挿入
  ↓
使用履歴を記録
  - last_used更新
  - usage_count +1
  - used_in_projects追加
  ↓
custom_prompts.json更新
```

### 3. プロンプト編集・削除

```
ライブラリパネル（自作カテゴリ）
  ↓
[編集] ボタンクリック
  ↓
編集ダイアログ表示（保存ダイアログと同じ）
  ↓
内容を編集 → [保存]
  ↓
custom_prompts.json更新

または

[削除] ボタンクリック
  ↓
確認ダイアログ表示
  ↓
[削除] 確定
  ↓
CustomPromptManagerから削除
  ↓
custom_prompts.json更新
```

---

## 実装優先順位

### Phase 1: 基本機能（必須）
1. ✅ CustomPromptモデル作成
2. ✅ CustomPromptManagerクラス作成
3. ✅ JSON読み書き機能
4. ✅ シーンエディタに[💾保存]ボタン追加
5. ✅ 保存ダイアログUI作成
6. ✅ ライブラリパネルに「自作」カテゴリ表示

### Phase 2: 詳細機能（推奨）
1. 編集機能（編集ダイアログ）
2. 削除機能（確認ダイアログ付き）
3. 使用履歴記録
4. よく使うプロンプト表示

### Phase 3: 拡張機能（オプション）
1. インポート・エクスポート機能
2. プロジェクト間でのプロンプト共有
3. タグによる高度な検索
4. 統計情報表示

---

## テスト計画

### 1. ユニットテスト

```python
# test_custom_prompt_manager.py

def test_add_prompt():
    """プロンプト追加のテスト"""
    manager = CustomPromptManager(data_dir)

    prompt = manager.add_prompt(
        prompt="crotch_grab,fondling",
        label_ja="服の上から愛撫",
        category="行為"
    )

    assert prompt.id == "custom_001"
    assert prompt.label_ja == "服の上から愛撫"
    assert len(prompt.tags) > 0

def test_record_usage():
    """使用履歴記録のテスト"""
    manager = CustomPromptManager(data_dir)
    prompt = manager.add_prompt("test", "テスト")

    manager.record_usage(prompt.id, "テストプロジェクト")

    updated_prompt = manager.get_prompt_by_id(prompt.id)
    assert updated_prompt.usage_count == 1
    assert "テストプロジェクト" in updated_prompt.used_in_projects

def test_search():
    """検索機能のテスト"""
    manager = CustomPromptManager(data_dir)
    manager.add_prompt("crotch_grab", "服の上から愛撫")
    manager.add_prompt("school infirmary", "保健室")

    results = manager.search("服")
    assert len(results) == 1
    assert results[0].label_ja == "服の上から愛撫"
```

### 2. 統合テスト

```python
# test_custom_prompt_integration.py

def test_save_and_load():
    """保存・読み込みの統合テスト"""
    manager = CustomPromptManager(data_dir)

    # プロンプト追加
    manager.add_prompt("test prompt", "テスト")

    # 新しいマネージャーで読み込み
    manager2 = CustomPromptManager(data_dir)

    assert len(manager2.prompts) == 1
    assert manager2.prompts[0].label_ja == "テスト"
```

---

## セキュリティ・品質要件

### データ整合性
- ✅ 一時ファイル方式で安全な保存（.json.tmp → .json）
- ✅ JSON保存失敗時のエラーハンドリング
- ✅ ロギング完備

### パフォーマンス
- ✅ メモリ上でプロンプトを管理（高速アクセス）
- ✅ 保存時のみファイルI/O
- ✅ 検索処理の最適化

### ユーザビリティ
- ✅ 直感的なUI
- ✅ 自動タグ生成でユーザーの手間を削減
- ✅ 使用履歴で便利なプロンプトを把握

---

## まとめ

FR-004「自作プロンプトライブラリ」機能の設計が完了しました。

### 次のステップ
1. CustomPromptモデル実装
2. CustomPromptManagerクラス実装
3. UI実装（保存ダイアログ、ライブラリパネル統合）
4. テスト実施
5. ドキュメント更新

この設計に基づいて実装を進めます。
