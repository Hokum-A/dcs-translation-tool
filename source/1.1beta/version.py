class VersionInfo:
    """Управление версиями программы"""
    # МЕСТО ДЛЯ ИЗМЕНЕНИЯ ВЕРСИИ ПРОГРАММЫ
    CURRENT = "1.03" 
    RELEASE_DATE = "2026"

    HISTORY = {
        "1.03": "Стабилизация: исправление запуска, очистка предпросмотра от проверки слешей",
        "1.02": "Рефакторинг сохранения CMP (диалог, бэкапы), исправление дублирования ключей, улучшенные заглушки",
        "1.01": "Выбор папки при перезаписи, исправление кодировки имен ZIP (LRM fix), обновление интерфейса",
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
