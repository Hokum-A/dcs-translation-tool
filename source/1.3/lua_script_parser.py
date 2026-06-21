"""
Парсер Lua скриптов DCS миссий для извлечения и перезаписи переводимого текста.

Поддерживаемые паттерны:
  - subtitle = "текст" (включая конкатенацию с переменными через ..)
  - trigger.action.outText("текст", duration)

Автономный модуль — не зависит от основной программы.
"""

import re
import os
import zipfile
import tempfile


class LuaScriptParser:
    """Парсер Lua скриптов для извлечения переводимого текста из DCS миссий"""

    def __init__(self):
        # subtitle = <expression>,
        # Группы: (1: prefix с '='), (2: expression), (3: trailing ',')
        self._subtitle_re = re.compile(r'^(\s*subtitle\s*=\s*)(.+?)(,\s*)$')

        # trigger.action.outText(<expression>, <duration>)
        # Группы: (1: prefix с '('), (2: text expression), (3: duration), (4: ')' и далее)
        self._outtext_re = re.compile(
            r'^(.*trigger\.action\.outText\(\s*)(.+?)\s*,\s*(\d+)\s*(\).*)$'
        )

    # ──────────────────────────────────────────────
    #  Быстрое сканирование (для кнопки в UI)
    # ──────────────────────────────────────────────

    def quick_scan(self, miz_path):
        """Быстрая проверка: есть ли в .miz архиве Lua файлы с переводимым текстом.

        Returns:
            bool: True если найден хотя бы один переводимый фрагмент
        """
        try:
            with zipfile.ZipFile(miz_path, 'r') as zf:
                for info in zf.infolist():
                    name = self._fix_filename(info.filename)
                    if not name.lower().endswith('.lua'):
                        continue
                    try:
                        content = zf.read(info.filename).decode('utf-8')
                    except Exception:
                        continue
                    if self._has_translatable(content):
                        return True
        except Exception as e:
            print(f"WARNING: Lua quick_scan failed: {e}")
        return False

    # ──────────────────────────────────────────────
    #  Полное сканирование
    # ──────────────────────────────────────────────

    def scan_miz(self, miz_path):
        """Сканирует .miz архив и возвращает все Lua файлы с переводимым текстом.

        Returns:
            dict: {display_path: {'content': str, 'archive_name': str}}
                  display_path  — исправленный путь для отображения
                  archive_name  — оригинальное имя в архиве (для zipfile.read)
        """
        lua_files = {}
        try:
            with zipfile.ZipFile(miz_path, 'r') as zf:
                for info in zf.infolist():
                    display_name = self._fix_filename(info.filename)
                    if not display_name.lower().endswith('.lua'):
                        continue
                    try:
                        content = zf.read(info.filename).decode('utf-8')
                    except Exception:
                        continue
                    if self._has_translatable(content):
                        lua_files[display_name] = {
                            'content': content,
                            'archive_name': info.filename,
                        }
        except Exception as e:
            print(f"ERROR: Failed to scan miz for Lua: {e}")
        return lua_files

    # ──────────────────────────────────────────────
    #  Извлечение переводимых строк
    # ──────────────────────────────────────────────

    def extract_all(self, lua_files):
        """Извлекает все переводимые строки из набора Lua файлов.
        Присваивает глобальные маркеры 🔹N🔹.

        Args:
            lua_files: dict от scan_miz()

        Returns:
            tuple: (entries_by_file, marker_map, total_markers)
                entries_by_file — {file_path: [entry, ...]}
                marker_map      — {marker_idx: (file_path, entry_idx, seg_idx)}
                total_markers   — int
        """
        entries_by_file = {}
        marker_map = {}
        marker_counter = 0

        for file_path in sorted(lua_files.keys()):
            content = lua_files[file_path]['content']
            entries = self._extract_from_content(content)

            if not entries:
                continue

            entries_by_file[file_path] = entries

            for entry_idx, entry in enumerate(entries):
                for seg_idx, seg in enumerate(entry['segments']):
                    # Маркер присваивается только непустым текстовым фрагментам
                    if seg['type'] == 'text' and seg['value'].strip():
                        marker_counter += 1
                        seg['marker_idx'] = marker_counter
                        marker_map[marker_counter] = (file_path, entry_idx, seg_idx)

        return entries_by_file, marker_map, marker_counter

    # ──────────────────────────────────────────────
    #  Формирование текста для отображения/копирования
    # ──────────────────────────────────────────────

    def build_display_text(self, entries_by_file):
        """Формирует текст для левой панели с маркерами 🔹N🔹.

        Returns:
            str: текст для QPlainTextEdit с маркерами
        """
        lines = []
        for file_path in sorted(entries_by_file.keys()):
            for entry in entries_by_file[file_path]:
                for seg in entry['segments']:
                    marker = seg.get('marker_idx')
                    if marker is not None:
                        lines.append(f'🔹{marker}🔹 {seg["value"]}')

        return '\n'.join(lines)

    # ──────────────────────────────────────────────
    #  Перезапись .miz архива
    # ──────────────────────────────────────────────

    def rewrite_miz(self, miz_path, translations, entries_by_file, lua_files):
        """Перезаписывает .miz архив с переведёнными Lua файлами.

        Args:
            miz_path:        путь к .miz файлу
            translations:    {marker_idx: translated_text}
            entries_by_file: данные от extract_all()
            lua_files:       данные от scan_miz()

        Returns:
            tuple: (files_modified, strings_replaced) — статистика
        """
        # 1. Собираем модифицированный контент для каждого Lua файла
        modified_files = {}  # archive_name -> new_content_bytes
        files_modified = 0
        strings_replaced = 0

        for file_path, entries in entries_by_file.items():
            content = lua_files[file_path]['content']
            archive_name = lua_files[file_path]['archive_name']

            new_content, replaced = self._rebuild_lua(content, entries, translations)

            if replaced > 0:
                modified_files[archive_name] = new_content.encode('utf-8')
                files_modified += 1
                strings_replaced += replaced

        if not modified_files:
            return 0, 0

        # 2. Перезаписываем .miz (atomic: temp + rename)
        temp_miz = miz_path + '.lua_tmp'
        try:
            with zipfile.ZipFile(miz_path, 'r') as zin:
                with zipfile.ZipFile(temp_miz, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        if item.filename in modified_files:
                            # Заменяем модифицированный Lua файл
                            # Сохраняем метаданные оригинального файла
                            new_info = item
                            try:
                                fixed = item.filename.encode('cp437').decode('utf-8')
                                new_info.filename = fixed
                                new_info.flag_bits |= 0x800  # UTF-8 flag
                            except (UnicodeEncodeError, UnicodeDecodeError):
                                pass
                            zout.writestr(new_info, modified_files[item.filename])
                        else:
                            # Копируем без изменений
                            original_name = item.filename
                            try:
                                fixed = item.filename.encode('cp437').decode('utf-8')
                                item.filename = fixed
                                item.flag_bits |= 0x800
                            except (UnicodeEncodeError, UnicodeDecodeError):
                                pass
                            zout.writestr(item, zin.read(original_name))

            # Atomic replace
            os.replace(temp_miz, miz_path)
            print(f"✅ Lua rewrite: {files_modified} files, {strings_replaced} strings")

        except Exception as e:
            # Cleanup temp file on error
            if os.path.exists(temp_miz):
                try:
                    os.remove(temp_miz)
                except Exception:
                    pass
            raise e

        return files_modified, strings_replaced

    # ──────────────────────────────────────────────
    #  ВНУТРЕННИЕ МЕТОДЫ
    # ──────────────────────────────────────────────

    def _fix_filename(self, name):
        """Исправляет кодировку имени файла из архива (CP437 → UTF-8)."""
        try:
            return name.encode('cp437').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return name

    def _has_translatable(self, content):
        """Быстрая проверка: есть ли в содержимом переводимые паттерны."""
        for raw_line in content.split('\n'):
            line = raw_line.rstrip('\r\n')
            # Пропускаем комментарии
            stripped = line.lstrip()
            if stripped.startswith('--'):
                continue
            if self._subtitle_re.search(line):
                # Дополнительно проверяем что есть непустой текст
                m = self._subtitle_re.search(line)
                expr = m.group(2)
                segments = self._parse_expression(expr)
                if any(s['type'] == 'text' and s['value'].strip() for s in segments):
                    return True
            if self._outtext_re.search(line):
                m = self._outtext_re.search(line)
                expr = m.group(2)
                segments = self._parse_expression(expr)
                if any(s['type'] == 'text' and s['value'].strip() for s in segments):
                    return True
        return False

    def _extract_from_content(self, content):
        """Извлекает все переводимые записи из содержимого одного Lua файла.

        Returns:
            list: [entry, ...] где каждый entry — словарь:
                {
                    'line_num': int (0-indexed),
                    'pattern': 'subtitle' | 'outText',
                    'segments': [{'type': 'text'|'var', 'value': str, 'marker_idx': int|None}],
                    'original_line': str,
                }
        """
        entries = []
        lines = content.split('\n')

        for i, raw_line in enumerate(lines):
            line = raw_line.rstrip('\r\n')

            # Пропускаем комментарии
            stripped = line.lstrip()
            if stripped.startswith('--'):
                continue

            entry = None

            # Проверяем subtitle
            m_sub = self._subtitle_re.search(line)
            if m_sub:
                expr = m_sub.group(2)
                segments = self._parse_expression(expr)
                # Проверяем наличие непустого текста
                if any(s['type'] == 'text' and s['value'].strip() for s in segments):
                    entry = {
                        'line_num': i,
                        'pattern': 'subtitle',
                        'segments': segments,
                        'original_line': line,
                    }

            # Проверяем outText (только если subtitle не найден на этой строке)
            if not entry:
                m_out = self._outtext_re.search(line)
                if m_out:
                    expr = m_out.group(2)
                    segments = self._parse_expression(expr)
                    if any(s['type'] == 'text' and s['value'].strip() for s in segments):
                        entry = {
                            'line_num': i,
                            'pattern': 'outText',
                            'segments': segments,
                            'original_line': line,
                        }

            if entry:
                entries.append(entry)

        return entries

    def _parse_expression(self, expr):
        """Парсит Lua выражение в список сегментов (текст и переменные).

        Корректно обрабатывает:
        - Строковые литералы в двойных кавычках
        - Конкатенацию через .. (только вне строк)
        - Escape-последовательности внутри строк

        Args:
            expr: строка Lua выражения (например: '"Strike: ".. flightBoardNumber ..", copies."')

        Returns:
            list: [{'type': 'text'|'var', 'value': str}, ...]
        """
        parts = self._split_by_concat(expr.strip())
        segments = []

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if part.startswith('"') and part.endswith('"') and len(part) >= 2:
                # Строковый литерал — извлекаем содержимое между кавычками
                text = part[1:-1]
                segments.append({'type': 'text', 'value': text})
            else:
                # Переменная или выражение
                segments.append({'type': 'var', 'value': part})

        return segments

    def _split_by_concat(self, expr):
        """Разбивает Lua выражение по оператору конкатенации (..)
        с учётом строковых литералов (не разбивает .. внутри кавычек).

        Args:
            expr: строка выражения

        Returns:
            list[str]: части выражения
        """
        parts = []
        current = []
        in_string = False
        i = 0

        while i < len(expr):
            c = expr[i]

            # Обработка escape-последовательности внутри строки
            if in_string and c == '\\':
                current.append(c)
                if i + 1 < len(expr):
                    current.append(expr[i + 1])
                    i += 2
                else:
                    i += 1
                continue

            # Переключение состояния строки
            if c == '"':
                in_string = not in_string
                current.append(c)
                i += 1
                continue

            # Оператор конкатенации вне строки
            if not in_string and c == '.' and i + 1 < len(expr) and expr[i + 1] == '.':
                # Проверяем что это не ... (varargs) — три точки
                if i + 2 < len(expr) and expr[i + 2] == '.':
                    # Это ..., оставляем как часть текущего токена
                    current.append(c)
                    i += 1
                    continue
                # Это .. (конкатенация) — сохраняем текущую часть
                part = ''.join(current).strip()
                if part:
                    parts.append(part)
                current = []
                i += 2  # Пропускаем обе точки
                continue

            current.append(c)
            i += 1

        # Последняя часть
        part = ''.join(current).strip()
        if part:
            parts.append(part)

        return parts

    def _rebuild_lua(self, content, entries, translations):
        """Подставляет переводы обратно в содержимое Lua файла.

        Args:
            content:      оригинальное содержимое .lua файла
            entries:      список entry от _extract_from_content (с marker_idx)
            translations: {marker_idx: translated_text}

        Returns:
            tuple: (new_content, replaced_count)
        """
        lines = content.split('\n')
        replaced = 0

        for entry in entries:
            line_num = entry['line_num']
            original_line = lines[line_num].rstrip('\r\n')
            # Проверяем сохранился ли \r в конце (для корректного восстановления)
            has_cr = lines[line_num].endswith('\r\n') or lines[line_num].endswith('\r')

            # Проверяем, есть ли хотя бы один перевод для этой записи
            entry_has_translation = False
            for seg in entry['segments']:
                marker = seg.get('marker_idx')
                if marker and marker in translations:
                    entry_has_translation = True
                    break

            if not entry_has_translation:
                continue

            # Собираем новое выражение из сегментов
            new_expr = self._build_expression(entry['segments'], translations)

            # Заменяем выражение в строке через regex
            if entry['pattern'] == 'subtitle':
                new_line = self._subtitle_re.sub(
                    lambda m: m.group(1) + new_expr + m.group(3),
                    original_line
                )
            elif entry['pattern'] == 'outText':
                new_line = self._outtext_re.sub(
                    lambda m: m.group(1) + new_expr + ', ' + m.group(3) + m.group(4),
                    original_line
                )
            else:
                continue

            if new_line != original_line:
                # Восстанавливаем окончание строки
                if has_cr:
                    lines[line_num] = new_line + '\r'
                else:
                    lines[line_num] = new_line
                replaced += 1

        new_content = '\n'.join(lines)
        return new_content, replaced

    def _build_expression(self, segments, translations):
        """Собирает Lua выражение из сегментов с применёнными переводами.

        Args:
            segments:     список сегментов entry
            translations: {marker_idx: translated_text}

        Returns:
            str: Lua выражение (например: '"Страйк: " .. flightBoardNumber .. ", копирует."')
        """
        parts = []

        for seg in segments:
            if seg['type'] == 'var':
                parts.append(seg['value'])
            elif seg['type'] == 'text':
                marker = seg.get('marker_idx')
                if marker and marker in translations:
                    text = self._escape_lua_string(translations[marker])
                else:
                    text = seg['value']
                parts.append(f'"{text}"')

        return ' .. '.join(parts)

    def _escape_lua_string(self, text):
        """Экранирует специальные символы для Lua строкового литерала.
        Не экранирует то, что уже экранировано (двойное экранирование).
        """
        # Заменяем только неэкранированные кавычки
        result = []
        i = 0
        while i < len(text):
            c = text[i]
            if c == '\\' and i + 1 < len(text):
                # Уже экранированный символ — оставляем как есть
                result.append(c)
                result.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                result.append('\\"')
                i += 1
                continue
            result.append(c)
            i += 1
        return ''.join(result)
