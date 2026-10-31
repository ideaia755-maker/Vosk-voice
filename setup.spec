# -*- mode: python ; coding: utf-8 -*-
import os

project_dir = os.path.abspath(SPECPATH)

a = Analysis(
    ['installer_builder.py'],
    pathex=[project_dir],
    binaries=[],
    datas=[
        ('installer_payload.zip', '.'),
        ('assets', 'assets'),
    ],
    hiddenimports=['tkinter', 'PIL', 'winreg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'playwright', 'numpy'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AuraVoice_Setup_v1.0.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=os.path.join(project_dir, 'assets', 'aura_app.ico'),
)
