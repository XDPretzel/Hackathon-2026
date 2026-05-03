# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('/Users/rossbaldwin/Desktop/Hackathon-2026/.venv/lib/python3.11/site-packages/customtkinter', 'customtkinter'), ('/Users/rossbaldwin/Desktop/Hackathon-2026/.venv/lib/python3.11/site-packages/mediapipe', 'mediapipe')],
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
    [],
    exclude_binaries=True,
    name='Gest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Gest',
)
app = BUNDLE(
    coll,
    name='Gest.app',
    icon=None,
    bundle_identifier='com.gest.media.controller',
)
