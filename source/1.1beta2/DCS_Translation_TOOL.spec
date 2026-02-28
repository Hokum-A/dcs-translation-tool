# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for DCS Translation TOOL
# Updated: 2026-02-21

block_cipher = None

# List of all additional files to include in the executable
# Format: (source_path, destination_folder_in_exe)
# destination_folder_in_exe: '.' means root of the internal directory
added_files = [
    ('DCSTT_logo.png', '.'),
    ('Drag.png', '.'),
    ('Exit1.png', '.'),
    ('Exit2.png', '.'),
    ('cat.png', '.'),
    ('radiocat.png', '.'),       # Used in dialogs.py and as fallback
    ('radiocat2.png', '.'),      # Used in main.py for radio button
    ('filescat.png', '.'),       # Used in main.py for files button
    ('optionscat.png', '.'),     # Used in main.py for options button
    ('EXIT.gif', '.'),
    ('down.gif', '.'),
    ('arrow1.gif', '.'),
    ('arrow2.gif', '.'),
    ('DSCTT.ico', '.')
]

# Analysis of the main script and its dependencies
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['PyQt5', 'pygame', 'PyQt5.QtNetwork'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='DCS_Translation_TOOL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI application)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='DSCTT.ico',
)
