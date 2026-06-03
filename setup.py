"""
Script de empaquetado con cx_Freeze para Simulador de Distribucion de Pesos

Uso:
    python setup.py build          # Construir en build/
    python setup.py bdist_msi      # Crear instalador MSI (Windows)
    python setup.py bdist_mac      # Crear .app (macOS)
    python setup.py bdist_rpm      # Crear RPM (Linux)
    python setup.py bdist_deb      # Crear .deb (Debian/Ubuntu)
"""

import sys
import os
from cx_Freeze import setup, Executable

# Configuracion de la aplicacion
APP_NAME = "SimuladorCeldas"
VERSION = "1.1.0"
DESCRIPTION = "Simulador de distribucion de pesos con protocolo HBM"
AUTHOR = "Anthony Josue Lauar Perez"

# Archivo principal
MAIN_SCRIPT = "app.py"

# Incluir/Excluir paquetes
build_exe_options = {
    "packages": [
        "tkinter",           # GUI
        "serial",            # pyserial - comunicacion con puerto COM
        "serial.tools.list_ports",  # escaneo de puertos
        "numpy",             # operaciones numericas
        "json",              # parseo de datos y configuracion
        "re",                # expresiones regulares (protocolo HBM)
        "threading",         # hilo de lectura serial
        "time",              # pausas en bucle de lectura
        "traceback",         # manejo de errores
    ],
    "excludes": [
        # Excluir paquetes innecesarios para reducir el tamano
        "unittest",
        "email",
        "html",
        "http",
        "urllib",
        "xml",
        "xmlrpc",
        "pydoc",
        "doctest",
        "test",
        "distutils",
        "lib2to3",
        "concurrent",
        "asyncio",
        "multiprocessing",
        "pdb",
        "profile",
        "pstats",
        "tabnanny",
        "pickle",
        "audiodev",
        "audioop",
        "imghdr",
        "sunaudio",
        "chunk",
        "sndhdr",
        "ossaudiodev",
        "curses",
        "nis",
        "dbm",
        "gdbm",
        "sqlite3",
        "turtle",
        "turtledemo",
    ],
    "include_files": [
        # Archivos de configuracion
        ("config/settings.json", "config/settings.json"),
        # Documentacion (opcional - solo .md, sin emojis ni imagenes)
        ("docs/protocolo_comunicacion.md", "docs/protocolo_comunicacion.md"),
        ("README.md", "README.md"),
    ],
    "optimize": 2,
    "silent": True,
}

# Configuracion del ejecutable
base = None
icon_path = None

if sys.platform == "win32":
    # Usar Win32GUI para ocultar la consola (comentar para ver logs [SERIAL])
    # base = "Win32GUI"
    base = None  # None = mantener consola visible (util para depuracion)

    # Ruta del icono (opcional - desempaquetar uno si existe)
    icon_candidates = [
        "icon.ico",
        "resources/icon.ico",
        "app.ico",
    ]
    for ico in icon_candidates:
        if os.path.exists(ico):
            icon_path = ico
            break

executable = Executable(
    script=MAIN_SCRIPT,
    base=base,
    target_name=APP_NAME,
    icon=icon_path,
    shortcut_name=APP_NAME,
    shortcut_dir="ProgramMenuFolder",
)

# Llamada a setup()
setup(
    name=APP_NAME,
    version=VERSION,
    description=DESCRIPTION,
    author=AUTHOR,
    options={"build_exe": build_exe_options},
    executables=[executable],
)
