import re
import os
from typing import List, Tuple, Optional, Dict

class CampaignParser:
    """
    Улучшенный парсер файлов кампаний DCS (.cmp).
    Парсит файл построчно, сохраняя структуру многострочных значений 
    с использованием обратных слешей (\) или [[ ]], аналогично LuaDictionaryParser.
    Теперь поддерживает дублирующиеся ключи (для вложенных структур) и фильтрует их по отступам.
    """

    def __init__(self):
        self.cmp_data = {}
        # Убрали necessaryUnits из базовых ключей
        self.base_keys = ["name", "description", "pictureSuccess", "pictureFailed", "picture"]
        # Список ключей, которые не нужно отображать (технические)
        self.excluded_keys = ["directory", "fullPath", "stages", "necessaryUnits", "version", "startStage"]
        
        self.supported_languages = ['EN', 'RU', 'CN', 'CS', 'FR', 'ES', 'JP', 'DE', 'KO']
        
        self.default_texts = {
            'EN': {'name': "Enter campaign name", 'description': "Enter campaign description"},
            'RU': {'name': "Введите название кампании", 'description': "Введите описание кампании"},
            'DE': {'name': "Geben Sie einen Kampagnennamen ein", 'description': "Geben Sie eine Kampagnenbeschreibung ein"},
            'FR': {'name': "Entrez le nom de la campagne", 'description': "Entrez la description de la campagne"},
            'ES': {'name': "Introduzca el nombre de la campaña", 'description': "Introduzca la descripción de la campaña"},
            'CN': {'name': "输入战役名称", 'description': "输入战役描述"},
            'JP': {'name': "キャンペーン名を入力してください", 'description': "キャンペーンの説明を入力してください"},
            'KO': {'name': "캠페인 이름을 입력하십시오", 'description': "캠페인 설명을 입력하십시오"},
            'CS': {'name': "Zadejte název kampaně", 'description': "Zadejte popis kampaně"},
        }
        
        self.current_key = None
        self.current_raw_parts = []
        self.current_file_lines = []
        self.entries = [] # Список словарей: {'key': str, 'parts': list, 'lines': list, 'indent': int}
        self.is_multiline_lua = False 
        self.current_indent = 0

    def parse_content(self, content: str) -> List[Dict]:
        """
        Парсит контент .cmp файла и возвращает список структур для отображения.
        """
        self.entries = []
        self.current_key = None
        self.current_raw_parts = []
        self.current_file_lines = []
        self.current_indent = 0
        
        lines = content.splitlines()
        
        for line in lines:
            self._process_line(line)
            
        if self.current_key:
            self._save_current_entry()

        # Теперь формируем all_lines_data из списка entries с фильтрацией
        return self._prepare_display_data()

    def _process_line(self, line: str):
        """Обрабатывает одну строку файла по аналогии с parser.py"""
        
        # Если мы уже внутри многострочного блока [[ ]]
        if self.is_multiline_lua:
            self.current_file_lines.append(line)
            if ']]' in line:
                # Конец блока [[ ]]
                end_pos = line.find(']]')
                self.current_raw_parts.append(line[:end_pos])
                self._save_current_entry()
                self.is_multiline_lua = False
                self.current_key = None
            else:
                self.current_raw_parts.append(line)
            return

        # Ищем начало ключа: ["key"] = 
        # Добавляем захват отступа
        key_match = re.search(r'^(\s*)\["([^"]+)"\]\s*=\s*', line)
        if key_match:
            if self.current_key:
                self._save_current_entry()
            
            indent_str = key_match.group(1)
            # Считаем табы за 4 пробела, хотя в DCS обычно пробелы
            self.current_indent = len(indent_str.replace('\t', '    '))
            
            self.current_key = key_match.group(2)
            self.current_raw_parts = []
            self.current_file_lines = [line]
            
            # Остаток строки после =
            after_eq = line[key_match.end():].strip()
            
            if after_eq.startswith('[['):
                self.is_multiline_lua = True
                content_start = after_eq[2:]
                if ']]' in content_start:
                    # Однострочный [[ ]]
                    end_pos = content_start.find(']]')
                    self.current_raw_parts.append(content_start[:end_pos])
                    self._save_current_entry()
                    self.is_multiline_lua = False
                    self.current_key = None
                else:
                    self.current_raw_parts.append(content_start)
            
            elif after_eq.startswith('"'):
                content_start = after_eq[1:]
                # Проверяем, заканчивается ли строка на \ (многострочность типа dictionary)
                if line.endswith('\\'):
                    self.current_raw_parts.append(content_start[:-1]) # убираем \
                elif content_start.endswith('",') or content_start.endswith('"'):
                    # Однострочный в кавычках
                    actual_end = -2 if content_start.endswith('",') else -1
                    self.current_raw_parts.append(content_start[:actual_end])
                    self._save_current_entry()
                    self.current_key = None
                else:
                    # Просто строка в кавычках без запятой (бывает)
                    self.current_raw_parts.append(content_start)
        
        elif self.current_key:
            # Мы внутри многострочного блока с обратными слешами
            self.current_file_lines.append(line)
            if line.endswith('\\'):
                self.current_raw_parts.append(line[:-1])
            elif line.endswith('",') or line.endswith('"'):
                actual_end = -2 if line.endswith('",') else -1
                self.current_raw_parts.append(line[:actual_end])
                self._save_current_entry()
                self.current_key = None
            else:
                self.current_raw_parts.append(line)

    def _save_current_entry(self):
        """Сохраняет текущую запись"""
        if not self.current_key:
            return
        
        # Декодируем каждый кусок (как в parser.py)
        decoded_parts = [self._decode_text(p) for p in self.current_raw_parts]
        
        # Сохраняем в список словарей
        self.entries.append({
            'key': self.current_key,
            'parts': decoded_parts,
            'lines': self.current_file_lines.copy(),
            'indent': self.current_indent
        })
        
        self.current_key = None
        self.current_raw_parts = []
        self.current_file_lines = []
        self.current_indent = 0

    def _decode_text(self, text: str) -> str:
        """Преобразует текст из файла для отображения (как в parser.py)"""
        result = text.replace('\\"', '"')
        result = result.replace('\\\\', '\\')
        return result

    def _prepare_display_data(self) -> List[Dict]:
        """Подготавливает данные для all_lines_data с фильтрацией по отступам"""
        all_lines_data = []
        
        # 1. Сначала найдем "корневой" уровень отступа для наших base_keys.
        # Обычно это 4 пробела. Но может быть и 0, и 2.
        # Найдем минимальный отступ среди всех вхождений base_keys.
        min_indent = 1000
        found_any = False
        
        for entry in self.entries:
            key_base, _ = self._split_key(entry['key'])
            if key_base in self.base_keys:
                if entry['indent'] < min_indent:
                    min_indent = entry['indent']
                    found_any = True
        
        if not found_any:
            min_indent = 4 # Fallback default
            
        print(f"[CampaignParser] Detected root indent: {min_indent}")

        # 2. Теперь фильтруем и группируем только те ключи, которые находятся на корневом уровне
        # (допускаем небольшое отклонение, например +2 пробела, но не +10 как для вложенных миссий)
        root_entries = {} # base_key -> { LANG: parts }
        
        processed_keys = set()

        for entry in self.entries:
            full_key = entry['key']
            base, lang = self._split_key(full_key)
            
            # Проверяем интересные нам ключи
            if base in self.base_keys:
                # Фильтр по отступу: только корневые!
                # Nested ключи обычно имеют +1 уровень отступа (например +4 пробела)
                if entry['indent'] <= min_indent + 2:
                    if base not in root_entries: root_entries[base] = {}
                    # Если такой язык уже есть (дубликат на руте?), перезапишем (last wins) или сохраним первый?
                    # Обычно на руте дубликатов быть не должно.
                    root_entries[base][lang] = entry['parts']
        
        # 3. Формируем список для отображения
        
        # 3. Формируем список для отображения
        
        # Сначала base_keys в заданном порядке + автозаполнение
        for b_key in self.base_keys:
            # Получаем существующие языки для этого ключа (если есть)
            existing_langs = list(root_entries.get(b_key, {}).keys())
            
            # Собираем полный набор языков: ORIGINAL + поддерживаемые
            all_langs = set(['ORIGINAL']) | set(self.supported_languages)
            
            # Сортируем: ORIGINAL первый, затем EN, потом остальные
            sorted_langs = sorted(list(all_langs), key=lambda x: (x != 'ORIGINAL', x != 'EN', x))
            
            for lang in sorted_langs:
                # Определяем полный ключ
                if lang == 'ORIGINAL':
                    full_key = b_key
                else:
                    full_key = f"{b_key}_{lang}"
                
                parts = []
                is_placeholder = False
                
                # Если такой ключ есть в файле - берем его
                if b_key in root_entries and lang in root_entries[b_key]:
                    parts = root_entries[b_key][lang]
                else:
                    # Если ключа нет - создаем дефолтный (кроме ORIGINAL)
                    if lang != 'ORIGINAL':
                        default_val = ""
                        if b_key == 'name':
                             # Берем текст для конкретного языка или дефолтный EN
                             lang_defaults = self.default_texts.get(lang, self.default_texts['EN'])
                             default_val = lang_defaults.get(b_key, "")
                             if default_val:
                                 parts = [default_val]
                                 is_placeholder = True
                        elif b_key == 'description':
                             # Для description копируем СТРУКТУРУ из ORIGINAL
                             lang_defaults = self.default_texts.get(lang, self.default_texts['EN'])
                             default_text = lang_defaults.get(b_key, "Enter campaign description")
                             
                             # Берем структуру из ORIGINAL (количество частей и пустые строки)
                             original_parts = root_entries.get(b_key, {}).get('ORIGINAL', [])
                             if original_parts:
                                 # Копируем структуру: заменяем непустые части на заглушку, пустые оставляем пустыми
                                 parts = []
                                 for idx, orig_part in enumerate(original_parts):
                                     if orig_part.strip():  # Если строка непустая
                                         parts.append(default_text)
                                     else:  # Если строка пустая
                                         parts.append("")
                                 is_placeholder = True
                             else:
                                 # Если ORIGINAL нет, просто одна строка
                                 parts = [default_text]
                                 is_placeholder = True
                        elif b_key in ['picture', 'pictureSuccess', 'pictureFailed']:
                             # Для картинок берем значение из ORIGINAL или EN (если есть)
                             # Попробуем найти хоть какое-то значение в root_entries[b_key]
                             if b_key in root_entries:
                                 if 'ORIGINAL' in root_entries[b_key]:
                                     default_val = root_entries[b_key]['ORIGINAL'][0]
                                 elif 'EN' in root_entries[b_key]:
                                     default_val = root_entries[b_key]['EN'][0]
                                 elif list(root_entries[b_key].values()): # Берем первый попавшийся
                                     default_val = list(root_entries[b_key].values())[0][0]
                             
                             if default_val:
                                 parts = [default_val]
                                 is_placeholder = True
                
                if parts:
                    for part in parts:
                        all_lines_data.append({
                            'key': full_key,
                            'original_text': part,
                            'display_text': part,
                            'translated_text': part, # По умолчанию заполняем оригиналом для удобства
                                                                             # Или лучше оставить пустым, если мы хотим чтобы при пустом переводе брался оригинал?
                                                                             # Нет, в данном случае "оригинал" - это заглушка.
                                                                             # Если мы оставим translated_text пустым, при сохранении возьмется original_text (заглушка).
                                                                             # Это ОК.
                            'should_translate': True,
                            'is_empty': not part.strip(),
                            'ends_with_backslash': part.endswith('\\') if part else False,
                            'is_placeholder': is_placeholder
                        })
                
            processed_keys.add(b_key)
        
        # Затем остальные ключи (не base_keys), если они на руте?
        # В .cmp обычно нас интересуют только base_keys.
        # Но если есть кастомные поля на руте, добавим их.
        
        # Соберем остальные рутовые ключи
        other_root_entries = {}
        for entry in self.entries:
            full_key = entry['key']
            base, lang = self._split_key(full_key)
            if base not in self.base_keys and base not in processed_keys:
                 # Не берем excluded_keys
                 if base not in self.excluded_keys:
                     if entry['indent'] <= min_indent + 2:
                         if base not in other_root_entries: other_root_entries[base] = {}
                         other_root_entries[base][lang] = entry['parts']
                     
        for b_key in sorted(other_root_entries.keys()):
             for lang in sorted(other_root_entries[b_key].keys(), key=lambda x: (x != 'ORIGINAL', x)):
                full_key = b_key if lang == 'ORIGINAL' else f"{b_key}_{lang}"
                parts = other_root_entries[b_key][lang]
                for part in parts:
                    all_lines_data.append({
                        'key': full_key,
                        'original_text': part,
                        'display_text': part,
                        'translated_text': part,
                        'should_translate': True,
                        'is_empty': not part.strip(),
                        'ends_with_backslash': part.endswith('\\') if part else False
                    })
        
        return all_lines_data

    def _split_key(self, full_key: str) -> Tuple[str, str]:
        """Разбивает ключ на базовый и язык"""
        parts = full_key.split('_')
        # Проверяем, является ли последний элемент языковым кодом (2 заглавные буквы)
        if len(parts) > 1 and parts[-1].isupper() and len(parts[-1]) == 2:
            return '_'.join(parts[:-1]), parts[-1]
        return full_key, "ORIGINAL"

    def _encode_text(self, text: str) -> str:
        """Преобразует текст для записи в файл (как в parser.py)"""
        result = text.replace('\\', '\\\\')
        result = result.replace('"', '\\"')
        return result

    def generate_lua_lines(self, key: str, parts: List[str]) -> List[str]:
        """
        Генерирует строки Lua для ключа и его частей (как в parser.py).
        """
        if not parts:
            return [f'    ["{key}"] = "",']

        encoded = [self._encode_text(p) for p in parts]
        lines = []
        
        if len(encoded) == 1:
            lines.append(f'    ["{key}"] = "{encoded[0]}",')
        else:
            # Первая строка с ключом и началом кавычки
            lines.append(f'    ["{key}"] = "{encoded[0]}\\')
            # Средние строки (если есть)
            for i in range(1, len(encoded) - 1):
                lines.append(f'{encoded[i]}\\')
            # Последняя строка
            lines.append(f'{encoded[-1]}",')
            
        return lines
