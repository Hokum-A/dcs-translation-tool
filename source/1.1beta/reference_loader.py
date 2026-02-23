import zipfile
import os
import tempfile
from parser import LuaDictionaryParser


class ReferenceLoader:
    """Загрузчик и кэшер словаря из .miz архива для любой локали.

    Хранит маппинг: (miz_path, locale) -> { key: [parts...] }
    """
    def __init__(self):
        self.cache = {}  # (miz_path, locale) -> { key: [parts...] }
        self.last_fallback = None  # Если было fallback на DEFAULT — хранит имя исходной локали

    def clear_cache(self):
        """Очищает весь кэш (вызывать при открытии нового .miz файла)"""
        self.cache.clear()

    def load_locale_from_miz(self, miz_path, locale='DEFAULT'):
        """Загрузить и закэшировать dictionary для указанной локали из .miz файла.

        Возвращает маппинг key -> [parts...]
        """
        if not miz_path or not os.path.exists(miz_path):
            return {}

        cache_key = (miz_path, locale)
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            with zipfile.ZipFile(miz_path, 'r') as miz_archive:
                # Ищем dictionary внутри l10n/<locale>
                # Учитываем регистр, возможные расширения (dictionary.lua) и вложенные пути
                target = f'l10n/{locale}/dictionary'
                found_path = None
                for item in miz_archive.infolist():
                    name = item.filename
                    try:
                        nm = name.encode('cp437').decode('utf-8')
                    except Exception:
                        nm = name
                    path_norm = nm.replace('\\', '/').strip('/')
                    path_norm_lower = path_norm.lower()

                    # Прямое совпадение
                    if path_norm_lower == target.lower():
                        found_path = item.filename
                        break

                    # Файл может иметь расширение или находиться внутри вложенной структуры,
                    # например l10n/RU/dictionary.lua — проверяем имя последнего сегмента
                    parts = path_norm.split('/')
                    last = parts[-1].lower() if parts else ''
                    if path_norm_lower.startswith(f'l10n/{locale.lower()}/') and last.startswith('dictionary'):
                        found_path = item.filename
                        break

                if not found_path:
                    # Fallback: если запрошенная локаль не найдена — пробуем DEFAULT
                    if locale != 'DEFAULT':
                        print(f"WARNING: Locale '{locale}' not found in miz, falling back to DEFAULT")
                        self.last_fallback = locale
                        self.cache[cache_key] = {}
                        return self.load_locale_from_miz(miz_path, 'DEFAULT')
                    self.cache[cache_key] = {}
                    return {}

                # Локаль найдена — сбрасываем флаг fallback
                self.last_fallback = None

                raw = miz_archive.read(found_path).decode('utf-8', errors='replace')

                # Используем существующий LuaDictionaryParser для корректного разбора
                parser = LuaDictionaryParser()
                # Parser expects a file; use a temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False, encoding='utf-8') as tf:
                    tf.write(raw)
                    tfname = tf.name

                try:
                    entries = parser.parse_file(tfname)
                finally:
                    try:
                        os.unlink(tfname)
                    except Exception:
                        pass

                mapping = {}
                for key, (text_parts, _, _) in entries.items():
                    mapping[key] = list(text_parts)

                self.cache[cache_key] = mapping
                return mapping
        except Exception:
            # Не поднимаем исключение — возвращаем пустой маппинг
            self.cache[cache_key] = {}
            return {}

    def load_default_from_miz(self, miz_path):
        """Обратная совместимость: загружает DEFAULT locale"""
        return self.load_locale_from_miz(miz_path, 'DEFAULT')

    def get_parts_for_key(self, miz_path, locale, key):
        """Возвращает список частей для ключа в закэшированной локали или []"""
        cache_key = (miz_path, locale)
        mapping = self.cache.get(cache_key, {})
        return mapping.get(key, [])
