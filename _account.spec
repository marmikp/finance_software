# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['C:/Users/Raja/Desktop/marmik/finance_software/_account.py'],
             pathex=['C:\\Users\\Raja\\Desktop\\marmik\\finance_software'],
             binaries=[],
             datas=[('C:/Users/Raja/Desktop/marmik/finance_software/api-ms-win-core-heat-key-l1-1-0-1.dll', '.'), ('C:/Users/Raja/Desktop/marmik/finance_software/api-ms-win-core-heat-l1-1-0-1.dll', '.'), ('C:/Users/Raja/Desktop/marmik/finance_software/web', 'web/'), ('C:/Users/Raja/Desktop/marmik/finance_software/Documents', 'Documents/'), ('C:/Users/Raja/Desktop/marmik/finance_software/icon.ico', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='_account',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='C:\\Users\\Raja\\Desktop\\marmik\\finance_software\\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='_account')
