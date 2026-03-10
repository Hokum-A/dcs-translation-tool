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
            'highlight_empty_label': 'Подсветка полей ввода',
            'highlight_color_label': 'Цвет подсветки',
            'enable_logs_label': 'Включить логи',
            'preview_font_family_label': 'Шрифт текста нижнего окна',
            'preview_font_size_label': 'Размер шрифта',
            'reference_locale_label': 'Референс-локаль',
            'settings_skip_locale_dialog': 'Пропускать окно выбора локали',
            'settings_default_open_locale': 'Установить локаль по умолчанию при открытии файла:',
            'settings_multi_window_mode': 'Многооконный режим',
        
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
        'open_btn': 'Открыть',
        
        # Сообщения об ошибках
        'error_title': 'Ошибка',
        'file_not_found': 'Файл не найден',
        'file_read_error': 'Ошибка чтения файла',
        'file_save_error': 'Ошибка сохранения файла',
        'miz_error': 'Ошибка работы с файлом миссии',
        'error_miz_save': 'Ошибка при сохранении .miz файла: {error}',
        'error_truncated_header': 'Ошибка при сохранении: усечён заголовок ZIP-архива. Возможно, файл повреждён или занят другим приложением.',
        'error_no_lines_found': 'Не найдено строк для перевода по выбранным фильтрам',
        'error_no_lines_found_miz': 'Не найдено строк для перевода по выбранным фильтрам в файле dictionary',
        'miz_select_folder_title': 'Выберите папку с локализацией',
        'miz_select_folder_desc': '(Если не уверены, выберите DEFAULT)',
        'miz_save_folder_title': 'Выберите язык вашего перевода',
        'miz_save_folder_desc': '(Если не уверены, выберите "DEFAULT")',
        'localization_label': 'локализация:',
        'show_all_keys_label': 'Показывать все ключи',
        'btn_radio': 'Радио',
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
        'fm_col_actions': 'Действия',
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
        'fm_btn_batch_export': '🡇 Сохранить выбранное',
        'fm_btn_batch_replace': '⟲ Заменить выбранное',
        'fm_menu_rename': 'Переименовать',
        'fm_menu_show_in_editor': 'Показать в редакторе',
        'fm_replace_suffix_title': 'Префикс и суффикс замены',
        'fm_replace_suffix_label': 'Суффикс (будет ПОСЛЕ имени):',
        'fm_br_prefix_label': 'Префикс (будет ПЕРЕД именем):',
        'fm_batch_replace_success': 'Успешно заменено {count} из {total} файлов{path}',
        'fm_shift_selection_hint': '💡 Зажмите Shift для выделения диапазона',
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

        
        # Аудиоплеер
        'audio_player_title': 'Аудиопроигрыватель',
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
        'search_matches': 'Совпадений: {count}',
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
        
        'instruction_content': """<div style="font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; line-height: 1.4;">
<div style="text-align: center; color: #777;">----------------------------------</div>
<div style="text-align: center; color: #ff9900; font-weight: bold;">ИНСТРУКЦИЯ ПО ПЕРЕВОДУ МИССИЙ DCS World</div>
<div style="text-align: center; color: #777;">----------------------------------</div>
<br>
<table width="100%" cellspacing="0" cellpadding="0" style="margin: 5px 20px 5px 5px;">
    <tr><td align="center" style="background-color: #ff9900; color: #000000; font-weight: bold; padding: 6px; border-radius: 4px;">🚀 БЫСТРЫЙ СТАРТ (ДЛЯ СЕБЯ)</td></tr>
</table>
<br>
<br>
🟩 ОТКРЫТЬ ФАЙЛ МИССИИ<br>
Нажмите "📂 Открыть файл миссии (.miz)" → выберите MyMission.miz<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟦 СКОПИРОВАТЬ ТЕКСТ<br>
Нажмите "📋 Копировать весь текст" в левой панели<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟪 ПЕРЕВЕСТИ (ВНИМАТЕЛЬНО! КОЛИЧЕСТВО СТРОК ПЕРЕВОДА ДОЛЖНО СТРОГО СОВПАДАТЬ С КОЛИЧЕСТВОМ СТРОК ИЗ ОКНА ОРИГИНАЛЬНОГО ТЕКСТА)<br>
-----<br>
→ Обычный переводчик (Google Translate, DeepL):<br>
Вставьте текст → переведите → скопируйте<br>
⚠️ Может перевести названия кнопок, технические термины<br>
-----<br>
<br>
→ ИИ-переводчик (ChatGPT, DeepSeek):<br>
Вставьте текст и инструкцию для ИИ:<br>
<br>
Переведи текст для игры DCS World. <br>
Количество строк должно остаться без изменений!<br>
НЕ переводи:<br>
- Названия кнопок (SPACE, ENTER, F1-F12)<br>
- Технические термины (FL, RPM, NM, Mhz)<br>
- Названия самолетов (F-16, Su-27)<br>
- Кодовые названия (Sword 2-1, Alpha)<br>
+<br>
"ТЕКСТ ПЕРЕВОДА"<br>
<br>
Получите качественный перевод с сохранением игровых терминов<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟨 ВСТАВИТЬ ПЕРЕВОД<br>
Нажмите "📋 Вставить из буфера" в правой панели<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟧 СОХРАНИТЬ<br>
Нажмите "💾 Сохранить перевод"<br>
Выберите "💾 Перезаписать файл"<br>
Активируйте параметр «Создать резервную копию»<br>
<br>
Готово!<br>
<div style="color: #666; margin: 8px 0;"></div>
<br>
<table width="100%" cellspacing="0" cellpadding="0" style="margin: 5px 20px 5px 5px;">
    <tr><td align="center" style="background-color: #ff9900; color: #000000; font-weight: bold; padding: 6px; border-radius: 4px;">🧠 ПРАВИЛЬНЫЙ СПОСОБ (С СОХРАНЕНИЕМ ОРИГИНАЛА)</td></tr>
</table>
<br>
<br>
🟩 СДЕЛАЙТЕ ВСЁ КАК В БЫСТРОМ СТАРТЕ (шаги 1-4)<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟧 СОХРАНИТЕ ПРАВИЛЬНО<br>
Нажмите "💾 Сохранить перевод"<br>
Выберите "💾 Сохранить как..."<br>
Выберите язык перевода "RU"<br>
Сохраните под тем же именем MyMission.miz<br>
<br>
📂 ВНУТРИ ФАЙЛА ВСЕ ПРИМЕНИТСЯ АВТОМАТИЧЕСКИ<br>
<br>
MyMission.miz (архив)<br>
├── l10n/<br>
│   ├── DEFAULT/     ← Английский оригинал<br>
│   └── RU/          ← Ваш русский перевод<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟨 ЧТО БУДЕТ В ИГРЕ<br>
Русский игрок: ваш перевод (RU)<br>
Английский игрок: оригинал (DEFAULT)<br>
<br>
ИГРА автоматически выберет нужную папку с переводом исходя из языка своего интерфейса<br>
<div style="color: #666; margin: 8px 0;"></div>
<br>
<table width="100%" cellspacing="0" cellpadding="0" style="margin: 5px 20px 5px 5px;">
    <tr><td align="center" style="background-color: #ff9900; color: #000000; font-weight: bold; padding: 6px; border-radius: 4px;">🌍 ЕСЛИ ХОТИТЕ СДЕЛАТЬ НЕСКОЛЬКО ЯЗЫКОВ</td></tr>
</table>
<br>
<br>
Русский перевод → сохранить в RU<br>
Немецкий перевод → сохранить в DE<br>
Французский перевод → сохранить в FR<br>
<br>
📊 ВСЕ ЯЗЫКИ В ОДНОМ .MIZ ФАЙЛЕ!<br>
<br>
ВСЁ ПРОСТО: Открыл → Перевел → Сохранил в RU папку → Готово! 🎮🌍<br>
<div style="color: #666; margin: 8px 0;"></div>
<br>
<table width="100%" cellspacing="0" cellpadding="0" style="margin: 5px 20px 5px 5px;">
    <tr><td align="center" style="background-color: #ff9900; color: #000000; font-weight: bold; padding: 6px; border-radius: 4px;">РАБОТА С ФАЙЛАМИ КАМПАНИЙ (.cmp)</td></tr>
</table>
<div style="color: #666; margin: 8px 0;"></div>

<br>
Текстовый перевод файлов кампаний (.cmp) почти ничем не отличается от перевода миссий.<br>
При открытии файла кампании вы увидите в окне оригинального текста все возможные варианты локализации.<br>
Количество строк для перевода отдельного описания кампании будет таким же, как и у описания по умолчанию,<br>
поэтому вы без труда сможете перевести текст (сохраняя количество строк) и подставить его под нужный вам ключ локализации (description_RU, description_DE и другие).<br>
Если вы хотите изменить картинки, включите отображение всех ключей (ориентируйтесь на [picture_RU], [picture_DE] и другие).<br>
<div style="color: #666; margin: 8px 0;"></div>
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

Вот текст для перевода:"""
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
            'highlight_empty_label': 'Highlight input fields',
            'highlight_color_label': 'Highlight color',
            'enable_logs_label': 'Enable logs',
            'preview_font_family_label': 'Bottom window text font',
            'preview_font_size_label': 'Font size',
            'reference_locale_label': 'Reference locale',
            'settings_skip_locale_dialog': 'Skip locale selection window',
            'settings_default_open_locale': 'Set default locale when opening file:',
            'settings_multi_window_mode': 'Multi-window mode',
        
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
        'open_btn': 'Open',
        
        # Сообщения об ошибках
        'error_title': 'Error',
        'file_not_found': 'File not found',
        'file_read_error': 'File read error',
        'file_save_error': 'File save error',
        'miz_error': 'Mission file error',
        'error_miz_save': 'Error saving .miz file: {error}',
        'error_truncated_header': 'Save error: truncated ZIP header. The file may be corrupted or in use by another application.',
        'error_no_lines_found': 'No lines found for translation with selected filters',
        'error_no_lines_found_miz': 'No lines found for translation with selected filters in dictionary file',
        'miz_select_folder_title': 'Select localization folder',
        'miz_select_folder_desc': '(If unsure, select DEFAULT)',
        'miz_save_folder_title': 'Select your translation language',
        'miz_save_folder_desc': '(If unsure, select "DEFAULT")',
        'localization_label': 'localization:',
        'show_all_keys_label': 'Show all keys',
        'btn_radio': 'Radio',
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
        'fm_col_actions': 'Actions',
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
        'fm_btn_batch_export': '🡇 Save Selected',
        'fm_btn_batch_replace': '⟲ Replace Selected',
        'fm_menu_rename': 'Rename',
        'fm_menu_show_in_editor': 'Show in Editor',
        'fm_replace_suffix_title': 'Replacement Prefix & Suffix',
        'fm_replace_suffix_label': 'Suffix (added AFTER name):',
        'fm_br_prefix_label': 'Prefix (added BEFORE name):',
        'fm_batch_replace_success': 'Successfully replaced {count} of {total} files{path}',
        'fm_shift_selection_hint': '💡 Hold Shift to select a range',
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


        # Audio Player
        'audio_player_title': 'Audio Player',
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
        'tooltip_add_context': 'Adds context to the beginning of the translation for the AI translator',
        'tooltip_default_context': 'Default Context',
        'tooltip_multi_window_mode': 'Enable to allow opening multiple instances of the program. If disabled, new files will open in the current window.',
        'audio_replace_help_tooltip': 'Alternative replacement method: drag a file from File Explorer onto the name of the current audio file in the main window.',
        'about_title': 'Program Information',
        'about_text': 'DCS Translation TOOL v{version}\n\nA tool for translating text in DCS World missions.\nWorks with dictionary files and .miz archives.\nFree and will remain so.\n\nSource code and feedback:\nGitHub: https://github.com/Hokum-A/dcs-translation-tool\n\nSupport the project:\nBoosty: https://boosty.to/hokuma\nUSDT TRC20: TKLcwmrNmwXFgwbpS66UnAGsB3Lvnqpwv5\n\nDeveloper: Hokum (Andrey Varlamov)\nLicense: MIT License\n\nThank you for using this tool.',
        'exit_btn': 'Back',
        'ok_btn': 'OK',
        
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
        'search_matches': 'Matches: {count}',
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
        'instruction_content': """<div style="font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; line-height: 1.4;">
<div style="text-align: center; color: #777;">----------------------------------</div>
<div style="text-align: center; color: #ff9900; font-weight: bold;">DCS World MISSION TRANSLATION GUIDE</div>
<div style="text-align: center; color: #777;">----------------------------------</div>
<br>
<table width="100%" cellspacing="0" cellpadding="0" style="margin: 5px 20px 5px 5px;">
    <tr><td align="center" style="background-color: #ff9900; color: #000000; font-weight: bold; padding: 6px; border-radius: 4px;">🚀 QUICK START (FOR PERSONAL USE)</td></tr>
</table>
<br>
<br>
🟩 OPEN MISSION FILE<br>
Click "📂 Open mission file (.miz)" → select MyMission.miz<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟦 COPY TEXT<br>
Click "📋 Copy all text" in the left panel<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟪 TRANSLATE (ATTENTION! THE NUMBER OF LINES IN THE TRANSLATION MUST STRICTLY MATCH THE NUMBER OF LINES IN THE ORIGINAL TEXT WINDOW)<br>
-----<br>
→ Regular translator (Google Translate, DeepL):<br>
Paste text → translate → copy back<br>
⚠️ May translate button names, technical terms<br>
-----<br>
<br>
→ AI translator (ChatGPT, DeepSeek):<br>
Paste text and instructions for AI:<br>
<br>
Translate this text for DCS World game.<br>
The number of lines must remain unchanged!<br>
DO NOT translate:<br>
- Button names (SPACE, ENTER, F1-F12)<br>
- Technical terms (FL, RPM, NM, Mhz)<br>
- Aircraft names (F-16, Su-27)<br>
- Callsigns (Sword 2-1, Alpha)<br>
+<br>
"TRANSLATION TEXT"<br>
<br>
Get quality translation with preserved game terms<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟨 PASTE TRANSLATION<br>
Click "📋 Paste from clipboard" in the right panel<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟧 SAVE<br>
Click "💾 Save translation"<br>
Select "💾 Overwrite file"<br>
Enable the “Create backup” option<br>
<br>
Done!<br>
<div style="color: #666; margin: 8px 0;"></div>
<br>
<table width="100%" cellspacing="0" cellpadding="0" style="margin: 5px 20px 5px 5px;">
    <tr><td align="center" style="background-color: #ff9900; color: #000000; font-weight: bold; padding: 6px; border-radius: 4px;">🧠 PROPER METHOD (WITH ORIGINAL PRESERVED)</td></tr>
</table>
<br>
<br>
🟩 FOLLOW QUICK START (steps 1-4)<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟧 SAVE PROPERLY<br>
Click "💾 Save translation"<br>
Select "💾 Save as..."<br>
Choose translation language "DE"<br>
Save with the same name MyMission.miz<br>
<br>
📂 EVERYTHING WILL BE APPLIED AUTOMATICALLY INSIDE THE FILE<br>
<br>
MyMission.miz (archive)<br>
├── l10n/<br>
│   ├── DEFAULT/     ← English original<br>
│   └── DE/          ← Your translation<br>
<div style="color: #666; margin: 8px 0;">__________</div>
<br>
🟨 WHAT HAPPENS IN GAME<br>
German player: your translation (DE)<br>
English player: original (DEFAULT)<br>
<br>
THE GAME will automatically select the appropriate translation folder based on its interface language<br>
<div style="color: #666; margin: 8px 0;"></div>
<br>
<table width="100%" cellspacing="0" cellpadding="0" style="margin: 5px 20px 5px 5px;">
    <tr><td align="center" style="background-color: #ff9900; color: #000000; font-weight: bold; padding: 6px; border-radius: 4px;">🌍 IF YOU WANT MULTIPLE LANGUAGES</td></tr>
</table>
<br>
<br>
German translation → save to DE<br>
French translation → save to FR<br>
<br>
📊 ALL LANGUAGES IN ONE .MIZ FILE!<br>
<br>
IT'S SIMPLE: Open → Translate → Save to DE folder → Done! 🎮🌍<br>
<div style="color: #666; margin: 8px 0;"></div>
<br>
<table width="100%" cellspacing="0" cellpadding="0" style="margin: 5px 20px 5px 5px;">
    <tr><td align="center" style="background-color: #ff9900; color: #000000; font-weight: bold; padding: 6px; border-radius: 4px;">WORKING WITH CAMPAIGN FILES (.cmp)</td></tr>
</table>
<div style="color: #666; margin: 8px 0;"></div>
<br>
Text-based translation of campaign files (.cmp) is almost no different from mission translation.<br>
When opening a campaign file, you will see all available localization variants in the original text window.<br>
The number of lines for translating a single campaign description will be the same as in the default description,<br>
so you can easily translate the text (while preserving the number of lines) and assign it to the localization key you need (description_RU, description_DE, and others).<br>
If you want to change images, enable the display of all keys (refer to [picture_RU], [picture_DE], and others).<br>
<div style="color: #666; margin: 8px 0;"></div>
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

Here is the text to translate:"""
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