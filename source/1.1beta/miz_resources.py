# -*- coding: utf-8 -*-
"""
=== МОДУЛЬ РЕСУРСОВ МИССИИ ===
Парсинг и управление ресурсами локализации из .miz файлов:
- mission: связи TransmitMessage (subtitle → audio file)
- mapResource: привязка ресурсных ключей к файлам
- В будущем: работа с картинками (ImageBriefing и др.)
"""

import re
import logging
import os
import shutil
import tempfile
import zipfile

logger = logging.getLogger(__name__)


class MizResourceManager:
    """Менеджер ресурсов миссии (.miz)
    
    Парсит файл mission и mapResource для получения привязок
    аудиофайлов к ключам словаря (DictKey_subtitle → .ogg/.wav).
    """
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Сброс всех данных"""
        # Связи из mission: DictKey_subtitle_* → ResKey_advancedFile_*
        self.subtitle_to_reskey = {}
        
        # Ключи, связанные эвристически (Stage 4)
        self.heuristic_matched_keys = set()
        
        # mapResource текущей локали: ResKey_* → filename
        self.map_resource_current = {}
        
        # mapResource из DEFAULT: ResKey_* → filename
        self.map_resource_default = {}
        
        # Файлы на замену (отложенная запись): { target_path_in_zip : source_abs_path }
        self.pending_files = {}
        
        # Измененные записи в mapResource (для сохранения при смене локали)
        self.modified_map_resources = {}
        
        # Текущая папка (для формирования путей)
        self.current_folder = "DEFAULT"
        
        # Порядок предпочтения смещений для эвристики (-1 первый по умолчанию)
        self.preferred_offset_order = [-1, 1]
        
        # Кэш данных для повторного запуска эвристики
        self._cached_mission_text = None
        self._cached_dictionary_keys = None
    
    # ─── Парсинг mission ───────────────────────────────────────────────
    
    def parse_mission_audio_links(self, miz_archive=None, dictionary_keys=None, _cached_text=None):
        """Парсит файл mission из ZIP для извлечения связей текст → аудио.
        
        В DCS правило сопоставления: все a_out_text_delay в одном триггере/команде
        разделяют один a_out_sound. То есть связь N текстов → 1 звук.
        
        Args:
            miz_archive: открытый ZIP-архив (или None при повторном запуске из кэша)
            dictionary_keys: dict ключей из dictionary (для Stage 4 эвристики)
            _cached_text: внутренний параметр для повторного запуска из кэша
        """
        self.subtitle_to_reskey = {}
        self.heuristic_matched_keys = set()  # Ключи, связанные эвристически
        
        # Получаем текст mission (из архива или из кэша)
        if _cached_text is not None:
            text = _cached_text
        elif miz_archive is not None:
            mission_path = 'mission'
            if mission_path not in miz_archive.namelist():
                return self.subtitle_to_reskey
            try:
                with miz_archive.open(mission_path, 'r') as f:
                    text = f.read().decode('utf-8')
            except Exception as e:
                logger.error(f"Ошибка чтения файла mission: {e}")
                return self.subtitle_to_reskey
        else:
            return self.subtitle_to_reskey
        
        # Кэшируем для повторного запуска
        self._cached_mission_text = text
        if dictionary_keys is not None:
            self._cached_dictionary_keys = dictionary_keys

        # Проверка: является ли ресурс аудиофайлом
        def is_audio_res(rk):
            if not rk: return False
            fname = self.map_resource_current.get(rk) or self.map_resource_default.get(rk)
            if not fname: return False
            return fname.lower().strip().endswith(('.ogg', '.wav'))

        # --- 1. TransmitMessage (стандартные радиосообщения) ---
        block_pattern = r'\["id"\]\s*=\s*"TransmitMessage".*?\["params"\]\s*=\s*\{(.*?)\},\s*--\s*end of \["params"\]'
        for block in re.findall(block_pattern, text, re.DOTALL):
            file_m = re.search(r'\["file"\]\s*=\s*"(ResKey_[^"]+)"', block)
            sub_m = re.search(r'\["subtitle"\]\s*=\s*"(DictKey_[^"]+)"', block)
            if file_m and sub_m:
                self.subtitle_to_reskey[sub_m.group(1)] = file_m.group(1)

        # --- 2. Скриптовые команды (trig.func) ---
        # Формат: [N] = "a_out_text_delay(...);a_out_sound(...);...",
        # ПРАВИЛО: ВСЕ тексты в одной строке-команде связаны с ОДНИМ звуком.
        func_pattern = r'\[\d+\]\s*=\s*"((?:[^"\\]|\\.)*)"\s*,'
        for script in re.findall(func_pattern, text):
            clean = script.replace('\\"', '"')
            # Извлекаем вызовы a_out_text_delay(getValueDictByKey("DictKey_..."))
            d_keys = re.findall(
                r'a_out_text_delay\(getValueDictByKey\("(DictKey_[^"]+)"\)', clean
            )
            # Извлекаем вызов a_out_sound(getValueResourceByKey("ResKey_..."))
            s_keys = re.findall(
                r'a_out_sound\(getValueResourceByKey\("(ResKey_[^"]+)"\)', clean
            )
            # Фильтруем только аудио
            s_keys = [rk for rk in s_keys if is_audio_res(rk)]
            
            # N текстов → 1 звук (все тексты связаны с первым звуком)
            if d_keys and s_keys:
                sound = s_keys[0]
                for dk in d_keys:
                    if dk not in self.subtitle_to_reskey:
                        self.subtitle_to_reskey[dk] = sound

        # --- 3. Структурированные блоки действий (["actions"]) ---
        # Каждый блок содержит пронумерованные действия [N] = { ["predicate"]="...", ... }
        # a_out_text_delay имеет ["text"] = "DictKey_..."
        # a_out_sound имеет ["file"] = "ResKey_..."
        # ПРАВИЛО: все тексты в блоке связаны с звуком в том же блоке.
        action_pattern = r'\["actions"\]\s*=\s*\{(.*?)\},\s*--\s*end of \["actions"\]'
        for block in re.findall(action_pattern, text, re.DOTALL):
            # Находим все пронумерованные элементы
            items = re.findall(r'\[\d+\]\s*=\s*\{(.*?)\},?\s*--\s*end of \[\d+\]', block, re.DOTALL)
            
            texts = []
            sounds = []
            for item in items:
                pred = re.search(r'\["predicate"\]\s*=\s*"([^"]+)"', item)
                if not pred:
                    continue
                if pred.group(1) == "a_out_text_delay":
                    tk = re.search(r'\["text"\]\s*=\s*"(DictKey_[^"]+)"', item)
                    if tk:
                        texts.append(tk.group(1))
                elif pred.group(1) == "a_out_sound":
                    fk = re.search(r'\["file"\]\s*=\s*"(ResKey_[^"]+)"', item)
                    if fk and is_audio_res(fk.group(1)):
                        sounds.append(fk.group(1))
            
            # N текстов → 1 звук
            if texts and sounds:
                sound = sounds[0]
                for dk in texts:
                    if dk not in self.subtitle_to_reskey:
                        self.subtitle_to_reskey[dk] = sound

        stage123_count = len(self.subtitle_to_reskey)
        logger.info(f"Stages 1-3: found {stage123_count} text->audio links")
        print(f"MizResources: Stages 1-3: found {stage123_count} text->audio links")

        # --- 4. Эвристика: сопоставление «сиротских» ResKey_Action по числовой близости ---
        # Если после стадий 1-3 остались ResKey_Action_* без привязки,
        # ищем ближайший DictKey_ActionText_* или DictKey_ActionRadioText_* по ID.
        # Приоритет отдаётся DictKey с непустым текстом (адаптивно под разные миссии).
        all_map_res = {**self.map_resource_default, **self.map_resource_current}
        
        # Собираем все ResKey_Action_*, которые указывают на аудио и ещё не привязаны
        already_linked_reskeys = set(self.subtitle_to_reskey.values())
        orphan_reskeys = {}  # {numeric_id: reskey_str}
        for rk, fname in all_map_res.items():
            if not rk.startswith('ResKey_Action_'):
                continue
            if not fname.lower().strip().endswith(('.ogg', '.wav')):
                continue
            if rk in already_linked_reskeys:
                continue
            m = re.match(r'ResKey_Action_(\d+)', rk)
            if m:
                orphan_reskeys[int(m.group(1))] = rk
        
        if orphan_reskeys:
            # Собираем доступные DictKey_ActionText_* и DictKey_ActionRadioText_*
            # dictionary_keys теперь dict {key: text_value}
            available_dictkeys = {}  # {numeric_id: (dictkey_str, has_text)}
            if dictionary_keys:
                dk_items = dictionary_keys if isinstance(dictionary_keys, dict) else {k: '' for k in dictionary_keys}
                for dk, text_val in dk_items.items():
                    m = re.match(r'(DictKey_Action(?:Text|RadioText)_)(\d+)', dk)
                    if m and dk not in self.subtitle_to_reskey:
                        available_dictkeys[int(m.group(2))] = (dk, bool(text_val.strip()))
            
            if available_dictkeys:
                for res_id, rk in sorted(orphan_reskeys.items()):
                    # Пробуем оба смещения, предпочитаем кандидата С текстом
                    candidates = []  # [(offset, dk_name, has_text)]
                    for offset in self.preferred_offset_order:
                        candidate_id = res_id + offset
                        if candidate_id in available_dictkeys:
                            dk_candidate, has_text = available_dictkeys[candidate_id]
                            if dk_candidate not in self.subtitle_to_reskey:
                                candidates.append((offset, dk_candidate, has_text))
                    
                    if not candidates:
                        continue
                    
                    # Выбираем лучшего: приоритет текстовым, затем по abs(offset)
                    best = None
                    for c in candidates:
                        if best is None:
                            best = c
                        elif c[2] and not best[2]:  # c имеет текст, best нет
                            best = c
                        elif c[2] == best[2] and abs(c[0]) < abs(best[0]):  # оба равны по тексту, ближе по смещению
                            best = c
                    
                    if best:
                        offset, best_dk, has_text = best
                        self.subtitle_to_reskey[best_dk] = rk
                        self.heuristic_matched_keys.add(best_dk)
                        text_flag = '+text' if has_text else 'empty'
                        print(f"MizResources: [Heuristic] {best_dk} <-> {rk} (offset {offset:+d}, {text_flag})")
                
                stage4_count = len(self.subtitle_to_reskey) - stage123_count
                if stage4_count > 0:
                    logger.info(f"Stage 4 (heuristic): dobavleno {stage4_count} svyazej")
                    print(f"MizResources: Stage 4 (heuristic): dobavleno {stage4_count} svyazej")

        print(f"MizResources: TOTAL {len(self.subtitle_to_reskey)} text->audio links")
        return self.subtitle_to_reskey
    
    # ─── Парсинг mapResource ───────────────────────────────────────────
    
    def parse_map_resource(self, miz_archive, folder_name):
        """Парсит файл mapResource из указанной папки локали."""
        self.map_resource_raw = ""
        path = f'l10n/{folder_name}/mapResource'
        
        # Поиск файла (регистронезависимо)
        found_path = None
        for name in miz_archive.namelist():
            if name.lower() == path.lower():
                found_path = name
                break
        
        if not found_path:
            logger.info(f"mapResource не найден для локали {folder_name}")
            return {}

        try:
            with miz_archive.open(found_path, 'r') as f:
                text = f.read().decode('utf-8')
                self.map_resource_raw = text
        except Exception as e:
            logger.error(f"Ошибка чтения mapResource {found_path}: {e}")
            return {}

        # Гибкая регулярка: поддерживает любые кавычки и пробелы
        # Формат: ["key"] = "value" или ['key'] = 'value'
        pattern = r'\[\s*(["\'])([^"\']+)\1\s*\]\s*=\s*(["\'])([^"\']+)\3'
        matches = re.findall(pattern, text)
        
        # Извлекаем второй и четвертый элементы (сами ключи и значения)
        mapping = {m[1]: m[3] for m in matches}
        
        if folder_name == 'DEFAULT':
            self.map_resource_default = mapping
        else:
            self.map_resource_current = mapping
            
        logger.info(f"mapResource [{folder_name}]: {len(mapping)} записей")
        print(f"MizResources: mapResource [{folder_name}]: {len(mapping)} записей")
        
        return mapping
    # ─── Загрузка всех данных ──────────────────────────────────────────
    
    def _extract_dictionary_keys(self, miz_archive):
        """Извлекает ключи и их текст из dictionary файла архива.
        
        Returns:
            dict: {key_name: text_value} для всех DictKey_ записей
        """
        keys_dict = {}
        for folder in ['DEFAULT']:
            dict_path = f'l10n/{folder}/dictionary'
            # Поиск файла (регистронезависимо)
            found_path = None
            for name in miz_archive.namelist():
                if name.lower() == dict_path.lower():
                    found_path = name
                    break
            if not found_path:
                continue
            try:
                raw = miz_archive.read(found_path).decode('utf-8', errors='replace')
                # Парсим ключи и определяем, есть ли у них текст
                # Формат: ["DictKey_..."] = "текст", или ["DictKey_..."] = "", (пустой)
                # Многострочные значения используют \ для переноса строк
                key_pattern = re.compile(r'\["(DictKey_[^"]+)"\]\s*=\s*"')
                for m in key_pattern.finditer(raw):
                    key = m.group(1)
                    # Проверяем что идёт после открывающей кавычки
                    rest = raw[m.end():]
                    # Пустое значение: сразу закрывающая кавычка ("",)
                    has_text = len(rest) > 0 and rest[0] != '"'
                    keys_dict[key] = 'x' if has_text else ''
            except Exception:
                pass
        return keys_dict
    
    def load_from_miz(self, miz_archive, current_folder, dictionary_keys=None):
        """Загружает все ресурсные данные из .miz архива."""
        self.reset()
        self.current_folder = current_folder
        
        # 1. СНАЧАЛА парсим mapResource (нужно для фильтрации аудио в mission)
        self.map_resource_default = self.parse_map_resource(miz_archive, "DEFAULT")
        if current_folder != "DEFAULT":
            self.map_resource_current = self.parse_map_resource(miz_archive, current_folder)
        else:
            self.map_resource_current = self.map_resource_default.copy()
        
        # Автоматически извлекаем ключи из dictionary, если не переданы
        if dictionary_keys is None:
            dictionary_keys = self._extract_dictionary_keys(miz_archive)
            
        # 2. ЗАТЕМ парсим mission для связей текст → аудио
        self.parse_mission_audio_links(miz_archive, dictionary_keys=dictionary_keys)
    
    def toggle_heuristic_offset(self):
        """Переключает порядок смещений эвристики и перезапускает анализ.
        
        Сохраняет: replaced_audio, pending_files, modified_map_resources, mapResource.
        Пересчитывает: subtitle_to_reskey, heuristic_matched_keys.
        
        Returns:
            bool: True если переключение выполнено успешно
        """
        if self._cached_mission_text is None:
            print("MizResources: toggle_heuristic_offset: no cached data")
            return False
        
        # Переключаем порядок: [1,-1] <-> [-1,1]
        self.preferred_offset_order = list(reversed(self.preferred_offset_order))
        offset_str = ", ".join(f"{o:+d}" for o in self.preferred_offset_order)
        print(f"MizResources: toggle_heuristic_offset -> [{offset_str}]")
        
        # Перезапускаем парсинг mission из кэша (не трогает mapResource, pending_files и т.д.)
        dk = self._cached_dictionary_keys
        self.parse_mission_audio_links(_cached_text=self._cached_mission_text, dictionary_keys=dk)
        
        return True
    
    def get_current_offset_label(self):
        """Возвращает текущий приоритетный offset для отображения в UI."""
        if self.preferred_offset_order:
            return self.preferred_offset_order[0]
        return 1
    
    def update_locale(self, miz_archive, new_folder, dictionary_keys=None):
        """Обновляет mapResource при смене локали."""
        self.current_folder = new_folder
        if new_folder == "DEFAULT":
            self.map_resource_current = self.map_resource_default.copy()
        else:
            self.map_resource_current = self.parse_map_resource(miz_archive, new_folder)
        
        # Автоматически извлекаем ключи из dictionary, если не переданы
        if dictionary_keys is None:
            dictionary_keys = self._extract_dictionary_keys(miz_archive)
            
        # ПЕРЕПАРСИВАЕМ AUDIO LINKS (так как map_resource_current изменился, а он важен для фильтрации)
        self.parse_mission_audio_links(miz_archive, dictionary_keys=dictionary_keys)
            
        # Применяем отложенные изменения
        if new_folder in self.modified_map_resources:
            for res_key, filename in self.modified_map_resources[new_folder].items():
                self.map_resource_current[res_key] = filename

    # ─── Получение данных для отображения ──────────────────────────────
    
    def is_heuristic_match(self, dict_key):
        """Проверяет, была ли связь ключа с аудио установлена эвристически."""
        if dict_key in self.heuristic_matched_keys:
            return True
        # Проверяем с/без префикса
        if dict_key.startswith("DictKey_"):
            return dict_key[8:] in self.heuristic_matched_keys
        return f"DictKey_{dict_key}" in self.heuristic_matched_keys
    
    def get_audio_for_key(self, dict_key):
        """Возвращает информацию об аудиофайле для данного ключа словаря."""
        # 1. Ищем прямую связь
        res_key = self.subtitle_to_reskey.get(dict_key)
        
        # 2. Если не нашли, пробуем с префиксом/без префикса DictKey_
        if not res_key:
            if dict_key.startswith("DictKey_"):
                res_key = self.subtitle_to_reskey.get(dict_key[8:])
            else:
                res_key = self.subtitle_to_reskey.get(f"DictKey_{dict_key}")
                
        if not res_key:
            return None
            
        return self.get_audio_for_res_key(res_key)

    def get_audio_for_res_key(self, res_key):
        """Возвращает информацию об аудиофайле для данного ресурсного ключа.
        
        Returns:
            tuple (filename, is_current_locale) или None
        """
        # 1. Ищем файл в mapResource текущей локали
        filename = self.map_resource_current.get(res_key)
        if filename:
            return (filename, True)
        
        # 2. Fallback: ищем в DEFAULT
        filename = self.map_resource_default.get(res_key)
        if filename:
            return (filename, False)
        
        return None

    # ─── Управление файлами ────────────────────────────────────────────

    def replace_audio(self, key, source_path):
        """Заменяет аудиофайл для указанного ключа в ТЕКУЩЕЙ локали.
        
        Args:
            key: ключ словаря (DictKey) или ресурса (ResKey)
            source_path: абсолютный путь к новому файлу на диске
            
        Returns:
            str: имя нового файла
        """
        # Если передан DictKey, ищем соответствующий ResKey
        if key.startswith("DictKey_"):
            res_key = self.subtitle_to_reskey.get(key)
            if not res_key:
                logger.warning(f"Не найден ResKey для {key}")
                return None
        else:
            res_key = key
            
        filename = os.path.basename(source_path)
        
        # 1. Обновляем mapResource текущей локали
        self.map_resource_current[res_key] = filename
        
        # 1.1 Сохраняем изменение для возможности восстановления при смене локали
        if self.current_folder not in self.modified_map_resources:
            self.modified_map_resources[self.current_folder] = {}
        self.modified_map_resources[self.current_folder][res_key] = filename
        
        # 2. Добавляем в pending_files
        # Путь внутри ZIP: l10n/<current_folder>/filename
        target_path = f"l10n/{self.current_folder}/{filename}"
        self.pending_files[target_path] = source_path
        
        logger.info(f"Замена аудио: {res_key} -> {filename} ({target_path})")
        return filename

    def is_audio_replaced(self, dict_key):
        """Проверяет, был ли аудиофайл для этого ключа заменён (ещё не сохранён)."""
        # Ищем ResKey для данного DictKey
        res_key = self.subtitle_to_reskey.get(dict_key)
        if not res_key:
            if dict_key.startswith("DictKey_"):
                res_key = self.subtitle_to_reskey.get(dict_key[8:])
            else:
                res_key = self.subtitle_to_reskey.get(f"DictKey_{dict_key}")
        if not res_key:
            return False
        
        # Проверяем, есть ли замена для этого ResKey в текущей локали
        locale_mods = self.modified_map_resources.get(self.current_folder, {})
        return res_key in locale_mods

    def clear_pending_changes(self):
        """Сбрасывает все отложенные изменения (после успешного сохранения)."""
        self.modified_map_resources.clear()
        self.pending_files.clear()

    def get_updated_map_resource_content(self, miz_archive, locale):
        """Возвращает обновленное содержимое mapResource для локали с учетом замен."""
        # 1. Получаем базу (без побочных эффектов!)
        if locale == "DEFAULT":
            map_data = self.map_resource_default.copy()
        else:
            # Читаем из архива напрямую, чтобы не перезаписывать self.map_resource_current
            map_data = {}
            path = f'l10n/{locale}/mapResource'
            found_path = None
            for name in miz_archive.namelist():
                if name.lower() == path.lower():
                    found_path = name
                    break
            if found_path:
                try:
                    with miz_archive.open(found_path, 'r') as f:
                        text = f.read().decode('utf-8')
                    pattern = r'\[\s*(["\'])([^"\']+)\1\s*\]\s*=\s*(["\'])([^"\']+)\3'
                    matches = re.findall(pattern, text)
                    map_data = {m[1]: m[3] for m in matches}
                except Exception as e:
                    logger.error(f"Ошибка чтения mapResource для {locale}: {e}")
                
        # 2. Накладываем все изменения для этой локали
        if locale in self.modified_map_resources:
            map_data.update(self.modified_map_resources[locale])
            
        # 3. Формируем Lua контент
        lines = ["mapResource =", "{"]
        for res_key, filename in sorted(map_data.items()):
            lines.append(f'    ["{res_key}"] = "{filename}",')
        lines.append("} -- end of mapResource")
        
        return "\n".join(lines)


    def extract_audio_to_temp(self, miz_path, key):
        """Извлекает аудиофайл во временную директорию для воспроизведения.
        
        Учитывает pending_files (если файл был заменен, берет его).
        
        Args:
            miz_path: путь к .miz файлу
            key: ключ словаря (DictKey) или ресурса (ResKey)
            
        Returns:
            str: путь к временному файлу или None
        """
        # 1. Определяем имя файла и локаль через унифицированный поиск
        audio_info = self.get_audio_for_key(key)
        
        # Если не нашли как DictKey, возможно это прямой ResKey
        if not audio_info:
            audio_info = self.get_audio_for_res_key(key)
            
        if not audio_info:
            logger.warning(f"extract_audio_to_temp: Не найден аудиофайл для ключа {key}")
            return None
            
        filename, is_current_locale = audio_info
        
        # Определяем папку источника
        folder = self.current_folder if is_current_locale else "DEFAULT"
        target_path_in_zip = f"l10n/{folder}/{filename}"
        
        # 2. Проверяем, есть ли этот файл в pending_files (свежая замена)
        # Важно: если мы в RU, и заменили файл, он будет в pending с путем l10n/RU/...
        # Если мы берем из DEFAULT, то путь l10n/DEFAULT/...
        
        # Проверяем точное совпадение пути
        if target_path_in_zip in self.pending_files:
            source_path = self.pending_files[target_path_in_zip]
            if os.path.exists(source_path):
                return source_path # Возвращаем оригинал с диска
        
        # 3. Извлекаем из ZIP
        try:
            import random, string
            suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"dcs_preview_{suffix}_{filename}")
            
            with zipfile.ZipFile(miz_path, 'r') as z:
                # 1. Пробуем основной путь (текущая локаль)
                actual_path = target_path_in_zip
                if actual_path not in z.namelist():
                    # 2. Если нет, пробуем без учета регистра
                    found = False
                    for name in z.namelist():
                        if name.lower() == target_path_in_zip.lower():
                            actual_path = name
                            found = True
                            break
                    
                    if not found:
                        # 3. Fallback: пробуем DEFAULT (всегда должен быть там согласно mapResource)
                        fallback_path = f"l10n/DEFAULT/{filename}"
                        if fallback_path in z.namelist():
                            actual_path = fallback_path
                            logger.info(f"Fallback to DEFAULT: {filename}")
                        else:
                            # 4. Совсем не нашли
                            logger.warning(f"Файл {filename} не найден в ZIP (ни в {target_path_in_zip}, ни в DEFAULT)")
                            return None

                with z.open(actual_path) as source, open(temp_path, 'wb') as dest:
                    shutil.copyfileobj(source, dest)
                
                return temp_path
                
        except Exception as e:
            logger.error(f"Ошибка извлечения аудио: {e}")
            return None

    def get_pending_files(self):
        """Возвращает список файлов для сохранения"""
        return self.pending_files

