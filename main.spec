# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_all

# Ajouter le répertoire courant au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(SPECPATH))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Collecter les bibliothèques dynamiques de Python
python_libs = collect_dynamic_libs('python')

# Collecter tous les éléments de cryptography
crypto_datas, crypto_binaries, crypto_hiddenimports = collect_all('cryptography')

a = Analysis(
    ['main.py'],
    pathex=[current_dir],
    binaries=python_libs + crypto_binaries,  # Ajouter les bibliothèques cryptography
    datas=[
        ('gui/*.py', 'gui'),
        ('utils/*.py', 'utils'),
        ('constants.py', '.'),
        ('__init__.py', '.'),
    ] + crypto_datas,  # Ajouter les données cryptography
    hiddenimports=[
        # Modules de la bibliothèque standard
        'json',
        'os',
        'sys',
        'datetime',
        'time',
        'typing',
        'pathlib',
        'subprocess',
        'tempfile',
        'shutil',
        'random',
        'base64',
        'hashlib',
        # Modules cryptography
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.asymmetric',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.kdf',
        'cryptography.hazmat.primitives.padding',
        'cryptography.hazmat.primitives.serialization',
        # Modules PyQt
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        # Modules de l'application
        'gui',
        'utils',
        'constants',
        'gui.main_window',
        'gui.mount_dialog',
        'gui.loading_dialog',
        'gui.mounted_volumes_list',
        'gui.preferences_dialog',
        'gui.create_volume_wizard',
        'gui.change_password_dialog',
        'gui.device_dialog',
        'gui.progress_dialog',
        'utils.favorites',
        'utils.veracrypt',
        'utils.system',
        'utils.entropy_collector',
        'utils.volume_creation',
        'utils.sudo_session',
        'utils.preferences',
        'utils.themes',
        'utils.crypto'
    ] + crypto_hiddenimports,  # Ajouter les imports cachés de cryptography
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Ajouter les bibliothèques système nécessaires
extra_binaries = []
for lib in ['libpython3.12.so.1.0', 'libpython3.12.so', 'libpython3.so']:
    lib_path = os.path.join('/usr/lib', lib)
    if os.path.exists(lib_path):
        extra_binaries.append((lib_path, '.'))

# Ajouter les bibliothèques OpenSSL nécessaires pour cryptography
for lib in ['libssl.so.3', 'libcrypto.so.3']:
    lib_path = os.path.join('/usr/lib', lib)
    if os.path.exists(lib_path):
        extra_binaries.append((lib_path, '.'))

a.binaries += extra_binaries

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
