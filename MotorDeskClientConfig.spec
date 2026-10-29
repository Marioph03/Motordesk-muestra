# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["client_setup/motordesk_client_setup.py"],
    pathex=[],
    binaries=[],
    datas=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MotorDesk-Configurar-Cliente",
    icon="installer/assets/MotorDesk.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # Mantener el binario sin UPX reduce falsos positivos heurísticos.
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
