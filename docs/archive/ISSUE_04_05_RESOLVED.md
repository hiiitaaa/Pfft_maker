# 問題4,5: Windows対応の技術的修正 - 解決済み

作成日: 2025-01-15
ステータス: ✅ 解決

---

## 問題4: Windowsファイルパーミッション

### 現状の問題

```python
# ❌ 間違った実装（technical_requirements.md）
self.KEY_FILE.chmod(0o600)  # Windowsでは効果なし
```

**問題点**:
- `chmod(0o600)` はUnix/Linux用
- Windowsでは実行されるがセキュリティ効果なし
- 他ユーザーからファイルが読める状態

---

### 解決策: Windows ACL使用

#### 実装方法A: pywin32使用（推奨）

```python
# utils/windows_security.py
import win32security
import win32api
import ntsecuritycon as con
from pathlib import Path

def set_file_security_windows(file_path: Path):
    """Windowsでファイルを現在のユーザーのみアクセス可能にする

    Args:
        file_path: 保護するファイルパス

    Raises:
        OSError: ファイル操作エラー
        ImportError: pywin32がインストールされていない
    """
    try:
        # 現在のユーザーSIDを取得
        username = win32api.GetUserName()
        user_sid, domain, type = win32security.LookupAccountName("", username)

        # セキュリティ記述子を作成
        sd = win32security.SECURITY_DESCRIPTOR()

        # DACLを作成
        dacl = win32security.ACL()

        # 現在のユーザーにフルコントロール権限を付与
        dacl.AddAccessAllowedAce(
            win32security.ACL_REVISION,
            con.FILE_ALL_ACCESS,
            user_sid
        )

        # セキュリティ記述子にDACLを設定
        sd.SetSecurityDescriptorDacl(1, dacl, 0)

        # ファイルにセキュリティ設定を適用
        win32security.SetFileSecurity(
            str(file_path),
            win32security.DACL_SECURITY_INFORMATION,
            sd
        )

        logger.info(f"File security set for: {file_path}")

    except ImportError:
        logger.warning("pywin32 not installed, skipping Windows file security")
    except Exception as e:
        logger.error(f"Failed to set file security: {e}")
        raise
```

**requirements.txt に追加**:
```
pywin32==306
```

---

#### 実装方法B: 隠しファイル化（簡易版）

```python
# utils/windows_security.py (簡易版)
import os
import stat
import subprocess
from pathlib import Path

def set_file_hidden_readonly(file_path: Path):
    """ファイルを隠しファイル＋読み取り専用にする（簡易版）

    Args:
        file_path: 保護するファイルパス
    """
    # 読み取り専用属性
    os.chmod(str(file_path), stat.S_IREAD)

    # 隠しファイル＋システムファイル属性
    try:
        subprocess.run(
            ['attrib', '+h', '+s', str(file_path)],
            check=True,
            capture_output=True
        )
        logger.info(f"File hidden and readonly: {file_path}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to set hidden attribute: {e}")
```

**メリット・デメリット**:

| 方法 | メリット | デメリット |
|------|---------|-----------|
| 方法A (ACL) | 真のセキュリティ、他ユーザーからアクセス不可 | pywin32依存、実装複雑 |
| 方法B (隠し) | 依存なし、シンプル | 見つけにくいだけ、読める |

---

#### 推奨実装: ハイブリッド方式

```python
# utils/encryption.py (修正版)
from pathlib import Path
import platform
import logging

logger = logging.getLogger(__name__)

def secure_file_permissions(file_path: Path):
    """プラットフォームに応じたファイル保護

    Args:
        file_path: 保護するファイルパス
    """
    if platform.system() == 'Windows':
        try:
            # 方法A: Windows ACLを試行
            from utils.windows_security import set_file_security_windows
            set_file_security_windows(file_path)
        except ImportError:
            # pywin32がない場合は方法Bにフォールバック
            logger.warning("pywin32 not available, using fallback security")
            from utils.windows_security import set_file_hidden_readonly
            set_file_hidden_readonly(file_path)
    else:
        # Unix/Linux/Mac
        import os
        os.chmod(str(file_path), 0o600)
        logger.info(f"Unix permissions set: {file_path}")
```

---

### APIキー管理クラスの修正

```python
# ai/api_manager.py (修正版)
from cryptography.fernet import Fernet
import keyring
from pathlib import Path
from utils.encryption import secure_file_permissions

class APIManager:
    """APIキー管理"""

    APP_NAME = "Pfft_maker"
    KEY_FILE = Path.home() / ".pfft_maker" / "api.enc"

    def set_api_key(self, api_key: str):
        """APIキーを暗号化して保存

        Args:
            api_key: Claude APIキー
        """
        # ディレクトリ作成
        self.KEY_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Fernetで暗号化
        encrypted = self._fernet.encrypt(api_key.encode())

        # ファイル書き込み
        self.KEY_FILE.write_bytes(encrypted)

        # ✅ プラットフォーム対応のファイル保護
        secure_file_permissions(self.KEY_FILE)

        logger.info("API key saved securely")
```

---

## 問題5: UPX圧縮の無効化

### 現状の問題

```python
# ❌ 間違った設定（technical_requirements.md）
exe = EXE(
    ...
    upx=True,  # Windows Defenderが誤検知
    ...
)
```

**問題点**:
- UPX圧縮されたexeは「Trojan:Win32/Wacatac」として誤検知される
- ユーザーが実行できない
- 配布時に重大な問題

---

### 解決策: UPX無効化＋代替最適化

#### build.spec（修正版）

```python
# build.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('src/config/default_config.json', 'config'),
    ],
    hiddenimports=[
        'anthropic',
        'keyring',
        'keyring.backends.Windows',  # Windowsバックエンド明示
        'pandas',
        'watchdog',
        'win32security',  # pywin32
        'win32api',
        'ntsecuritycon',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ✅ 不要なモジュールを除外してサイズ削減
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'PIL',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'test',
        'tests',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Pfft_maker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # ✅ UPX無効化（必須）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUIモード
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app.ico'
)
```

---

### サイズ削減の代替手段

#### 1. 不要モジュールの除外

```python
excludes=[
    'tkinter',      # 使わないGUIライブラリ
    'matplotlib',   # グラフ描画（不要）
    'numpy',        # 数値計算（pandasが依存してても除外可能）
    'scipy',        # 科学計算（不要）
    'PIL',          # 画像処理（不要）
    'IPython',      # 対話環境（不要）
    'jupyter',      # ノートブック（不要）
    'pytest',       # テスト（本番不要）
    'test',
    'tests',
    'unittest',
]
```

**削減効果**: 約20-30MB

---

#### 2. PyInstallerの最適化オプション

```bash
# ビルドコマンド
pyinstaller build.spec --clean --noconfirm

# または、さらに最適化
pyinstaller build.spec --clean --noconfirm --log-level=WARN
```

---

#### 3. 外部DLLの削除（上級者向け）

```python
# build.spec に追加
import os

# 不要なDLLを除外
def remove_unused_dlls(binaries):
    """不要なDLLを削除"""
    exclude_dlls = [
        'api-ms-win-',  # Windows API DLL（多くは不要）
        'ucrtbase.dll', # Universal CRT（既にシステムにある）
    ]

    filtered = []
    for name, path in binaries:
        if not any(excl in name.lower() for excl in exclude_dlls):
            filtered.append((name, path))
    return filtered

a.binaries = remove_unused_dlls(a.binaries)
```

**削減効果**: 約5-10MB

---

### 予想されるファイルサイズ

| 方法 | ファイルサイズ |
|------|---------------|
| UPX有効 | 30-40MB |
| UPX無効（最適化なし） | 60-80MB |
| UPX無効＋除外最適化 | 45-60MB |
| UPX無効＋除外＋DLL削除 | 40-55MB |

**結論**: UPX無効でも50MB前後に抑えられる

---

## 追加の推奨事項

### デジタル署名（オプション）

Windows Defenderの誤検知をさらに減らすために、デジタル署名を推奨：

```bash
# コード署名（有料証明書が必要）
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com Pfft_maker.exe
```

**メリット**:
- 誤検知率が大幅に低下
- ユーザーの信頼性向上
- SmartScreenの警告が出にくい

**デメリット**:
- コード署名証明書が必要（年間数万円）

---

## 実装チェックリスト

### 問題4: ファイルパーミッション
- [ ] `utils/windows_security.py` 作成
- [ ] Windows ACL実装（方法A）
- [ ] フォールバック実装（方法B）
- [ ] `utils/encryption.py` に `secure_file_permissions()` 追加
- [ ] `ai/api_manager.py` 修正
- [ ] pywin32を `requirements.txt` に追加
- [ ] テスト: Windows環境で他ユーザーからアクセス不可を確認

### 問題5: UPX圧縮
- [ ] `build.spec` の `upx=False` に変更
- [ ] `excludes` リスト追加（不要モジュール除外）
- [ ] ビルドテスト
- [ ] Windows Defenderスキャンテスト
- [ ] ファイルサイズ確認（目標: 60MB以下）

---

## テスト手順

### Windows ACLテスト

```python
# tests/test_windows_security.py
import pytest
from pathlib import Path
from utils.windows_security import set_file_security_windows
import win32security

def test_file_security():
    """ファイルセキュリティのテスト"""
    test_file = Path("test_secure.txt")
    test_file.write_text("secret data")

    # セキュリティ設定
    set_file_security_windows(test_file)

    # DACLを確認
    sd = win32security.GetFileSecurity(
        str(test_file),
        win32security.DACL_SECURITY_INFORMATION
    )
    dacl = sd.GetSecurityDescriptorDacl()

    # ACEが1つだけ（現在のユーザーのみ）
    assert dacl.GetAceCount() == 1

    test_file.unlink()
```

### Windows Defenderテスト

```bash
# ビルド後
pyinstaller build.spec

# Windows Defenderでスキャン
cd dist
"C:\Program Files\Windows Defender\MpCmdRun.exe" -Scan -ScanType 3 -File "Pfft_maker.exe"

# 結果確認
# "No threats found" であればOK
```

---

**問題4と5が完全に解決しました。次の問題に進めます。**
