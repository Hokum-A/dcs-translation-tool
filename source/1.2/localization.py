"""
Система локализации для DCS Translation TOOL
Словарь переводов для русского и английского языков
"""

# [LOCALIZATION]
TRANSLATIONS = {
    'ru': {
        # Основные элементы интерфейса
        'window_title': 'DCS Translation TOOL v{version}',
        'status_ready': 'Готово. Откройте файл для начала работы',
        'status_file_saved': 'DONE. File saved: {filename}',
        'status_translation_cleared': 'DONE. All translation cleared',
        'status_copied_lines': 'DONE. Copied {count} lines',
        'status_pasted': 'DONE. Text pasted from clipboard',
        'status_default_filters': 'DONE. Default filters set',
        'status_replace_success': 'DONE. Replaced {count} occurrences',
        
        # Кнопки и меню
        'open_file_btn': '📂 Открыть файл (dictionary .txt .cmp)',
        'open_miz_btn': '📂 Открыть файл миссии (.miz)',
        'open_unified_btn': '📂 Открыть (.miz, .cmp, dictionary)',
        'open_miz_menu_item': '📂 Открыть файл миссии (.miz)',
        'open_dict_menu_item': '📄 Открыть файл (dictionary, .txt, .cmp)',
        'recent_files_label': 'Недавние файлы',
        'clear_recent_btn': 'Очистить историю',
        'no_recent_files': 'Нет недавних файлов',
        'open_new_instance_btn': 'Открыть новый экземпляр программы',
        'save_file_btn': '💾 Сохранить перевод…',
        'copy_all_btn': '📋 Копировать весь текст',
        'show_keys_btn': '🔑 Показать/скрыть ключи',
        'paste_btn': '📋 Вставить из буфера',
        'clear_btn': '🗑️ Очистить перевод',
        'default_filters_btn': 'Фильтры по умолчанию',
        'view_log_btn': '📋 Просмотреть лог ошибок',
            'settings_btn': 'Настройки',
            'settings_window_title': 'Настройки',
            'theme_bg_even_label': 'Цвет фона строк 1 (нечетные)',
            'theme_bg_odd_label': 'Цвет фона строк 2 (четные)',
            'theme_text_modified_label': 'Цвет изменённого текста',
            'theme_text_saved_label': 'Цвет исходного текста',
            'theme_text_session_label': 'Цвет изменённого и сохранённого текста в текущей сессии',
            'highlight_empty_label': 'Подсветка полей ввода',
            'highlight_color_label': 'Цвет подсветки',
            'enable_logs_label': 'Включить логи',
            'preview_font_family_label': 'Шрифт текста нижнего окна',
            'preview_font_size_label': 'Размер шрифта',
            'reference_locale_label': 'Референс-локаль',
            'settings_skip_locale_dialog': 'Пропускать окно выбора локали',
            'settings_default_open_locale': 'Установить локаль по умолчанию при открытии файла:',
            'settings_multi_window_mode': 'Многооконный режим',
            'case_sensitive_search': 'Учитывать регистр',
            'settings_smart_paste_enabled': 'Умная вставка с маркерами (Smart Paste AI)',
            'tab_instruction': 'Инструкция по переводу',
            'tab_user_manual': 'Руководство пользователя',
            'tooltip_smart_paste': 'При использовании кнопки "Копировать весь текст" к строкам\nавтоматически добавляются маркеры 🔹N🔹. При вставке программа\nраспознаёт их и точечно подставляет перевод в нужные строки.\nЕсли опция выключена — текст копируется и вставляется без маркеров.',
            'bookmark_colors_label': 'Цвет фона закладок:',
            'bookmark_opacity_label': 'Прозрачность:',
        
        # Заголовки групп
        'filters_group': 'Фильтры ключей для перевода:',
        'preview_group': 'Предварительный просмотр перевода:',
        # Заголовки внутри панели предпросмотра
        'preview_header_meta': 'Метаданные',
        'preview_header_ref': 'Референсный текст:',
        'preview_header_editor': 'Редактор перевода: {locale}',
        
        # Метки
        'original_text_label': 'Оригинальный текст:',
        'translation_label': 'Перевод:',
        'additional_keys_label': 'Дополнительные ключи:',
        'skip_empty_label': 'Пропускать пустые строки',
        'skip_empty_keys_label': 'Пропускать пустые ключи',
        'show_audio_keys_label': 'Показывать ключи с аудио',
        'preview_no_keys_match': 'Нет ключей соответствующих фильтрам',
        'preview_info': 'Показано {count} строк',
        'stats_label': 'Строк для перевода: {count}',
        'english_count': '{count} строк',
        'russian_count': '{filled}/{total} заполнено',
        'custom_filter_placeholder': 'Ключ {index}',
        
        # Стандартные фильтры
        'filter_action_text': 'ActionText',
        'filter_action_radio': 'ActionRadioText',
        'filter_description': 'description',
        'filter_subtitle': 'subtitle',
        'filter_sortie': 'sortie',
        'filter_name': 'name',
        
        # Диалоги сохранения
        'save_dialog_title': 'Сохранение миссии .miz',
        'save_dialog_info': 'Выберите способ сохранения переведенной миссии:',
        'overwrite_btn': '💾 Перезаписать файл…',
        'overwrite_cmp_btn': '💾 Перезаписать файл',
        'miz_backup_label': 'Создать резервную копию',
        'save_as_btn': '💾 Сохранить как…',
        'save_btn': '💾 Сохранить',
        'save_txt_separately_btn': '💾 Сохранить отдельно в .txt…',
        'cancel_btn': 'Отмена',
        'close_btn': 'Закрыть',
        'open_btn': 'Открыть',
        
        # Сообщения об ошибках
        'error_title': 'Ошибка',
        'success_title': 'Успех',
        'file_not_found': 'Файл не найден',
        'file_read_error': 'Ошибка чтения файла',
        'file_save_error': 'Ошибка сохранения файла',
        'miz_error': 'Ошибка работы с файлом миссии',
        'error_miz_save': 'Ошибка при сохранении .miz файла: {error}',
        'error_truncated_header': 'Ошибка при сохранении: усечён заголовок ZIP-архива. Возможно, файл повреждён или занят другим приложением.',
        'error_no_lines_found': 'Не найдено строк для перевода по выбранным фильтрам',
        'error_no_lines_found_miz': 'Не найдено строк для перевода по выбранным фильтрам в файле dictionary',
        'key_not_found_msg': 'Ключ "{key_name}" не найден в данном файле',
        'key_hidden_by_filters_msg': 'Ключ "{key_name}" скрыт текущими фильтрами',
        'miz_select_folder_title': 'Выберите папку с локализацией',
        'miz_select_folder_desc': '(Если не уверены, выберите DEFAULT)',
        'miz_save_folder_title': 'Выберите язык вашего перевода',
        'miz_save_folder_desc': '(Если не уверены, выберите "DEFAULT")',
        'localization_label': 'локализация:',
        'show_all_keys_label': 'Показывать все ключи',
        'btn_radio': 'Плеер',
        'btn_files': 'Файлы',
        'btn_briefing': 'Брифинг',
        'files_window_title': 'Менеджер файлов',
        'files_window_placeholder': 'Файловый менеджер (в разработке)',

        # Менеджер файлов
        'fm_col_number': '#',
        'fm_col_type': 'Тип',
        'fm_col_filename': 'Имя файла',
        'fm_col_description': 'Описание',
        'fm_col_status': 'Статус',
        'fm_col_info': 'Инфо',
        'fm_col_link': '🔗',
        'fm_col_actions': 'Действия',
        'fm_col_gen_duration': 'Ген. длит.',
        'fm_col_orig_duration': 'Ориг. длит.',
        'fm_filter_audio': '♫ Аудио',
        'fm_filter_images': '🖼 Изображения',
        'fm_filter_kneeboard': '📋 Планшет',
        'fm_search_placeholder': 'Поиск по имени файла...',
        'fm_preview_placeholder': 'Выберите файл для предпросмотра',
        'fm_desc_briefing_blue': 'Брифинг Синих',
        'fm_desc_briefing_red': 'Брифинг Красных',
        'fm_desc_briefing_neutral': 'Брифинг Нейтралов',
        'fm_desc_trigger': 'Триггер',
        'fm_desc_kneeboard': 'Планшет (KNEEBOARD)',
        'fm_desc_audio_linked': 'Радиосообщение',
        'fm_desc_audio_trigger': 'Триггер (аудио)',
        'fm_no_files': 'Нет файлов для отображения',
        'fm_status_in_locale': 'Файл расположен в текущей папке локализации',
        'fm_status_default_only': 'Файл расположен в папке "DEFAULT"',
        'fm_status_replaced': 'Ожидает сохранения',
        'fm_tooltip_play': 'Воспроизвести',
        'fm_tooltip_stop': 'Остановить',
        'fm_tooltip_view': 'Просмотреть изображение',
        'fm_tooltip_replace': 'Заменить файл',
        'fm_tooltip_download': 'Сохранить на диск',
        'fm_tooltip_has_link': 'Привязка аудиофайла к тексту',
        'tts_install_success_title': 'TTS',
        'tts_install_success_msg': 'Piper успешно установлен! Теперь вы можете генерировать озвучку.',
        'tts_install_error_title': 'TTS',
        'tts_install_error_msg': 'Ошибка при загрузке компонентов.\nПроверьте подключение к интернету и попробуйте снова.',
        'tts_init_error_title': 'Ошибка',
        'tts_init_error_msg': 'Ошибка инициализации TTS: {error}',
        'tts_general_error_title': 'Ошибка',
        'tts_general_error_msg': 'Ошибка TTS: {error}',
        'logs_cleared': '✓ Логи очищены ({count} файлов)',
        'logs_no_files': '✓ Нет файлов логов для очистки',
        'fm_btn_batch_export': '🡇 Сохранить выбранное',
        'fm_btn_batch_replace': '⟲ Заменить выбранное',
        'fm_menu_rename': 'Переименовать',
        'fm_menu_show_in_editor': 'Показать в редакторе',
        'fm_replace_suffix_title': 'Префикс и суффикс замены',
        'fm_replace_suffix_label': 'Суффикс (будет ПОСЛЕ имени):',
        'fm_br_prefix_label': 'Префикс (будет ПЕРЕД именем):',
        'fm_batch_replace_success': 'Успешно заменено {count} из {total} файлов{path}',
        'fm_shift_selection_hint': '💡 Зажмите Shift для выделения диапазона',
        'fm_status_shown': 'Отображено: {current} из {total}',
        'fm_status_selected': 'Выбрано: {count} ({size})',
        'fm_btn_select_all': 'Выбрать все',
        'fm_btn_select_none': 'Снять выделение',
        'fm_btn_select_invert': 'Инвертировать',
        'fm_audio_no_file': 'Файл не выбран',
        'img_prev_export': '🡇 Экспорт',
        'img_prev_replace': '⟲ Заменить',
        'fm_batch_replace_zero': 'Не найдено подходящих файлов для замены из {total} выбранных{path}',
        'fm_export_success': 'Файлы успешно экспортированы в папку:{path}',
        'fm_export_zero': 'Не удалось экспортировать ни одного файла из выбранных',
        'fm_br_desc_suffix': '<b>Поиск по префиксу и суффиксу:</b> Программа будет искать файлы в папке по правилу: <i>Префикс + ИмяФайла + Суффикс</i>. Например, "new_" + "music.ogg" + "_old" → "new_music_old.ogg". Оставьте поля пустыми, если они не нужны.',
        'fm_br_desc_prefix_suffix': '<b>Поиск по префиксу и суффиксу:</b> Программа будет искать файлы в папке по правилу: <i>Префикс + ИмяФайла + Суффикс</i>. Например, "new_" + "music.ogg" + "_old" → "new_music_old.ogg". Оставьте поля пустыми, если они не нужны.',
        'fm_br_desc_single': '<b>Один файл для всех:</b> Все выбранные ресурсы будут заменены одним и тем же файлом. Удобно для замены заглушек.',
        'fm_br_mode_suffix': 'По преф. / суф.',
        'fm_br_mode_single': 'Один файл для всех',
        'fm_br_desc_drop': '<b>Пакетное сопоставление файлов:</b> Программа будет искать соответствия именам ресурсов миссии среди перетащенных файлов (<b>{count} шт.</b>).<br/><br/>Используйте префиксы/суффиксы, если имена файлов в Windows отличаются от имен в миссии.',
        'fm_br_btn_apply': 'Применить',
        'fm_br_btn_cancel': 'Отмена',
        'fm_br_select_file': 'Выберите файл для замены',
        'fm_br_title_window': 'Пакетная замена ресурсов',
        'fm_br_title': 'Пакетная замена ресурсов',
        
        # Type Mismatch Dialog
        'type_mismatch_title': 'Внимание: Несовпадение форматов!',
        'type_mismatch_desc': 'Вы пытаетесь заменить {orig_cat} ({orig_ext}) на {new_cat} ({new_ext}).\n\nВстроенная логика игры может не распознать новый формат, и файл не будет работать в миссии.\n\nВы уверены, что хотите продолжить?',
        'continue_btn': 'Продолжить',
        'briefing_window_title': 'Брифинг',
        'briefing_window_placeholder': 'Брифинг (в разработке)',
        'miz_executing': 'Выполняется',
        'no_reference_marker': '[НЕТ В РЕФЕРЕНСЕ] ',
        'no_translation_marker': '[НЕТ В ПЕРЕВОДЕ, ДОБАВИТЬ?]',
        'briefing_mission_name_label': 'Название миссии:',
        'briefing_tab_description': 'Описание миссии:',
        'briefing_tab_red_task': 'Задача для красных:',
        'briefing_tab_blue_task': 'Задача для синих:',
        'briefing_tab_neutrals_task': 'Задача для нейтральных:',

        # Закладки
        'bookmark_set_star': '★ Установить звезду',
        'bookmark_set_question': '? Установить вопрос',
        'bookmark_set_alert': '! Установить важное',
        'bookmark_comment': '💬 Комментарий...',
        'bookmark_comment_title': 'Комментарий к закладке',
        'bookmark_clear_all': '🗑 Очистить все закладки',
        'bookmark_clear_all_confirm': 'Удалить все закладки и комментарии для текущей миссии?',
        'delete_comment_tooltip': 'Удалить комментарий',

        
        # Аудиоплеер
        'audio_player_title': 'Аудиопроигрыватель',
        'playlist_total_duration': 'Общее время: {duration}',
        'replace_audio_btn': 'Заменить аудиофайл',
        'audio_file_label': 'Файл:',
        'play_btn': 'Play',
        'pause_btn': 'Pause',
        'stop_btn': 'Stop',
        'file_from_default': 'Используется файл из DEFAULT',
        'volume_label': 'Громкость',
        'error_audio_file': 'Файл не найден',
        'select_new_audio_title': 'Выберите аудиофайл',
        'audio_file_filter': 'Аудиофайлы (*.ogg *.wav);;Все файлы (*)',
        'audio_replaced_success': 'Аудиофайл успешно заменен',
        'heuristic_audio_warning': 'ВНИМАНИЕ! Аудио файл сопоставлен с текущим ключем\nметодом эвристического анализа. На работу миссии не повлияет.',
        'heuristic_toggle_btn': 'Смещение эвристического анализа: {offset}',
        'no_audio_file': 'Файл не выбран',
        'error_utf8_read': 'Невозможно прочитать файл в кодировке UTF-8.',
        'error_utf8_convert': 'Попробуйте преобразовать файл в UTF-8.',
        'error_bad_zip': 'Файл {filename} не является корректным ZIP-архивом или поврежден',
        'error_details': 'Детали: {details}',
        'error_title_encoding': 'Ошибка кодировки',
        
        # Диалог очистки
        'clear_dialog_title': 'Очистка перевода',
        'clear_question': 'Вы уверены, что хотите очистить весь перевод?',
        'yes_btn': 'ДА',
        'no_btn': 'НЕТ',
        
        # Отчеты сохранения
        'save_report_title': '✅ Файл сохранен',
        'save_stats': '📊 Статистика:',
        'total_lines': '• Всего ключей в файле: {count}',
        'translatable_lines': '• Строк для перевода: {count}',
        'translated_lines': '• Переведено строк: {count}',
        'remaining_lines': '• Осталось перевести: {count}',
        'tts_downloading_msg': 'Загрузка Piper TTS и голосов (~85 МБ)...',
        'tts_status_dl_python': '📥 Скачивание Python 3.11 (~15 МБ)...',
        'tts_status_unpack_python': '📦 Распаковка Python...',
        'tts_status_install_pip': '📥 Установка pip...',
        'tts_status_pip_fix': '🔧 pip не работает, переустановка...',
        'tts_status_check_pip': '🔍 Проверка pip...',
        'tts_status_install_numpy': '📦 Установка инструментов сборки и numpy (1/3)...',
        'tts_status_install_xtts_libs': '📦 Установка XTTS и библиотек (2/3)...',
        'tts_status_install_torch': '📦 Установка Torch GPU (3/3) (около 3 ГБ)...',
        'tts_status_install_success': '✅ Установка успешно завершена!',
        'tts_status_unpack_piper': '📦 Распаковка Piper...',
        'tts_status_dl_piper_core': '📥 Скачивание ядра Piper...',
        'tts_status_piper_install_done': '✅ Установка Piper завершена!',
        'tts_status_dl_model_file': '📥 Скачивание {f_name}...',
        'tts_status_model_loaded': '✅ Модель загружена!',
        'tts_err_dl_python': '❌ Не удалось скачать Python.',
        'tts_err_pip_install': '❌ Ошибка установки pip: {error}',
        'tts_err_pip_fix': '❌ Не удалось восстановить pip. Удалите .python и попробуйте снова.',
        'tts_err_install_tools': '❌ Ошибка при установке инструментов сборки. См. install_log.txt.',
        'tts_err_install_xtts_libs': '❌ Ошибка при установке TTS. См. install_log.txt.',
        'tts_err_install_torch': '❌ Ошибка установки Torch. См. install_log.txt.',
        'tts_err_dl_piper': '❌ Ошибка при скачивании Piper.',
        'tts_err_piper_zip': '❌ Скачанный файл поврежден (не ZIP).',
        'tts_err_generic': '❌ Ошибка: {error}',
        'tts_status_dl_progress': '{label}: {current} МБ / {total} МБ',
        'tts_status_python_ready': '✅ Python 3.11 готов!',
        'tts_err_pip_not_working': '❌ pip установлен, но не работает. Попробуйте удалить .python и повторить.',
        'tts_err_model_load': '❌ Ошибка загрузки модели!',
        'tts_log_start_install': 'Начало чистой установки XTTS и зависимостей...',
        'tts_log_vpn_hint': 'ВАЖНО: Если установка прерывается (10054), попробуйте включить VPN.',
        'tts_log_portable_python_failed': 'ОШИБКА: _ensure_portable_python вернул None',
        'tts_log_portable_python_ready': 'Портативный Python готов: {python_exe}',
        'tts_log_pip_not_working': 'pip не работает! Попытка исправления...',
        'tts_log_pip_reinstall_failed': 'ОШИБКА: не удалось переустановить pip',
        'tts_log_pip_reinstalled_not_working': 'ОШИБКА: pip переустановлен, но всё равно не работает',
        'tts_log_pip_fixed': 'pip успешно исправлен!',
        'tts_log_pip_ok': 'pip работает нормально',
        'tts_log_install_foundation': 'Шаг 1: Установка инструментов сборки и numpy...',
        'tts_log_install_foundation_failed': 'ОШИБКА: Шаг 1 (основа) не удался.',
        'tts_log_install_xtts_libs': 'Шаг 2: Установка XTTS и базовых библиотек...',
        'tts_log_install_xtts_libs_failed': 'ОШИБКА: Шаг 2 (XTTS и библиотеки) не удался.',
        'tts_log_install_torch': 'Шаг 3: Установка Torch с поддержкой GPU (CUDA 12.1)...',
        'tts_status_install_torch_gpu': '📦 Установка Torch GPU (3/3) (около 3 ГБ)...',
        'tts_log_install_torch_failed': 'ОШИБКА: Шаг 3 (Torch) не удался.',
        'tts_log_install_success': 'Установка успешно завершена!',
        
        # Удаление локалей
        'delete_locale_btn': 'Удалить',
        'delete_confirm_title': 'Удаление локали',
        'delete_confirm_msg': 'Вы уверены, что хотите удалить {locale}?',
        'backup_created': '🔄 Создана резервная копия:',
        'file_saved_to': '📁 Файл сохранен в:',
        'slash_warning': '⚠ Предупреждение: {count} строк потеряли завершающий слеш',
        'replacements_done': '🔧 Отладка:',
        'replacements_count': '• Выполнено замен: {done}',
        'replacements_expected': '• Ожидалось замен: {expected}',
        'failed_replacements': '⚠ ВНИМАНИЕ:\nНе удалось заменить {count} строк.',
        'file_save_success': 'Файл успешно сохранен:\n{filename}',
        'miz_overwrite_success': 'Файл миссии успешно перезаписан:\n{filename}',
        'miz_save_as_success': 'Миссия успешно сохранена:\n{filename}',
        
        # Тултипы и подсказки
        'tooltip_drag': 'Окно программы перетаскивается левой или правой кнопкой мыши, на любом месте экрана',
        'tooltip_open_file': 'Открыть текстовый файл словаря (.txt или .lua)',
        'tooltip_open_miz': 'Открыть файл миссии (.miz) для перевода',
        'tooltip_save_file': 'Сохранить текущий перевод в файл',
        'tooltip_instructions': 'Показать подробную инструкцию по работе с программой',
        'tooltip_ai_context': 'Управление контекстом для ИИ-переводчика',
        'tooltip_copy_all': 'Скопировать весь английский текст в буфер обмена',
        'tooltip_show_keys': 'Показать или скрыть ключи словаря',
        'tooltip_paste': 'Вставить текст из буфера обмена',
        'tooltip_clear': 'Очистить весь переведенный текст',
        'tooltip_default_filters': 'Установить фильтры по умолчанию',
        'tooltip_view_log': 'Просмотреть лог ошибок',
        'tooltip_warning_slash': 'Количество знаков \\ слеш не совпадает с переводом. Можно игнорировать.',
        'tooltip_about_program': 'Информация о программе',
        'tooltip_add_context': 'Добавляет контекст в начало перевода для ИИ переводчика',
        'tooltip_default_context': 'Контекст по умолчанию',
        'tooltip_multi_window_mode': 'Включите, чтобы разрешить открытие нескольких окон программы одновременно. Если выключено — новые файлы будут открываться в текущем окне.',
        'audio_replace_help_tooltip': 'Альтернативный способ замены: перетащите файл из проводника на имя текущего аудиофайла в главном окне.',
        'about_title': 'Информация о программе',
        'about_text': 'DCS Translation TOOL v{version}\n\nИнструмент для перевода текста в миссиях DCS World.\nРаботает с файлами dictionary и архивами .miz.\nБесплатен и будет оставаться таким.\n\nИсходный код и обратная связь:\nGitHub: https://github.com/Hokum-A/dcs-translation-tool\n\nПоддержать проект:\nBoosty: https://boosty.to/hokuma\nUSDT TRC20: TKLcwmrNmwXFgwbpS66UnAGsB3Lvnqpwv5\n\nРазработчик: Hokum (Андрей Варламов)\nЛицензия: MIT License\n\nСпасибо, что используете этот инструмент.',
        'exit_btn': 'Назад',
        'ok_btn': 'ОК',
        'tts_loading_msg': 'Подготовка генерации голоса...',
        'tts_btn': 'Озвучить',
        
        # Дополнительные элементы интерфейса
        'skip_empty_label': 'Пропускать пустые строки',
        'additional_keys_label': 'Дополнительные ключи:',
        'original_text_label': 'Оригинальный текст:',
        'translation_label': 'Перевод:',
        'not_translated': '[не переведено]',
        'preview_info': 'Загружено {count} блоков',
        'preview_info_progress': 'Загружено {current} из {total} блоков',
        'stats_lines': 'Строк для перевода: {count}',
        'stats_to_translate': 'Строк для перевода: {count}',
        'stats_translated': 'Переведено: {count}',
        'stats_not_translated': 'Не переведено: {count}',
        'english_count_label': '{count} строк',
        'russian_count_label': '{filled}/{total} заполнено',
        
        # Поиск
        'search_label': 'Найти:',
        'search_placeholder': 'Текст...',
        'replace_placeholder': 'Текст...',
        'search_matches': 'Совпадений: {count}',
        'replace_label': 'Заменить на:',
        'replace_btn': 'Заменить',
        'replace_all_btn': 'Заменить всё',
        'find_and_replace_menu': 'Найти и заменить...',
        'search_scope_label': 'Область поиска:',
        'scope_original': 'Оригинал',
        'scope_reference': 'Референс',
        'scope_editor': 'Редактор',
        'scope_audio': 'Названия аудиофайлов',
        
        # Метки файлов
        'file_label': 'Файл:',
        'mission_label': 'Миссия:',
        'mission_file_label': 'Файл миссии:',
        'campaign_label': 'Кампания:',
        
        # Сообщения статуса
        'status_lines_loaded': 'Загружено {count} строк для перевода',
        'status_mission_lines_loaded': 'Загружено {count} строк из файла миссии',
        'status_context_stripped': 'Контекст AI автоматически удален из вставленного текста',
        'status_smart_paste': '✅ Умная вставка: распознано {count} маркеров 🔹',
        'status_no_lines_to_copy': 'Нет строк для копирования',
        'status_copied': 'Скопировано {count} строк',
        'status_text_pasted': 'Текст вставлен из буфера обмена',
        'status_clipboard_empty': 'Буфер обмена пуст',
        'status_translation_updated': 'Перевод обновлен',
        'status_translation_cleared': 'Весь перевод очищен',
        'status_translation_updated': 'Перевод обновлен',
        'status_mission_overwritten': 'Миссия перезаписана с резервной копией',
        'status_mission_saved': 'Миссия сохранена в новое местоположение',
        'status_waiting_sync': 'Ожидание синхронизации...',
        'status_sync_complete': 'Синхронизация завершена',
        'status_line_deleted': 'Строка удалена',
        'status_cannot_delete_last': 'Нельзя удалить последнюю строку в группе!',
        'status_ref_locale_fallback': '⚠ Референс-локаль \'{locale}\' не найдена в миссии, используется DEFAULT',
        'status_quick_save': 'Файл сохранен (Ctrl+S; Ctrl+клик "💾 Сохранить перевод…")',
        'status_key_default_only': '⚠ Аудио "{filename}" привязано к ключу, который отсутствует в локали {locale}. Этот ключ доступен только в DEFAULT.',
        
        # Подтверждение выхода
        'confirm_exit_title': 'Несохраненные изменения',
        'confirm_exit_msg': 'Изменения не сохранены, вы уверены, что хотите закрыть программу?',
        'confirm_open_new_title': 'Несохраненные изменения',
        'confirm_open_new_msg': 'Изменения не сохранены, вы уверены, что хотите открыть новый файл?',
        'yes_exit_btn': 'Да',
        'cancel_exit_btn': 'Отмена',
        'briefing_exit_msg': 'Есть несохраненные изменения. Выйти без сохранения?',
        'briefing_exit_yes': 'Да',
        'briefing_exit_no': 'Нет',
        'tts_close_warning_title': 'Предупреждение',
        'tts_close_warning_msg': 'При закрытии окна TTS не применённые сгенерированные файлы будут удалены. Продолжить?',
        
        # Многопоточность и запуск
        'multi_instance_title': 'Запущен другой экземпляр',
        'multi_instance_question': 'Другой экземпляр программы уже запущен. Вы хотите запустить еще один?',
        'instance_open_choice_title': 'Открытие файла',
        'instance_open_choice_msg': 'Программа уже запущена. Где вы хотите открыть файл?\n\nФайл: {filename}',
        'choice_current_instance': 'Открыть в текущем окне',
        'choice_new_instance': 'Открыть в новом окне',
        'choice_cancel': 'Отмена',
        'unsaved_warning_ipc': 'ВНИМАНИЕ: В текущем окне есть не сохраненные изменения!\nОни будут потеряны при открытии нового файла.',
        'yes_btn': 'Да',
        'no_btn': 'Нет',
        
        # Контекст ИИ
        'add_context_label': 'Добавить контекст',
        'context_select_lang': 'Выбор шаблона:',
        'tooltip_add_context': 'Добавляет контекст в начало перевода для ИИ переводчика',
        'ai_context_mgmt_btn': 'Управление контекстом для ИИ',
        'instructions_btn': '📖 Инструкция по переводу',
        
        # Синхронизация прокрутки
        'sync_scroll_label': 'Синхр. прокрутки',
        'tooltip_sync_scroll': 'Синхронизирует вертикальную прокрутку окон оригинала и перевода',
        
        'instruction_content': """<div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; line-height: 1.5; color: #ddd; padding: 15px 20px;">

<div style="text-align: center; color: #ff9900; font-weight: bold; font-size: 16px;">ИНСТРУКЦИЯ ПО ПЕРЕВОДУ МИССИЙ DCS World</div>
<table width="100%" cellpadding="0" cellspacing="0" style="margin: 10px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🟩 ОТКРЫТЬ ФАЙЛ МИССИИ</div>
<br>Нажмите кнопку «📂 Открыть (.miz, .cmp, dictionary)» → выберите MyMission.miz

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🟦 СКОПИРОВАТЬ ТЕКСТ</div>
<br>Нажмите кнопку «📋 Копировать весь текст» под окном оригинального текста<br>
• Если включена опция «Добавить контекст», то в самое начало копируемого текста добавляется контекст для ИИ‑переводчика, который вы можете поменять в соответствующем разделе в зависимости от предпочитаемого языка перевода.<br>
• По умолчанию включена опция, которая автоматически, при копировании, добавляет в начало каждой строки маркер с номером строки.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🟪 ПЕРЕВЕСТИ</div>
<div style="color: #ff6666; font-weight: bold; margin: 4px 0;">(ВНИМАТЕЛЬНО! КОЛИЧЕСТВО СТРОК ПЕРЕВОДА ДОЛЖНО СТРОГО СОВПАДАТЬ С КОЛИЧЕСТВОМ СТРОК В ОКНЕ ОРИГИНАЛЬНОГО ТЕКСТА)</div>
<br>• Если вы использовали маркеры с номерами строк, то переведённый текст копируйте вместе с ними. Программа автоматически подставит строки согласно маркерам, даже если ИИ «склеит» строки, а сами маркеры будут удалены при вставке.<br>
• Подробная информация по маркерам в руководстве пользователя.<br>

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>
→ <b>Обычный переводчик</b> (Google Translate, DeepL):<br>
Вставьте текст → переведите → скопируйте<br>
<span style="color: #ffcc00;">⚠️ Может перевести названия кнопок, технические термины</span>
<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

→ <b>ИИ‑переводчик</b> (ChatGPT, DeepSeek):<br>
Вставьте текст и инструкцию для ИИ (если не воспользовались опцией «Добавить контекст»):<br><br>

<div style="border-left: 3px solid #ff9900; padding: 8px 12px; margin: 8px 0; background-color: #333; border-radius: 0 4px 4px 0;">
Переведи текст для игры DCS World.<br>
Количество строк должно остаться без изменений!<br>
НЕ переводи:<br>
• Названия кнопок (SPACE, ENTER, F1‑F12)<br>
• Технические термины (FL, RPM, NM, Mhz)<br>
• Названия самолётов (F‑16, Su‑27)<br>
• Кодовые названия (Sword 2‑1, Alpha)<br>
<br>
Затем вставьте текст для перевода.<br>
<br>
Получите качественный перевод с сохранением игровых терминов.
</div>

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🟨 ВЫБРАТЬ ЛОКАЛИЗАЦИЮ И ВСТАВИТЬ ПЕРЕВОД</div>
<br>Выберите нужную локализацию (в верхней части окна: DEFAULT или создайте нужную вам).<br>
Нажмите «📋 Вставить из буфера» под окном перевода<br>
• Проверьте, что количество строк в окне «Оригинальный текст» совпадает с количеством строк в окне «Перевод».

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🟧 СОХРАНИТЬ</div>
<br>Нажмите «💾 Сохранить перевод…» или комбинацию клавиш Ctrl+S.<br>
Выберите «💾 Перезаписать файл» или другой вариант в зависимости от ваших предпочтений.<br>
Опционально можете активировать параметр «Создать резервную копию».<br>
<br>
<b style="color: #88ff88;">Текстовый перевод готов!</b><br>
<br>
Вы можете быстро добавить голосовой перевод с помощью генерации голоса ИИ к тем аудиофайлам, которые были сопоставлены с текстом из миссии.<br>
Для этого нужно:<br>
1. Нажмите кнопку «Озвучить», чтобы вызвать соответствующее окно.<br>
2. Выбрать, скачать и настроить необходимый голосовой «движок» (работает локально на вашем ПК).<br>
3. Отметьте в плейлисте все или необходимые вам аудиофайлы и нажмите кнопку генерации.<br>
4. После того как все выбранные аудиофайлы будут сгенерированы, вы можете их прослушать и при необходимости сгенерировать заново.<br>
5. Нажмите кнопку «Заменить выделенные аудиофайлы в миссии» и закройте окно.<br>
6. Нажмите «💾 Сохранить перевод…»

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🌍 ЕСЛИ ХОТИТЕ СДЕЛАТЬ НЕСКОЛЬКО ЯЗЫКОВ</div>
<br><span style="color: #999;">(Все изменения в процессе перехода от локализации к локализации сохраняются)</span><br><br>
Русский перевод → сохранить в RU<br>
Немецкий перевод → сохранить в DE<br>
Французский перевод → сохранить в FR<br>
<br>
<b>📊 ВСЕ ЯЗЫКИ В ОДНОМ .MIZ ФАЙЛЕ!</b><br>
<br>
<div style="color: #88ff88; font-weight: bold; font-size: 14px;">ВСЁ ПРОСТО: Открыл → Перевёл → Сохранил → Готово! 🎮🌍</div>

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 10px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">РАБОТА С ФАЙЛАМИ КАМПАНИЙ (.cmp)</div><br>
Текстовый перевод файлов кампаний (.cmp) почти ничем не отличается от перевода миссий.<br>
Если вы хотите изменить картинки, включите отображение всех ключей (ориентируйтесь на [picture_RU], [picture_DE] и другие).

</div>""",

        'user_manual_content': """<div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; line-height: 1.5; color: #ddd; padding: 15px 20px;">

<div style="text-align: center; color: #ff9900; font-weight: bold; font-size: 16px;">Руководство пользователя DCS Translator TOOL</div>
<table width="100%" cellpadding="0" cellspacing="0" style="margin: 10px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<b>DCS Translation TOOL</b> — это мощный инструмент для перевода, озвучки и модификации миссий игры DCS World.<br>
Программа позволяет напрямую редактировать архивы миссий (<code>.miz</code>) и словари-локализации (<code>.lua</code>), переводить текст, заменять аудио и изображения, генерировать новую озвучку нейросинтезом речи (TTS), управлять планшетом (Kneeboard) и анализировать брифинг.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Основные возможности</div><br>
• Удобная работа с архивами <code>.miz</code> без необходимости их ручной распаковки и упаковки.<br>
• Редактирование текстов всех локализаций внутри миссии.<br>
• <b>Встроенный нейросинтез речи (TTS)</b> с поддержкой популярных движков Piper и XTTSv2 (включая пакетную автоматическую генерацию аудио по выделенным файлам).<br>
• Управление ресурсами: замена аудиофайлов радиопередач и картинок брифинга/планшета в пару кликов.<br>
• Встроенный функциональный аудиоплеер.<br>
• <b>Drag‑and‑drop</b> интерфейс для лёгкого массового извлечения (экспорта) медиафайлов миссии на рабочий стол.<br>
• Режим нескольких открытых окон для одновременного перевода.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Главное окно и таблица перевода</div><br>
После загрузки файла вы увидите внизу основную таблицу, где:<br>
• <b>Ключ (DictKey)</b>: внутренний уникальный идентификатор строки в DCS World.<br>
• <b>Состояние</b>: цветовые индикаторы.<br>
• <b>Референсный текст</b>: исходный текст (обычно берётся из системной локали <code>DEFAULT</code>). Этот столбец доступен только для чтения — это ваш референс (исходник) для перевода. Можно менять локаль.<br>
• <b>Редактор перевода</b>: ваш текущий текст для выбранной в данный момент локали. Это главное редактируемое поле.<br>
• <b>Звук</b>: индикатор наличия привязанного аудио (иконка аудио). Если кликнуть по нему, можно открыть интерфейс привязанного звука в аудиоплеере.<br>
<br>
<b>Цветовая индикация строк:</b><br>
• <span style="color: #88ff88;"><b>Зелёный текст</b></span>: исходный цвет текста.<br>
• <span style="color: #ff6666;"><b>Красный текст</b></span>: строка отредактирована и ожидает сохранения.<br>
• <span style="color: #ffcc00;"><b>Жёлтый текст</b></span>: текст в этой строке был изменён и сохранён в текущей сессии.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Работа с локалями (языки миссии)</div><br>
Миссии DCS поддерживают множество языков. Сверху над таблицей находится выпадающий список:<br>
• Выбор нужной локали (например, <code>RU</code>, <code>EN</code>, <code>DE</code>, <code>FR</code>) мгновенно переключает столбец «Редактор перевода» на выбранный язык из архива.<br>
• Переключаться между локалями можно «на лету», все несохранённые изменения текста бережно кэшируются программой в памяти.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Умная вставка с маркерами</div><br>
Программа оснащена системой точечной передачи текста обратно в таблицу миссии. При копировании всего текста оригинала (кнопкой «Копировать оригинал») каждая строка автоматически нумеруется специальными синими ромбиками (маркерами), например: <code>🔹1🔹 Текст</code>.<br>
<br>
Попросите ИИ перевести текст и сохранить эти маркеры в начале переведённой фразы (в формате <code>🔹N🔹 Перевод</code>). Когда вы скопируете ответ ИИ и нажмёте кнопку «Вставить из буфера», <code>Ctrl+V</code> (или вставить через ПКМ) в любое окно перевода, программа перехватит этот текст и активирует режим «умной вставки».<br>
<br>
<b>Как это работает:</b><br>
Программа строго ищет шаблон <code>🔹Цифра🔹</code>. Если он найден, текст вставляется только в те ячейки, номера которых совпали, не трогая остальную таблицу!<br>
<br>
<b>Обработка нестандартных случаев ИИ:</b><br>
• <b>Болтовня ИИ:</b> нейросети любят писать <i>«Конечно, вот ваш перевод:»</i> перед текстом. Парсер намеренно игнорирует любой текст до первого правильного маркера — весь «мусор» просто отсекается.<br>
• <b>Дыры и пропуски:</b> если вставить текст только с маркерами 2, 5 и 10, переведутся только эти строки. Строки 1, 3, 4, 6–9 останутся нетронутыми.<br>
• <b>Несуществующие маркеры:</b> если номер маркера <code>🔹99🔹</code>, а у вас всего 20 строк, программа его просто бесшумно проглотит, не вызвав ошибки.<br>
• <b>Склейка абзацев:</b> если ИИ внутри одного перевода (маркера) сделал физический перенос строки (Enter), программа умно соединит её, чтобы не нарушать строгую табличную структуру DCS-миссии.<br>
• <b>Поломанные маркеры:</b> если маркер скопирован без цифры внутри (например, <code>🔹🔹 Завершить миссию</code>), программа забракует его как маркер и вставит как самый обычный текст прямо под ваш курсор.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Озвучка текста (модуль TTS)</div><br>
Одна из главных фишек программы — возможность автоматически озвучить весь игровой текст (субтитры радиопереговоров) героев миссии.<br>
<br>
В программе доступны два движка:<br>
1. <b>Piper (офлайн‑синтез)</b>: быстрый, лёгкий движок. Загружает модели из интернета на лету и озвучивает текст практически мгновенно, используя CPU. Не требует интернета после скачивания модели голоса.<br>
2. <b>XTTS v2 (нейроклонирование)</b>: тяжёлая нейросеть от компании Coqui (потребует около 6 Гб места на диске под файлы). Работает медленнее, но качество генерации выше — позволяет задать ЛЮБОЙ короткий <code>WAV</code>-файл в качестве «голоса‑образца» — и ваш текст будет озвучен именно этим голосом с сохранением оригинальных интонаций, акцента и эмоций диктора. По умолчанию использует GPU (~4 ГБ видеопамяти).<br>
<br>
<i style="color: #999;">Все необходимые для работы с озвучкой файлы скачиваются в каталог с исполняемым файлом, через который была запущена программа.</i><br>
<br>
<b>Как пользоваться:</b><br>
1. Отметьте нужные строки в главной таблице галочками (крайний левый столбец списка).<br>
2. Выберите язык и желаемый голос диктора (Speaker) в настройках окна TTS.<br>
3. Отрегулируйте скорость и паузы.<br>
4. <b>Одиночная генерация</b>: чтобы сгенерировать фразу для одной конкретной строки, нажмите на нужный аудиофайл в списке.<br>
5. <b>Пакетная генерация</b>: если у вас выбрано (отмечено галочками) много фраз, нажмите большую кнопку «Сгенерировать выбранное». Программа последовательно, в фоновом режиме, озвучит все тексты, показывая прогресс‑бар и оставшееся время.<br>
6. В завершении нажмите <b>«Заменить выделенные аудиофайлы в миссии»</b>. Все сгенерированные аудиофайлы будут автоматически привязаны к соответствующим строкам субтитров в миссии. В таблице эти аудио станут красными. (Не забудьте сохранить миссию, чтобы встроить готовое аудио в <code>.miz</code>‑архив.)

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Менеджер файлов миссии (ресурсы и аудио)</div><br>
Мощный инструмент для визуального управления всеми медиафайлами внутри миссии (внутри <code>l10n/ваша_локаль/</code>).<br>
Здесь собраны все встроенные файлы архива: аудио радиоэфиров, звуки окружения, триггерные эффекты, картинки брифинга и страницы наколенного планшета пилота (Kneeboard).<br>
<br>
<b>Возможности менеджера:</b><br>
• <b>Предпросмотр</b>: кликните по любому файлу в списке, чтобы прослушать аудио через встроенный плеер или посмотреть увеличенную картинку.<br>
• <b>Drag &amp; Drop экспорт</b>: вы можете «схватить» любой файл (или несколько) за иконку левой кнопкой мыши и «вытащить» (drag &amp; drop) его в любую папку на рабочем столе Windows — файлы моментально извлекутся из архива миссии.<br>
• <b>Пакетная замена</b>: выделите файлы, которые хотите заменить. Нажмите кнопку «Заменить выбранное». Откроется окно пакетной замены файлов. Можно использовать префиксы, суффиксы, прямую замену совпадающих названий или один файл для всех. Старые файлы будут безопасно удалены из архива миссии DCS, а новые — упакованы на их место. Умный алгоритм программы предварительно проверит, не используются ли эти заменяемые файлы где‑то ещё у других сопоставлений.<br>
• <b>Фильтрация вкладок</b>: вкладки сверху позволяют отдельно посмотреть слои: только аудио, только изображения брифинга и отдельно файлы планшета (Kneeboard).

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Анализ брифинга</div><br>
Вызов: кнопка «Брифинг»<br>
<br>
В структуре файлов DCS World текст брифинга жёстко разбит на ключи.<br>
Окно показывает текст брифинга (постановку задачи/ситуацию) последовательно, как в игре.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Мультиоконный режим и синхронизация</div><br>
В этом режиме вы можете открыть саму программу несколько раз независимо (например, открыть Миссию 1, Миссию 2 и Миссию 3 в трёх разных окнах).

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Закладки</div><br>
Кликните по значку ⭐ любой ячейки в таблице, чтобы добавить строку в закладки (появится жёлтая звезда). Вы можете добавить разные значки, настроить цвет выделения строк и добавить комментарий.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<i style="color: #999;">Техническое примечание: Программа спроектирована так, чтобы автоматически и безопасно управлять своими временными файлами при распаковке слоёв миссии, управлять кэшами генерации TTS и гарантированно самостоятельно очищать за собой весь рабочий «мусор» (TEMP-директории) при штатном выходе (закрытии) приложения.</i>

</div>""",
    
        'ai_context_title': 'Управление контекстом для ИИ',
        'context_default_btn': 'Контекст по умолчанию',
        'context_label_1': 'Используемый контекст:',
        'context_label_2': 'Запасной контекст:',
        'context_swap_btn': 'Поменять местами',
        'context_save_btn': 'Сохранить',
        'context_back_btn': 'Назад',
        'context_unsaved_warning': 'Текст не сохранен!',
        'default_context_text': """Ты переводчик миссий DCS World (авиасимулятор).

Задача:
Переведи текст на РУССКИЙ ЯЗЫК максимально точно, без художественных вольностей.

ОБЯЗАТЕЛЬНО:
- Сохраняй количество строк 1 в 1 даже если это не имеет смысла, даже если кажется, что это одно предложение, не объединяй строки
- НИЧЕГО не добавляй и не удаляй
- НЕ объединяй строки
- НЕ переводить технические элементы, имена файлов, ключи, идентификаторы, переменные
- НЕ переводить позывные, если они выглядят как callsign (Brutus, Colt 1-1, Ford 2)
- НЕ переводить значения времени, координаты, высоты, частоты
- Форматирование и количество строк должно остаться исходным

ПЕРЕВОДИТЬ:
- Радиообмен
- Инструкции игроку
- Сообщения от инструктора
- Брифинги и подсказки

Контекст:
Текст используется в миссии DCS World.
Тематика — авиация и военные полёты.

Вот текст для перевода:""",
        
        # Окно TTS
        'tts_window_title': 'Генерация голоса Text-To-Speech',
        'tts_title': 'Генерация голоса TTS',
        'tts_tab_piper': 'Piper (Быстрый)',
        'tts_tab_xtts': 'XTTS v2 (Качественный)',
        'tts_manual_install_btn': 'Инструкция по ручной установке',
        'tts_manual_install_title': 'Ручная установка движков TTS',
        'tts_manual_install_text': """<div style="font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; line-height: 1.4;">
<div style="text-align: center; color: #ff9900; font-weight: bold; font-size: 16px;">РУЧНАЯ УСТАНОВКА ДВИЖКОВ TTS</div>
<table width="100%" cellpadding="0" cellspacing="0" style="margin: 10px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>
Если автоматическое скачивание или установка библиотек не работает из-за блокировок провайдера (ошибка WSAECONNRESET) или антивируса, вы можете скачать все необходимые компоненты вручную.<br><br>

<b><span style="color: #ff9900;">1. Базовая установка Python и библиотек (Только для исходников)</span></b><br>
Если вы используете .exe версию, этот шаг не нужен.<br>
• Скачайте <b>Python 3.10</b> или <b>3.11</b> с python.org.<br>
• При установке ОБЯЗАТЕЛЬНО отметьте галочку <i>"Add Python to PATH"</i>.<br>
• Откройте cmd и выполните: <code>pip install PyQt5 mutagen colorama chardet</code><br><br>

<b><span style="color: #ff9900;">2. Движок Piper (Оффлайн синтез)</span></b><br>
Piper — это автономная программа, не требующая Python.<br>
• Скачайте архив <code>piper_windows_amd64.zip</code> со страницы релизов Piper на Github.<br>
• Распакуйте его в папку <code>tts_data</code> внутри папки с программой. Точный путь до файла запуска должен быть таким:<br>
&nbsp;&nbsp;<code>Ваша_Папка_Программы/tts_data/piper/piper.exe</code><br>
• Модели (голоса) программа докачивает автономно в папку <code>tts_data/models/</code>. Если это тоже не работает, скачайте их вручную с Hugging Face (нужны файлы .onnx и .onnx.json) и положите туда.<br><br>

<b><span style="color: #ff9900;">3. Движок XTTS v2 (Нейро-клонирование)</span></b><br>
XTTS работает через Python и требует тяжелых библиотек.<br>
<b>А. Установка библиотек:</b><br>
• Откройте командную строку и установите PyTorch:<br>
&nbsp;&nbsp;<code>pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118</code><br>
• Установите движок TTS:<br>
&nbsp;&nbsp;<code>pip install TTS</code><br>
<b>Б. Установка моделей (~2 ГБ):</b><br>
• Создайте папку <code>xtts</code> внутри <code>tts_data</code> в корне вашей программы.<br>
• Зайдите на Hugging Face в репозиторий <i>coqui/XTTS-v2</i>.<br>
• Скачайте 4 файла: <code>model.pth</code>, <code>config.json</code>, <code>vocab.json</code>, <code>speakers_xtts.pth</code>.<br>
• Положите их строго внутрь папки <code>tts_data/xtts/</code>.<br>
</div>""",
        'tts_filter_symbols': 'При генерации заменять символы на пробел:',
        'tts_replace_symbol_from': 'символы',
        'tts_replace_symbol_to': 'на',
        'tts_replace_symbol_tooltip': 'Посимвольная замена: каждый символ из первого поля заменяется на символ из второго поля на той же позиции (например, точка на запятую).',
        'tts_btn_generate': 'Генерация голоса TTS',
        'tts_btn_generate_tooltip': 'Запустить процесс генерации аудио на основе выбранного движка и настроек',
        'tts_auto_play': 'Авто-воспроизведение',
        'tts_auto_play_tooltip': 'Автоматически начинать воспроизведение сразу после успешной генерации',
        'tts_playlist_title': 'Аудиофайлы миссии с привязкой к тексту',
        'tts_btn_apply': 'Заменить выделенные аудиофайлы в миссии',
        'tts_piper_info': 'Piper TTS: быстрый движок для мгновенной озвучки.',
        'tts_btn_engine': '📦 Engine',
        'tts_btn_engine_tooltip': 'Статус движка Piper. Если не запущен — нажмите для исправления установки.',
        'tts_lbl_lang': 'Язык:',
        'tts_lbl_voice': 'Голос:',
        'tts_lbl_speed': 'Скорость:',
        'tts_lbl_speed_tooltip': 'Скорость произношения текста (от 0.5x до 2.0x)',
        'tts_lbl_pause': 'Паузы:',
        'tts_lbl_pause_tooltip': 'Длительность пауз между знаками препинания и предложениями',
        'tts_lbl_noise': 'Эмоции:',
        'tts_lbl_noise_tooltip': 'Вариативность интонации. Чем выше, тем более эмоциональным может быть голос',
        'tts_btn_reset': 'Сбросить ползунки',
        'tts_btn_reset_tooltip': 'Вернуть настройки к значениям по умолчанию',
        'tts_xtts_info': 'XTTS v2: выберите стандартный голос или клонируйте образец.',
        'tts_btn_libs': '📦 Libs',
        'tts_btn_libs_tooltip': 'Статус библиотек (PyTorch, MeMo). Если не OK — нажмите для автоматической настройки.',
        'tts_btn_model': '📥 Model',
        'tts_btn_model_tooltip': 'Статус модели XTTS v2 (~1.5GB). Нажмите для скачивания или переустановки.',
        'tts_lbl_xtts_status': 'Проверка модели XTTS v2...',
        'tts_xtts_clone': '👤 [Клонировать образец]',
        'tts_lbl_wav': 'WAV:',
        'tts_wav_placeholder': 'Путь к образцу...',
        'tts_lbl_xtts_speed': 'Скорость:',
        'tts_lbl_xtts_speed_tooltip': 'Скорость произношения (от 0.5x до 2.0x)',
        'tts_lbl_xtts_temp': 'Эмоции:',
        'tts_lbl_xtts_temp_tooltip': 'Степень изменчивости и эмоциональности голоса (0.1 - 1.0)',
        'tts_lbl_xtts_rep': 'Повторы:',
        'tts_lbl_xtts_rep_tooltip': 'Штраф за повторение одних и тех же слов или слогов',
        'tts_lbl_xtts_k': 'Top-K:',
        'tts_lbl_xtts_k_tooltip': 'Ограничение выбора только K самых вероятных вариантов (влияет на стабильность)',
        'tts_lbl_xtts_p': 'Top-P:',
        'tts_lbl_xtts_p_tooltip': 'Ограничение выбора вариантами, суммарная вероятность которых не превышает P',
        'tts_lbl_xtts_len': 'Длина:',
        'tts_lbl_xtts_len_tooltip': 'Штраф за излишнюю длину генерации (влияет на лаконичность)',
        'tts_btn_reset_xtts_tooltip': 'Вернуть настройки XTTS к значениям по умолчанию',
        'tts_status_loaded_edited': '📁 Загружен измененный текст для: {key}',
        'tts_status_loaded_orig': '📁 Загружен текст для: {key}',
        'tts_status_err_ogg': '⚠️ PyGame не может проиграть оригинал OGG. Сгенерируйте аудио 🧠',
        'tts_status_err_load': '❌ Ошибка загрузки аудио (файл поврежден или 0 байт)',
        'tts_status_gen_prefix': 'Сгенерировано',
        'tts_status_orig_prefix': 'Оригинал',
        'tts_status_piper_not_found': '⚠️ Engine Piper не найден. Будет использован SAPI5.',
        'tts_status_piper_ok': '✅ Engine OK',
        'tts_btn_gen_voice': 'Генерация голосом: {name}',
        'tts_btn_download_voice': 'Скачать голос: {name}',
        'tts_status_libs_ok': '✅ Libs OK',
        'tts_status_model_ok': '✅ Модель OK',
        'tts_status_xtts_ready': '✅ XTTS v2 готов',
        'tts_btn_gen_clone': 'Генерация голосом: Клон',
        'tts_status_xtts_req': '⚠️ Требуется установка компонентов XTTS',
        'tts_status_xtts_waiting': 'Ждёт установки компонентов',
        'tts_select_wav': 'Выберите образец голоса',
        'tts_status_stop_batch': '⏸️ Остановка после текущего файла...',
        'tts_err_clone_wav': '❌ Ошибка: выберите .wav образец для клонирования',
        'tts_err_dl_voice': '❌ Сначала скачайте голосовой пакет',
        'tts_err_install_libs': '❌ Сначала установите библиотеки',
        'tts_err_dl_model': '❌ Сначала скачайте модель XTTS',
        'tts_err_no_files': '❌ Нет файлов с текстом для генерации (пропущено: {count})',
        'tts_btn_stop_gen': 'Остановить генерацию голоса',
        'tts_status_gen_progress': '🧠 Генерация {index}/{total}: {filename}',
        'tts_status_gen_rem': ' | ~{mins}:{secs} осталось | ~{avg} сек/файл',
        'tts_status_batch_stopped': '⏸️ Остановлено. Сгенерировано: {count}/{total} за {mins}:{secs}',
        'tts_status_batch_done': '✅ Готово! Сгенерировано: {count}/{total} за {mins}:{secs}',
        'tts_status_generating': 'Генерация голоса...',
        'tts_status_done': '✅ Готово!',
        'tts_err_gen_failed': '❌ Ошибка: {error}',
        'tts_msgbox_gen_err_title': 'Ошибка TTS',
        'tts_msgbox_gen_err_msg': 'Не удалось сгенерировать аудио:\n{error}',
        'tts_status_extract_orig': '📂 Извлечение оригинала...',
        'tts_err_no_mission': '❌ Ошибка: миссия не загружена',
        'tts_err_file_not_found': '❌ Ошибка: файл не найден',
        'tts_status_saved': '✅ Сохранено: {name}',
        'tts_msgbox_save_err': 'Ошибка сохранения',
        'tts_msgbox_save_err_msg': 'Не удалось сохранить файл:\n{error}',
        'tts_status_dl_piper': '📥 Скачивание Piper Engine...',
        'tts_status_piper_installed': '✅ Piper Engine установлен!',
        'tts_err_dl_piper': '❌ Ошибка при скачивании Piper',
        'tts_status_install_libs': '📦 Установка библиотек (coqui-tts, torch)...',
        'tts_status_libs_installed': '✅ Библиотеки установлены! Теперь скачайте модель.',
        'tts_err_libs_dll': '❌ Библиотеки скачаны, но не могут быть загружены (ошибка DLL).',
        'tts_err_install_libs_log': '❌ Ошибка при установке библиотек. Проверьте install_log.txt.',
        'tts_msgbox_xtts_err_title': 'Ошибка установки XTTS',
        'tts_msgbox_xtts_err_text': 'Не удалось установить компоненты XTTS автоматически.',
        'tts_msgbox_xtts_err_info': 'Основные причины проблемы:\n1. Сетевая блокировка (WSAECONNRESET 10054). Решение: ВКЛЮЧИТЕ VPN.\n2. Антивирус или брандмауэр обрывает соединение. Решение: ВРЕМЕННО ОТКЛЮЧИТЕ их.\n\nПодробности ошибки записаны в файл \'install_log.txt\' рядом с программой.',
        'tts_status_dl_done': '✅ Загрузка завершена!',
        'tts_err_dl_net': '❌ Ошибка при загрузке. Проверьте интернет.',
        'tts_status_replaced': '✅ Заменено: {count} файлов',
        'tts_err_no_gen_files': '❌ Нет сгенерированных файлов среди выделенных',
        'tts_tab_bark': 'Оригинал (Bark)'
    },
    
    'en': {
        # Основные элементы интерфейса
        'window_title': 'DCS Translation TOOL v{version}',
        'status_ready': 'Ready. Open a file to start working',
        'status_file_saved': '✅ File saved: {filename}',
        'status_translation_updated': 'Translation updated',
        'status_translation_cleared': '✅ All translation cleared',
        'status_copied_lines': '✅ Copied {count} lines',
        'status_pasted': '✅ Text pasted from clipboard',
        'status_default_filters': '✅ Default filters set',
        'status_replace_success': '✅ Replaced {count} occurrences',
        
        # Кнопки и меню
        'open_file_btn': '📂 Open file (dictionary .txt .cmp)',
        'open_miz_btn': '📂 Open mission file (.miz)',
        'open_unified_btn': '📂 Open (.miz, .cmp, dictionary)',
        'open_miz_menu_item': '📂 Open mission file (.miz)',
        'open_dict_menu_item': '📄 Open file (dictionary, .txt, .cmp)',
        'recent_files_label': 'Recent files',
        'clear_recent_btn': 'Clear history',
        'no_recent_files': 'No recent files',
        'open_new_instance_btn': 'Open a new program instance',
        'save_file_btn': '💾 Save translation…',
        'copy_all_btn': '📋 Copy all text',
        'show_keys_btn': '🔑 Show/hide keys',
        'paste_btn': '📋 Paste from clipboard',
        'clear_btn': '🗑️ Clear translation',
        'default_filters_btn': 'Default filters',
        'view_log_btn': '📋 View error log',
            'settings_btn': 'Settings',
            'settings_window_title': 'Settings',
            'theme_bg_even_label': 'Row background color 1 (odd)',
            'theme_bg_odd_label': 'Row background color 2 (even)',
            'theme_text_modified_label': 'Modified text color',
            'theme_text_saved_label': 'Original text color',
            'theme_text_session_label': 'Modified and saved text color in the current session',
            'highlight_empty_label': 'Highlight input fields',
            'highlight_color_label': 'Highlight color',
            'enable_logs_label': 'Enable logs',
            'preview_font_family_label': 'Bottom window text font',
            'preview_font_size_label': 'Font size',
            'reference_locale_label': 'Reference locale',
            'settings_skip_locale_dialog': 'Skip locale selection window',
            'settings_default_open_locale': 'Set default locale when opening file:',
            'settings_multi_window_mode': 'Multi-window mode',
            'case_sensitive_search': 'Case sensitive search',
            'settings_smart_paste_enabled': 'Smart Paste AI (marker-based paste)',
            'tab_instruction': 'Instruction',
            'tab_user_manual': 'User Manual',
            'tooltip_smart_paste': 'When using the "Copy all text" button, lines automatically include\n🔹N🔹 markers. When pasting, the program recognizes these markers\nand accurately inserts the translation into the corresponding rows.\nIf disabled, text is copied and pasted without markers.',
            'bookmark_colors_label': 'Bookmark background colors:',
            'bookmark_opacity_label': 'Opacity:',
        
        # Заголовки групп
        'filters_group': 'Key filters for translation:',
        'preview_group': 'Translation preview:',
        # Headers inside preview panel
        'preview_header_meta': 'Metadata',
        'preview_header_ref': 'Reference text:',
        'preview_header_editor': 'Translation editor: {locale}',
        
        # Метки
        'original_text_label': 'Original text:',
        'translation_label': 'Translation:',
        'additional_keys_label': 'Additional keys:',
        'skip_empty_label': 'Skip empty lines',
        'skip_empty_keys_label': 'Skip empty keys',
        'show_audio_keys_label': 'Show keys with audio',
        'preview_no_keys_match': 'No keys match the filters',
        'preview_info': 'Showing {count} lines',
        'stats_label': 'Lines to translate: {count}',
        'english_count': '{count} lines',
        'russian_count': '{filled}/{total} filled',
        'custom_filter_placeholder': 'Key {index}',
        
        # Стандартные фильтры
        'filter_action_text': 'ActionText',
        'filter_action_radio': 'ActionRadioText',
        'filter_description': 'description',
        'filter_subtitle': 'subtitle',
        'filter_sortie': 'sortie',
        'filter_name': 'name',
        
        # Диалоги сохранения
        'save_dialog_title': 'Mission .miz file save',
        'save_dialog_info': 'Choose how to save the translated mission:',
        'overwrite_btn': '💾 Overwrite file…',
        'overwrite_cmp_btn': '💾 Overwrite file',
        'miz_backup_label': 'Create backup',
        'save_as_btn': '💾 Save as…',
        'save_btn': '💾 Save',
        'save_txt_separately_btn': '💾 Save separately to .txt…',
        'cancel_btn': 'Cancel',
        'close_btn': 'Close',
        'open_btn': 'Open',
        
        # Сообщения об ошибках
        'error_title': 'Error',
        'success_title': 'Success',
        'file_not_found': 'File not found',
        'file_read_error': 'File read error',
        'file_save_error': 'File save error',
        'miz_error': 'Mission file error',
        'error_miz_save': 'Error saving .miz file: {error}',
        'error_truncated_header': 'Save error: truncated ZIP header. The file may be corrupted or in use by another application.',
        'error_no_lines_found': 'No lines found for translation with selected filters',
        'error_no_lines_found_miz': 'No lines found for translation with selected filters in dictionary file',
        'key_not_found_msg': 'Key "{key_name}" not found in this file',
        'key_hidden_by_filters_msg': 'Key "{key_name}" is hidden by current filters',
        'miz_select_folder_title': 'Select localization folder',
        'miz_select_folder_desc': '(If unsure, select DEFAULT)',
        'miz_save_folder_title': 'Select your translation language',
        'miz_save_folder_desc': '(If unsure, select "DEFAULT")',
        'localization_label': 'localization:',
        'show_all_keys_label': 'Show all keys',
        'btn_radio': 'Player',
        'btn_files': 'Files',
        'btn_briefing': 'Briefing',
        'files_window_title': 'File Manager',
        'files_window_placeholder': 'File Manager (under development)',

        # File Manager
        'fm_col_number': '#',
        'fm_col_type': 'Type',
        'fm_col_filename': 'Filename',
        'fm_col_description': 'Description',
        'fm_col_status': 'Status',
        'fm_col_info': 'Info',
        'fm_col_link': '🔗',
        'fm_col_actions': 'Actions',
        'fm_col_gen_duration': 'Gen. dur.',
        'fm_col_orig_duration': 'Orig. dur.',
        'fm_filter_audio': '♫ Audio',
        'fm_filter_images': '🖼 Images',
        'fm_filter_kneeboard': '📋 Kneeboard',
        'fm_search_placeholder': 'Search by filename...',
        'fm_preview_placeholder': 'Select a file to preview',
        'fm_desc_briefing_blue': 'Blue Briefing',
        'fm_desc_briefing_red': 'Red Briefing',
        'fm_desc_briefing_neutral': 'Neutral Briefing',
        'fm_desc_trigger': 'Trigger',
        'fm_desc_kneeboard': 'Kneeboard',
        'fm_desc_audio_linked': 'Radio Message',
        'fm_desc_audio_trigger': 'Trigger (audio)',
        'fm_no_files': 'No files to display',
        'fm_status_in_locale': 'File is in the current locale folder',
        'fm_status_default_only': 'File is in the "DEFAULT" folder',
        'fm_status_replaced': 'Pending save',
        'fm_tooltip_play': 'Play',
        'fm_tooltip_stop': 'Stop',
        'fm_tooltip_view': 'View image',
        'fm_tooltip_replace': 'Replace file',
        'fm_tooltip_download': 'Save to disk',
        'fm_tooltip_has_link': 'Audio file text link',
        'tts_install_success_title': 'TTS',
        'tts_install_success_msg': 'Piper successfully installed! You can now generate voiceovers.',
        'tts_install_error_title': 'TTS',
        'tts_install_error_msg': 'Error downloading components.\nPlease check your internet connection and try again.',
        'tts_init_error_title': 'Error',
        'tts_init_error_msg': 'TTS initialization error: {error}',
        'tts_general_error_title': 'Error',
        'tts_general_error_msg': 'TTS error: {error}',
        'logs_cleared': '✓ Logs cleared ({count} files)',
        'logs_no_files': '✓ No log files to clear',
        'fm_btn_batch_export': '🡇 Save Selected',
        'fm_btn_batch_replace': '⟲ Replace Selected',
        'fm_menu_rename': 'Rename',
        'fm_menu_show_in_editor': 'Show in Editor',
        'fm_replace_suffix_title': 'Replacement Prefix & Suffix',
        'fm_replace_suffix_label': 'Suffix (added AFTER name):',
        'fm_br_prefix_label': 'Prefix (added BEFORE name):',
        'fm_batch_replace_success': 'Successfully replaced {count} of {total} files{path}',
        'fm_shift_selection_hint': '💡 Hold Shift to select a range',
        'fm_status_shown': 'Shown: {current} of {total}',
        'fm_status_selected': 'Selected: {count} ({size})',
        'fm_btn_select_all': 'Select All',
        'fm_btn_select_none': 'Deselect All',
        'fm_btn_select_invert': 'Inverse',
        'fm_audio_no_file': 'No file selected',
        'img_prev_export': '🡇 Export',
        'img_prev_replace': '⟲ Replace',
        'fm_batch_replace_zero': 'No suitable files found for replacement out of {total} selected{path}',
        'fm_export_success': 'Files successfully exported to folder:{path}',
        'fm_export_zero': 'No files were exported from the selected items',
        'fm_br_title': 'Batch Resource Replacement',
        'fm_br_desc_suffix': '<b>Prefix & Suffix Search:</b> The program will look for files in the folder using the rule: <i>Prefix + FileName + Suffix</i>. For example, "new_" + "music.ogg" + "_old" → "new_music_old.ogg". Leave empty if not needed.',
        'fm_br_desc_prefix_suffix': '<b>Prefix & Suffix Search:</b> The program will look for files in the folder using the rule: <i>Prefix + FileName + Suffix</i>. For example, "new_" + "music.ogg" + "_old" → "new_music_old.ogg". Leave empty if not needed.',
        'fm_br_desc_single': '<b>Single File for All:</b> All selected resources will be replaced by the same file. Useful for placeholder replacement.',
        'fm_br_mode_suffix': 'By Pref. / Suff.',
        'fm_br_mode_single': 'Single File for All',
        'fm_br_desc_drop': '<b>Batch File Matching:</b> The program will look for matches for mission resource names among the dropped files (<b>{count} pcs.</b>).<br/><br/>Use prefixes/suffixes if the filenames in Windows differ from the names in the mission.',
        'fm_br_btn_apply': 'Apply',
        'fm_br_btn_cancel': 'Cancel',
        'fm_br_select_file': 'Select replacement file',
        'fm_br_title_window': 'Batch Resource Replacement',
        
        # Type Mismatch Dialog
        'type_mismatch_title': 'Warning: Format Mismatch!',
        'type_mismatch_desc': 'You are attempting to replace {orig_cat} ({orig_ext}) with {new_cat} ({new_ext}).\n\nThe game\'s internal logic might not recognize the new format, and the file may not work in the mission.\n\nAre you sure you want to continue?',
        'continue_btn': 'Continue',
        'briefing_window_title': 'Briefing',
        'briefing_window_placeholder': 'Briefing (under development)',
        'miz_executing': 'Executing',
        'no_reference_marker': '[NO REFERENCE] ',
        'no_translation_marker': '[NOT TRANSLATED, ADD?]',
        'briefing_mission_name_label': 'Mission Name:',
        'briefing_tab_description': 'Mission Description:',
        'briefing_tab_red_task': 'Red Task:',
        'briefing_tab_blue_task': 'Blue Task:',
        'briefing_tab_neutrals_task': 'Neutral Task:',

        # Bookmarks
        'bookmark_set_star': '★ Set Star',
        'bookmark_set_question': '? Set Question',
        'bookmark_set_alert': '! Set Important',
        'bookmark_comment': '💬 Comment...',
        'bookmark_comment_title': 'Bookmark Comment',
        'bookmark_clear_all': '🗑 Clear All Bookmarks',
        'bookmark_clear_all_confirm': 'Remove all bookmarks and comments for the current mission?',
        'delete_comment_tooltip': 'Delete comment',


        # Audio Player
        'audio_player_title': 'Audio Player',
        'playlist_total_duration': 'Total time: {duration}',
        'replace_audio_btn': 'Replace Audio File',
        'audio_file_label': 'File:',
        'play_btn': 'Play',
        'pause_btn': 'Pause',
        'stop_btn': 'Stop',
        'file_from_default': 'File from DEFAULT',
        'volume_label': 'Volume',
        'error_audio_file': 'File not found',
        'select_new_audio_title': 'Select Audio File',
        'audio_file_filter': 'Audio Files (*.ogg *.wav);;All Files (*)',
        'audio_replaced_success': 'Audio file replaced successfully',
        'heuristic_audio_warning': 'WARNING! Audio file matched with the current key\nby heuristic analysis. Will not affect mission.',
        'heuristic_toggle_btn': 'Heuristic analysis bias: {offset}',
        'no_audio_file': 'File not selected',
        'error_utf8_read': 'Unable to read file in UTF-8 encoding.',
        'error_utf8_convert': 'Please try to convert the file to UTF-8.',
        'error_bad_zip': 'File {filename} is not a valid ZIP archive or is corrupted.',
        'error_details': 'Details: {details}',
        'error_title_encoding': 'Encoding Error',
        
        # Sync scroll
        'sync_scroll_label': 'Sync scrolling',
        'tooltip_sync_scroll': 'Synchronizes vertical scrolling of original and translation windows',
        
        # Диалог очистки
        'clear_dialog_title': 'Clear translation',
        'clear_question': 'Are you sure you want to clear all translation?',
        'yes_btn': 'YES',
        'no_btn': 'NO',
        'tts_close_warning_title': 'Warning',
        'tts_close_warning_msg': 'When closing the TTS window, unapplied generated files will be deleted. Continue?',
        
        # Отчеты сохранения
        'save_report_title': '✅ File saved',
        'save_stats': '📊 Statistics:',
        'total_lines': '• Total keys in file: {count}',
        'translatable_lines': '• Lines for translation: {count}',
        'translated_lines': '• Translated lines: {count}',
        'remaining_lines': '• Remaining to translate: {count}',
        'backup_created': '🔄 Backup created:',
        'file_saved_to': '📁 File saved to:',
        'slash_warning': '⚠ Warning: {count} lines lost trailing backslash',
        'replacements_done': '🔧 Debug:',
        'replacements_count': '• Replacements done: {done}',
        'replacements_expected': '• Expected replacements: {expected}',
        'failed_replacements': '⚠ WARNING:\nFailed to replace {count} lines.',
        'file_save_success': 'File successfully saved:\n{filename}',
        'miz_overwrite_success': 'Mission file successfully overwritten:\n{filename}',
        'miz_save_as_success': 'Mission successfully saved:\n{filename}',
        
        # Locale deletion
        'delete_locale_btn': 'Delete',
        'delete_confirm_title': 'Delete Locale',
        'delete_confirm_msg': 'Are you sure you want to delete {locale}?',
        
        # Тултипы и подсказки
        'tooltip_drag': 'Program window can be dragged by left or right mouse button, anywhere on screen',
        'tooltip_open_file': 'Open dictionary text file (.txt or .lua)',
        'tooltip_open_miz': 'Open mission file (.miz) for translation',
        'tooltip_save_file': 'Save current translation to file',
        'tooltip_instructions': 'Show detailed instructions for using the program',
        'tooltip_ai_context': 'AI translator context management',
        'tooltip_copy_all': 'Copy all English text to clipboard',
        'tooltip_show_keys': 'Show or hide dictionary keys',
        'tooltip_paste': 'Paste text from clipboard',
        'tooltip_clear': 'Clear all translated text',
        'tooltip_default_filters': 'Set default filters',
        'tooltip_view_log': 'View error log',
        'tooltip_warning_slash': 'The number of \\ backslashes may differ. This can be ignored.',
        'tooltip_about_program': 'Program Information',
        'tooltip_default_context': 'Default Context',
        'tooltip_multi_window_mode': 'Enable to allow opening multiple instances of the program. If disabled, new files will open in the current window.',
        'audio_replace_help_tooltip': 'Alternative replacement method: drag a file from File Explorer onto the name of the current audio file in the main window.',
        'about_title': 'Program Information',
        'about_text': 'DCS Translation TOOL v{version}\n\nA tool for translating text in DCS World missions.\nWorks with dictionary files and .miz archives.\nFree and will remain so.\n\nSource code and feedback:\nGitHub: https://github.com/Hokum-A/dcs-translation-tool\n\nSupport the project:\nBoosty: https://boosty.to/hokuma\nUSDT TRC20: TKLcwmrNmwXFgwbpS66UnAGsB3Lvnqpwv5\n\nDeveloper: Hokum (Andrey Varlamov)\nLicense: MIT License\n\nThank you for using this tool.',
        'exit_btn': 'Back',
        'ok_btn': 'OK',
        'tts_loading_msg': 'Preparing voice generation...',
        'tts_btn': 'Speak',
        
        # Дополнительные элементы интерфейса
        'skip_empty_label': 'Skip empty lines',
        'additional_keys_label': 'Additional keys:',
        'original_text_label': 'Original text:',
        'translation_label': 'Translation:',
        'not_translated': '[not translated]',
        'preview_info': 'Loaded {count} blocks',
        'preview_info_progress': 'Loaded {current} of {total} blocks',
        'stats_lines': 'Lines to translate: {count}',
        'stats_to_translate': 'Lines to translate: {count}',
        'stats_translated': 'Translated: {count}',
        'stats_not_translated': 'Not translated: {count}',
        'english_count_label': '{count} lines',
        'russian_count_label': '{filled}/{total} filled',
        
        # Search
        'search_label': 'Find:',
        'search_placeholder': 'Text...',
        'replace_placeholder': 'Text...',
        'search_matches': 'Matches: {count}',
        'replace_label': 'Replace with:',
        'replace_btn': 'Replace',
        'replace_all_btn': 'Replace all',
        'find_and_replace_menu': 'Find and replace...',
        'search_scope_label': 'Search Area:',
        'scope_original': 'Original',
        'scope_reference': 'Reference',
        'scope_editor': 'Editor',
        'scope_audio': 'Audio filenames',
        
        # Метки файлов
        'file_label': 'File:',
        'mission_label': 'Mission:',
        'mission_file_label': 'Mission file:',
        'campaign_label': 'Campaign:',
        
        # Сообщения статуса
        'status_lines_loaded': 'Loaded {count} lines for translation',
        'status_mission_lines_loaded': 'Loaded {count} lines from mission file',
        'status_context_stripped': 'AI Context automatically stripped from pasted text',
        'status_smart_paste': '✅ Smart paste: recognized {count} markers 🔹',
        'status_no_lines_to_copy': 'No lines to copy',
        'status_copied': 'Copied {count} lines',
        'status_text_pasted': 'Text pasted from clipboard',
        'status_clipboard_empty': 'Clipboard is empty',
        'status_translation_updated': 'Translation updated',
        'status_translation_cleared': 'All translation cleared',
        'status_mission_overwritten': 'Mission overwritten with backup',
        'status_mission_saved': 'Mission saved to new location',
        'status_waiting_sync': 'Waiting for sync...',
        'status_sync_complete': 'Sync complete',
        'status_line_deleted': 'Row deleted',
        'status_cannot_delete_last': 'Cannot delete the last row in a group!',
        'status_ref_locale_fallback': '⚠ Reference locale \'{locale}\' not found in mission, using DEFAULT',
        'status_quick_save': 'File saved (Ctrl+S; Ctrl+click "💾 Save translation…")',
        'status_key_default_only': '⚠ Audio "{filename}" is linked to a key that is missing in locale {locale}. This key is only available in DEFAULT.',
        
        'ai_context_title': 'AI Context Management',
        # Exit Confirmation
        'confirm_exit_title': 'Unsaved Changes',
        'confirm_exit_msg': 'Unsaved changes will be lost. Are you sure you want to close the program?',
        'confirm_open_new_title': 'Unsaved Changes',
        'confirm_open_new_msg': 'Unsaved changes will be lost. Are you sure you want to open a new file?',
        'yes_exit_btn': 'Yes',
        'cancel_exit_btn': 'Cancel',
        'briefing_exit_msg': 'Unsaved changes. Exit without saving?',
        'briefing_exit_yes': 'Yes',
        'briefing_exit_no': 'No',
        
        # Multi-instance and Startup
        'multi_instance_title': 'Another Instance Running',
        'multi_instance_question': 'Another instance of the program is already running. Do you want to start another one?',
        'instance_open_choice_title': 'Opening File',
        'instance_open_choice_msg': 'The program is already running. Where do you want to open the file?\n\nFile: {filename}',
        'choice_current_instance': 'Open in current window',
        'choice_new_instance': 'Open in a new window',
        'choice_cancel': 'Cancel',
        'unsaved_warning_ipc': 'WARNING: There are unsaved changes in the current window!\nThey will be lost if you open a new file.',
        'yes_btn': 'Yes',
        'no_btn': 'No',
        
        # AI Context
        'add_context_label': 'Add context',
        'context_select_lang': 'Select template:',
        'tooltip_add_context': 'Adds context to the beginning of the translation for the AI translator',
        'ai_context_mgmt_btn': 'AI Context Management',
        'instructions_btn': '📖 Translation Instructions',
        'instruction_content': """<div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; line-height: 1.5; color: #ddd; padding: 15px 20px;">

<div style="text-align: center; color: #ff9900; font-weight: bold; font-size: 16px;">DCS World MISSION TRANSLATION INSTRUCTION</div>
<table width="100%" cellpadding="0" cellspacing="0" style="margin: 10px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🟩 OPEN MISSION FILE</div>
<br>Click "📂 Open (.miz, .cmp, dictionary)" → select MyMission.miz

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🟦 COPY TEXT</div>
<br>Click "📋 Copy all text" below the original text window<br>
• If the "Add context" option is enabled, context for the AI translator is added to the very beginning of the copied text. You can change it in the corresponding section depending on your preferred translation language.<br>
• By default, the option that automatically adds a line number marker to the beginning of each line when copying is enabled.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🟪 TRANSLATE</div>
<div style="color: #ff6666; font-weight: bold; margin: 4px 0;">(ATTENTION! THE NUMBER OF LINES IN THE TRANSLATION MUST STRICTLY MATCH THE NUMBER OF LINES IN THE ORIGINAL TEXT WINDOW)</div>
<br>• If you used line number markers, copy the translated text together with them. The program will automatically match lines according to the markers, even if the AI "glues" lines together, and the markers themselves will be removed upon pasting.<br>
• Detailed information about markers is in the user manual.<br>

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>
→ <b>Regular translator</b> (Google Translate, DeepL):<br>
Paste the text → translate → copy<br>
<span style="color: #ffcc00;">⚠️ May translate button names, technical terms</span>
<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

→ <b>AI translator</b> (ChatGPT, DeepSeek):<br>
Paste the text and instructions for AI (if you did not use the "Add context" option):<br><br>

<div style="border-left: 3px solid #ff9900; padding: 8px 12px; margin: 8px 0; background-color: #333; border-radius: 0 4px 4px 0;">
Translate the text for the DCS World game.<br>
The number of lines must remain unchanged!<br>
DO NOT translate:<br>
• Button names (SPACE, ENTER, F1‑F12)<br>
• Technical terms (FL, RPM, NM, Mhz)<br>
• Aircraft names (F‑16, Su‑27)<br>
• Code names (Sword 2‑1, Alpha)<br>
<br>
Then paste the text to be translated.<br>
<br>
Get a high‑quality translation while preserving game terms.
</div>

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🟨 SELECT LOCALIZATION AND PASTE TRANSLATION</div>
<br>Select the appropriate localization (at the top of the window: DEFAULT or create your own).<br>
Click "📋 Paste from clipboard" below the translation window<br>
• Check that the number of lines in the "Original text" window matches the number of lines in the "Translation" window.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🟧 SAVE</div>
<br>Click "💾 Save translation…" or press Ctrl+S.<br>
Select "💾 Overwrite file" or another option depending on your preference.<br>
Optionally, you can activate the "Create backup" parameter.<br>
<br>
<b style="color: #88ff88;">The text translation is ready!</b><br>
<br>
You can quickly add voice‑over using AI voice generation for the audio files that have been linked to the text from the mission.<br>
To do this:<br>
1. Click the "Voice‑over" button to open the corresponding window.<br>
2. Select, download, and configure the necessary voice engine (runs locally on your PC).<br>
3. In the playlist, check all or the required audio files and click the generate button.<br>
4. After all selected audio files have been generated, you can listen to them and regenerate if necessary.<br>
5. Click the "Replace selected audio files in the mission" button and close the window.<br>
6. Click "💾 Save translation…"

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">🌍 IF YOU WANT TO MAKE MULTIPLE LANGUAGES</div>
<br><span style="color: #999;">(All changes are preserved when switching between localizations)</span><br><br>
Russian translation → save as RU<br>
German translation → save as DE<br>
French translation → save as FR<br>
<br>
<b>📊 ALL LANGUAGES IN ONE .MIZ FILE!</b><br>
<br>
<div style="color: #88ff88; font-weight: bold; font-size: 14px;">IT'S SIMPLE: Open → Translate → Save → Done! 🎮🌍</div>

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 10px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">WORKING WITH CAMPAIGN FILES (.cmp)</div><br>
Text translation of campaign files (.cmp) is almost no different from translating missions.<br>
If you want to change images, enable the display of all keys (refer to [picture_RU], [picture_DE], etc.).

</div>""",

        'user_manual_content': """<div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; line-height: 1.5; color: #ddd; padding: 15px 20px;">

<div style="text-align: center; color: #ff9900; font-weight: bold; font-size: 16px;">DCS Translator TOOL User Manual</div>
<table width="100%" cellpadding="0" cellspacing="0" style="margin: 10px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<b>DCS Translation TOOL</b> is a powerful tool for translating, voice‑over, and modifying DCS World missions.<br>
The program allows you to directly edit mission archives (<code>.miz</code>) and localization dictionaries (<code>.lua</code>), translate text, replace audio and images, generate new voice‑over using neural speech synthesis (TTS), manage the kneeboard, and analyze the briefing.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Main Features</div><br>
• Convenient work with <code>.miz</code> archives without manual packing/unpacking.<br>
• Edit texts for all localizations inside the mission.<br>
• <b>Built‑in neural speech synthesis (TTS)</b> with support for popular engines Piper and XTTSv2 (including batch automatic audio generation for selected files).<br>
• Resource management: replace radio transmission audio files and briefing/kneeboard images in a few clicks.<br>
• Built‑in functional audio player.<br>
• <b>Drag‑and‑drop</b> interface for easy mass extraction (export) of mission media files to the desktop.<br>
• Multiple‑window mode for simultaneous translation.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Main Window and Translation Table</div><br>
After loading a file, you will see the main table at the bottom, where:<br>
• <b>Key (DictKey)</b>: internal unique identifier of the string in DCS World.<br>
• <b>Status</b>: color indicators.<br>
• <b>Reference Text</b>: source text (usually taken from the system <code>DEFAULT</code> locale). This column is read‑only — it is your reference (original) for translation. The locale can be changed.<br>
• <b>Translation Editor</b>: your current text for the currently selected locale. This is the main editable field.<br>
• <b>Audio</b>: indicator of linked audio (audio icon). Clicking it opens the linked audio interface in the audio player.<br>
<br>
<b>Row Color Indication:</b><br>
• <span style="color: #88ff88;"><b>Green text</b></span>: original text color.<br>
• <span style="color: #ff6666;"><b>Red text</b></span>: row has been edited and awaits saving.<br>
• <span style="color: #ffcc00;"><b>Yellow text</b></span>: text in this row has been changed and saved in the current session.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Working with Locales (Mission Languages)</div><br>
DCS missions support multiple languages. Above the table there is a drop‑down list:<br>
• Selecting a locale (e.g., <code>RU</code>, <code>EN</code>, <code>DE</code>, <code>FR</code>) instantly switches the "Translation Editor" column to the selected language from the archive.<br>
• You can switch between locales "on the fly"; all unsaved text changes are carefully cached by the program in memory.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Smart Paste with Markers</div><br>
The program features a system for targeted insertion of text back into the mission table. When copying all original text (using the "Copy original" button), each line is automatically numbered with special blue diamond markers, for example: <code>🔹1🔹 Text</code>.<br>
<br>
Ask the AI to translate the text and keep these markers at the beginning of each translated phrase (in the format <code>🔹N🔹 Translation</code>). When you paste the AI's response and click the "Paste from clipboard" button, <code>Ctrl+V</code> (or paste via right‑click) into any translation window, the program intercepts this text and activates the "Smart Paste" mode.<br>
<br>
<b>How it works:</b><br>
The program strictly looks for the pattern <code>🔹Number🔹</code>. If found, the text is inserted only into the cells whose numbers match, without touching the rest of the table!<br>
<br>
<b>Handling AI Edge Cases:</b><br>
• <b>AI chatter:</b> neural networks like to write <i>"Certainly, here is your translation:"</i> before the text. The parser deliberately ignores any text before the first valid marker — all "garbage" is simply cut off.<br>
• <b>Holes and gaps:</b> if you paste text with only markers 2, 5, and 10, only those rows will be translated. Rows 1, 3, 4, 6–9 remain untouched.<br>
• <b>Non‑existent markers:</b> if the marker number is <code>🔹99🔹</code> and you have only 20 rows, the program silently ignores it without an error.<br>
• <b>Paragraph merging:</b> if the AI inserts a physical line break (Enter) inside a single translation (marker), the program intelligently merges it so as not to break the strict tabular structure of the DCS mission.<br>
• <b>Broken markers:</b> if a marker is copied without a number inside (e.g., <code>🔹🔹 Complete mission</code>), the program rejects it as a marker and inserts it as ordinary text directly under the cursor.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Text Voice‑over (TTS Module)</div><br>
One of the program's main features is the ability to automatically voice all in‑game text (radio subtitles) for mission characters.<br>
<br>
Two engines are available:<br>
1. <b>Piper (offline synthesis)</b>: fast, lightweight engine. Downloads models from the internet on the fly and voices text almost instantly using the CPU. No internet required after the voice model is downloaded.<br>
2. <b>XTTS v2 (neural voice cloning)</b>: heavy neural network from Coqui (requires about 6 GB of disk space for files). Slower but provides higher generation quality — allows you to use ANY short <code>WAV</code> file as a "voice sample" — your text will be spoken with that voice, preserving the original intonation, accent, and emotions of the speaker. By default uses GPU (~4 GB VRAM).<br>
<br>
<i style="color: #999;">All files required for voice‑over are downloaded to the directory containing the executable from which the program was launched.</i><br>
<br>
<b>How to use:</b><br>
1. Check the desired rows in the main table using the checkboxes (far left column of the list).<br>
2. Select the language and desired voice (Speaker) in the TTS window settings.<br>
3. Adjust speed and pauses.<br>
4. <b>Single generation:</b> to generate a phrase for a specific row, click on the corresponding audio file in the list.<br>
5. <b>Batch generation:</b> if you have selected (checked) many phrases, click the large "Generate selected" button. The program will sequentially generate audio for all texts in the background, showing a progress bar and estimated remaining time.<br>
6. Finally, click <b>"Replace selected audio files in the mission"</b>. All generated audio files will be automatically linked to the corresponding subtitle rows in the mission. In the table, these audio entries will turn red. (Don't forget to save the mission to embed the finished audio into the <code>.miz</code> archive.)

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Mission File Manager (Resources and Audio)</div><br>
A powerful tool for visual management of all media files inside the mission (inside <code>l10n/your_locale/</code>).<br>
All embedded archive files are collected here: radio transmission audio, ambient sounds, trigger effects, briefing images, and kneeboard pages.<br>
<br>
<b>Manager Features:</b><br>
• <b>Preview</b>: click any file in the list to listen to the audio via the built‑in player or view an enlarged image.<br>
• <b>Drag &amp; Drop export</b>: you can "grab" any file (or multiple files) by its icon with the left mouse button and "drag &amp; drop" it into any folder on the Windows desktop — files are instantly extracted from the mission archive.<br>
• <b>Batch replacement</b>: select the files you want to replace. Click the "Replace selected" button. A batch file replacement window opens. You can use prefixes, suffixes, direct name‑matching replacement, or a single file for all. Old files are safely removed from the DCS mission archive, and new ones are packed in their place. The program's smart algorithm will first check whether these replaceable files are used elsewhere in other associations.<br>
• <b>Tab filtering</b>: tabs at the top allow you to view separate layers: only audio, only briefing images, and only kneeboard files.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Briefing Analysis</div><br>
Invocation: "Briefing" button<br>
<br>
In the DCS World file structure, the briefing text is strictly split into keys.<br>
The window displays the briefing text (mission description / situation) sequentially, as it appears in the game.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Multi‑Window Mode and Synchronization</div><br>
In this mode, you can open the program itself several times independently (for example, open Mission 1, Mission 2, and Mission 3 in three different windows).

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<div style="color: #ff9900; font-weight: bold; font-size: 14px;">Bookmarks</div><br>
Click the ⭐ icon in any table cell to add the row to bookmarks (a yellow star will appear). You can add different icons, customize the row highlight color, and add a comment.

<table width="100%" cellpadding="0" cellspacing="0" style="margin: 14px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>

<i style="color: #999;">Technical note: The program is designed to automatically and safely manage its temporary files when extracting mission layers, manage TTS generation caches, and guarantee cleaning up all working "junk" (TEMP directories) upon normal exit (closing) of the application.</i>

</div>""",
        
        'ai_context_title': 'AI Context Management',
        'context_default_btn': 'Default Context',
        'context_label_1': 'Current Context:',
        'context_label_2': 'Backup Context:',
        'context_swap_btn': 'Swap',
        'context_save_btn': 'Save',
        'context_back_btn': 'Back',
        'context_unsaved_warning': 'Text not saved!',
        'default_context_text': """You are a translator for DCS World mission texts (combat flight simulator).

Task:
Translate the following text as accurately as possible, without creative alterations. 
The target language for the translation is determined by the language in which this very task is written.

MANDATORY:
- Preserve the exact number of lines (1:1), even if it doesn't make sense, even if it seems like one sentence — do not merge lines.
- Do NOT add or remove anything
- Do NOT merge lines
- Do NOT translate technical elements, file names, keys, identifiers, variables
- Do NOT translate callsigns if they look like real callsigns (Brutus, Colt 1-1, Ford 2)
- Do NOT translate time values, coordinates, altitudes, frequencies
- Formatting and line count must remain exactly the same as the source

TRANSLATE:
- Radio communications
- Player instructions
- Messages from the Instructor Pilot
- Briefings and hints

Context:
The text is used in a DCS World mission.
Theme: aviation and military flight operations.

Here is the text to translate:""",
        
        # TTS Window
        'tts_window_title': 'Text-To-Speech Generation',
        'tts_title': 'TTS Voice Generation',
        'tts_tab_piper': 'Piper (Fast)',
        'tts_tab_xtts': 'XTTS v2 (High Quality)',
        'tts_manual_install_btn': 'Manual Installation Guide',
        'tts_manual_install_title': 'Manual TTS Engines Installation',
        'tts_manual_install_text': """<div style="font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; line-height: 1.4;">
<div style="text-align: center; color: #ff9900; font-weight: bold; font-size: 16px;">MANUAL TTS ENGINES INSTALLATION</div>
<table width="100%" cellpadding="0" cellspacing="0" style="margin: 10px 0;"><tr><td style="border-top: 1px solid #444; font-size: 1px; line-height: 1px;"></td></tr></table>
If the automatic download or library installation fails due to network restrictions (e.g. WSAECONNRESET) or antivirus blocking, you can manually download and configure all necessary components.<br><br>

<b><span style="color: #ff9900;">1. Python and Dependencies (For Source Code Only)</span></b><br>
If you are using the compiled .exe version, skip this step.<br>
• Download <b>Python 3.10</b> or <b>3.11</b> from python.org.<br>
• During installation, you MUST check the <i>"Add Python to PATH"</i> box.<br>
• Open cmd and run: <code>pip install PyQt5 mutagen colorama chardet</code><br><br>

<b><span style="color: #ff9900;">2. Piper Engine (Offline Synthesis)</span></b><br>
Piper is a standalone executable engine and does not require Python.<br>
• Download the <code>piper_windows_amd64.zip</code> archive from the Piper releases page on Github.<br>
• Extract the archive into the <code>tts_data</code> folder inside your program's directory. The exact path to the executable MUST be:<br>
&nbsp;&nbsp;<code>Your_Program_Folder/tts_data/piper/piper.exe</code><br>
• The program automatically downloads voice models into the <code>tts_data/models/</code> subfolder. If this fails, download the voices manually from Hugging Face (.onnx and .onnx.json files are needed) and place them there.<br><br>

<b><span style="color: #ff9900;">3. XTTS v2 Engine (Neural Cloning)</span></b><br>
XTTS requires Python and downloading large libraries.<br>
<b>A. Installing Libraries:</b><br>
• Open cmd and install PyTorch with CUDA support:<br>
&nbsp;&nbsp;<code>pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118</code><br>
• Install the Coqui TTS engine:<br>
&nbsp;&nbsp;<code>pip install TTS</code><br>
<b>B. Installing Models (~2 GB):</b><br>
• Create a folder named <code>xtts</code> inside the <code>tts_data</code> directory in the root of your program.<br>
• Go to the Hugging Face repository <i>coqui/XTTS-v2</i>.<br>
• Download these 4 files: <code>model.pth</code>, <code>config.json</code>, <code>vocab.json</code>, <code>speakers_xtts.pth</code>.<br>
• Place them directly inside the <code>tts_data/xtts/</code> folder.<br>
</div>""",
        'tts_filter_symbols': 'Replace symbols with space during generation:',
        'tts_replace_symbol_from': 'symbols',
        'tts_replace_symbol_to': 'to',
        'tts_replace_symbol_tooltip': 'Character-by-character replacement: each character from the first field is replaced by the character from the second field at the same position (e.g., dot to comma).',
        'tts_btn_generate': 'Generate TTS Voice',
        'tts_btn_generate_tooltip': 'Start the audio generation process based on selected engine and settings',
        'tts_auto_play': 'Auto-play',
        'tts_auto_play_tooltip': 'Automatically start playback right after successful generation',
        'tts_playlist_title': 'Mission audio files linked to text',
        'tts_btn_apply': 'Replace selected audio files in mission',
        'tts_piper_info': 'Piper TTS: fast engine for instant voice generation.',
        'tts_btn_engine': '📦 Engine',
        'tts_btn_engine_tooltip': 'Piper engine status. If not running — click to fix installation.',
        'tts_lbl_lang': 'Language:',
        'tts_lbl_voice': 'Voice:',
        'tts_lbl_speed': 'Speed:',
        'tts_lbl_speed_tooltip': 'Speech speed (from 0.5x to 2.0x)',
        'tts_lbl_pause': 'Pauses:',
        'tts_lbl_pause_tooltip': 'Duration of pauses between punctuation marks and sentences',
        'tts_lbl_noise': 'Emotions:',
        'tts_lbl_noise_tooltip': 'Intonation variability. The higher, the more emotional the voice can be',
        'tts_btn_reset': 'Reset sliders',
        'tts_btn_reset_tooltip': 'Reset settings to default values',
        'tts_xtts_info': 'XTTS v2: choose a standard voice or clone a sample.',
        'tts_btn_libs': '📦 Libs',
        'tts_btn_libs_tooltip': 'Libraries status (PyTorch, MeMo). If not OK — click for automatic setup.',
        'tts_btn_model': '📥 Model',
        'tts_btn_model_tooltip': 'XTTS v2 model status (~1.5GB). Click to download or reinstall.',
        'tts_lbl_xtts_status': 'Checking XTTS v2 model...',
        'tts_xtts_clone': '👤 [Clone sample]',
        'tts_lbl_wav': 'WAV:',
        'tts_wav_placeholder': 'Path to sample...',
        'tts_lbl_xtts_speed': 'Speed:',
        'tts_lbl_xtts_speed_tooltip': 'Speech speed (from 0.5x to 2.0x)',
        'tts_lbl_xtts_temp': 'Emotions:',
        'tts_lbl_xtts_temp_tooltip': 'Degree of variability and emotionality of the voice (0.1 - 1.0)',
        'tts_lbl_xtts_rep': 'Repetitions:',
        'tts_lbl_xtts_rep_tooltip': 'Penalty for repeating the same words or syllables',
        'tts_lbl_xtts_k': 'Top-K:',
        'tts_lbl_xtts_k_tooltip': 'Limit choice to only K most likely options (affects stability)',
        'tts_lbl_xtts_p': 'Top-P:',
        'tts_lbl_xtts_p_tooltip': 'Limit choice to options whose cumulative probability does not exceed P',
        'tts_lbl_xtts_len': 'Length:',
        'tts_lbl_xtts_len_tooltip': 'Penalty for excessive generation length (affects conciseness)',
        'tts_btn_reset_xtts_tooltip': 'Reset XTTS settings to default values',
        'tts_status_loaded_edited': '📁 Loaded edited text for: {key}',
        'tts_status_loaded_orig': '📁 Loaded text for: {key}',
        'tts_status_err_ogg': '⚠️ PyGame cannot play original OGG. Generate audio 🧠',
        'tts_status_err_load': '❌ Error loading audio (file corrupted or 0 bytes)',
        'tts_status_gen_prefix': 'Generated',
        'tts_status_orig_prefix': 'Original',
        'tts_status_piper_not_found': '⚠️ Piper Engine not found. SAPI5 will be used.',
        'tts_status_piper_ok': '✅ Engine OK',
        'tts_btn_gen_voice': 'Generate with voice: {name}',
        'tts_btn_download_voice': 'Download voice: {name}',
        'tts_status_libs_ok': '✅ Libs OK',
        'tts_status_model_ok': '✅ Model OK',
        'tts_status_xtts_ready': '✅ XTTS v2 ready',
        'tts_btn_gen_clone': 'Generate with voice: Clone',
        'tts_status_xtts_req': '⚠️ XTTS components installation required',
        'tts_status_xtts_waiting': 'Waiting for components installation',
        'tts_select_wav': 'Select voice sample',
        'tts_status_stop_batch': '⏸️ Stopping after current file...',
        'tts_err_clone_wav': '❌ Error: select .wav sample for cloning',
        'tts_err_dl_voice': '❌ Download voice package first',
        'tts_err_install_libs': '❌ Install libraries first',
        'tts_err_dl_model': '❌ Download XTTS model first',
        'tts_err_no_files': '❌ No files with text for generation (skipped: {count})',
        'tts_btn_stop_gen': 'Stop voice generation',
        'tts_status_gen_progress': '🧠 Generation {index}/{total}: {filename}',
        'tts_status_gen_rem': ' | ~{mins}:{secs} remaining | ~{avg} sec/file',
        'tts_status_batch_stopped': '⏸️ Stopped. Generated: {count}/{total} in {mins}:{secs}',
        'tts_status_batch_done': '✅ Done! Generated: {count}/{total} in {mins}:{secs}',
        'tts_status_generating': 'Generating voice...',
        'tts_status_done': '✅ Done!',
        'tts_err_gen_failed': '❌ Error: {error}',
        'tts_msgbox_gen_err_title': 'TTS Error',
        'tts_msgbox_gen_err_msg': 'Failed to generate audio:\n{error}',
        'tts_status_extract_orig': '📂 Extracting original...',
        'tts_err_no_mission': '❌ Error: mission not loaded',
        'tts_err_file_not_found': '❌ Error: file not found',
        'tts_status_saved': '✅ Saved: {name}',
        'tts_msgbox_save_err': 'Save Error',
        'tts_msgbox_save_err_msg': 'Failed to save file:\n{error}',
        'tts_status_dl_piper': '📥 Downloading Piper Engine...',
        'tts_status_piper_installed': '✅ Piper Engine installed!',
        'tts_err_dl_piper': '❌ Error downloading Piper',
        'tts_status_install_libs': '📦 Installing libraries (coqui-tts, torch)...',
        'tts_status_libs_installed': '✅ Libraries installed! Now download the model.',
        'tts_err_libs_dll': '❌ Libraries downloaded but cannot be loaded (DLL error).',
        'tts_err_install_libs_log': '❌ Error installing libraries. Check install_log.txt.',
        'tts_msgbox_xtts_err_title': 'XTTS Installation Error',
        'tts_msgbox_xtts_err_text': 'Failed to install XTTS components automatically.',
        'tts_msgbox_xtts_err_info': 'Main causes of the problem:\n1. Network block (WSAECONNRESET 10054). Solution: TURN ON VPN.\n2. Antivirus or firewall drops connection. Solution: TEMPORARILY DISABLE them.\n\nError details are logged in \'install_log.txt\' next to the program.',
        'tts_status_dl_done': '✅ Download completed!',
        'tts_err_dl_net': '❌ Download error. Check your internet connection.',
        'tts_status_replaced': '✅ Replaced: {count} files',
        'tts_err_no_gen_files': '❌ No generated files among selected',
        'tts_downloading_msg': 'Downloading Piper TTS and voices (~85 MB)...',
        'tts_status_dl_python': '📥 Downloading Python 3.11 (~15 MB)...',
        'tts_status_unpack_python': '📦 Unpacking Python...',
        'tts_status_install_pip': '📥 Installing pip...',
        'tts_status_pip_fix': '🔧 pip is not working, reinstalling...',
        'tts_status_check_pip': '🔍 Checking pip...',
        'tts_status_install_numpy': '📦 Installing build tools and numpy (1/3)...',
        'tts_status_install_xtts_libs': '📦 Installing XTTS and libraries (2/3)...',
        'tts_status_install_torch': '📦 Installing Torch GPU (3/3) (~3 GB)...',
        'tts_status_install_success': '✅ Installation completed successfully!',
        'tts_status_unpack_piper': '📦 Unpacking Piper...',
        'tts_status_dl_piper_core': '📥 Downloading Piper core...',
        'tts_status_piper_install_done': '✅ Piper installation completed!',
        'tts_status_dl_model_file': '📥 Downloading {f_name}...',
        'tts_status_model_loaded': '✅ Model loaded!',
        'tts_err_dl_python': '❌ Failed to download Python.',
        'tts_err_pip_install': '❌ Pip installation error: {error}',
        'tts_err_pip_fix': '❌ Failed to restore pip. Delete .python and try again.',
        'tts_err_install_tools': '❌ Error installing build tools. See install_log.txt.',
        'tts_err_install_xtts_libs': '❌ Error installing TTS libraries. See install_log.txt.',
        'tts_err_install_torch': '❌ Error installing Torch. See install_log.txt.',
        'tts_err_dl_piper': '❌ Error downloading Piper.',
        'tts_err_piper_zip': '❌ Downloaded file is corrupted (not ZIP).',
        'tts_err_generic': '❌ Error: {error}',
        'tts_status_dl_progress': '{label}: {current} MB / {total} MB',
        'tts_status_python_ready': '✅ Python 3.11 ready!',
        'tts_err_pip_not_working': '❌ pip installed but not working. Try deleting .python and repeating.',
        'tts_err_model_load': '❌ Model loading error!',
        'tts_log_start_install': 'Starting clean XTTS installation and dependencies...',
        'tts_log_vpn_hint': 'IMPORTANT: If installation fails (10054), try enabling VPN.',
        'tts_log_portable_python_failed': 'ERROR: _ensure_portable_python returned None',
        'tts_log_portable_python_ready': 'Portable Python ready: {python_exe}',
        'tts_log_pip_not_working': 'pip not working! Trying to fix...',
        'tts_log_pip_reinstall_failed': 'ERROR: failed to reinstall pip',
        'tts_log_pip_reinstalled_not_working': 'ERROR: pip reinstalled but still not working',
        'tts_log_pip_fixed': 'pip fixed successfully!',
        'tts_log_pip_ok': 'pip is working OK',
        'tts_log_install_foundation': 'Step 1: Installing build tools and numpy...',
        'tts_log_install_foundation_failed': 'ERROR: Step 1 (foundation) failed.',
        'tts_log_install_xtts_libs': 'Step 2: Installing XTTS and base libraries...',
        'tts_log_install_xtts_libs_failed': 'ERROR: Step 2 (XTTS and base libraries) failed.',
        'tts_log_install_torch': 'Step 3: Installing Torch with GPU support (CUDA 12.1)...',
        'tts_status_install_torch_gpu': '📦 Installing Torch GPU (3/3) (approx. 3 GB)...',
        'tts_log_install_torch_failed': 'ERROR: Step 3 (Torch) failed.',
        'tts_log_install_success': 'Installation completed successfully!',
        'tts_tab_bark': 'Original (Bark)'
    }
}

def get_translation(language, key, **kwargs):
    """Получить перевод для указанного языка с подстановкой параметров"""
    if language not in TRANSLATIONS:
        language = 'ru'  # По умолчанию русский
    
    if key not in TRANSLATIONS[language]:
        # Если перевода нет, возвращаем ключ
        return key
    
    text = TRANSLATIONS[language][key]
    
    # Подставляем параметры если они есть
    if kwargs:
        try:
            text = text.format(**kwargs)
        except:
            pass
    
    return text