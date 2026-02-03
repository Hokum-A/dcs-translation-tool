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
        'status_file_saved': '✅ Файл сохранен: {filename}',
        'status_translation_updated': 'Перевод обновлен',
        'status_translation_cleared': '✅ Весь перевод очищен',
        'status_copied_lines': '✅ Скопировано {count} строк',
        'status_pasted': '✅ Текст вставлен из буфера обмена',
        'status_default_filters': '✅ Установлены фильтры по умолчанию',
        
        # Кнопки и меню
        'open_file_btn': '📂 Открыть файл (dictionary, .txt)',
        'open_miz_btn': '📂 Открыть файл миссии (.miz)',
        'save_file_btn': '💾 Сохранить перевод…',
        'copy_all_btn': '📋 Копировать весь текст',
        'show_keys_btn': '🔑 Показать/скрыть ключи',
        'paste_btn': '📋 Вставить из буфера',
        'clear_btn': '🗑️ Очистить перевод',
        'default_filters_btn': 'Фильтры по умолчанию',
        'view_log_btn': '📋 Просмотреть лог ошибок',
        
        # Заголовки групп
        'filters_group': 'Фильтры ключей для перевода:',
        'preview_group': 'Предварительный просмотр перевода:',
        
        # Метки
        'original_text_label': 'Оригинальный текст:',
        'translation_label': 'Перевод:',
        'additional_keys_label': 'Дополнительные ключи:',
        'skip_empty_label': 'Пропускать пустые строки',
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
        
        # Диалоги сохранения
        'save_dialog_title': 'Сохранение миссии .miz',
        'save_dialog_info': 'Выберите способ сохранения переведенной миссии:',
        'overwrite_btn': '💾 Перезаписать файл',
        'miz_backup_label': 'Создать резервную копию',
        'save_as_btn': '💾 Сохранить как…',
        'save_txt_separately_btn': '💾 Сохранить отдельно в .txt…',
        'cancel_btn': 'Отмена',
        
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
        'save_btn': 'Сохранить как…',
        'open_btn': 'Открыть',
        'show_all_keys_label': 'Показывать все ключи',
        'miz_executing': 'Выполняется',
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
        'about_title': 'Информация о программе',
        'about_text': 'DCS Translation TOOL v1.0\n\nИнструмент для перевода текста в миссиях DCS World.\nРаботает с файлами dictionary и архивами .miz.\nБесплатен и будет оставаться таким.\n\nИсходный код и обратная связь:\nGitHub: https://github.com/Hokum-A/dcs-translation-tool\n\nПоддержать проект:\nBoosty: https://boosty.to/hokuma\nUSDT TRC20: TKLcwmrNmwXFgwbpS66UnAGsB3Lvnqpwv5\n\nРазработчик: Hokum (Андрей Варламов)\nЛицензия: MIT License\n\nСпасибо, что используете этот инструмент.',
        'exit_btn': 'НАЗАД',
        'ok_btn': 'ОК',
        
        # Дополнительные элементы интерфейса
        'skip_empty_label': 'Пропускать пустые строки',
        'additional_keys_label': 'Дополнительные ключи:',
        'original_text_label': 'Оригинальный текст:',
        'translation_label': 'Перевод:',
        'not_translated': '[не переведено]',
        'preview_info': 'Показано {count} строк',
        'stats_lines': 'Строк для перевода: {count}',
        'stats_to_translate': 'Строк для перевода: {count}',
        'stats_translated': 'Переведено: {count}',
        'stats_not_translated': 'Не переведено: {count}',
        'english_count_label': '{count} строк',
        'russian_count_label': '{filled}/{total} заполнено',
        
        # Метки файлов
        'file_label': 'Файл:',
        'mission_label': 'Миссия:',
        'mission_file_label': 'Файл миссии:',
        
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
        
        # Контекст ИИ
        'add_context_label': 'Добавить контекст',
        'tooltip_add_context': 'Добавляет контекст в начало перевода для ИИ переводчика',
        'ai_context_mgmt_btn': 'Управление контекстом для ИИ',
        'instructions_btn': '📖 Инструкция по переводу',
        'instruction_content': """----------------------------------
ИНСТРУКЦИЯ ПО ПЕРЕВОДУ МИССИЙ DCS
----------------------------------

🚀 БЫСТРЫЙ СТАРТ (ДЛЯ СЕБЯ)

🟩 ОТКРЫТЬ ФАЙЛ МИССИИ
Нажмите "📂 Открыть файл миссии (.miz)" → выберите MyMission.miz

__________

🟦 СКОПИРОВАТЬ ТЕКСТ
Нажмите "📋 Копировать весь текст" в левой панели

__________

🟪 ПЕРЕВЕСТИ (ВНИМАТЕЛЬНО!)
-----
→ Обычный переводчик (Google Translate, DeepL):

Вставьте текст → переведите → скопируйте

⚠️ Может перевести названия кнопок, технические термины
-----

-----
→ ИИ-переводчик (ChatGPT, DeepSeek):

Вставьте текст и инструкцию для ИИ:


Переведи текст для игры DCS World. 
Количество строк должно остаться без изменений!
НЕ переводи:
- Названия кнопок (SPACE, ENTER, F1-F12)
- Технические термины (FL, RPM, NM, Mhz)
- Названия самолетов (F-16, Su-27)
- Кодовые названия (Sword 2-1, Alpha)
+
"ТЕКСТ ПЕРЕВОДА"
-----

Получите качественный перевод с сохранением игровых терминов

__________

🟨 ВСТАВИТЬ ПЕРЕВОД
Нажмите "📋 Вставить из буфера" в правой панели

__________

🟧 СОХРАНИТЬ
Нажмите "💾 Сохранить перевод"

Выберите "💾 Перезаписать файл"

Активируйте параметр «Создать резервную копию»

Готово!

========================================

🧠 ПРАВИЛЬНЫЙ СПОСОБ (С СОХРАНЕНИЕМ ОРИГИНАЛА)

🟩 СДЕЛАЙТЕ ВСЁ КАК В БЫСТРОМ СТАРТЕ (шаги 1-4)

__________

🟧 СОХРАНИТЕ ПРАВИЛЬНО
Нажмите "💾 Сохранить перевод"

Выберите "💾 Сохранить как..."

Выберите язык перевода "RU"

Сохраните под тем же именем MyMission.miz

📂 ВНУТРИ ФАЙЛА ВСЕ ПРИМЕНИТСЯ АВТОМАТИЧЕСКИ

MyMission.miz (архив)
├── l10n/
│   ├── DEFAULT/     ← Английский оригинал
│   └── RU/          ← Ваш русский перевод

__________

🟨 ЧТО БУДЕТ В ИГРЕ
Русский игрок: ваш перевод (RU)

Английский игрок: оригинал (DEFAULT)

ИГРА автоматически выберет нужную папку с переводом исходя из языка своего интерфейса

========================================

🌍 ЕСЛИ ХОТИТЕ СДЕЛАТЬ НЕСКОЛЬКО ЯЗЫКОВ
Русский перевод → сохранить в RU

Немецкий перевод → сохранить в DE

Французский перевод → сохранить в FR

📊 ВСЕ ЯЗЫКИ В ОДНОМ .MIZ ФАЙЛЕ!

ВСЁ ПРОСТО: Открыл → Перевел → Сохранил в RU папку → Готово! 🎮🌍
========================================

PS: Вы также можете выполнить быстрый перевод описания кампании (с заменой языка по умолчанию — для себя), открыв файл кампании с расширением .cmp в папке кампании. Используйте стандартные фильтры ключей.

========================================"""
,
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
Перевести текст на МОЙ ЯЗЫК максимально точно, без художественных вольностей.

ОБЯЗАТЕЛЬНО:
- Сохраняй количество строк 1 в 1
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
        'open_file_btn': '📂 Open file (dictionary, .txt)',
        'open_miz_btn': '📂 Open mission file (.miz)',
        'save_file_btn': '💾 Save translation…',
        'copy_all_btn': '📋 Copy all text',
        'show_keys_btn': '🔑 Show/hide keys',
        'paste_btn': '📋 Paste from clipboard',
        'clear_btn': '🗑️ Clear translation',
        'default_filters_btn': 'Default filters',
        'view_log_btn': '📋 View error log',
        
        # Заголовки групп
        'filters_group': 'Key filters for translation:',
        'preview_group': 'Translation preview:',
        
        # Метки
        'original_text_label': 'Original text:',
        'translation_label': 'Translation:',
        'additional_keys_label': 'Additional keys:',
        'skip_empty_label': 'Skip empty lines',
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
        
        # Диалоги сохранения
        'save_dialog_title': 'Mission .miz file save',
        'save_dialog_info': 'Choose how to save the translated mission:',
        'overwrite_btn': '💾 Overwrite file',
        'miz_backup_label': 'Create backup',
        'save_as_btn': '💾 Save as…',
        'save_txt_separately_btn': '💾 Save separately to .txt…',
        'cancel_btn': 'Cancel',
        
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
        'save_btn': 'Save As…',
        'open_btn': 'Open',
        'show_all_keys_label': 'Show all keys',
        'miz_executing': 'Executing',
        'error_utf8_read': 'Unable to read file in UTF-8 encoding.',
        'error_utf8_convert': 'Please try to convert the file to UTF-8.',
        'error_bad_zip': 'File {filename} is not a valid ZIP archive or is corrupted.',
        'error_details': 'Details: {details}',
        'error_title_encoding': 'Encoding Error',
        
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
        'about_title': 'Program Information',
        'about_text': 'DCS Translation TOOL v1.0\n\nA tool for translating text in DCS World missions.\nWorks with dictionary files and .miz archives.\nFree and will remain so.\n\nSource code and feedback:\nGitHub: https://github.com/Hokum-A/dcs-translation-tool\n\nSupport the project:\nBoosty: https://boosty.to/hokuma\nUSDT TRC20: TKLcwmrNmwXFgwbpS66UnAGsB3Lvnqpwv5\n\nDeveloper: Hokum (Andrey Varlamov)\nLicense: MIT License\n\nThank you for using this tool.',
        'exit_btn': 'BACK',
        'ok_btn': 'OK',
        
        # Дополнительные элементы интерфейса
        'skip_empty_label': 'Skip empty lines',
        'additional_keys_label': 'Additional keys:',
        'original_text_label': 'Original text:',
        'translation_label': 'Translation:',
        'not_translated': '[not translated]',
        'preview_info': 'Showing {count} lines',
        'stats_lines': 'Lines to translate: {count}',
        'stats_to_translate': 'Lines to translate: {count}',
        'stats_translated': 'Translated: {count}',
        'stats_not_translated': 'Not translated: {count}',
        'english_count_label': '{count} lines',
        'russian_count_label': '{filled}/{total} filled',
        
        # Метки файлов
        'file_label': 'File:',
        'mission_label': 'Mission:',
        'mission_file_label': 'Mission file:',
        
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
        
        # AI Context
        'add_context_label': 'Add context',
        'tooltip_add_context': 'Adds context to the beginning of the translation for the AI translator',
        'ai_context_mgmt_btn': 'AI Context Management',
        'instructions_btn': '📖 Translation Instructions',
        'instruction_content': """----------------------------------
DCS MISSION TRANSLATION GUIDE
----------------------------------

🚀 QUICK START (FOR PERSONAL USE)

🟩 OPEN MISSION FILE
Click "📂 Open mission file (.miz)" → select MyMission.miz

__________

🟦 COPY TEXT
Click "📋 Copy all text" in the left panel

__________

🟪 TRANSLATE (CAREFULLY!)
-----
→ Regular translator (Google Translate, DeepL):

Paste text → translate → copy back

⚠️ May translate button names, technical terms
-----

-----
→ AI translator (ChatGPT, DeepSeek):

Paste text and instructions for AI:


Translate this text for DCS World game.
The number of lines must remain unchanged!
DO NOT translate:
- Button names (SPACE, ENTER, F1-F12)
- Technical terms (FL, RPM, NM, Mhz)
- Aircraft names (F-16, Su-27)
- Callsigns (Sword 2-1, Alpha)
+
"TRANSLATION TEXT"
-----

Get quality translation with preserved game terms

__________

🟨 PASTE TRANSLATION
Click "📋 Paste from clipboard" in the right panel

__________

🟧 SAVE
Click "💾 Save translation"

Select "💾 Overwrite file"

Enable the “Create backup” option

Done!

========================================

🧠 PROPER METHOD (WITH ORIGINAL PRESERVED)

🟩 FOLLOW QUICK START (steps 1-4)

__________

🟧 SAVE PROPERLY
Click "💾 Save translation"

Select "💾 Save as..."

Choose translation language "DE"

Save with the same name MyMission.miz

📂 EVERYTHING WILL BE APPLIED AUTOMATICALLY INSIDE THE FILE

MyMission.miz (archive)
├── l10n/
│   ├── DEFAULT/     ← English original
│   └── DE/          ← Your translation

__________

🟨 WHAT HAPPENS IN GAME
German player: your translation (DE)

English player: original (DEFAULT)

THE GAME will automatically select the appropriate translation folder based on its interface language

========================================

🌍 IF YOU WANT MULTIPLE LANGUAGES

German translation → save to DE

French translation → save to FR

📊 ALL LANGUAGES IN ONE .MIZ FILE!

IT'S SIMPLE: Open → Translate → Save to DE folder → Done! 🎮🌍
========================================

PS: You can also quickly translate the campaign description (by replacing the default language for your own use) by opening the campaign file with the .cmp extension in the campaign folder. Use the standard key filters.

========================================"""
,
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
Translate the text into MY LANGUAGE as accurately as possible, without creative rewriting.

MANDATORY:
- Preserve the exact number of lines (1:1)
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