from cx_Freeze import setup, Executable
import os.path
import sys

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = {
    'build_exe': {
        'include_files': [
            os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
            os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
            'proiezione.prj'
        ],
    },
}

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('gui.py', base=base, targetName='MappeVale.exe')
]

setup(name='Mappe Valentina',
      version='2.0',
      description='Il programma genera dei diagrammi a torta rappresentanti i superamenti, partendo da un file excel',
      options=buildOptions,
      executables=executables)
