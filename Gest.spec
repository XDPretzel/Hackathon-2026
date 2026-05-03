# -*- mode: python ; coding: utf-8 -*-


import os
import customtkinter
import mediapipe

ctk_path = os.path.dirname(customtkinter.__file__)
mp_path = os.path.dirname(mediapipe.__file__)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(ctk_path, 'customtkinter'), (mp_path, 'mediapipe'), ('gest.png', '.')],
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
    icon='Gest.icns',
    bundle_identifier='com.gest.media.controller',
    info_plist={
        'NSCameraUsageDescription': 'Gest needs camera access for hand tracking media control.',
        'NSHighResolutionCapable': True,
    },
)
