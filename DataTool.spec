# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# --- 1. 在这里一次性收集所有的数据文件 ---
all_datas = []

# 添加字体文件，使用和下面一致的2元素元组格式
all_datas.append(('resources/simhei.ttf', 'resources'))

# 添加 matplotlib 和 pandas 的数据文件
all_datas.extend(collect_data_files('matplotlib'))
all_datas.extend(collect_data_files('pandas'))


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=all_datas,  # --- 2. 将准备好的完整列表传递给 datas 参数 ---
    hiddenimports=[
        'PyQt5.sip',
        'PyQt5.QtPrintSupport',
        'pandas._libs.tslibs.base',
        'watchdog.observers.polling',
    ],
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
    name='DataTool',
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
    icon=None # 在这里可以指定图标路径, e.g., icon='app.ico'
)
