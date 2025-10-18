# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller設定ファイル
個人情報を除外した配布版をビルドするための設定
"""

import sys
from pathlib import Path

block_cipher = None

# プロジェクトルート
project_root = Path.cwd()

# 配布に含めるデータファイル
# 形式: (ソースパス, 配布先フォルダ)
datas = [
    # プロンプトライブラリ（共通データ）
    ('data/prompts_library.csv', 'data'),

    # デフォルト設定ファイル（個人情報なし）
    ('data/settings.default.json', 'data'),

    # リソースファイル（アイコン、スタイルなど）
    ('resources', 'resources'),

    # サンプルワイルドカード（個人情報を含まないサンプルのみ）
    # 注意: 個人のワイルドカードは除外
    # ('wildcards', 'wildcards_samples'),  # 必要に応じてコメント解除
]

# 除外するモジュール（サイズ削減）
excludes = [
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'tkinter',
]

a = Analysis(
    ['run.py'],
    pathex=[
        str(project_root),
        str(project_root / 'src'),  # srcディレクトリを明示的に追加
    ],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # PyQt6
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        # 外部ライブラリ
        'chardet',
        'cryptography',
        'anthropic',
        'openai',
        # メインモジュール
        'main',
        # config
        'config',
        'config.settings',
        # ai
        'ai',
        'ai.api_key_manager',
        'ai.cost_estimator',
        'ai.label_generator',
        # core
        'core',
        'core.backup_manager',
        'core.custom_prompt_manager',
        'core.file_sync_manager',
        'core.label_preserver',
        'core.library_manager',
        'core.project_library_manager',
        'core.prompt_builder',
        'core.scene_library_manager',
        'core.template_manager',
        'core.wildcard_parser',
        # models
        'models',
        'models.base',
        'models.block',
        'models.common_prompt',
        'models.custom_prompt',
        'models.project',
        'models.project_library',
        'models.prompt',
        'models.scene',
        'models.scene_library',
        'models.template',
        # ui
        'ui',
        'ui.batch_edit_dialog',
        'ui.batch_scene_save_dialog',
        'ui.block_edit_dialog',
        'ui.category_edit_dialog',
        'ui.custom_prompt_dialog',
        'ui.custom_prompt_manager_dialog',
        'ui.library_panel',
        'ui.main_window',
        'ui.output_dialog',
        'ui.preview_panel',
        'ui.project_save_dialog',
        'ui.scene_editor_panel',
        'ui.scene_save_dialog',
        'ui.scene_select_dialog',
        'ui.settings_dialog',
        'ui.template_save_dialog',
        'ui.template_select_dialog',
        'ui.update_notification_banner',
        'ui.welcome_dialog',
        # utils
        'utils',
        'utils.file_utils',
        'utils.logger',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 個人情報を含むファイルを明示的に除外
excluded_files = [
    'settings.json',           # 個人のパス設定
    'project_library.json',    # 個人の作品
    'scene_library.json',      # 個人の作品
    'custom_prompts.json',     # 個人のプロンプト
    'templates.json',          # 個人のテンプレート
    '.api_keys.enc',           # APIキー（暗号化）
    '.master_key',             # マスターキー
]

# データから個人情報ファイルを除外
a.datas = [
    (dest, source, type_) for dest, source, type_ in a.datas
    if not any(excluded in dest for excluded in excluded_files)
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Pfft_maker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX圧縮を無効化（誤検知防止）
    console=False,  # コンソールウィンドウを非表示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico' if Path('resources/icon.ico').exists() else None,
    version='version_info.txt',  # バージョン情報追加（誤検知軽減）
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # UPX圧縮を無効化（誤検知防止）
    upx_exclude=[],
    name='Pfft_maker',
)
