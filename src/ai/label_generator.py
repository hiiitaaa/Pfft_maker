"""ラベル自動生成モジュール

Claude APIまたはLM Studioを使用してプロンプトに日本語ラベルを自動生成します。
FR-016: ラベル・タグ自動生成
"""

import re
import asyncio
from typing import List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from models import Prompt


class LabelGenerator:
    """ラベル自動生成クラス

    4段階フォールバック方式:
    1. Claude API（優先）- 高精度、要APIキー
    2. OpenAI API（次点）- ChatGPT、要APIキー
    3. LM Studio（フォールバック）- ローカルLLM、オフライン可能
    4. 辞書ベース（最終手段）- 単語分割のみ、常に有効
    """

    def __init__(self, api_key_manager=None, use_claude: bool = True, use_openai: bool = False, use_lm_studio: bool = False, max_concurrent: int = 10, settings=None):
        """初期化

        Args:
            api_key_manager: APIKeyManagerインスタンス（オプション）
            use_claude: Claude APIを使用するか
            use_openai: OpenAI APIを使用するか
            use_lm_studio: LM Studioを使用するか
            max_concurrent: 並列処理時の最大同時実行数（デフォルト: 10）
            settings: Settings インスタンス（LM Studio設定用、オプション）
        """
        self.api_key_manager = api_key_manager
        self.use_claude = use_claude
        self.use_openai = use_openai
        self.use_lm_studio = use_lm_studio
        self.settings = settings

        # LM Studioの場合は設定から同時実行数を取得
        if use_lm_studio and settings:
            self.max_concurrent = settings.lm_studio_max_concurrent
        else:
            self.max_concurrent = max_concurrent

    def generate_labels_batch(
        self,
        prompts: List[Prompt],
        progress_callback=None,
        mode: str = "auto"
    ) -> Tuple[int, int, List[str]]:
        """プロンプトリストに対して一括でラベルを生成

        Args:
            prompts: Promptオブジェクトのリスト
            progress_callback: 進捗コールバック関数(current, total, message)
            mode: 処理モード - "auto" (自動判定), "async" (並列処理), "batch" (Batch API), "sync" (同期処理)

        Returns:
            (成功数, 失敗数, エラーメッセージリスト)
        """
        # label_jaが空のプロンプトのみを対象
        target_prompts = [p for p in prompts if not p.label_ja or p.label_ja == p.prompt]
        total = len(target_prompts)

        if total == 0:
            return 0, 0, ["ラベル生成が必要なプロンプトがありません"]

        # モード自動判定
        if mode == "auto":
            if total > 1000:
                mode = "batch"
            elif total > 50:
                mode = "async"
            else:
                mode = "sync"

        # モード別処理
        if mode == "async":
            return self._generate_labels_async(target_prompts, progress_callback)
        elif mode == "batch":
            return self._generate_labels_batch_api(target_prompts, progress_callback)
        else:  # sync
            return self._generate_labels_sync(target_prompts, progress_callback)

    def _generate_labels_sync(
        self,
        target_prompts: List[Prompt],
        progress_callback=None
    ) -> Tuple[int, int, List[str]]:
        """同期処理でラベルを生成（従来の実装）

        Args:
            target_prompts: 対象プロンプトのリスト
            progress_callback: 進捗コールバック関数(current, total, message)

        Returns:
            (成功数, 失敗数, エラーメッセージリスト)
        """
        success_count = 0
        failure_count = 0
        errors = []
        total = len(target_prompts)

        for i, prompt in enumerate(target_prompts):
            if progress_callback:
                progress_callback(i + 1, total, f"[同期] ラベル生成中: {prompt.prompt[:30]}...")

            try:
                # ラベル生成
                label_ja = self.generate_label(prompt.prompt)

                if label_ja:
                    prompt.label_ja = label_ja
                    prompt.label_source = self._get_label_source()
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append(f"ラベル生成失敗: {prompt.prompt[:30]}...")

            except Exception as e:
                failure_count += 1
                errors.append(f"エラー: {prompt.prompt[:30]}... - {str(e)}")

        return success_count, failure_count, errors

    def _generate_labels_async(
        self,
        target_prompts: List[Prompt],
        progress_callback=None
    ) -> Tuple[int, int, List[str]]:
        """非同期並列処理でラベルを生成

        Args:
            target_prompts: 対象プロンプトのリスト
            progress_callback: 進捗コールバック関数(current, total, message)

        Returns:
            (成功数, 失敗数, エラーメッセージリスト)
        """
        import asyncio

        # 新しいイベントループを作成（既存のものと競合しないように）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                self._async_generate_all(target_prompts, progress_callback)
            )
            return result
        finally:
            loop.close()

    async def _async_generate_all(
        self,
        target_prompts: List[Prompt],
        progress_callback=None
    ) -> Tuple[int, int, List[str]]:
        """非同期でラベルを一括生成

        Args:
            target_prompts: 対象プロンプトのリスト
            progress_callback: 進捗コールバック関数(current, total, message)

        Returns:
            (成功数, 失敗数, エラーメッセージリスト)
        """
        success_count = 0
        failure_count = 0
        errors = []
        total = len(target_prompts)
        completed = 0

        # セマフォで同時実行数を制限
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def generate_with_semaphore(prompt: Prompt):
            nonlocal success_count, failure_count, completed

            async with semaphore:
                try:
                    # 同期関数を別スレッドで実行
                    loop = asyncio.get_event_loop()
                    label_ja = await loop.run_in_executor(
                        None,
                        self.generate_label,
                        prompt.prompt
                    )

                    if label_ja:
                        prompt.label_ja = label_ja
                        prompt.label_source = self._get_label_source()
                        success_count += 1
                    else:
                        failure_count += 1
                        errors.append(f"ラベル生成失敗: {prompt.prompt[:30]}...")

                except Exception as e:
                    failure_count += 1
                    errors.append(f"エラー: {prompt.prompt[:30]}... - {str(e)}")

                finally:
                    completed += 1
                    if progress_callback:
                        progress_callback(
                            completed,
                            total,
                            f"[並列 {self.max_concurrent}] ラベル生成中: {prompt.prompt[:30]}..."
                        )

        # すべてのタスクを並列実行
        tasks = [generate_with_semaphore(prompt) for prompt in target_prompts]
        await asyncio.gather(*tasks)

        return success_count, failure_count, errors

    def _generate_labels_batch_api(
        self,
        target_prompts: List[Prompt],
        progress_callback=None
    ) -> Tuple[int, int, List[str]]:
        """Claude Batch APIでラベルを生成（大量処理向け、50%コスト削減）

        Args:
            target_prompts: 対象プロンプトのリスト
            progress_callback: 進捗コールバック関数(current, total, message)

        Returns:
            (成功数, 失敗数, エラーメッセージリスト)
        """
        success_count = 0
        failure_count = 0
        errors = []
        total = len(target_prompts)

        try:
            import anthropic
            import json
            import time
            from pathlib import Path
            import tempfile

            api_key = self.api_key_manager.get_api_key("claude")
            if not api_key:
                errors.append("Claude APIキーが設定されていません")
                return 0, total, errors

            client = anthropic.Anthropic(api_key=api_key)

            if progress_callback:
                progress_callback(0, total, "[Batch API] リクエストを準備中...")

            # システムプロンプト
            system_prompt = """あなたはStable Diffusion用のプロンプトに日本語ラベルを付けるアシスタントです。
以下のルールに従って、簡潔で分かりやすい日本語ラベルを生成してください：

1. 最も重要な要素を3-5文字程度で表現
2. 平易な日本語を使用（カタカナ混在OK）
3. ラベルのみを出力（説明不要）

例：
- "clothed masturbation" → "服着たままオナニー"
- "school infirmary, beds with curtain dividers" → "保健室"
- "classroom interior, desks in rows" → "教室"
- "sitting, spread legs" → "座り開脚"
"""

            # バッチリクエスト作成
            requests = []
            for i, prompt in enumerate(target_prompts):
                requests.append({
                    "custom_id": f"prompt_{i}",
                    "params": {
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 50,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": f"プロンプト: {prompt.prompt}\n\n日本語ラベル:"}
                        ]
                    }
                })

            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
                for req in requests:
                    f.write(json.dumps(req, ensure_ascii=False) + '\n')
                batch_file_path = f.name

            if progress_callback:
                progress_callback(0, total, "[Batch API] バッチジョブを送信中...")

            # バッチジョブ作成
            with open(batch_file_path, 'rb') as f:
                message_batch = client.messages.batches.create(
                    requests=requests
                )

            batch_id = message_batch.id

            if progress_callback:
                progress_callback(0, total, f"[Batch API] ジョブID: {batch_id}\n処理待機中...")

            # バッチ処理完了を待機（ポーリング）
            max_wait_time = 3600  # 最大1時間
            poll_interval = 10  # 10秒ごとにチェック
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                batch_status = client.messages.batches.retrieve(batch_id)

                status = batch_status.processing_status

                if status == "ended":
                    # 完了
                    break
                elif status in ["canceling", "canceled"]:
                    errors.append("バッチジョブがキャンセルされました")
                    return 0, total, errors
                elif status == "expired":
                    errors.append("バッチジョブがタイムアウトしました")
                    return 0, total, errors

                # 進捗表示
                processing_count = getattr(batch_status.request_counts, 'processing', 0) or 0
                succeeded_count = getattr(batch_status.request_counts, 'succeeded', 0) or 0
                processed = processing_count + succeeded_count
                if progress_callback:
                    progress_callback(
                        processed,
                        total,
                        f"[Batch API] 処理中... ({status})\n処理済み: {processed}/{total}"
                    )

                time.sleep(poll_interval)
                elapsed_time += poll_interval

            if elapsed_time >= max_wait_time:
                errors.append("バッチ処理がタイムアウトしました")
                return 0, total, errors

            # 結果取得
            if progress_callback:
                progress_callback(total, total, "[Batch API] 結果を取得中...")

            results = client.messages.batches.results(batch_id)

            # 結果を各プロンプトに適用
            result_map = {}
            for result in results:
                custom_id = result.custom_id
                if result.result.type == "succeeded":
                    message = result.result.message
                    label = message.content[0].text.strip()

                    # サニタイズ
                    import re
                    label = re.sub(r'[\n\r]', '', label)
                    label = label.strip('"').strip("'").strip()

                    result_map[custom_id] = label
                else:
                    result_map[custom_id] = None

            # プロンプトに適用
            for i, prompt in enumerate(target_prompts):
                custom_id = f"prompt_{i}"
                label = result_map.get(custom_id)

                if label:
                    prompt.label_ja = label
                    prompt.label_source = "ai_generated"
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append(f"ラベル生成失敗: {prompt.prompt[:30]}...")

            # 一時ファイル削除
            try:
                Path(batch_file_path).unlink()
            except:
                pass

            return success_count, failure_count, errors

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            errors.append(f"Batch API エラー: {str(e)}\n\n{error_detail}")
            return 0, total, errors

    def generate_label(self, prompt: str) -> Optional[str]:
        """プロンプトから日本語ラベルを生成

        Args:
            prompt: プロンプト文字列

        Returns:
            日本語ラベル、生成失敗時はNone
        """
        # ステップ1: Claude API（優先）
        if self.use_claude and self.api_key_manager:
            label = self._generate_with_claude(prompt)
            if label:
                return label

        # ステップ2: OpenAI API（次点）
        if self.use_openai and self.api_key_manager:
            label = self._generate_with_openai(prompt)
            if label:
                return label

        # ステップ3: LM Studio（フォールバック）
        if self.use_lm_studio:
            label = self._generate_with_lm_studio(prompt)
            if label:
                return label

        # ステップ4: 辞書ベース（最終手段）
        return self._generate_with_dictionary(prompt)

    def _generate_with_claude(self, prompt: str) -> Optional[str]:
        """Claude APIで日本語ラベルを生成

        Args:
            prompt: プロンプト文字列

        Returns:
            日本語ラベル、失敗時はNone
        """
        try:
            import anthropic

            api_key = self.api_key_manager.get_api_key("claude")
            if not api_key:
                return None

            client = anthropic.Anthropic(api_key=api_key)

            # プロンプト作成
            system_prompt = """あなたはStable Diffusion用のプロンプトに日本語ラベルを付けるアシスタントです。
以下のルールに従って、簡潔で分かりやすい日本語ラベルを生成してください：

1. 最も重要な要素を3-5文字程度で表現
2. 平易な日本語を使用（カタカナ混在OK）
3. ラベルのみを出力（説明不要）

例：
- "clothed masturbation" → "服着たままオナニー"
- "school infirmary, beds with curtain dividers" → "保健室"
- "classroom interior, desks in rows" → "教室"
- "sitting, spread legs" → "座り開脚"
"""

            message = client.messages.create(
                model="claude-3-haiku-20240307",  # コスト効率の良いHaikuを使用
                max_tokens=50,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"プロンプト: {prompt}\n\n日本語ラベル:"}
                ]
            )

            # レスポンス抽出
            label = message.content[0].text.strip()

            # サニタイズ（改行や余分な文字を削除）
            label = re.sub(r'[\n\r]', '', label)
            label = label.strip('"').strip("'").strip()

            return label if label else None

        except Exception as e:
            print(f"[Warning] Claude API error: {e}")
            return None

    def _generate_with_openai(self, prompt: str) -> Optional[str]:
        """OpenAI APIで日本語ラベルを生成

        Args:
            prompt: プロンプト文字列

        Returns:
            日本語ラベル、失敗時はNone
        """
        try:
            import openai

            api_key = self.api_key_manager.get_api_key("openai")
            if not api_key:
                return None

            client = openai.OpenAI(api_key=api_key)

            # プロンプト作成
            system_prompt = """あなたはStable Diffusion用のプロンプトに日本語ラベルを付けるアシスタントです。
以下のルールに従って、簡潔で分かりやすい日本語ラベルを生成してください：

1. 最も重要な要素を3-5文字程度で表現
2. 平易な日本語を使用（カタカナ混在OK）
3. ラベルのみを出力（説明不要）

例：
- "clothed masturbation" → "服着たままオナニー"
- "school infirmary, beds with curtain dividers" → "保健室"
- "classroom interior, desks in rows" → "教室"
- "sitting, spread legs" → "座り開脚"
"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # コスト効率の良いgpt-3.5-turboを使用
                max_tokens=50,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"プロンプト: {prompt}\n\n日本語ラベル:"}
                ]
            )

            # レスポンス抽出
            label = response.choices[0].message.content.strip()

            # サニタイズ（改行や余分な文字を削除）
            import re
            label = re.sub(r'[\n\r]', '', label)
            label = label.strip('"').strip("'").strip()

            return label if label else None

        except Exception as e:
            print(f"[Warning] OpenAI API error: {e}")
            return None

    def _generate_with_lm_studio(self, prompt: str) -> Optional[str]:
        """LM Studioで日本語ラベルを生成

        Args:
            prompt: プロンプト文字列

        Returns:
            日本語ラベル、失敗時はNone
        """
        try:
            import openai
            from config.settings import Settings

            settings = Settings()

            # LM StudioはOpenAI互換APIを提供
            client = openai.OpenAI(
                base_url=settings.lm_studio_endpoint,
                api_key="lm-studio"  # LM Studioはダミーキーで動作
            )

            # プロンプト作成
            system_prompt = """あなたはStable Diffusion用のプロンプトに日本語ラベルを付けるアシスタントです。
以下のルールに従って、簡潔で分かりやすい日本語ラベルを生成してください：

1. 最も重要な要素を3-5文字程度で表現
2. 平易な日本語を使用（カタカナ混在OK）
3. ラベルのみを出力（説明不要）

例：
- "clothed masturbation" → "服着たままオナニー"
- "school infirmary, beds with curtain dividers" → "保健室"
- "classroom interior, desks in rows" → "教室"
- "sitting, spread legs" → "座り開脚"
"""

            response = client.chat.completions.create(
                model=settings.lm_studio_model,
                max_tokens=50,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"プロンプト: {prompt}\n\n日本語ラベル:"}
                ]
            )

            # レスポンス抽出
            label = response.choices[0].message.content.strip()

            # サニタイズ（改行や余分な文字を削除）
            label = re.sub(r'[\n\r]', '', label)
            label = label.strip('"').strip("'").strip()

            return label if label else None

        except Exception as e:
            print(f"[Warning] LM Studio API error: {e}")
            return None

    def _generate_with_dictionary(self, prompt: str) -> Optional[str]:
        """辞書ベースでラベルを生成

        プロンプトの先頭部分を抽出してラベルとする。

        Args:
            prompt: プロンプト文字列

        Returns:
            ラベル（プロンプトの先頭30文字）
        """
        # プロンプトの先頭部分を抽出（最大30文字）
        label = prompt.strip()
        if len(label) > 30:
            label = label[:30] + "..."
        return label

    def _get_label_source(self) -> str:
        """現在使用している生成方法を返す

        Returns:
            "ai_generated" または "auto_extract"
        """
        if self.use_claude and self.api_key_manager:
            return "ai_generated"
        elif self.use_openai and self.api_key_manager:
            return "ai_generated"
        elif self.use_lm_studio:
            return "ai_generated"
        else:
            return "auto_extract"


def generate_tags_auto(prompt: str) -> List[str]:
    """自動タグ生成（シンプルな単語分割）

    FR-016仕様に準拠した単語分割ロジック。

    Args:
        prompt: プロンプト文字列

    Returns:
        タグのリスト（最大10個）

    Examples:
        >>> generate_tags_auto("school_infirmary")
        ['school', 'infirmary']

        >>> generate_tags_auto("clothed masturbation")
        ['clothed', 'masturbation']

        >>> generate_tags_auto("classroom interior, desks in rows")
        ['classroom', 'interior', 'desks', 'in', 'rows']
    """
    # 1. 小文字化
    text = prompt.lower()

    # 2. カンマ、アンダースコア、スペースで分割
    words = re.split(r'[,_\s]+', text)

    # 3. フィルタリング
    tags = [
        w.strip() for w in words
        if w.strip() and len(w.strip()) > 1 and w.strip().isalnum()
    ]

    # 4. 重複削除（順序保持）
    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    # 5. 最大10タグ
    return unique_tags[:10]
