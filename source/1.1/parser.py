import re
from typing import List, Tuple, Optional, Dict


class LuaDictionaryParser:
    """
    Парсер файлов dictionary.lua.
    Каждая строка файла становится отдельной строкой для редактирования.
    """

    def __init__(self):
        self.current_key = None
        self.current_raw_parts = []
        self.current_file_lines = []
        self.entries = {}
        self.total_lines_count = 0
        self.current_entry_start_line = 0

    def parse_file(self, filepath: str) -> Dict[str, Tuple[List[str], List[str], int]]:
        """
        Парсит файл dictionary.lua

        Returns:
            Словарь: ключ -> (список_строк_значения, строки_файла, start_line_index)
        """
        self.total_lines_count = 0
        self.entries = {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            self._process_line(line.rstrip('\n'))
            self.total_lines_count += 1

        if self.current_key:
            self._save_current_entry()

        return self.entries

    def _process_line(self, line: str):
        """Обрабатывает одну строку файла"""

        if self._is_ignored_line(line):
            return

        key = self._extract_key(line)
        if key:
            if self.current_key:
                self._save_current_entry()

            self.current_key = key
            self.current_raw_parts = []
            self.current_file_lines = [line]
            self.current_entry_start_line = self.total_lines_count

            value_start = self._find_value_start(line)
            if value_start == -1:
                return

            if line.endswith('\\'):
                text_part = line[value_start:-1]
                self.current_raw_parts.append(text_part)
            elif line.endswith('",'):
                text_part = line[value_start:-2]
                self.current_raw_parts.append(text_part)
                self._save_current_entry()
                self.current_key = None

        elif self.current_key:
            self.current_file_lines.append(line)

            if line.endswith('\\'):
                self.current_raw_parts.append(line[:-1])
            elif line.endswith('",'):
                self.current_raw_parts.append(line[:-2])
                self._save_current_entry()
                self.current_key = None

    def _is_ignored_line(self, line: str) -> bool:
        """Проверяет, нужно ли игнорировать строку"""
        line_stripped = line.strip()

        if not line_stripped:
            return True

        ignore_patterns = [
            'dictionary =',
            '} -- end of dictionary',
            '}',
        ]

        return any(line_stripped.startswith(patt) for patt in ignore_patterns)

    def _extract_key(self, line: str) -> Optional[str]:
        """Извлекает ключ из строки"""
        pattern = r'^[ \t]*\["([^"]+)"\][ \t]*=[ \t]*"'
        match = re.match(pattern, line)
        return match.group(1) if match else None

    def _find_value_start(self, line: str) -> int:
        """Находит позицию начала значения"""
        pos = line.find('= "')
        if pos != -1:
            return pos + 3

        pos = line.find('="')
        if pos != -1:
            return pos + 2

        return -1

    def _save_current_entry(self):
        """Сохраняет текущую запись"""
        if not self.current_key or not self.current_raw_parts:
            return

        decoded_parts = [self._decode_text(part) for part in self.current_raw_parts]

        self.entries[self.current_key] = (
            decoded_parts, 
            self.current_file_lines.copy(),
            self.current_entry_start_line
        )

        self.current_raw_parts.clear()
        self.current_file_lines.clear()

    def _decode_text(self, text: str) -> str:
        """Преобразует текст из файла для отображения"""
        result = text.replace('\\"', '"')
        result = result.replace('\\\\', '\\')
        return result

    def _encode_text(self, text: str) -> str:
        """Преобразует текст для записи в файл"""
        result = text.replace('\\', '\\\\')
        result = result.replace('"', '\\"')
        return result

    def prepare_for_editing(self) -> Dict[str, List[str]]:
        """
        Подготавливает текст для редактирования.
        Возвращает словарь: ключ -> список строк для редактирования.
        """
        editing_dict = {}

        for key, (text_parts, _, _) in self.entries.items():
            editing_dict[key] = text_parts

        return editing_dict

    def save_translations(self, filepath: str, translations: Dict[str, List[str]]):
        """
        Сохраняет переводы в файл.

        Поддерживает динамическое количество строк перевода:
        - больше чем в оригинале: дописывает дополнительные строки с \\ разделителем
        - меньше: записывает только столько строк, сколько есть в переводе
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("dictionary = \n{\n")

            for key, (_, file_lines, _) in self.entries.items():
                if key not in translations:
                    for line in file_lines:
                        f.write(line + '\n')
                    continue

                translated_parts = translations[key]
                encoded_parts = [self._encode_text(part) for part in translated_parts]
                n = len(encoded_parts)

                if n == 0:
                    # Нет перевода — пишем оригинал как есть
                    for line in file_lines:
                        f.write(line + '\n')
                    continue

                # Извлекаем prefix ключа из первой строки оригинала (["key"] = ")
                first_line = file_lines[0] if file_lines else ''
                key_prefix = ''
                if '["' in first_line and '"] = "' in first_line:
                    key_part_end = first_line.find('"] = "') + 6
                    key_prefix = first_line[:key_part_end]
                else:
                    # Фолбэк: восстанавливаем prefix вручную
                    key_prefix = f'["{key}"] = "'

                # Записываем первую строку
                f.write(key_prefix)
                f.write(encoded_parts[0])
                if n > 1:
                    f.write('\\')
                else:
                    f.write('",')
                f.write('\n')

                # Записываем средние строки
                for i in range(1, n - 1):
                    f.write(encoded_parts[i])
                    f.write('\\\n')

                # Записываем последнюю строку (если их > 1)
                if n > 1:
                    f.write(encoded_parts[n - 1])
                    f.write('",\n')

            f.write("} -- end of dictionary\n")
