import sys
import os

# PyInstaller bundle fix for Vosk & DLLs
if getattr(sys, 'frozen', False):
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    
    # Добавляем папку бандла в пути DLL Windows для Python 3.8+
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(base_dir)
        except Exception:
            pass

    # Папка vosk внутри _MEIPASS
    vosk_dir = os.path.join(base_dir, 'vosk')
    if os.path.exists(vosk_dir) and hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(vosk_dir)
        except Exception:
            pass

    os.environ['PATH'] = base_dir + os.pathsep + vosk_dir + os.pathsep + os.environ.get('PATH', '')
