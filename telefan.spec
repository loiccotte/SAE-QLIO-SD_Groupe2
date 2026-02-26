# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — T'ELEFAN MES 4.0 standalone executable."""

import os

block_cipher = None

a = Analysis(
    ['standalone.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('data/mes4.db', 'data'),
        ('config.example.ini', '.'),
    ],
    hiddenimports=[
        'app',
        'app.routes',
        'app.auth',
        'app.export',
        'app.models',
        'app.services',
        'waitress',
        'pymysql',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest_flask',
        'weasyprint',
        'tkinter',
        '_tkinter',
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TelefanMES',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TelefanMES',
)
