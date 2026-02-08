# DCS Translation Tool v1.02 - Changelog / Список изменений

## [RU] Русский
### Основные изменения:
- **📦 Поддержка кампаний (.cmp)**: Полная поддержка открытия, перевода и сохранения файлов кампаний DCS (.cmp). Теперь вы можете переводить целые кампании так же легко, как и миссии.
- **Визуальный комфорт**: Добавлено чередование фона строк (светлее/темнее) в основном окне перевода для улучшения читаемости.
- **Интеллектуальный контекст**: 
    - Добавлена поддержка 14 языков: **EN, RU, CN, CS, DE, ES, FR, JP, KO, IT, PL, PT, TR, UK**.
    - Шаблоны инструкций для ИИ вынесены во внешний файл `Context.py`.
    - Добавлен стильный выпадающий список для быстрого переключения между языковыми шаблонами.
- **Стабильность интерфейса**:
    - Список языков теперь всегда открывается строго вниз.
    - Исправлено «дёрганье» окна: перетаскивание диалогов теперь блокируется при нажатии на кнопки, списки и поля ввода.
- **Надежность**: При отсутствии файла настроек программа автоматически использует актуальные шаблоны из `Context.py`.

---

## [EN] English
### Key Changes:
- **📦 Campaign Support (.cmp)**: Full support for opening, translating, and saving DCS campaign files (.cmp). You can now translate entire campaigns as easily as missions.
- **Visual Comfort**: Added alternating row backgrounds in the main translation window for improved readability.
- **Smart Context**:
    - Added support for 14 languages: **EN, RU, CN, CS, DE, ES, FR, JP, KO, IT, PL, PT, TR, UK**.
    - AI instruction templates moved to an external `Context.py` file.
    - Added a stylish dropdown for quick switching between language templates.
- **Interface Stability**:
    - The language dropdown now strictly opens downwards.
    - Fixed window "jittering": dialog dragging is now disabled when interacting with buttons, dropdowns, and input fields.
- **Reliability**: If the settings file is missing, the program automatically uses the latest templates from `Context.py`.