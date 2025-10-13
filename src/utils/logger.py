"""ロギングユーティリティ

アプリケーション全体で使用するロガーを提供。
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


class AppLogger:
    """アプリケーションロガー

    ファイルとコンソールの両方にログを出力。
    ファイルログはローテーションされる（最大5MB、5世代保持）。
    """

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初期化（シングルトン）"""
        if self._logger is not None:
            return

        # ロガー作成
        self._logger = logging.getLogger("Pfft_maker")
        self._logger.setLevel(logging.DEBUG)

        # 既存のハンドラーをクリア（重複防止）
        self._logger.handlers.clear()

        # ログディレクトリ作成
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        # ログファイルパス（日付付き）
        log_file = log_dir / f"pfft_maker_{datetime.now().strftime('%Y%m%d')}.log"

        # ファイルハンドラー（ローテーション付き）
        # 最大5MB、5世代保持
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)

        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # コンソールはINFO以上のみ
        console_formatter = logging.Formatter(
            '[%(levelname)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

        # 初期化ログ
        self._logger.info("=" * 60)
        self._logger.info(f"Pfft_maker ログシステム初期化完了")
        self._logger.info(f"ログファイル: {log_file}")
        self._logger.info("=" * 60)

    def get_logger(self) -> logging.Logger:
        """ロガーを取得

        Returns:
            ロガーオブジェクト
        """
        return self._logger

    def debug(self, message: str):
        """DEBUGレベルログ"""
        self._logger.debug(message)

    def info(self, message: str):
        """INFOレベルログ"""
        self._logger.info(message)

    def warning(self, message: str):
        """WARNINGレベルログ"""
        self._logger.warning(message)

    def error(self, message: str, exc_info: bool = False):
        """ERRORレベルログ

        Args:
            message: エラーメッセージ
            exc_info: 例外情報を含めるか（Tracebackを出力）
        """
        self._logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False):
        """CRITICALレベルログ

        Args:
            message: クリティカルエラーメッセージ
            exc_info: 例外情報を含めるか（Tracebackを出力）
        """
        self._logger.critical(message, exc_info=exc_info)

    def exception(self, message: str):
        """例外ログ（自動的にTracebackを出力）

        Args:
            message: エラーメッセージ
        """
        self._logger.exception(message)


# グローバルロガーインスタンス
_app_logger = None


def get_logger() -> AppLogger:
    """グローバルロガーを取得

    Returns:
        AppLoggerインスタンス

    Example:
        >>> from utils.logger import get_logger
        >>> logger = get_logger()
        >>> logger.info("アプリケーション起動")
        >>> logger.error("エラーが発生しました", exc_info=True)
    """
    global _app_logger
    if _app_logger is None:
        _app_logger = AppLogger()
    return _app_logger


# 便利な関数（直接使用可能）
def debug(message: str):
    """DEBUGレベルログ"""
    get_logger().debug(message)


def info(message: str):
    """INFOレベルログ"""
    get_logger().info(message)


def warning(message: str):
    """WARNINGレベルログ"""
    get_logger().warning(message)


def error(message: str, exc_info: bool = False):
    """ERRORレベルログ"""
    get_logger().error(message, exc_info=exc_info)


def critical(message: str, exc_info: bool = False):
    """CRITICALレベルログ"""
    get_logger().critical(message, exc_info=exc_info)


def exception(message: str):
    """例外ログ（自動的にTracebackを出力）"""
    get_logger().exception(message)
