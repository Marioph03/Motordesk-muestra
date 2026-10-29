# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


# MotorDesk usa varias bibliotecas que importan handlers, fuentes, codecs o
# clientes por nombre durante la ejecucion. Incluirlos aqui evita depender de
# que PyInstaller pueda inferir esos imports dinamicos desde el codigo.
hiddenimports = sorted(
    set(
        collect_submodules('passlib.handlers')
        + collect_submodules('cryptography')
        + collect_submodules('qrcode')
        + collect_submodules('openpyxl')
        + collect_submodules('reportlab')
        + collect_submodules('groq')
        + collect_submodules('openai')
        + collect_submodules('requests_pkcs12')
    )
)

datas = (
    collect_data_files('reportlab')
    + collect_data_files('openpyxl')
    + collect_data_files('qrcode')
    # La versión nativa ejecuta Alembic al iniciar. Estas fuentes no se
    # detectan como imports de Python, por lo que deben viajar con el backend.
    + [
        ('alembic.ini', '.'),
        ('migrations', 'migrations'),
        # La plantilla de inspeccion es un recurso binario y PyInstaller no
        # puede descubrirla mediante imports. El PDF la necesita para dibujar
        # el croquis de danos del vehiculo.
        ('app/assets', 'app/assets'),
    ]
)


a = Analysis(
    ['run_motordesk.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='MotorDeskBackend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX aumenta las detecciones heurísticas en algunos antivirus. El
    # instalador prioriza compatibilidad y trazabilidad sobre unos MB menos.
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MotorDeskBackend',
)
