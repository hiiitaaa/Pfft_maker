"""ファイル操作ユーティリティ

共通のファイル操作処理を提供。コードの再利用を促進。
"""

from pathlib import Path
from typing import List, Optional
import chardet
import fnmatch


def detect_encoding(file_path: Path) -> str:
    """エンコーディングを検出（フォールバック付き）

    優先エンコーディングを順に試行し、失敗した場合はchardetで検出。

    Args:
        file_path: 対象ファイルパス

    Returns:
        検出されたエンコーディング名

    Note:
        短いファイルや日本語ファイルでのchardet誤判定を防ぐため、
        一般的なエンコーディングを優先的に試行する。
    """
    # 試行順序（優先度順）
    encodings = ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932']

    # バイナリ読み込み
    with file_path.open('rb') as f:
        raw = f.read()

    # 優先エンコーディングで順次試行
    for encoding in encodings:
        try:
            raw.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue

    # すべて失敗した場合: chardetで検出
    detected = chardet.detect(raw)
    return detected.get('encoding') or 'utf-8'


def read_text_file(file_path: Path, remove_bom: bool = True) -> List[str]:
    """テキストファイルを読み込み

    エンコーディング自動検出、BOM除去、空行スキップを行う。

    Args:
        file_path: ファイルパス
        remove_bom: BOM除去フラグ

    Returns:
        行のリスト（空行除外）
    """
    encoding = detect_encoding(file_path)

    with file_path.open('r', encoding=encoding) as f:
        content = f.read()

    # BOM除去
    if remove_bom:
        content = content.lstrip('\ufeff')

    # 行ごとに分割、空行スキップ
    lines = [line.strip() for line in content.splitlines() if line.strip()]

    return lines


def extract_category_from_path(file_path: Path, root_dir: Path) -> str:
    """ファイルパスからカテゴリを抽出（最大2階層）

    Args:
        file_path: ファイルパス
        root_dir: ルートディレクトリ

    Returns:
        カテゴリ名

    Example:
        >>> extract_category_from_path(
        ...     Path("E:/wildcards/背景/学校.txt"),
        ...     Path("E:/wildcards/")
        ... )
        "背景"
    """
    relative = file_path.relative_to(root_dir)
    parts = relative.parts[:-1]  # ファイル名を除く

    if len(parts) == 0:
        return "その他"
    elif len(parts) == 1:
        return parts[0]
    else:
        # 2階層以上: 最初の2階層のみ使用
        return f"{parts[0]}/{parts[1]}"


def format_wildcard_path(file_path: Path, root_dir: Path) -> str:
    """ワイルドカード形式に変換

    Args:
        file_path: ファイルパス
        root_dir: ルートディレクトリ

    Returns:
        ワイルドカード形式（例: __posing/arm__）
    """
    relative_path = file_path.relative_to(root_dir)
    stem = relative_path.with_suffix('')  # 拡張子削除
    unix_path = str(stem).replace('\\', '/')  # Unixスタイル
    return f"__{unix_path}__"


def should_exclude(path: Path, exclude_patterns: List[str], root_dir: Path) -> bool:
    """パスが除外パターンに一致するかチェック

    Args:
        path: チェック対象パス
        exclude_patterns: 除外パターンのリスト（例: ["backup_*", ".git"]）
        root_dir: ルートディレクトリ

    Returns:
        除外すべき場合True

    Note:
        ファイル名だけでなく、パス内のすべてのディレクトリ名もチェックします。
        例: "backup_20250902/posing/arm.txt" は "backup_*" パターンで除外されます。
    """
    # 相対パスを取得
    try:
        relative = path.relative_to(root_dir)
    except ValueError:
        # root_dirの外部の場合は除外しない
        return False

    # パス内の各パーツをチェック
    for part in relative.parts:
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(part, pattern):
                return True

    return False


def scan_text_files(directory: Path, recursive: bool = True, exclude_patterns: Optional[List[str]] = None) -> List[Path]:
    """ディレクトリ内のテキストファイルをスキャン

    Args:
        directory: スキャン対象ディレクトリ
        recursive: 再帰的にスキャンするか
        exclude_patterns: 除外パターンのリスト（例: ["backup_*", ".git"]）

    Returns:
        テキストファイルのパスリスト
    """
    pattern = "**/*.txt" if recursive else "*.txt"
    all_files = directory.glob(pattern)

    # 除外パターンが指定されている場合はフィルタリング
    if exclude_patterns:
        filtered_files = [
            f for f in all_files
            if not should_exclude(f, exclude_patterns, directory)
        ]
        return sorted(filtered_files)
    else:
        return sorted(all_files)
