# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import vosk

block_cipher = None
project_dir = os.path.abspath(SPECPATH)

# DLL файлы Vosk
vosk_dir = os.path.dirname(vosk.__file__)
vosk_binaries = [
    (os.path.join(vosk_dir, f), 'vosk')
    for f in os.listdir(vosk_dir)
    if f.endswith('.dll')
] + [
    (os.path.join(vosk_dir, f), '.')
    for f in os.listdir(vosk_dir)
    if f.endswith('.dll')
]

a = Analysis(
    ['app.py'],
    pathex=[project_dir],
    binaries=vosk_binaries,
    datas=[
        ('model', 'model'),
        ('assets', 'assets'),
        (vosk_dir, 'vosk'), # Кладем всю папку пакета vosk внутрь бандла
    ],
    hiddenimports=[
        'vosk',
        'sounddevice',
        'pynput',
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'pyperclip',
        'pystray',
        'pystray._win32',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_vosk.py'],
    excludes=['matplotlib', 'scipy', 'playwright', 'tkinter.test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AuraVoice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_dir, 'assets', 'aura_app.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AuraVoice',
)
