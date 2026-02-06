# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('DSCTT.ico', '.'), ('Drag.png', '.'), ('Exit1.png', '.'), ('Exit2.png', '.'), ('EXIT.gif', '.'), ('DCSTT_logo.png', '.'), ('cat.png', '.'), ('arrow1.gif', '.'), ('arrow2.gif', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DCS_Translation_TOOL_1.01',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['DSCTT.ico'],
)
