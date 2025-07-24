# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ['Themis SELA.py'],
    pathex=[],
    binaries=[],
    datas=[
        ( 'C:/Users/kanal/.EasyOCR/model', 'easyocr/model' ),
        ( 'usernames.txt', '.' ),
        ('arrow.png', '.'),
        ('Themis.ico', '.'),
        ( 'IBMPlexSans-Medium.ttf', '.' )      ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tk', 'tcl', '_tkinter', 'tkinter',
        'PyQt5', 
        'pandas', 
        'matplotlib',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.hiddenimports += ['torch', 'torch.nn', 'torch.nn.functional']


pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Themis_SELA',
    debug=False,
    console=False,
    upx=False, 
    bootloader_ignore_signals=False,
    strip=False,
    icon='Themis.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False, 
    upx_exclude=[],
    name='Themis_SELA'
)