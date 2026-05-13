# -*- mode: python ; coding: utf-8 -*-
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))

a = Analysis(
    [os.path.join(ROOT, 'xadrez', 'app.py')],
    pathex=[ROOT],
    binaries=[
        (r'C:\stockfish\stockfish-windows-x86-64-avx2.exe', '.'),
    ],
    datas=[
        (os.path.join(ROOT, 'Chess_asset'), 'Chess_asset'),
        (os.path.join(ROOT, 'pixel chess'), 'pixel chess'),
    ],
    hiddenimports=['chess', 'chess.engine', 'pygame'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# Rename bundled stockfish to stockfish.exe
# TOC format: (name_in_bundle, source_path, typecode)
for i, (name, path, kind) in enumerate(a.binaries):
    if 'stockfish' in name.lower() and kind == 'BINARY':
        a.binaries[i] = ('stockfish.exe', path, kind)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Xadrez',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Xadrez',
)
