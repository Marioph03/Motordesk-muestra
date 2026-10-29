# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['launcher/motordesk_launcher.py'],
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
    [],
    exclude_binaries=True,
    name='MotorDesk',
    icon='installer/assets/MotorDesk.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # No comprimimos el ejecutable: los binarios con UPX reciben más alertas
    # heurísticas de Defender que los empaquetados convencionales.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# El lanzador se instala como una carpeta autocontenida. Evitamos el modo
# "onefile", que crea un proceso hijo temporal y puede activar la validación
# de proceso padre de PyInstaller en algunos Windows al arrancar desde un
# instalador o acceso directo. El backend ya se distribuye de este modo.
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    # No comprimimos el ejecutable: los binarios con UPX reciben más alertas
    # heurísticas de Defender que los empaquetados convencionales.
    upx=False,
    upx_exclude=[],
    name='MotorDesk',
)
