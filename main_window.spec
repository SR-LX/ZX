# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['c:\\Users\\Administrator\\Desktop\\摘星0_0_1\\ZX\\main_window.py'],
    pathex=[],
    binaries=[],
    datas=[('c:\\Users\\Administrator\\Desktop\\摘星0_0_1\\ZX\\resource', 'resource'), ('c:\\Users\\Administrator\\Desktop\\摘星0_0_1\\ZX\\resource\\light', 'resource\\light'), ('c:\\Users\\Administrator\\Desktop\\摘星0_0_1\\ZX\\resource\\dark', 'resource\\dark')],
    hiddenimports=['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'qfluentwidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PySide6'],
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
    name='main_window',
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
    icon=['c:\\Users\\Administrator\\Desktop\\摘星0_0_1\\00.ico'],
)
