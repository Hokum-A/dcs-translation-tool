class VersionInfo:
    """Управление версиями программы"""
    CURRENT = "1.0"
    RELEASE_DATE = "2026"

    HISTORY = {
        "1.0": "Полный рефакторинг программы с новой модульной структурой и интеграция нового парсера LuaDictionaryParser"
    }

    @classmethod
    def get_info(cls):
        return {
            "version": cls.CURRENT,
            "date": cls.RELEASE_DATE,
            "history": cls.HISTORY
        }

    @classmethod
    def print_version(cls):
        """Выводит информацию о версии в консоль"""
        info = cls.get_info()
        print(f"\n{'='*50}")
        print(f"DCS TRANSLATION TOOL v{info['version']}")
        print(f"{'='*50}")
        for ver, desc in info['history'].items():
            print(f"v{ver}: {desc}")
        print(f"{'='*50}\n")
