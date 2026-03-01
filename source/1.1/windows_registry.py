import sys
import os
import winreg
import ctypes

def _read_reg_value(key_path, value_name=""):
    """Вспомогательная функция для безопасного чтения из реестра"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
            return value
    except FileNotFoundError:
        return None

def register_file_associations():
    """
    Регистрирует расширения .miz и .cmp для текущего пользователя, 
    чтобы Windows использовала иконку программы для этих файлов.
    """
    # Работает только в скомпилированном EXE (pyinstaller) на Windows
    if sys.platform != "win32" or not getattr(sys, 'frozen', False):
        return

    exe_path = sys.executable
    icon_path = f'"{exe_path}",0' # Иконка из нашего EXE
    command = f'"{exe_path}" "%1"'

    extensions = {
        '.miz': 'DCSTranslatorTool.miz',
        '.cmp': 'DCSTranslatorTool.cmp'
    }

    needs_update = False

    try:
        # Проверяем, нужно ли обновлять реестр
        for ext, prog_id in extensions.items():
            current_prog_id = _read_reg_value(rf"Software\Classes\{ext}")
            current_command = _read_reg_value(rf"Software\Classes\{prog_id}\shell\open\command")
            
            # Если ассоциации нет или путь изменился (программу переместили)
            if current_prog_id != prog_id or current_command != command:
                needs_update = True
                break

        # Если пути актуальны, моментально выходим
        if not needs_update:
            return

        # Прописываем ключи
        for ext, prog_id in extensions.items():
            # Привязка расширения
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{ext}") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, prog_id)
            
            # Настройка ProgID
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"DCS Mission File ({ext})")
                
            # Иконка
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}\DefaultIcon") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, icon_path)
                
            # Команда автооткрытия
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}\shell\open\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, command)

        # Вызываем обновление иконок в Windows Explorer (Только при реальных изменениях в реестре)
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
        print("System file associations updated successfully.")
        
    except Exception as e:
        print(f"Failed to register file associations: {e}")
