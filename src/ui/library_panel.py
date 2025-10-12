"""ライブラリパネル

プロンプトライブラリの表示・検索を行うパネル。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from typing import List

from ..models import Prompt


class LibraryPanel(QWidget):
    """ライブラリパネル

    プロンプトの検索・選択機能を提供。

    Signals:
        prompt_selected: プロンプトが選択された時（Promptオブジェクト）
    """

    # シグナル定義
    prompt_selected = pyqtSignal(object)  # Prompt

    def __init__(self):
        """初期化"""
        super().__init__()

        self.prompts: List[Prompt] = []
        self.filtered_prompts: List[Prompt] = []

        # UI構築
        self._create_ui()

        # デバウンスタイマー（検索用）
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._execute_search)

    def _create_ui(self):
        """UI構築"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # タイトル
        title_label = QLabel("プロンプトライブラリ")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(title_label)

        # 検索バー
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 検索...")
        self.search_bar.textChanged.connect(self._on_search_input)
        layout.addWidget(self.search_bar)

        # 読み込みボタン
        load_button = QPushButton("ライブラリを読み込み")
        load_button.clicked.connect(self._on_load_library)
        layout.addWidget(load_button)

        # ツリー表示
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ラベル", "プロンプト"])
        self.tree.setColumnWidth(0, 200)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)

        # ステータス
        self.status_label = QLabel("ライブラリ: 0件")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

    def load_prompts(self, prompts: List[Prompt]):
        """プロンプトを読み込み

        Args:
            prompts: プロンプトのリスト
        """
        self.prompts = prompts
        self.filtered_prompts = prompts
        self._update_tree()
        self.status_label.setText(f"ライブラリ: {len(prompts)}件")

    def _on_search_input(self, text: str):
        """検索入力時（デバウンス処理）

        Args:
            text: 検索クエリ
        """
        # 既存のタイマーを停止
        self.search_timer.stop()
        # 300ms後に検索実行
        self.search_timer.start(300)

    def _execute_search(self):
        """検索実行"""
        query = self.search_bar.text().strip()

        if not query:
            # 検索クエリが空の場合、すべて表示
            self.filtered_prompts = self.prompts
        else:
            # 検索実行
            self.filtered_prompts = [
                p for p in self.prompts
                if p.matches_search(query)
            ]

        self._update_tree()
        self.status_label.setText(
            f"検索結果: {len(self.filtered_prompts)}件 / {len(self.prompts)}件"
        )

    def _update_tree(self):
        """ツリー表示更新"""
        self.tree.clear()

        # カテゴリごとにグループ化
        categories = {}
        for prompt in self.filtered_prompts:
            category = prompt.category or "その他"
            if category not in categories:
                categories[category] = []
            categories[category].append(prompt)

        # カテゴリごとにツリーアイテム作成
        for category, prompts in sorted(categories.items()):
            # カテゴリノード
            category_item = QTreeWidgetItem([f"{category} ({len(prompts)})", ""])
            category_item.setExpanded(True)
            self.tree.addTopLevelItem(category_item)

            # プロンプトノード
            for prompt in prompts:
                prompt_item = QTreeWidgetItem([
                    prompt.label_ja or prompt.prompt[:30],
                    prompt.prompt[:50] + "..." if len(prompt.prompt) > 50 else prompt.prompt
                ])
                prompt_item.setData(0, Qt.ItemDataRole.UserRole, prompt)
                category_item.addChild(prompt_item)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """アイテムダブルクリック時

        Args:
            item: クリックされたアイテム
            column: カラム番号
        """
        # プロンプトデータを取得
        prompt = item.data(0, Qt.ItemDataRole.UserRole)
        if prompt:
            self.prompt_selected.emit(prompt)

    def _on_load_library(self):
        """ライブラリ読み込み（テスト用）"""
        # TODO: 実際のワイルドカードパーサーと連携
        # 現在はダミーデータ
        from ..models import Prompt
        from datetime import datetime

        dummy_prompts = [
            Prompt(
                id="test_1",
                source_file="tipo_play.txt",
                original_line_number=1,
                original_number=1,
                label_ja="服着たままオナニー",
                label_en="clothed masturbation",
                prompt="clothed masturbation",
                category="行為",
                tags=["clothed", "masturbation"],
                created_date=datetime.now()
            ),
            Prompt(
                id="test_2",
                source_file="背景/学校.txt",
                original_line_number=1,
                original_number=1,
                label_ja="教室",
                label_en="classroom",
                prompt="classroom interior, desks in rows",
                category="背景",
                tags=["school", "classroom"],
                created_date=datetime.now()
            ),
        ]

        self.load_prompts(dummy_prompts)
