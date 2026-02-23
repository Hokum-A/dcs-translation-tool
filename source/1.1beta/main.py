# -*- coding: utf-8 -*-
import sys
import os
import re
import traceback
import json
import time
import logging
import zipfile
import shutil
import copy
import pygame
from datetime import datetime

"""
=== ОСНОВНАЯ ИНФОРМАЦИЯ ===
• Программа для перевода файлов dictionary DCS World
• Версия: 1.0 (добавлена поддержка .miz файлов)
• Автор: разработано с помощью ChatGPT
• Лицензия: открытый код для модификации

=== КЛЮЧЕВЫЕ ОСОБЕННОСТИ (ВАЖНО!) ===
1. ФИЛЬТРАЦИЯ: 4 стандартных ключа (ActionText, ActionRadioText, description, subtitle) 
   + 3 пользовательских фильтры (чекбокс + поле ввода)
   
2. Важный момент - синтаксис: 
    Правило 1: слеш-кавычка (\") так игра записывает в файл dictionary кавычки (пример - the \"Objective\" part в коде означает the "Objective" part в игре)
    Правило 2: Если строка закончится на слеш-кавычка-запятая(\",) это вызовет зависание игры при чтении файла, поэтому игра делает перенос кавычки-запятой на другую строку (строка1:текст(слеш) строка2:(кавычка-запятая))
     Правило 3: Строка не может заканчиваться на слеш-пробел (\\ ) вызывает зависание игры
    Правило 4: слеш в тексте в игре обозначается как два слеша подряд в коде(\\)
    Правило 5(самое главное!!): Структура файла с переносом строк после парсинга в файл должна остаться как в оригинале, это аксиома. Если в исходном коде была многострочная строка она обязательно должна остаться такой в коде после сохранения!!!
   
3. СОХРАНЕНИЕ НАСТРОЕК:
   • Файл: translation_tool_settings.json
   • Сохраняет все фильтры между запусками
   • Автоматическая загрузка/сохраниение
   
4. ИНТЕРФЕЙС v1.3:
   • Тёмная тема интерфейса (фон, панели, группы, текстовые окна)
   • Toggle-переключатели вместо стандартных чекбоксов
   • Hover-эффекты для всех кнопок
   • Оранжевые акцентные элементы синхронизированы
   • Уменьшенные toggle-переключатели с правильной анимации

5. ПОДДЕРЖКА .MIZ ФАЙЛОВ v1.02:
   • Открытие .miz архивов и автоматическое извлечение dictionary
   • Безопасное сохранение обратно в архив без изменения структуры
   • 3 варианта сохранения: перезапись, сохранение как, сохранить .txt отдельно
   • Предложение о создании резервных копий
   • Тёмная тема с оранжевой рамкой для всех всплывающих окон

=== СИСТЕМА МАРКЕРОВ [SECTION_NAME] ===
Для добавления/изменения кода используй маркеры:
• [IMPORTS] - импорты библиотеки
• [VERSION_INFO] - информация о версиях
• [MAIN_CLASS] - основной класс TranslationApp
• [UI_SETUP] - настройка интерфейса
• [SETTINGS_METHODS] - работа с настройками
• [FILE_PARSING] - парсинг файлов
• [FILTER_METHODS] - фильтрация строк
• [DISPLAY_METHODS] - обновление отображения
• [TEXT_PROCESSING] - unescape_string(), escape_string()
• [CLIPBOARD_METHODS] - работа с буфером обмена
• [PREVIEW_METHODS] - предварительный просмотр
• [SAVE_METHODS] - сохранение файлов
• [HELPER_METHODS] - вспомогательные функции
• [EVENT_HANDLERS] - обработчики событий
• [MAIN_FUNCTION] - функция main()

=== ИСТОРИЯ ВЕРСИЙ ===

v1.0 - Добавлена поддержка .miz файлов миссий DCS, исправлена замена файлов в архивах
v1.02 - Выбор папки при перезаписи, исправление LRM, динамическая версия

=== ВАЖНЫЕ ПРИНЦИПЫ ===
• Обратная совместимость: не ломать существующие функции
• Слеши: сохранять как есть, не дублировать
• Настройки: всегда сохранять/загружать корректно
• Интерфейс: не менять расположение ключевых элементов без команд разработчика
• .miz архивы: не изменять структуру сжатия, только заменять dictionary
================================================================================
"""

# [IMPORTS]
import re
import sys
import json
import os
import zipfile
import shutil

def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсу, работает в dev и в PyInstaller """
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTextEdit, QPushButton, QFileDialog,
                             QLabel, QMessageBox, QSplitter, QGroupBox,
                             QScrollArea, QFrame, QPlainTextEdit, QLineEdit,
                             QSizePolicy, QDialog, QToolTip, QGridLayout, QComboBox, QProgressBar, QTextBrowser)

# QScrollBar будет импортирован из widgets

# Импорты для локализации
from localization import get_translation
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QRect, QEasingCurve, QPoint, pyqtProperty, QEvent, QUrl
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette, QPainter, QBrush, QPixmap, QPen, QMovie, QPainterPath, QRegion, QDesktopServices, QFontInfo, QFontMetrics, QIcon, QTextCharFormat, QTextFormat
from PyQt5.QtCore import QRectF

# Импорты модулей
from widgets import (LineNumberArea, NumberedTextEdit, CustomScrollBar,
                    ToggleSwitch, LanguageToggleSwitch, CustomToolTip, ClickableLine, ClickableLabel, CustomImageButton, PreviewTextEdit)
from dialogs import (CustomDialog, MizFolderDialog, MizSaveAsDialog,
                    MizProgressDialog, AboutWindow, InstructionsWindow, AIContextWindow, DeleteConfirmDialog, AudioPlayerDialog, FilesWindow)
from error_logger import ErrorLogger
from version import VersionInfo
from parser import LuaDictionaryParser
from parserCMP import CampaignParser
from Context import AI_CONTEXTS
from miz_resources import MizResourceManager

class LineWidget(QWidget):
    """Виджет для рисования тонкой оранжевой линии"""
    def paintEvent(self, a0):
        painter = QPainter(self)
        # Настройка пера: оранжевый цвет, ширина 0.5 для идеальной тонкости
        pen = QPen(QColor("#ff9900"))
        pen.setWidthF(0.5)
        painter.setPen(pen)
        # Отключаем антиалиасинг для четкой линии в 1 пиксель
        painter.setRenderHint(QPainter.Antialiasing, False)
        # Рисуем линию от левого до правого края виджета
        painter.drawLine(0, 0, self.width(), 0)

# [MAIN_CLASS]
class TranslationApp(QMainWindow):
    """Основной класс приложения DCS Translation Tool"""
    
    def __init__(self):
        super().__init__()
        
        # === Инициализация логирования ===
        self.log_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'preview_split_merge.log'
        )
        # Создаём файл лога с очисткой (перезаписываем при каждом запуске)
        try:
            open(self.log_file_path, 'w', encoding='utf-8').close()
        except Exception:
            pass
        
        self.last_focused_preview_info = None
        
        # Инициализация данных
        self.current_file_path = None
        self.current_miz_path = None  # Новый атрибут для хранения пути к .miz файлу
        self.current_miz_folder = "DEFAULT"  # Текущая папка локализации в .miz
        self.miz_trans_memory = {} # Память переводов: {locale: [lines]}
        self.current_miz_l10n_folders = [] # Список доступных локалей
        self.is_switching_locale = False # Флаг переключения
        self.miz_resource_manager = MizResourceManager() # Менеджер ресурсов миссии (аудио, картинки)
        self.audio_player = None # Атрибут для синглтон-окна аудиоплеера
        self.audio_labels_map = {} # key -> ClickableLabel для обновления имени файла
        self.active_audio_key = None # Текущий выбранный аудиофайл (для подсветки рамкой)
        # Быстрое фоновое воспроизведение в превью
        self.quick_audio_buttons = {}  # key -> play QPushButton
        self.warning_icons_map = {}  # key -> warning icon label
        self.quick_playing_key = None
        self.quick_paused = False
        # Timer to monitor quick audio playback and reset buttons when finished
        try:
            self.quick_audio_timer = QTimer(self)
            self.quick_audio_timer.timeout.connect(self._check_quick_audio)
            self.quick_audio_timer.start(200)
        except Exception:
            self.quick_audio_timer = None
        # Preview button style templates (base values)
        # Original big buttons were ~40; current preview baseline we'll scale further by 30%
        # New base size = 40 * 0.7 * 0.7 ≈ 20 (approx 30% smaller from previous)
        self.preview_btn_size = 20
        self.preview_play_font = 16
        self.preview_stop_font = 14
        # Vertical offsets (adjust these numbers to nudge icons up/down)
        self.preview_play_top_offset = -2
        self.preview_stop_top_offset = 0

        self.preview_btn_base = """
QPushButton {{
    background-color: transparent;
    color: #ffffff;
    border: none;
    font-family: 'Segoe UI Symbol', Consolas, 'Segoe UI', sans-serif;
    font-weight: bold;
    font-size: {size}px;
    min-width: {w}px;
    min-height: {w}px;
    max-width: {w}px;
    max-height: {w}px;
    padding-top: {top}px;
    text-align: center;
}}
QPushButton:hover {{
    color: #ff9900;
}}
"""

        # Precompute styles using offsets (callers will update these if offsets change)
        self.preview_play_style = self.preview_btn_base.format(size=self.preview_play_font, w=self.preview_btn_size, top=self.preview_play_top_offset)
        self.preview_pause_style = self.preview_play_style
        self.preview_stop_style = self.preview_btn_base.format(size=self.preview_stop_font, w=self.preview_btn_size, top=self.preview_stop_top_offset)
        
        # Инциализация аудио
        self.audio_volume = 50 # Громкость по умолчанию (0-100)
        try:
            try:
                pygame.mixer.quit() # На всякий случай
                pygame.mixer.init(44100, -16, 2, 2048)
            except:
                pygame.mixer.init()
        except Exception as e:
            print(f"DEBUG: Ошибка инициализации миксера: {e}")
        
        # Поиск
        self.search_matches = []     # Индексы найденных строк
        self.search_match_types = [] # Типы совпадений: 'text' или 'audio'
        self.current_match_index = -1 # Текущий индекс в search_matches
        self.highlighted_audio_key = None  # Ключ файла, выделенного в поиске
        self.STANDARD_LOCALES = ["DEFAULT", "RU", "EN", "FR", "DE", "CN", "CS", "ES", "IT", "JP", "KO"]
        self.original_lines = []
        self.all_lines_data = []
        self.extra_translation_lines = [] # Строки буфера, выходящие за пределы оригинала
        self.filter_empty = True
        self.filter_empty_keys = True  # Новый: пропускать полностью пустые ключи
        # Настройки подсветки пустых полей (по умолчанию - ВКЛ и цвет #434343)
        self.highlight_empty_fields = True
        self.highlight_empty_color = '#434343'
        self.debug_logs_enabled = True  # Включение логирования по умолчанию
        self.is_updating_display = False
        self.is_preview_updating = False  # Флаг для предотвращения наложения отрисовок
        self.is_updating_from_preview = False # Флаг для синхронизации предпросмотра
        self.prevent_text_changed = False
        
        # Настройки темы (цвета зебры) — значения по умолчанию встроены в программу
        # Визуально первая строка (index 0) использует `theme_bg_even` — поэтому
        # для нечётных строк (1,3,...) задаём '#393939', для чётных — '#2f2f2f'
        self.theme_bg_even = '#393939'
        self.theme_bg_odd = '#2f2f2f'
        
        self.settings_file = "translation_tool_settings.json"
        self.preview_update_timer = None
        
        # [DEBOUNCE_SYNC] Таймер и очередь для синхронизации ИЗ предпросмотра В редактор
        self.preview_sync_timer = QTimer()
        self.preview_sync_timer.setSingleShot(True)
        self.preview_sync_timer.setInterval(100) # 100 ms задержки (уменьшено по запросу UI)
        self.preview_sync_timer.timeout.connect(self.apply_pending_preview_sync)
        self.pending_sync_edits = {} # {index: text}
        self.logo_pixmap_original = None
        self.is_resizing = False  # Флаг для отслеживания изменения размера
        self.current_language = 'ru'  # По умолчанию русский язык
        self.is_active = True      # Флаг активности окна
        
        # Инциализация кастомного тултипа (без родителя для стабильности на Windows)
        from widgets import CustomToolTip
        self.custom_tooltip = CustomToolTip()
        
        # Запоминание последних папок
        self.last_open_folder = ''  # Последняя папка для открытия файлов
        self.last_save_folder = ''  # Последняя папка для сохранения файлов
        self.last_audio_folder = '' # Последняя папка для выбора аудиофайлов на замену
        
        # Настройки контекста ИИ
        self.add_context = True    # Добавлять контекст по умолчанию
        self.ai_context_1 = AI_CONTEXTS.get('RU', get_translation(self.current_language, 'default_context_text')) 
        self.ai_context_2 = ""     # Дополнительный контекст ИИ
        self.ai_context_lang_1 = "RU" # Сохраненный язык шаблона

        # Настройки фильтров
        self.show_all_keys = False  # Показывать все ключи (по умолчанию выключено)
        self.sync_scroll = False    # Синхронизация прокрутки (по умолчанию выключено)
        self._is_syncing = False    # Флаг для предотвращения рекурсии при синхронизации
        self.preview_title_offset = 23 # Смещение заголовка предпросмотра (в пикселях вниз)
        self.has_unsaved_changes = False # Флаг несохраненных изменений

        # Пользовательские фильтры (3 штуки)
        self.custom_filters = []

        # Парсер dictionary (новый)
        self.dictionary_parser = LuaDictionaryParser()
        self.campaign_parser = CampaignParser()

        # Reference locale для превью (загружается с диска, read-only)
        from reference_loader import ReferenceLoader
        self.reference_locale = 'DEFAULT'
        self.reference_loader = ReferenceLoader()
        self.reference_data = {}  # key -> [parts...]
        
        # Флаг для защиты только что вставленных пустых строк от удаления фильтром
        self.suppress_empty_filter_for_indices = set()

        # Вывод информации о версии
        VersionInfo.print_version()
        # Инициализация UI и загрузка настроек выполняется один раз здесь
        try:
            self.init_ui()
        except Exception:
            pass
        try:
            self.load_settings()
        except Exception:
            pass
        try:
            self.center_on_screen()
        except Exception:
            pass
        
    @property
    def reference_locale(self):
        return getattr(self, '_reference_locale', 'DEFAULT')

    @reference_locale.setter
    def reference_locale(self, value):
        try:
            self._reference_locale = value
        except Exception:
            self._reference_locale = value
        # Обновляем заголовки предпросмотра сразу при изменении
        try:
            self.update_preview_header_texts()
        except Exception:
            pass
        # Примечание: не инициализируем UI и не перезагружаем настройки тут,
        # чтобы избежать рекурсивных вызовов при загрузке настроек.

    
    # [INITIALIZATION]
    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle(f'DCS Translation Tool v{VersionInfo.CURRENT}')
        self.setGeometry(100, 100, 1400, 1200)

        # Установка иконки приложения
        icon_path = resource_path("DSCTT.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Убираем стандартный заголовок окна Windows
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Устанавливаем атрибут для устранения моргания при изменении размера
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent)  # Добавлено для уменьшения моргания
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Делаем центральный виджет прозрачным — фон окна рисуется в paintEvent
        central_widget.setStyleSheet("background-color: transparent; border: none;")
        
        # Настройка всех компонентов UI
        self.setup_ui_components(main_layout)
        # Гарантированно обновляем шапку предпросмотра и убираем заголовок группы
        try:
            if hasattr(self, 'preview_group'):
                try:
                    self.preview_group.setTitle("")
                except Exception:
                    pass
            # Обновим тексты шапки (включая reference/editor локали)
            self.update_preview_header_texts()
        except Exception:
            pass
        
        # Устанавливаем eventFilter для перетаскивания окна
        central_widget.installEventFilter(self)
        central_widget.setMouseTracking(True)
        
        # Подключение сигналов
        self.translated_text_all.textChanged.connect(self.on_translation_changed)

        # Батчевая отрисовка предпросмотра для производительности
        self.preview_groups_queue = []
        # Маппинг key -> group_widget для селективного апдейта превью
        self.preview_key_to_group_widget = {}
        self.preview_batch_timer = QTimer(self)
        self.preview_batch_timer.timeout.connect(self.render_preview_batch)
        
        # Debounce для предпросмотра (иначе тяжело перерисовывать на каждый символ)
        self.preview_update_timer = QTimer(self)
        self.preview_update_timer.setSingleShot(True)
        self.preview_update_timer.timeout.connect(self.update_preview)
        
        # Таймер для отложенного обновления после ресайза
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.finish_resize)
        
        # Debounce для применения фильтров (чтобы пустые строки скрывались "сами" через паузу)
        self.filter_debounce_timer = QTimer(self)
        self.filter_debounce_timer.setSingleShot(True)
        # При авто-фильтрации по таймеру используем инкрементальное обновление
        self.filter_debounce_timer.timeout.connect(lambda: self.apply_filters(full_rebuild=False))
        
        # Статусная строка с цветом #3d4256
        self.statusBar().setStyleSheet('''
            QStatusBar {
                background-color: #3d4256;
                color: #ffffff;
                border: none;
                padding: 2px 5px;
            }
            QStatusBar::item {
                border: none;
            }
        ''')
        self.statusBar().showMessage(get_translation(self.current_language, 'status_ready'))
        
        # Атрибуты для перетаскивания окна
        self.drag_position = QPoint()
        self.dragging = False
        
        # Центрируем окно на экране
        self.center_on_screen()

    def center_on_screen(self):
        """Перемещает главное окно по центру доступного экрана"""
        try:
            screen = QApplication.primaryScreen()
            if not screen:
                return
            screen_geom = screen.availableGeometry()
            win_geom = self.frameGeometry()
            x = screen_geom.left() + (screen_geom.width() - win_geom.width()) // 2
            y = screen_geom.top() + (screen_geom.height() - win_geom.height()) // 2
            self.move(x, y)
        except Exception as e:
            ErrorLogger.log_error('CENTER', f'Не удалось центрировать окно: {e}')
    
    def paintEvent(self, event):
        """Рисует фон окна с тонкой рамкой в 1 пиксель"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        radius = 12
        
        # Рисуем основной фон
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(64, 64, 64)))  # #404040
        painter.drawRoundedRect(rect, radius, radius)
        
        # РАМКА: Рисуем тонкую статичную серую рамку в 1 пиксель по периметру
        # Используем QRectF и смещение 0.5 для четкости цвета.
        pen = QPen(QColor(85, 85, 85), 1) # #555555
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(
            QRectF(0.5, 0.5, rect.width() - 1, rect.height() - 1), 
            radius, radius
        )
        
        super().paintEvent(event)
    
    def resizeEvent(self, event):
        """Обработка изменения размера окна для устранения моргания"""
        # Если мы еще не в процессе ресайза, отключаем обновление тяжелых виджетов
        if not self.is_resizing:
            self.is_resizing = True
            # Отключаем обновление для самых тяжелых виджетов
            self.original_text_all.setUpdatesEnabled(False)
            self.translated_text_all.setUpdatesEnabled(False)
            self.preview_content.setUpdatesEnabled(False)
        
        # Перезапускаем таймер (отложенное обновление)
        self.resize_timer.start(400)  # Изменено на 400мс после последнего изменения размера
        
        # Вызываем базовый обработчик
        super().resizeEvent(event)
        
        # При ресайзе обновляем логотип
        if hasattr(self, 'logo_pixmap_original') and self.logo_pixmap_original is not None:
            self._update_logo_pixmap()

        # Расширение полосы в реальном времени при увеличении окна
        if event.oldSize().width() > 0 and self.width() > event.oldSize().width():
            # Обновляем геометрию абсолютной линии
            self._update_line_geometry()
    
    def finish_resize(self):
        """Завершение изменения размера - включаем обновление виджетов"""
        if self.is_resizing:
            self.is_resizing = False
            # Включаем обновление для виджетов
            self.original_text_all.setUpdatesEnabled(True)
            self.translated_text_all.setUpdatesEnabled(True)
            self.preview_content.setUpdatesEnabled(True)
            
            # Принудительное обновление
            self.original_text_all.update()
            self.translated_text_all.update()
            self.preview_content.update()
            
            # Обновляем стили рамок после изменения размера
            self.update_border_styles()
            
            # Обновляем геометрию линии
            self._update_line_geometry()

            # Обновляем позицию и размер всей центральной панели (заголовок)
            self._update_title_position()
    
    def _update_title_position(self):
        """Обновляет позицию заголовка с абсолютным позиционированием"""
        if not hasattr(self, 'center_panel'):
            return
            
        # Вычисляем ширину контейнера заголовка
        self.center_panel.adjustSize()
        title_width = self.center_panel.sizeHint().width()
        title_height = self.center_panel.sizeHint().height()
        
        # Вычисляем центр окна
        window_center_x = self.width() // 2
        title_x = window_center_x - title_width // 2
        title_y = self.title_vertical_offset
        
        # Устанавливаем абсолютную позицию заголовка
        self.center_panel.setGeometry(title_x, title_y, title_width, title_height)
        
        self.center_panel.raise_()  # Помещаем поверх всех элементов
    
    def update_border_styles(self):
        """Обновляет стили рамок для текстовых полей при изменении размера"""
        # Оригинальный текст
        original_style = '''
            QPlainTextEdit {
                color: #ffffff;
                background-color: #505050;
                border: 2px solid #777;
                border-radius: 6px;
            }
            QPlainTextEdit:focus {
                border: 2px solid #ff9900;
                border-radius: 6px;
            }
            QPlainTextEdit::selection {
                background-color: #ff9900;
                color: #000000;
            }
        '''
        self.original_text_all.setStyleSheet(original_style)
        
        # Переведенный текст
        translated_style = '''
            QPlainTextEdit {
                color: #ffffff;
                background-color: #505050;
                border: 2px solid #777;
                border-radius: 6px;
            }
            QPlainTextEdit:focus {
                border: 2px solid #ff9900;
                border-radius: 6px;
            }
            QPlainTextEdit::selection {
                background-color: #ff9900;
                color: #000000;
            }
        '''
        self.translated_text_all.setStyleSheet(translated_style)
        
        # Предпросмотр
        preview_style = '''
            background-color: #505050; 
            border: 1px solid #777; 
            border-radius: 6px;
        '''
        self.preview_content.setStyleSheet(preview_style)
    
    def changeEvent(self, event):
        """Отслеживает изменение состояния окна (фокус/активность) для смены цвета рамки"""
        if event.type() == QEvent.ActivationChange:
            self.is_active = self.isActiveWindow()
            self.update() # Принудительно перерисовываем рамку
        super().changeEvent(event)

    def mousePressEvent(self, event):
        """Обработка нажатия мыши для перетаскивания окна"""
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.pos()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Обработка движения мыши для перетаскивания окна"""
        if self.dragging and (event.buttons() & Qt.LeftButton or event.buttons() & Qt.RightButton):
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Обработка отпускания кнопки мыши"""
        if event.button() == Qt.LeftButton or event.button() == Qt.RightButton:
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    # [LOGGING_HELPERS]
    def _log_to_file(self, message):
        """Логирует сообщение в файл лога с временной меткой."""
        try:
            if not hasattr(self, 'log_file_path'):
                return
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            log_entry = f"[{timestamp}] {message}\n"
            
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass  # Предотвращаем ошибки логирования, чтобы не сломать программу
    
    # [UI_SETUP]
    def setup_ui_components(self, main_layout):
        """Настройка всех компонентов пользовательского интерфейса"""
        
        # 1. Верхняя панель с кнопками управления файлами
        self.setup_top_panel(main_layout)
        
        # 2. Строка фильтров и инструментов (Горизонтально!)
        filter_row_container = QWidget()
        filter_row_layout = QHBoxLayout(filter_row_container)
        filter_row_layout.setContentsMargins(0, 0, 0, 0)
        filter_row_layout.setSpacing(2) # Уменьшили расстояние между левой и правой областью
        
        # Настройка группы фильтров (добавляется в filter_row_layout)
        self.setup_filter_group(filter_row_layout)
        
        # Настройка панели инструментов (добавляется в filter_row_layout)
        self.setup_tools_panel(filter_row_layout)
        
        # filter_row_layout.addStretch() # Убрали стрейч, чтобы панель инструментов могла растягиваться
        
        main_layout.addWidget(filter_row_container)
        
        # 3. Основная область (включает редакторы и предпросмотр с разделителем)
        self.main_vertical_splitter = QSplitter(Qt.Vertical)
        self.main_vertical_splitter.setHandleWidth(4)
        self.main_vertical_splitter.setStyleSheet("""
            QSplitter::handle:vertical {
                background-color: #505050;
                height: 4px;
            }
            QSplitter::handle:vertical:hover {
                background-color: #606060;
            }
        """)
        main_layout.addWidget(self.main_vertical_splitter, 1)
        
        # 4. Настройка содержимого для вертикального разделителя
        self.setup_translation_area(self.main_vertical_splitter)
        self.setup_preview_panel(self.main_vertical_splitter)
        
        # Устанавливаем начальные размеры
        self.main_vertical_splitter.setSizes([700, 300])

    def setup_tools_panel(self, parent_layout):
        """Настройка панели инструментов (справа от фильтров)"""
        tools_container = QFrame()
        tools_container.setObjectName("toolsPanel")
        # Стиль под стать QGroupBox фильтров, уменьшили margin-top
        tools_container.setStyleSheet("""
            QFrame#toolsPanel {
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 0px;
                background-color: #505050;
            }
        """)
        
        tools_layout = QHBoxLayout(tools_container)
        tools_layout.setContentsMargins(10, 0, 10, 0) # Минимальные отступы
        tools_layout.setSpacing(0)
        
        tools_layout.addStretch() # Прижимаем кнопки к правому краю
        
        # Кнопка Радио
        radio_icon = resource_path("radiocat2.png")
        if not os.path.exists(radio_icon):
             radio_icon = resource_path("radiocat.png") # Фолбэк
             
        self.btn_radio = CustomImageButton(radio_icon, get_translation(self.current_language, 'btn_radio'))
        self.btn_radio.clicked.connect(self.toggle_audio_player)
        tools_layout.addWidget(self.btn_radio)
        
        # Кнопка Файлы
        files_icon = resource_path("filescat.png")
        self.btn_files = CustomImageButton(files_icon, get_translation(self.current_language, 'btn_files'))
        self.btn_files.clicked.connect(self.open_files_window)
        tools_layout.addWidget(self.btn_files)
        
        # Кнопка Настройки (Options)
        options_icon = resource_path("optionscat.png")
        if not os.path.exists(options_icon):
            options_icon = resource_path("optionscat.png")
        self.btn_settings = CustomImageButton(options_icon, get_translation(self.current_language, 'settings_btn'))
        self.btn_settings.clicked.connect(self.open_settings_window)
        tools_layout.addWidget(self.btn_settings)
        
        parent_layout.addWidget(tools_container, 1) # Добавили stretch=1 чтобы растягивалось до конца

    def toggle_audio_player(self):
        """Переключает видимость окна аудиоплеера"""
        if self.audio_player and self.audio_player.isVisible():
            self.audio_player.hide()
        else:
             if not self.audio_player:
                 # Default callback для плеера без открытой миссии
                 def default_replace_callback(key, new_path):
                     pass  # File will be played locally in audio player only
                 
                 self.audio_player = AudioPlayerDialog(
                     None, 
                     "Radio", 
                     self.current_language, 
                     parent=self,
                     on_replace_callback=default_replace_callback  # Добавляем default callback
                 )
                 # Восстанавливаем позицию если она есть
                 if hasattr(self, 'saved_audio_player_pos') and self.saved_audio_player_pos:
                     self.audio_player.move(self.saved_audio_player_pos[0], self.saved_audio_player_pos[1])
             
             self.audio_player.reset_to_no_file()
             self.audio_player.show()
             self.audio_player.raise_()
             self.audio_player.activateWindow()

    def open_files_window(self):
        """Переключает видимость окна менеджера файлов (немодально)"""
        if hasattr(self, 'files_manager_window') and self.files_manager_window and self.files_manager_window.isVisible():
            self.files_manager_window.hide()
            return

        if not hasattr(self, 'files_manager_window') or self.files_manager_window is None:
            self.files_manager_window = FilesWindow(self.current_language, self)
            # Восстанавливаем позицию если она есть
            if hasattr(self, 'saved_files_window_pos') and self.saved_files_window_pos:
                self.files_manager_window.move(self.saved_files_window_pos[0], self.saved_files_window_pos[1])
        
        self.files_manager_window.show()
        self.files_manager_window.raise_()
        self.files_manager_window.activateWindow()


    def open_settings_window(self):
        """Открывает окно настроек (немодально)"""
        if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.isVisible():
            self.settings_window.hide()
            return
        # Suppress autosave while settings dialog is being created/shown to avoid partial saves
        try:
            self._suppress_settings_save = True
        except Exception:
            pass

        from dialogs import SettingsWindow

        # Always recreate the settings window to ensure fresh snapshot of current parent values
        self.settings_window = SettingsWindow(self.current_language, self)
        if hasattr(self, 'saved_settings_window_pos') and self.saved_settings_window_pos:
            try:
                self.settings_window.move(self.saved_settings_window_pos[0], self.saved_settings_window_pos[1])
            except:
                pass

        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()


    
    def setup_top_panel(self, main_layout):
        """Настройка верхней панели с кнопками управления файлами"""
        # Изменяем на QVBoxLayout, чтобы размещать элементы вертикально
        top_panel_layout = QVBoxLayout()
        top_panel_layout.setContentsMargins(5, 5, 5, 5)
        top_panel_layout.setSpacing(5)
        
        # ЛЕВАЯ ЧАСТЬ: кнопки управления файлами
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: transparent; border: none;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        
        # ГОРИЗОНТАЛЬНЫЙ КОНТЕЙНЕР для Drag.png и языкового переключателя
        drag_lang_container = QWidget()
        drag_lang_layout = QHBoxLayout(drag_lang_container)
        drag_lang_layout.setContentsMargins(0, 0, 0, 0)
        drag_lang_layout.setSpacing(5)
        
        # Drag.png в левом верхнем углу
        self.drag_label = QLabel()
        self.drag_label.setFixedSize(34, 34)
        self.drag_label.setCursor(Qt.PointingHandCursor)
        
        # Загружаем PNG из папки с программой
        png_path = resource_path("Drag.png")
        if os.path.exists(png_path):
            self.drag_pixmap = QPixmap(png_path)
            self.drag_label.setPixmap(self.drag_pixmap.scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Заглушка: символ U+2194
            self.drag_label.setText("↔")
            self.drag_label.setStyleSheet("""
                QLabel {
                    background-color: #505050;
                    color: #ff9900;
                    font-size: 18px;
                    font-weight: bold;
                    border: 2px solid #ff9900;
                    border-radius: 6px;
                qproperty-alignment: AlignCenter;
                }
            """)
        
        # Используем кастомные тултипы
        self.register_custom_tooltip(self.drag_label, get_translation(self.current_language, 'tooltip_drag'), side='right')
        
        drag_lang_layout.addWidget(self.drag_label)
        
        # ЯЗЫКОВОЙ ПЕРЕКЛЮЧАТЕЛЬ - справа от drag.png
        # Метка "EN" слева
        en_label = QLabel("EN")
        en_label.setStyleSheet("color: #ffffff; font-size: 9px; font-weight: bold;")
        en_label.setFixedWidth(16)
        drag_lang_layout.addWidget(en_label)
        
        # Переключатель языков
        self.language_toggle = LanguageToggleSwitch()
        self.language_toggle.toggled.connect(self.change_language)
        # Устанавливаем начальное состояние (True = RU по умолчанию)
        self.language_toggle.setChecked(self.current_language == 'ru')
        drag_lang_layout.addWidget(self.language_toggle)
        
        # Метка "RU" справа
        ru_label = QLabel("RU")
        ru_label.setStyleSheet("color: #ffffff; font-size: 9px; font-weight: bold;")
        ru_label.setFixedWidth(16)
        drag_lang_layout.addWidget(ru_label)
        
        drag_lang_layout.addStretch()
        
        left_layout.addWidget(drag_lang_container)
        
        # Контейнер для кнопок и надписей о файлах
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)
        
        # Контейнер для первой кнопки и надписи
        open_file_container = QWidget()
        open_file_layout = QHBoxLayout(open_file_container)
        open_file_layout.setContentsMargins(0, 0, 0, 0)
        open_file_layout.setSpacing(10)
        
        # Кнопка "Открыть файл (dictionary, .txt)"
        self.open_btn = QPushButton('📂 Открыть файл (dictionary .txt .cmp)')
        self.open_btn.clicked.connect(self.open_file)
        self.open_btn.setStyleSheet('''
            QPushButton {
                background-color: #cccccc;
                color: #000000;
                border: none;
                padding: 8px 16px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #b8b8b8;
            }
            QPushButton:pressed {
                background-color: #a3a3a3;
            }
        ''')
        
        # Контейнер для меток обычного файла (Белый префикс + Оранжевое имя)
        self.selected_file_label = QWidget()
        selected_file_layout = QHBoxLayout(self.selected_file_label)
        selected_file_layout.setContentsMargins(0, 0, 0, 0)
        selected_file_layout.setSpacing(5)
        
        self.file_prefix_label = QLabel()
        self.file_prefix_label.setStyleSheet("color: white; font-weight: bold; background: transparent; border: none;")
        self.file_prefix_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.file_name_label = QLabel()
        self.file_name_label.setStyleSheet("color: #ff9900; font-weight: bold; background: transparent; border: none;")
        self.file_name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        selected_file_layout.addWidget(self.file_prefix_label)
        selected_file_layout.addWidget(self.file_name_label)
        selected_file_layout.addStretch()
        
        self.selected_file_label.setVisible(False)
        
        open_file_layout.addWidget(self.open_btn)
        open_file_layout.addWidget(self.selected_file_label)
        open_file_layout.addStretch()
        
        # Контейнер для второй кнопки и надписи
        open_miz_container = QWidget()
        open_miz_layout = QHBoxLayout(open_miz_container)
        open_miz_layout.setContentsMargins(0, 0, 0, 0)
        open_miz_layout.setSpacing(10)
        
        # Кнопка "Открыть файл миссии (.miz)"
        self.open_miz_btn = QPushButton('📂 Открыть файл миссии (.miz)')
        self.open_miz_btn.clicked.connect(self.open_miz_file)
        self.open_miz_btn.setStyleSheet('''
            QPushButton {
                background-color: #cccccc;
                color: #000000;
                border: none;
                padding: 8px 16px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #b8b8b8;
            }
            QPushButton:pressed {
                background-color: #a3a3a3;
            }
        ''')
        
        # Контейнер для меток .miz файла (Белый префикс + Оранжевое имя + Белая локализация + Оранжевая папка)
        self.selected_miz_label = QWidget()
        selected_miz_inner_layout = QHBoxLayout(self.selected_miz_label)
        selected_miz_inner_layout.setContentsMargins(0, 0, 0, 0)
        selected_miz_inner_layout.setSpacing(5)
        
        # Контейнер для "Миссия:" и названия файла для единого тултипа
        self.mission_info_container = QWidget()
        self.mission_info_container.setStyleSheet("background: transparent; border: none;")
        mission_info_layout = QHBoxLayout(self.mission_info_container)
        mission_info_layout.setContentsMargins(0, 0, 0, 0)
        mission_info_layout.setSpacing(5)

        self.mission_prefix_label = QLabel()
        self.mission_prefix_label.setStyleSheet("color: white; font-weight: bold; background: transparent; border: none;")
        
        self.mission_name_label = QLabel()
        self.mission_name_label.setStyleSheet("color: #ff9900; font-weight: bold; background: transparent; border: none;")
        
        mission_info_layout.addWidget(self.mission_prefix_label)
        mission_info_layout.addWidget(self.mission_name_label)

        self.loc_prefix_label = QLabel()
        self.loc_prefix_label.setStyleSheet("color: white; font-weight: bold; background: transparent; border: none;")
        
        self.miz_locale_combo = QComboBox()
        self.miz_locale_combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.miz_locale_combo.setStyleSheet("""
            QComboBox {
                background-color: #404040;
                color: #ff9900;
                font-weight: bold;
                border: 1px solid #777;
                border-radius: 4px;
                padding: 2px 10px;
                min-width: 50px;
                max-width: 100px;
                combobox-popup: 0;
            }
            QComboBox:focus {
                border: 1px solid #ff9900;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ff9900;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: #ffffff;
                selection-background-color: #ff9900;
                selection-color: #000000;
                border: 1px solid #ff9900;
                outline: none;
            }
        """)
        self.miz_locale_combo.setCursor(Qt.PointingHandCursor)
        self.miz_locale_combo.setMaxVisibleItems(20)
        self.miz_locale_combo.currentIndexChanged.connect(self.change_miz_locale)
        # Устанавливаем фильтр событий на VIEW комбобокса для отслеживания его скрытия (схлопывания)
        if hasattr(self.miz_locale_combo, 'view') and self.miz_locale_combo.view():
            self.miz_locale_combo.view().installEventFilter(self)
        
        selected_miz_inner_layout.addWidget(self.mission_info_container)
        selected_miz_inner_layout.addWidget(self.loc_prefix_label)
        selected_miz_inner_layout.addWidget(self.miz_locale_combo)
        
        # Кнопка удаления локали
        self.delete_locale_btn = QPushButton(get_translation(self.current_language, 'delete_locale_btn'))
        self.delete_locale_btn.setFixedSize(70, 21) # Высота 21px, ширина чуть увеличена для текста
        self.delete_locale_btn.setCursor(Qt.PointingHandCursor)
        self.delete_locale_btn.clicked.connect(self.confirm_delete_locale)
        self.delete_locale_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 10px;
                font-weight: bold;
                font-size: 10px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #c62828;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        selected_miz_inner_layout.addWidget(self.delete_locale_btn, 0, Qt.AlignVCenter)
        selected_miz_inner_layout.addStretch()
        
        self.selected_miz_label.setVisible(False)
        
        open_miz_layout.addWidget(self.open_miz_btn)
        open_miz_layout.addWidget(self.selected_miz_label)
        open_miz_layout.addStretch()
        
        # Кнопка "Сохранить перевод"
        self.save_file_btn = QPushButton('💾 Сохранить перевод')
        self.save_file_btn.clicked.connect(self.save_file)
        self.save_file_btn.setEnabled(False)
        self.save_file_btn.setStyleSheet('''
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 8px 16px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        ''')
        
        # Добавляем контейнеры в layout
        buttons_layout.addWidget(open_file_container)
        buttons_layout.addWidget(open_miz_container)
        buttons_layout.addWidget(self.save_file_btn)
        
        # Подгоняем размеры кнопок для одинаковой ширины
        button_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        # Фиксируем высоту, чтобы все кнопки выглядели одинаково (скруглённые)
        for button in [self.open_btn, self.open_miz_btn, self.save_file_btn]:
            button.setFixedHeight(36)
            button.setSizePolicy(button_policy)
        
        font_metrics = self.open_btn.fontMetrics()
        open_text_width = font_metrics.horizontalAdvance('📂 Открыть файл(dictionary, .txt)') + 32
        miz_text_width = font_metrics.horizontalAdvance('📂 Открыть файл миссии (.miz)') + 32
        save_text_width = font_metrics.horizontalAdvance('💾 Сохранить перевод') + 32
        max_width = max(open_text_width, miz_text_width, save_text_width)
        
        # Увеличиваем минимальную ширину для стабильного размера при переключении языков
        min_button_width = 280  # Увеличено с 250 для учета английского текста
        for button in [self.open_btn, self.open_miz_btn, self.save_file_btn]:
            button.setMinimumWidth(min_button_width)
            button.setMaximumWidth(min_button_width)  # Делаем максимум равным минимуму для фиксации
        
        # Сохраняем ширину для использования при переключении языков
        self.button_fixed_width = min_button_width
        
        left_layout.addWidget(buttons_container)
        left_layout.addStretch()
        
        # ПРАВАЯ ЧАСТЬ: кнопка выхода, логотип и статистика
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: transparent; border: none;")
        right_panel.setMinimumWidth(280)  # Гарантируем место для кнопок 260px + отступы
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)
        right_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)

        # Кнопка выхода над логотипом
        self.exit_container = QWidget()
        self.exit_container.setStyleSheet("background-color: transparent; border: none;")
        self.exit_container.setFixedSize(147, 33)  # 97 + 50 = 147
        exit_layout = QHBoxLayout(self.exit_container)
        exit_layout.setContentsMargins(0, 0, 0, 0)
        exit_layout.setSpacing(0)
        
        # Левая часть (EXIT.png) - изначально пустая, появится только при наведении
        self.exit_left_label = QLabel()
        self.exit_left_label.setFixedSize(97, 33)
        self.exit_left_label.setStyleSheet("background-color: transparent;")
        # Отключаем события мыши для левой части
        self.exit_left_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        # Правая часть (кнопка Exit1.png/Exit2.png) - кликабельная часть
        self.exit_right_label = QLabel()
        self.exit_right_label.setFixedSize(50, 33)
        self.exit_right_label.setCursor(Qt.PointingHandCursor)
        
        # Загружаем изображения для кнопки выхода
        exit1_path = resource_path("Exit1.png")
        exit2_path = resource_path("Exit2.png")
        exit_gif_path = resource_path("EXIT.gif")
        
        # Правая кнопка (Exit1.png)
        if os.path.exists(exit1_path):
            self.exit1_pixmap = QPixmap(exit1_path)
            self.exit_right_label.setPixmap(self.exit1_pixmap)
            self.exit_right_label.setScaledContents(True)
        
        if os.path.exists(exit2_path):
            self.exit2_pixmap = QPixmap(exit2_path)
            
        # Настройка GIF анимации (EXIT.gif)
        if os.path.exists(exit_gif_path):
            self.exit_movie = QMovie(exit_gif_path)
            # Отключаем зацикливание, если оно прописано в файле
            self.exit_movie.setCacheMode(QMovie.CacheAll)
            self.exit_left_label.setMovie(self.exit_movie)
            # Переходим к первому кадру и останавливаемся
            if self.exit_movie.jumpToFrame(0):
                self.exit_movie.stop()
        
        exit_layout.addWidget(self.exit_left_label)
        exit_layout.addWidget(self.exit_right_label)
        
        # Обработчики событий только для правой части кнопки
        self.exit_right_label.installEventFilter(self)
        
        right_layout.addWidget(self.exit_container, 0, Qt.AlignRight)
        
        # Логотип (прижат к верхнему правому углу)
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.logo_label.setStyleSheet("background-color: transparent; border: none; margin-top: 3px; padding: 0;")
        
        # Загружаем логотип из папки с программой (если есть)
        logo_path = resource_path("DCSTT_logo.png")
        if os.path.exists(logo_path):
            self.logo_pixmap_original = QPixmap(logo_path)
        else:
            # Если файла нет — просто не показываем логотип
            self.logo_label.setVisible(False)
        
        # Делаем логотип кликабельным и добавляем тултип
        self.logo_label.setCursor(Qt.PointingHandCursor)
        self.logo_label.installEventFilter(self)
        self.register_custom_tooltip(self.logo_label, get_translation(self.current_language, 'tooltip_about_program'), side='left')
        
        right_layout.addWidget(self.logo_label, 0, Qt.AlignRight)
        
        # Кнопки под логотипом
        right_buttons_container = QWidget()
        right_buttons_container.setStyleSheet("background-color: transparent; border: none;")
        right_buttons_layout = QVBoxLayout(right_buttons_container)
        right_buttons_layout.setContentsMargins(0, 10, 0, 0)
        right_buttons_layout.setSpacing(8)
        right_buttons_layout.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        
        # Кнопка "Инструкции"
        self.instructions_btn = QPushButton(get_translation(self.current_language, 'instructions_btn'))
        self.instructions_btn.setCursor(Qt.PointingHandCursor)
        self.instructions_btn.clicked.connect(self.show_instructions)
        self.instructions_btn.setStyleSheet('''
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 6px 12px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        ''')
        
        # Кнопка "Управление контекстом для ИИ"
        self.ai_context_mgmt_btn = QPushButton(get_translation(self.current_language, 'ai_context_mgmt_btn'))
        self.ai_context_mgmt_btn.setCursor(Qt.PointingHandCursor)
        self.ai_context_mgmt_btn.clicked.connect(self.show_ai_context_window)
        self.ai_context_mgmt_btn.setStyleSheet('''
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 6px 12px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        ''')
        
        # Устанавливаем ширину кнопок (фиксированная для предотвращения сжатия)
        self.instructions_btn_width = 215 # <--- ШИРИНА КНОПКИ "ИНСТРУКЦИЯ"
        self.ai_context_btn_width = 215   # <--- ШИРИНА КНОПКИ "КОНТЕКСТ"
        
        self.instructions_btn.setFixedWidth(self.instructions_btn_width)
        self.ai_context_mgmt_btn.setFixedWidth(self.ai_context_btn_width)
        
        right_buttons_layout.addStretch()
        right_buttons_layout.addWidget(self.instructions_btn, 0, Qt.AlignRight)
        right_buttons_layout.addWidget(self.ai_context_mgmt_btn, 0, Qt.AlignRight)
        
        right_layout.addWidget(right_buttons_container, 0, Qt.AlignRight)
        right_layout.addStretch()
        
        # ЦЕНТРАЛЬНАЯ ПАНЕЛЬ: заголовок "DCS Translation TOOL v1.01" - АБСОЛЮТНОЕ ПОЗИЦИОНИРОВАНИЕ
        self.center_panel = QWidget(self)
        self.center_panel.setAttribute(Qt.WA_TranslucentBackground)
        
        # Параметр для настройки вертикальной позиции (меняйте это значение!)
        self.title_vertical_offset = 21  # <-- МЕНЯЙТЕ ЭТО ЧИСЛО ДЛЯ ВЕРТИКАЛЬНОЙ ПОЗИЦИИ
        
        center_layout = QVBoxLayout(self.center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(3)
        center_layout.setAlignment(Qt.AlignCenter)
        
        # Контейнер для текста заголовка
        title_container = QWidget()
        title_container.setStyleSheet('background-color: transparent; border: none;')
        title_container_layout = QHBoxLayout(title_container)
        title_container_layout.setContentsMargins(0, 0, 0, 0)
        title_container_layout.setSpacing(3)
        
        # Список шрифтов в порядке приоритета для использования
        font_list = ['Sylfaen', 'Segoe UI', 'Arial', 'Calibri', 'Times New Roman']
        
        # "DCS Translation TOOL"
        app_title = QLabel('DCS Translation TOOL')
        app_title.setStyleSheet('''
            color: #ff9900;
            font-size: 18px;
            font-weight: bold;
            background-color: transparent;
            border: none;
        ''')
        # Используем первый доступный шрифт из списка
        app_font = QFont()
        for font_name in font_list:
            app_font = QFont(font_name, 18)
            app_font.setStyleHint(QFont.SansSerif)
            if QFontInfo(app_font).family() == font_name:
                break
        app_title.setFont(app_font)
        
        # Версия программы - берется из VersionInfo.CURRENT
        version_title = QLabel(f'v{VersionInfo.CURRENT}')
        version_title.setStyleSheet('''
            color: #cccccc;
            font-size: 12px;
            font-weight: bold;
            background-color: transparent;
            border: none;
        ''')
        # Используем первый доступный шрифт из списка
        version_font = QFont()
        for font_name in font_list:
            version_font = QFont(font_name, 12)
            version_font.setStyleHint(QFont.SansSerif)
            if QFontInfo(version_font).family() == font_name:
                break
        version_title.setFont(version_font)
        # Выравниваем по нижней линии
        version_title.setAlignment(Qt.AlignBottom)
        
        title_container_layout.addWidget(app_title)
        title_container_layout.addWidget(version_title)
        
        # Центрируем контейнер
        title_layout_center = QHBoxLayout()
        title_layout_center.addStretch()
        title_layout_center.addWidget(title_container)
        title_layout_center.addStretch()
        
        center_layout.addLayout(title_layout_center)
        
        # [LINE_WIDGET_REPLACEMENT]
        # Создаем новый виджет линии с абсолютным позиционированием
        self.abs_separator = LineWidget(self)
        self.abs_separator.setAttribute(Qt.WA_TranslucentBackground)
        self.abs_separator.setFixedHeight(2)  # Высота виджета для рисования
        
        # Параметры линии (меняйте эти значения для настройки)
        self.line_vertical_offset = 48  # Вертикальная позиция линии (y-координата)
        self.line_side_margin = 15      # Отступ линии от краев окна (с обеих сторон)
        
        # Инициализация позиции заголовка и линии
        self._update_title_position()
        self._update_line_geometry()
        
        # Нижняя строка - кнопки (слева) и right_panel (справа)
        bottom_row_layout = QHBoxLayout()
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.setSpacing(10)
        
        bottom_row_layout.addWidget(left_panel)
        bottom_row_layout.addStretch()
        bottom_row_layout.addWidget(right_panel)
        
        # Добавляем только нижнюю строку в top_panel_layout
        top_panel_layout.addLayout(bottom_row_layout)
        
        main_layout.addLayout(top_panel_layout)
        
        # Только после создания всех виджетов обновляем логотип
        self._update_logo_pixmap()
        
        # Обновляем позицию заголовка (абсолютное позиционирование)
        self._update_title_position()
        self._update_line_geometry()

    def _update_line_geometry(self):
        """Обновляет геометрию абсолютной линии"""
        if hasattr(self, 'abs_separator'):
            line_width = self.width() - (self.line_side_margin * 2)
            self.abs_separator.setGeometry(self.line_side_margin, self.line_vertical_offset, line_width, 2)
            self.abs_separator.lower() # Линия всегда под всеми кнопками
            self.abs_separator.update()
    
    def _update_logo_pixmap(self):
        """Обновляет масштаб логотипа (только уменьшение, без апскейла)"""
        # Проверяем, существуют ли необходимые атрибуты
        if not hasattr(self, 'logo_label'):
            return
            
        if self.logo_pixmap_original is None or self.logo_pixmap_original.isNull():
            self.logo_label.setVisible(False)
            return

        # Ширина примерно как у надписи "Строк для перевода: ..."
        target_text = "Строк для перевода: 000"
        font_metrics = self.logo_label.fontMetrics()
        target_width = max(140, font_metrics.horizontalAdvance(target_text))

        # Не увеличиваем картинку выше её исходной ширины
        width = min(target_width, self.logo_pixmap_original.width())
        scaled = self.logo_pixmap_original.scaledToWidth(width, Qt.SmoothTransformation)

        self.logo_label.setPixmap(scaled)
        # Устанавливаем ширину точно по картинке, а высоту с запасом для margin-top
        # Это предотвращает обрезку нижней части логотипа при смещении вниз
        self.logo_label.setFixedSize(scaled.width(), scaled.height() + 3) 
        self.logo_label.setVisible(True)
    
    def eventFilter(self, obj, event):
        """Глобальный обработчик событий (exit button, slash warning tooltip и подавление пустых системных тултипов)"""
        # Подавляем системные тултипы, у которых нет текста — это устраняет чёрную полосу
        if event.type() == QEvent.ToolTip:
            try:
                tip = obj.toolTip() if hasattr(obj, 'toolTip') else None
                if not tip or not str(tip).strip():
                    return True
            except Exception:
                return True

        # Обработка зарегистрированных виджетов с кастомными тултипами
        if hasattr(self, '_custom_tooltip_map') and obj in self._custom_tooltip_map:
            try:
                data = self._custom_tooltip_map[obj]
                text = data['text'] if isinstance(data, dict) else data
                side = data['side'] if isinstance(data, dict) else 'bottom'
                
                if event.type() == QEvent.Enter:
                    if text:
                        self.custom_tooltip.show_tooltip(text, obj, side)
                    return False
                elif event.type() == QEvent.Leave:
                    if hasattr(self, 'custom_tooltip'):
                        self.custom_tooltip.hide()
                    return False
                elif event.type() == QEvent.MouseMove:
                    if hasattr(self, 'custom_tooltip') and self.custom_tooltip.isVisible():
                        self.custom_tooltip.show_tooltip(text, obj, side)
                    return False
            except Exception:
                return False

        if hasattr(self, 'exit_right_label') and obj == self.exit_right_label:
            if event.type() == QEvent.Enter:
                # При наведении: меняем изображение на Exit2.png и запускаем анимацию
                if hasattr(self, 'exit2_pixmap'):
                    self.exit_right_label.setPixmap(self.exit2_pixmap)
                if hasattr(self, 'exit_movie'):
                    self.exit_movie.start()
                # Принудительно поднимаем контейнер, чтобы исключить перекрытие
                self.exit_container.raise_()
                return True
            elif event.type() == QEvent.Leave:
                # При уходе: возвращаем Exit1.png и сбрасываем гифку в начало (кадр 0)
                if hasattr(self, 'exit1_pixmap'):
                    self.exit_right_label.setPixmap(self.exit1_pixmap)
                if hasattr(self, 'exit_movie'):
                    self.exit_movie.stop()
                    self.exit_movie.jumpToFrame(0)
                return True
            elif event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    # Закрываем программу
                    self.close()
                    return True
        
        # Обработка закрытия (схлопывания) выпадающего списка локалей
        if hasattr(self, 'miz_locale_combo') and obj == self.miz_locale_combo.view():
            if event.type() == QEvent.Hide:
                def reset_combo_if_needed():
                    # ПРОВЕРКИ SAFETY: не сбрасываем, если:
                    # 1. Идет активное переключение локали
                    # 2. Мы как раз сейчас раскрываем плюс
                    # 3. Список ВИДИМ (значит showPopup() сработал сразу после Hide)
                    if not getattr(self, 'is_switching_locale', False) and \
                       not getattr(self, 'is_expanding_plus', False) and \
                       not self.miz_locale_combo.view().isVisible():
                       
                        has_plus = False
                        for i in range(self.miz_locale_combo.count()):
                            if self.miz_locale_combo.itemText(i).startswith("+"):
                                has_plus = True
                                break
                        if has_plus:
                            print("DEBUG: Resetting locale combo to compact mode after hide")
                            self.update_miz_locale_combo(show_all=False)
                QTimer.singleShot(150, reset_combo_if_needed)

        # Обработка клика по логотипу — открытие окна "О программе"
        if hasattr(self, 'logo_label') and obj == self.logo_label:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.show_about_window()
                    return True

        # Обработка поиска (выделение при клике и Esc для очистки)
        if hasattr(self, 'search_input') and obj == self.search_input:
            if event.type() == QEvent.FocusIn:
                # Выделяем весь текст при получении фокуса (удобно для быстрой замены)
                QTimer.singleShot(0, self.search_input.selectAll)
            elif event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Escape:
                    self.search_input.clear()
                    return True

        return super().eventFilter(obj, event)
    
    def show_about_window(self):
        """Показывает окно 'Об авторе'"""
        try:
            print("DEBUG: Opening About Window...")
            about = AboutWindow(self)
            about.exec_()
        except Exception as e:
            msg = f"Ошибка открытия окна 'О программе': {str(e)}"
            print(f"CRASH: {msg}")
            ErrorLogger.log_error("ABOUT_OPEN", msg)
            self.show_custom_dialog("Ошибка", msg, "error")

    def show_instructions(self):
        """Показывает окно инструкций"""
        try:
            dialog = InstructionsWindow(self)
            dialog.exec_()
        except Exception as e:
            ErrorLogger.log_error('UI', f'Ошибка при открытии окна инструкций: {e}')

    def show_ai_context_window(self):
        """Показывает окно управления контекстом ИИ"""
        try:
            dialog = AIContextWindow(self)
            # Передаем текущие значения контекста в окно
            dialog.context_1 = self.ai_context_1
            dialog.context_2 = self.ai_context_2
            dialog.context_lang_1 = self.ai_context_lang_1
            dialog.load_data()
            dialog.exec_()
        except Exception as e:
            ErrorLogger.log_error('UI', f'Ошибка при открытии окна контекста ИИ: {e}')

    def save_ai_context_settings(self, context_1, context_2, lang_1=None):
        """Сохраняет контекст ИИ в основные настройки приложения"""
        self.ai_context_1 = context_1
        self.ai_context_2 = context_2
        if lang_1:
            self.ai_context_lang_1 = lang_1
        # Вызываем общее сохранение настроек
        if hasattr(self, 'save_settings'):
            self.save_settings()
    
    def setup_filter_group(self, main_layout):
        """Настройка группы фильтров"""
        self.filters_group = QGroupBox(get_translation(self.current_language, 'filters_group'))
        # Уменьшили margin-top и padding-top еще сильнее
        self.filters_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 0px;
                padding-top: 5px;
                background-color: #505050;
                color: #fff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                top: 3px;
                padding: 0 10px 0 10px;
                color: #fff;
                background-color: transparent;
                border: none;
            }
        """)
        
        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(10, 20, 15, 0) 
        
        # Первая строка - стандартные фильтры с кнопкой "Фильтры по умолчанию"
        filter_row1 = QHBoxLayout()
        filter_row1.setSpacing(10)
        
        # Используем ToggleSwitch
        self.filter_action_text = ToggleSwitch()
        self.filter_action_text.setChecked(True)
        self.filter_action_text.animation.finished.connect(self.apply_filters)
        
        self.filter_action_radio = ToggleSwitch()
        self.filter_action_radio.setChecked(True)
        self.filter_action_radio.animation.finished.connect(self.apply_filters)
        
        self.filter_description = ToggleSwitch()
        self.filter_description.setChecked(True)
        self.filter_description.animation.finished.connect(self.apply_filters)
        
        self.filter_subtitle = ToggleSwitch()
        self.filter_subtitle.setChecked(True)
        self.filter_subtitle.animation.finished.connect(self.apply_filters)
        
        self.filter_sortie = ToggleSwitch()
        self.filter_sortie.setChecked(True)
        self.filter_sortie.animation.finished.connect(self.apply_filters)
        
        self.filter_name = ToggleSwitch()
        self.filter_name.setChecked(True)
        self.filter_name.animation.finished.connect(self.apply_filters)
        
        # Создаем контейнеры для переключателей с подписями
        def create_toggle_container(toggle, text):
            container = QWidget()
            container.setStyleSheet('background-color: #505050; border: none;')  # Добавили фон
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6)
            layout.addWidget(toggle)
            label = QLabel(text)
            label.setStyleSheet('''
                color: #ddd;
                background-color: #505050;  /* Изменено с transparent на #505050 */
                border: none;
                padding: 0;
            ''')
            layout.addWidget(label)
            return container, label
        
        container_at, self.label_filter_at = create_toggle_container(self.filter_action_text, "ActionText")
        container_art, self.label_filter_art = create_toggle_container(self.filter_action_radio, "ActionRadioText")
        container_desc, self.label_filter_desc = create_toggle_container(self.filter_description, "description")
        container_sub, self.label_filter_sub = create_toggle_container(self.filter_subtitle, "subtitle")
        container_sortie, self.label_filter_sortie = create_toggle_container(self.filter_sortie, "sortie")
        container_name, self.label_filter_name = create_toggle_container(self.filter_name, get_translation(self.current_language, 'filter_name'))
        
        filter_row1.addWidget(container_at)
        filter_row1.addWidget(container_art)
        filter_row1.addWidget(container_desc)
        filter_row1.addWidget(container_sub)
        filter_row1.addWidget(container_sortie)
        filter_row1.addWidget(container_name)
        
        

        # Кнопка "Фильтры по умолчанию" сразу после subtitle
        self.default_filters_btn = QPushButton('Фильтры по умолчанию')
        self.default_filters_btn.clicked.connect(self.set_default_filters)
        self.default_filters_btn.setFixedHeight(21)
        # Половина высоты кнопки 21px / 2 = 10.5, округляем в меньшую сторону = 10px
        self.default_filters_btn.setStyleSheet('''
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 2px 10px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        ''')
        
        # Вычисляем фиксированную ширину на основе русского текста
        if not hasattr(self, 'filter_btn_fixed_width'):
            font_metrics = self.default_filters_btn.fontMetrics()
            filter_btn_width = font_metrics.horizontalAdvance('Фильтры по умолчанию') + 40
            self.filter_btn_fixed_width = filter_btn_width
        
        self.default_filters_btn.setMinimumWidth(self.filter_btn_fixed_width)
        self.default_filters_btn.setMaximumWidth(self.filter_btn_fixed_width)
        

        filter_row1.addWidget(self.default_filters_btn)
        # Растяжка перед правым тогглом в первой строке, чтобы прижать его к правому краю
        filter_row1.addStretch()

        # Тоггл: Пропускать пустые ключи (справа от кнопки "Фильтры по умолчанию")
        self.filter_empty_keys_cb = ToggleSwitch()
        # состояние по умолчанию — True (включено)
        self.filter_empty_keys_cb.setChecked(getattr(self, 'filter_empty_keys', True))
        self.filter_empty_keys_cb.animation.finished.connect(self.toggle_empty_keys_filter)

        container_skip_keys, self.label_skip_empty_keys = create_toggle_container(self.filter_empty_keys_cb,
                                              get_translation(self.current_language, 'skip_empty_keys_label'))
        filter_row1.addWidget(container_skip_keys)
        
        filter_layout.addLayout(filter_row1)
        
        # Вторая строка - произвольные фильтры
        filter_row2 = QHBoxLayout()
        filter_row2.setContentsMargins(0, 0, 0, 0)
        filter_row2.setSpacing(5) # Вернули стандартный отступ 10
        filter_row2.setAlignment(Qt.AlignLeft) # Принудительное выравнивание влево

        self.additional_keys_label = QLabel(get_translation(self.current_language, 'additional_keys_label'))
        self.additional_keys_label.setStyleSheet('''
            color: #ddd;
            background-color: #505050;  /* Изменено с transparent на #505050 */
            border: none;
        ''')
        filter_row2.addWidget(self.additional_keys_label)
        
        # Создаем 3 произвольных фильтра
        self.custom_filters = []
        for i in range(3):
            custom_widget = QWidget()
            custom_widget.setStyleSheet('background-color: #505050; border: none;')  # Добавили фон
            custom_layout = QHBoxLayout(custom_widget)
            custom_layout.setContentsMargins(0, 0, 0, 0)
            custom_layout.setSpacing(6) # Вернули 6
            
            # Используем ToggleSwitch
            checkbox = ToggleSwitch()
            checkbox.setFixedSize(30, 14)
            checkbox.animation.finished.connect(self.apply_filters)
            
            line_edit = QLineEdit()
            line_edit.setFixedWidth(100)
            line_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            line_edit.setMaxLength(20)
            placeholder = get_translation(self.current_language, 'custom_filter_placeholder', index=i+1)
            line_edit.setPlaceholderText(placeholder)
            line_edit.textChanged.connect(self.apply_filters)
            line_edit.setStyleSheet('''
                QLineEdit {
                    background-color: #606060;
                    color: #ddd;
                    border: 1px solid #777;
                    border-radius: 3px;
                    padding: 2px 5px;
                }
                QLineEdit:focus {
                    border-color: #ff9900;
                }
            ''')
            
            custom_layout.addWidget(checkbox)
            custom_layout.addWidget(line_edit)
            
            self.custom_filters.append({
                'checkbox': checkbox,
                'line_edit': line_edit,
                'widget': custom_widget
            })
            custom_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            filter_row2.addWidget(custom_widget)
        
        # Переключатель "Показывать все ключи"
        self.show_all_keys_cb = ToggleSwitch()
        self.show_all_keys_cb.setChecked(getattr(self, 'show_all_keys', False))
        self.show_all_keys_cb.animation.finished.connect(self.toggle_show_all_keys)
        
        # Растяжка перед правой группой вторая строки — прижать правые тогглы к краю
        filter_row2.addStretch()
        container_all, self.label_show_all = create_toggle_container(self.show_all_keys_cb, 
                        get_translation(self.current_language, 'show_all_keys_label'))
        filter_row2.addSpacing(5) # Вернули 10
        filter_row2.addWidget(container_all)
        
        # Пропускать пустые строки (Переместили ПЕРЕД addStretch)
        filter_row2.addSpacing(5) # Вернули 15
        self.filter_empty_cb = ToggleSwitch()
        self.filter_empty_cb.setChecked(True)
        self.filter_empty_cb.animation.finished.connect(self.toggle_empty_filter)
        
        empty_container = QWidget()
        empty_container.setStyleSheet('background-color: #505050; border: none;')
        empty_layout = QHBoxLayout(empty_container)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.setSpacing(6)
        empty_layout.addWidget(self.filter_empty_cb)
        self.skip_empty_label = QLabel(get_translation(self.current_language, 'skip_empty_label'))
        self.skip_empty_label.setStyleSheet('''
            color: #ddd;
            background-color: #505050;
            border: none;
        ''')
        empty_layout.addWidget(self.skip_empty_label)
        filter_row2.addWidget(empty_container)
        filter_layout.addLayout(filter_row2)
        
        self.filters_group.setLayout(filter_layout)
        
        # [DYNAMIC_WIDTH] Ширина больше не фиксируется (930px), чтобы текст не обрезался при масштабировании.
        # Добавлен отступ справа 15px в filter_layout.setContentsMargins
        self.filters_group.setMinimumWidth(800) # Минимальная разумная ширина
        self.filters_group.setMaximumWidth(16777215) # Снимаем ограничение
        
        main_layout.addWidget(self.filters_group)
    
    def set_default_filters(self):
        """Устанавливает фильтры по умолчанию"""
        # Устанавливаем стандартные фильтры
        self.filter_action_text.setChecked(True)
        self.filter_action_radio.setChecked(True)
        self.filter_description.setChecked(True)
        self.filter_subtitle.setChecked(True)
        self.filter_sortie.setChecked(True)
        self.filter_name.setChecked(True)
        self.filter_empty_cb.setChecked(True)
        # Сбрасываем новый тоггл пропуска пустых ключей в ВКЛ
        if hasattr(self, 'filter_empty_keys_cb'):
            self.filter_empty_keys_cb.setChecked(True)
        
        # Отключаем "Показывать все ключи"
        if hasattr(self, 'show_all_keys_cb'):
            self.show_all_keys_cb.setChecked(False)
        
        # Отключаем произвольные фильтры
        for custom_filter in self.custom_filters:
            custom_filter['checkbox'].setChecked(False)
            custom_filter['line_edit'].clear()
        
        # Обновляем интерфейс
        self.filter_empty = True
        self.filter_empty_keys = True
        self.apply_filters()
        
        self.statusBar().showMessage(get_translation(self.current_language, 'status_default_filters'))
    
    def setup_translation_area(self, parent_container):
        """Настройка основной области перевода"""
        translation_frame = QFrame()
        translation_frame.setFrameShape(QFrame.StyledPanel)
        # Восстанавливаем полутемный фон для области перевода БЕЗ РАМКИ
        translation_frame.setStyleSheet("background-color: #505050; border: none;")
        translation_layout = QVBoxLayout(translation_frame)
        translation_layout.setContentsMargins(0, 0, 0, 0)
        translation_layout.setSpacing(0)
        
        # Разделитель для двух панелей (сделали атрибутом класса для сохранения размеров)
        self.pane_splitter = QSplitter(Qt.Horizontal)
        self.pane_splitter.setHandleWidth(4)
        
        # Левая панель - оригинальный текст
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)
        
        left_header = QHBoxLayout()
        self.original_text_header_label = QLabel(get_translation(self.current_language, 'original_text_label'))
        self.original_text_header_label.setStyleSheet('''
            color: #ddd; 
            font-weight: bold;
            background-color: transparent;
            border: none;
        ''')
        left_header.addWidget(self.original_text_header_label)
        self.english_count_label = QLabel('0 строк')
        self.english_count_label.setStyleSheet('''
            color: #aaa;
            background-color: transparent;
            border: none;
        ''')
        left_header.addStretch()
        left_header.addWidget(self.english_count_label)
        left_layout.addLayout(left_header)
        
        self.original_text_all = NumberedTextEdit()
        self.original_text_all.setReadOnly(True)
        
        # Добавили светло-серую рамку по умолчанию, оранжевую при фокусе
        self.original_text_all.setStyleSheet('''
            QPlainTextEdit {
                color: #ffffff;
                background-color: transparent;
                border: 2px solid #777;
                border-radius: 6px;
            }
            QPlainTextEdit:focus {
                border: 2px solid #ff9900;
                border-radius: 6px;
            }
            QPlainTextEdit::selection {
                background-color: #ff9900;
                color: #000000;
            }
            QMenu {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #777;
            }
            QMenu::item {
                padding: 4px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #ff9900;
                color: #000000;
            }
            QMenu::item:disabled {
                color: #808080;
            }
        ''')
        
        # Устанавливаем кастомный скроллбар
        self.original_text_all.setVerticalScrollBar(CustomScrollBar())
        self.original_text_all.setHorizontalScrollBar(CustomScrollBar())
        
        # Синхронизация видимости горизонтальных скроллбаров (чтобы высота вьюпортов всегда совпадала)
        self.original_text_all.horizontalScrollBar().rangeChanged.connect(self._sync_horizontal_scrollbar_visibility)
        
        left_layout.addWidget(self.original_text_all, 1)
        
        # Кнопки левой панели
        left_buttons = QHBoxLayout()
        left_buttons.setContentsMargins(0, 5, 0, 0)
        self.copy_all_btn = QPushButton('📋 Копировать весь текст')
        self.copy_all_btn.clicked.connect(self.copy_all_english)
        # Убрали tooltip для этой кнопки
        # Высота кнопки примерно 32px (padding 8px сверху/снизу + высота текста ~16px)
        # Половина высоты = 16px
        self.copy_all_btn.setStyleSheet('''
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 8px 16px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        ''')
        
        self.show_keys_btn = QPushButton('🔑 Показать/скрыть ключи')
        self.show_keys_btn.clicked.connect(self.toggle_keys_display)
        self.show_keys_btn.setCheckable(True)
        self.show_keys_btn.setStyleSheet('''
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 8px 16px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        ''')
        
        # Вычисляем фиксированные ширины на основе русского текста
        if not hasattr(self, 'copy_btn_fixed_width'):
            font_metrics = self.copy_all_btn.fontMetrics()
            copy_width = font_metrics.horizontalAdvance('📋 Копировать весь текст') + 70
            keys_width = font_metrics.horizontalAdvance('🔑 Показать/скрыть ключи') + 70
            self.copy_btn_fixed_width = copy_width
            self.keys_btn_fixed_width = keys_width
        
        self.copy_all_btn.setMinimumWidth(self.copy_btn_fixed_width)
        self.copy_all_btn.setMaximumWidth(self.copy_btn_fixed_width)
        self.show_keys_btn.setMinimumWidth(self.keys_btn_fixed_width)
        self.show_keys_btn.setMaximumWidth(self.keys_btn_fixed_width)
        
        # Тоггл "Добавить контекст"
        self.add_context_container = QWidget()
        self.add_context_container.setStyleSheet("background-color: transparent; border: none;")
        add_context_layout = QHBoxLayout(self.add_context_container)
        add_context_layout.setContentsMargins(10, 0, 0, 0)
        add_context_layout.setSpacing(6)
        
        self.add_context_toggle = ToggleSwitch()
        self.add_context_toggle.setChecked(getattr(self, 'add_context', True))
        self.add_context_toggle.toggled.connect(self.on_add_context_toggled)
        
        self.add_context_label_widget = QLabel(get_translation(self.current_language, 'add_context_label'))
        self.add_context_label_widget.setStyleSheet("color: #ddd; background-color: transparent; border: none; font-size: 11px;")
        
        add_context_layout.addWidget(self.add_context_toggle)
        add_context_layout.addWidget(self.add_context_label_widget)
        
        # Регистрируем тултип для надписи
        self.register_custom_tooltip(self.add_context_label_widget, get_translation(self.current_language, 'tooltip_add_context'))
        
        left_buttons.addWidget(self.copy_all_btn)
        left_buttons.addWidget(self.add_context_container)
        left_buttons.addStretch()
        left_buttons.addWidget(self.show_keys_btn)
        left_layout.addLayout(left_buttons)

        
        # Правая панель - перевод
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)
        
        right_header = QHBoxLayout()
        self.translation_header_label = QLabel(get_translation(self.current_language, 'translation_label'))
        self.translation_header_label.setStyleSheet('''
            color: #ddd; 
            font-weight: bold;
            background-color: transparent;
            border: none;
        ''')
        right_header.addWidget(self.translation_header_label)
        self.russian_count_label = QLabel('0 строк')
        self.russian_count_label.setStyleSheet('''
            color: #aaa;
            background-color: transparent;
            border: none;
        ''')
        right_header.addStretch()
        right_header.addWidget(self.russian_count_label)
        right_layout.addLayout(right_header)
        
        self.translated_text_all = NumberedTextEdit()
        
        # Добавили светло-серую рамку по умолчанию, оранжевую при фокусе
        self.translated_text_all.setStyleSheet('''
            QPlainTextEdit {
                color: #ffffff;
                background-color: transparent;
                border: 2px solid #777;
                border-radius: 6px;
            }
            QPlainTextEdit:focus {
                border: 2px solid #ff9900;
                border-radius: 6px;
            }
            QPlainTextEdit::selection {
                background-color: #ff9900;
                color: #000000;
            }
            QMenu {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #777;
            }
            QMenu::item {
                padding: 4px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #ff9900;
                color: #000000;
            }
            QMenu::item:disabled {
                color: #808080;
            }
        ''')
        
        # Устанавливаем кастомный скроллбар
        self.translated_text_all.setVerticalScrollBar(CustomScrollBar())
        self.translated_text_all.setHorizontalScrollBar(CustomScrollBar())
        
        # Синхронизация видимости горизонтальных скроллбаров
        self.translated_text_all.horizontalScrollBar().rangeChanged.connect(self._sync_horizontal_scrollbar_visibility)
        
        right_layout.addWidget(self.translated_text_all, 1)
        
        # Кнопки для правой панели
        right_buttons = QHBoxLayout()
        right_buttons.setContentsMargins(0, 5, 0, 0)
        self.paste_btn = QPushButton('📋 Вставить из буфера')
        self.paste_btn.clicked.connect(self.paste_from_clipboard)
        # Убрали tooltip для этой кнопки
        self.paste_btn.setStyleSheet('''
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 8px 16px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        ''')
        
        self.clear_btn = QPushButton('🗑️ Очистить перевод')
        self.clear_btn.clicked.connect(self.clear_translation)
        self.clear_btn.setStyleSheet('''
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 8px 16px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        ''')
        
        # Вычисляем фиксированные ширины на основе русского текста
        if not hasattr(self, 'paste_btn_fixed_width'):
            font_metrics = self.paste_btn.fontMetrics()
            paste_width = font_metrics.horizontalAdvance('📋 Вставить из буфера') + 70
            clear_width = font_metrics.horizontalAdvance('🗑️ Очистить перевод') + 70
            self.paste_btn_fixed_width = paste_width
            self.clear_btn_fixed_width = clear_width
        
        self.paste_btn.setMinimumWidth(self.paste_btn_fixed_width)
        self.paste_btn.setMaximumWidth(self.paste_btn_fixed_width)
        self.clear_btn.setMinimumWidth(self.clear_btn_fixed_width)
        self.clear_btn.setMaximumWidth(self.clear_btn_fixed_width)
        
        # Тоггл "Синхр. прокрутки" (ToggleSwitch + Label)
        self.sync_scroll_container = QWidget()
        self.sync_scroll_container.setStyleSheet("background-color: transparent; border: none;")
        sync_scroll_layout = QHBoxLayout(self.sync_scroll_container)
        sync_scroll_layout.setContentsMargins(10, 0, 0, 0)
        sync_scroll_layout.setSpacing(6)
        
        self.sync_scroll_toggle = ToggleSwitch()
        self.sync_scroll_toggle.setChecked(self.sync_scroll)
        self.sync_scroll_toggle.toggled.connect(self.toggle_sync_scroll)
        
        self.sync_scroll_label_widget = QLabel(get_translation(self.current_language, 'sync_scroll_label'))
        self.sync_scroll_label_widget.setStyleSheet("color: #ddd; background-color: transparent; border: none; font-size: 11px;")
        
        sync_scroll_layout.addWidget(self.sync_scroll_toggle)
        sync_scroll_layout.addWidget(self.sync_scroll_label_widget)
        
        # Регистрируем тултип только для лейбла
        self.register_custom_tooltip(self.sync_scroll_label_widget, get_translation(self.current_language, 'tooltip_sync_scroll'))
        
        right_buttons.addWidget(self.paste_btn)
        right_buttons.addWidget(self.sync_scroll_container)
        right_buttons.addStretch()
        right_buttons.addWidget(self.clear_btn)
        right_layout.addLayout(right_buttons)
        
        # Добавляем панели в разделитель
        self.pane_splitter.addWidget(left_widget)
        self.pane_splitter.addWidget(right_widget)
        self.pane_splitter.setSizes([600, 600])
        
        translation_layout.addWidget(self.pane_splitter)
        
        # Добавляем фрейм в переданный контейнер (сплиттер или лайаут)
        if isinstance(parent_container, QSplitter):
            parent_container.addWidget(translation_frame)
        else:
            parent_container.addWidget(translation_frame, 1)
    
    def setup_preview_panel(self, parent_container):
        """Настройка панели предварительного просмотра"""
        # --- Excel-like header row (always visible, outside scroll) ---
        # (создаём после preview_layout)

        self.preview_group = QGroupBox("")
        self.preview_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 0px;
                margin: 0px;
                padding: 0px;
                background-color: #505050;
                color: #fff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                top: 0px;
                padding: 0px;
                color: #fff;
                background-color: transparent;
                border: none;
            }
        """)
        preview_layout = QVBoxLayout(self.preview_group)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        headers_container = QWidget()
        headers_container.setStyleSheet('background-color: transparent; border: none;')
        self.headers_container = headers_container

        # Внутренний широкоформатный контейнер — он будет сдвигаться по X синхронно с прокруткой
        self.header_inner = QWidget(headers_container)
        self.header_inner.setStyleSheet('background-color: transparent; border: none;')
        # Начальные размеры установим позже, после создания меток, чтобы избежать обрезки текста
        self.header_inner.setFixedWidth(1600)

        header_inner_layout = QHBoxLayout(self.header_inner)
        header_inner_layout.setContentsMargins(0, 0, 0, 0)
        header_inner_layout.setSpacing(0)
        self.preview_header_layout = header_inner_layout

        # Метка 1: метаданные (локализуемая)
        self.preview_header_meta = QLabel()
        self.preview_header_meta.setStyleSheet('color: #fff; font-weight: bold; background: transparent; padding: 0px; margin: 0px; font-size: 11px;')
        self.preview_header_meta.setAlignment(Qt.AlignCenter)
        self.preview_header_meta.setFixedHeight(12)
        self.preview_header_meta.setText(get_translation(getattr(self, 'current_language', 'ru'), 'preview_header_meta'))

        # Метка 2: референсный текст — динамическая по локали (часть с локалью окрашена)
        self.preview_header_ref = QLabel()
        self.preview_header_ref.setStyleSheet('color: #fff; font-weight: bold; background: transparent; padding: 0px; margin: 0px; font-size: 11px;')
        self.preview_header_ref.setAlignment(Qt.AlignCenter)
        self.preview_header_ref.setFixedHeight(12)
        self.preview_header_ref.setTextFormat(Qt.RichText)
        ref_locale = getattr(self, 'reference_locale', 'DEFAULT')
        ref_text = get_translation(getattr(self, 'current_language', 'ru'), 'preview_header_ref', locale=f"<span style='color:#ff9900'>{ref_locale}</span>")
        self.preview_header_ref.setText(ref_text)

        # Метка 3: редактор перевода — показывает текущую редактируемую локаль (оранжевый цвет)
        self.preview_header_editor = QLabel()
        self.preview_header_editor.setStyleSheet('color: #fff; font-weight: bold; background: transparent; padding: 0px; margin: 0px; font-size: 11px;')
        self.preview_header_editor.setAlignment(Qt.AlignCenter)
        self.preview_header_editor.setFixedHeight(12)
        self.preview_header_editor.setTextFormat(Qt.RichText)
        editor_locale = (self.miz_locale_combo.currentText() if hasattr(self, 'miz_locale_combo') else getattr(self, 'current_miz_folder', ''))
        editor_text = get_translation(getattr(self, 'current_language', 'ru'), 'preview_header_editor', locale=f"<span style='color:#ff9900'>{editor_locale}</span>")
        self.preview_header_editor.setText(editor_text)

        header_inner_layout.addWidget(self.preview_header_meta)
        header_inner_layout.addWidget(self.preview_header_ref)
        header_inner_layout.addWidget(self.preview_header_editor)

        # Рассчитаем необходимую высоту по метрикам шрифта, чтобы избежать обрезки
        try:
            h_meta = self.preview_header_meta.fontMetrics().height()
            h_ref = self.preview_header_ref.fontMetrics().height()
            h_edit = self.preview_header_editor.fontMetrics().height()
            max_h = max(h_meta, h_ref, h_edit)
            # Добавим небольшой запас для безопасного отображения (спуск/подъём)
            outer_h = max_h + 0
            headers_container.setFixedHeight(outer_h)
            self.header_inner.setFixedHeight(outer_h)
        except Exception:
            # fallback — если что-то пошло не так, используем предыдущие значения
            headers_container.setFixedHeight(18)
            self.header_inner.setFixedHeight(18)

        # Добавляем внешнюю строку заголовков (фиксированную) над скроллом
        preview_layout.addWidget(headers_container)
        
        # Поле предпросмотра с прокруткой
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setFrameShape(QFrame.NoFrame)
        self.preview_scroll.setVerticalScrollBar(CustomScrollBar())
        self.preview_scroll.setHorizontalScrollBar(CustomScrollBar())
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setMinimumHeight(300)  # Увеличиваем высоту предпросмотра
        self.preview_scroll.setStyleSheet('''
            background-color: #505050; 
            border: none;
        ''')
        
        self.preview_content = QWidget()
        # Убираем все рамки и отступы
        self.preview_content.setStyleSheet('''
            background-color: #505050;
            border: none;
            margin: 0px;
            padding: 0px;
        ''')
        self.preview_layout = QVBoxLayout(self.preview_content)
        self.preview_layout.setSpacing(0)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.preview_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Создаём три невидимые колонки с QSplitter внутри preview_content
        self.preview_splitter = QSplitter(Qt.Horizontal)
        self.preview_splitter.setHandleWidth(3)  # Тонкая но удобная для перетаскивания
        # Стилизуем ручки — полностью невидимы
        self.preview_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """)

        # Колонка 1: метаданные и ключи
        meta_col = QWidget()
        meta_col.setStyleSheet('background-color: transparent; border: none;')
        self.preview_meta_layout = QVBoxLayout(meta_col)
        self.preview_meta_layout.setSpacing(0)
        self.preview_meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_col.setMinimumWidth(120)

        # Колонка 2: оригинальный текст
        orig_col = QWidget()
        orig_col.setStyleSheet('background-color: transparent; border: none;')
        self.preview_orig_layout = QVBoxLayout(orig_col)
        self.preview_orig_layout.setSpacing(0)
        self.preview_orig_layout.setContentsMargins(0, 0, 0, 0)
        orig_col.setMinimumWidth(200)

        # Колонка 3: переведённый текст
        trans_col = QWidget()
        trans_col.setStyleSheet('background-color: transparent; border: none;')
        self.preview_trans_layout = QVBoxLayout(trans_col)
        self.preview_trans_layout.setSpacing(0)
        self.preview_trans_layout.setContentsMargins(0, 0, 0, 0)
        trans_col.setMinimumWidth(200)

        # Добавляем три колонки в сплиттер
        self.preview_splitter.addWidget(meta_col)
        self.preview_splitter.addWidget(orig_col)
        self.preview_splitter.addWidget(trans_col)

        # Добавляем сплиттер в основной preview_layout
        self.preview_layout.addWidget(self.preview_splitter)
        
        self.preview_scroll.setWidget(self.preview_content)
        # Усиливаем общую рамку для всего окна предпросмотра
        self.preview_scroll.setStyleSheet('''
            QScrollArea {
                background-color: #505050; 
                border: 1px solid #777;
                border-radius: 6px;
            }
        ''')
        preview_layout.addWidget(self.preview_scroll)

        # Устанавливаем начальное распределение колонок: первая 319px, остальные пополам
        # Вызываем после добавления в лэйаут, чтобы сплиттер имел размеры
        QTimer.singleShot(100, lambda: self.preview_splitter.setSizes([319, 1000, 1000]))
        # Синхронизация ширины заголовков с размерами колонок и сдвиг по горизонтальной прокрутке
        def _update_header_widths():
            try:
                sizes = self.preview_splitter.sizes()
                labels = [self.preview_header_meta, self.preview_header_ref, self.preview_header_editor]
                for lbl, sz in zip(labels, sizes):
                    lbl.setFixedWidth(max(1, sz))
                total = sum(sizes)
                # Устанавливаем ширину внутреннего контейнера заголовков
                try:
                    self.header_inner.setFixedWidth(max(total, self.preview_scroll.viewport().width()))
                except Exception:
                    pass
            except Exception:
                pass

        try:
            self.preview_splitter.splitterMoved.connect(lambda pos, index: _update_header_widths())
            self.preview_scroll.horizontalScrollBar().valueChanged.connect(lambda v: self.header_inner.move(-v, 0))
            QTimer.singleShot(150, _update_header_widths)
        except Exception:
            pass
        
        preview_info_layout = QHBoxLayout()
        preview_info_layout.setContentsMargins(0, 5, 0, 0)
        
        self.preview_info = QLabel(get_translation(self.current_language, 'preview_info', count=0))
        self.preview_info.setStyleSheet('''
            color: #aaa;
            background-color: transparent;
            border: none;
        ''')
        
        preview_info_layout.addWidget(self.preview_info)
        
        # Отступ слева для кнопки (параметр для ручной настройки)
        BUTTON_OFFSET_LEFT = 70
        preview_info_layout.addSpacing(BUTTON_OFFSET_LEFT)
        
        # Кнопка переключения смещения эвристики (только для .miz)
        self.heuristic_toggle_btn = QPushButton(
            get_translation(self.current_language, 'heuristic_toggle_btn', offset='-1')
        )
        self.heuristic_toggle_btn.setFixedHeight(21)
        self.heuristic_toggle_btn.setStyleSheet('''
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 2px 10px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        ''')
        self.heuristic_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.heuristic_toggle_btn.clicked.connect(self.on_heuristic_toggle)
        self.heuristic_toggle_btn.setVisible(False)  # Скрыта по умолчанию
        
        # Минимальная ширина на основе текста
        font_metrics = self.heuristic_toggle_btn.fontMetrics()
        ht_btn_width = font_metrics.horizontalAdvance('Смещение: -1') + 30
        self.heuristic_toggle_btn.setMinimumWidth(ht_btn_width)
        # setMaximumWidth убрали, чтобы не сдавливало
        
        preview_info_layout.addWidget(self.heuristic_toggle_btn)
        
        # === ПОИСК ===
        self.search_label = QLabel(get_translation(self.current_language, 'search_label'))
        self.search_label.setStyleSheet("color: #cccccc; margin-left: 20px;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(get_translation(self.current_language, 'search_placeholder'))
        self.search_input.setClearButtonEnabled(True) # Кнопка очистки (X)
        self.search_input.setFixedWidth(200) # ~40 chars
        self.search_input.setStyleSheet("""
            QLineEdit {
                color: #ffffff;
                background-color: #404040;
                border: 1px solid #777;
                border-radius: 4px;
                padding: 2px 5px;
            }
            QLineEdit:focus {
                border: 1px solid #ff9900;
            }
            QMenu {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #777;
            }
            QMenu::item {
                padding: 4px 20px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: #ff9900;
                color: #000000;
            }
            QMenu::item:disabled {
                color: #808080;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.search_next)
        
        # Добавляем функции удобства: выделение при фокусе и очистка по Esc
        self.search_input.installEventFilter(self)
        # Также можно напрямую соединить сигнал для выделения всего текста
        self.search_input.selectionChanged.connect(lambda: None) # placeholder

        self.search_prev_btn = QPushButton("▲")
        self.search_prev_btn.setFixedSize(24, 24)
        self.search_prev_btn.setCursor(Qt.PointingHandCursor)
        self.search_prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                color: #ffffff;
                border: 1px solid #777;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #606060;
                border-color: #ff9900;
            }
        """)
        self.search_prev_btn.clicked.connect(self.search_prev)

        self.search_next_btn = QPushButton("▼")
        self.search_next_btn.setFixedSize(24, 24)
        self.search_next_btn.setCursor(Qt.PointingHandCursor)
        self.search_next_btn.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                color: #ffffff;
                border: 1px solid #777;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #606060;
                border-color: #ff9900;
            }
        """)
        self.search_next_btn.clicked.connect(self.search_next)

        preview_info_layout.addWidget(self.search_label)
        preview_info_layout.addWidget(self.search_input)
        preview_info_layout.addWidget(self.search_prev_btn)
        preview_info_layout.addWidget(self.search_next_btn)
        
        # Label с количеством совпадений
        matches_label_text = get_translation(self.current_language, 'search_matches', count=0)
        self.search_matches_label = QLabel(matches_label_text)
        self.search_matches_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.search_matches_label.setStyleSheet("color: #cccccc; margin-left: 10px;")
        preview_info_layout.addWidget(self.search_matches_label)

        preview_info_layout.addStretch()
        
        # Статистика строк для перевода
        initial_stats = get_translation(self.current_language, 'stats_lines', count=0)
        self.stats_label = QLabel(initial_stats)
        self.stats_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.stats_label.setStyleSheet('''
            font-weight: bold; 
            color: #27ae60;
            background-color: transparent;
            border: none;
            padding: 0;
        ''')
        self.stats_label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.stats_label.setAutoFillBackground(False)
        self.stats_label.setTextFormat(Qt.RichText)
        
        preview_info_layout.addWidget(self.stats_label)
        
        preview_layout.addLayout(preview_info_layout)
        
        # Добавляем группу предпросмотра в переданный контейнер
        if isinstance(parent_container, QSplitter):
            parent_container.addWidget(self.preview_group)
        else:
            parent_container.addWidget(self.preview_group)
    
    # [SETTINGS_METHODS]
    def load_settings(self):
        """Загружает настройки из файла"""
        if os.path.exists(self.settings_file):
            try:
                # Попробуем несколько раз загрузить JSON, возможно файл временно записывается
                settings = None
                last_exc = None
                for attempt in range(3):
                    try:
                        with open(self.settings_file, 'r', encoding='utf-8') as f:
                            settings = json.load(f)
                        last_exc = None
                        break
                    except Exception as e:
                        last_exc = e
                        time.sleep(0.05)
                if settings is None and last_exc:
                    raise last_exc
                
                # Загружаем язык
                if 'language' in settings:
                    self.current_language = settings['language']
                    if hasattr(self, 'language_toggle'):
                        self.language_toggle.setChecked(self.current_language == 'ru')
                
                # Загружаем стандартные фильтры
                if 'filter_action_text' in settings:
                    self.filter_action_text.setChecked(settings['filter_action_text'])
                if 'filter_action_radio' in settings:
                    self.filter_action_radio.setChecked(settings['filter_action_radio'])
                if 'filter_description' in settings:
                    self.filter_description.setChecked(settings['filter_description'])
                if 'filter_subtitle' in settings:
                    self.filter_subtitle.setChecked(settings['filter_subtitle'])
                if 'filter_sortie' in settings:
                    self.filter_sortie.setChecked(settings['filter_sortie'])
                if 'filter_name' in settings:
                    self.filter_name.setChecked(settings['filter_name'])
                if 'filter_empty' in settings:
                    self.filter_empty_cb.setChecked(settings['filter_empty'])
                    self.filter_empty = settings['filter_empty']
                if 'filter_empty_keys' in settings:
                    self.filter_empty_keys = settings['filter_empty_keys']
                    if hasattr(self, 'filter_empty_keys_cb'):
                        self.filter_empty_keys_cb.setChecked(self.filter_empty_keys)
                
                 # Загружаем новые настройки
                self.create_backup = settings.get('create_backup', False)
                self.show_all_keys = settings.get('show_all_keys', False)
                
                # Применяем состояние к тогглу, если он уже создан
                if hasattr(self, 'show_all_keys_cb'):
                    self.show_all_keys_cb.setChecked(self.show_all_keys)
                
                # Загружаем последние папки
                if 'last_open_folder' in settings:
                    self.last_open_folder = settings['last_open_folder']
                if 'last_save_folder' in settings:
                    self.last_save_folder = settings['last_save_folder']
                if 'last_audio_folder' in settings:
                    self.last_audio_folder = settings['last_audio_folder']
                
                # Загружаем настройку контекста
                self.add_context = settings.get('add_context', True)
                if hasattr(self, 'add_context_toggle'):
                    self.add_context_toggle.setChecked(self.add_context)

                # Загружаем сами тексты контекста
                self.ai_context_1 = settings.get('ai_context_1', AI_CONTEXTS.get('RU', get_translation(self.current_language, 'default_context_text')))
                self.ai_context_2 = settings.get('ai_context_2', "")
                self.ai_context_lang_1 = settings.get('ai_context_lang_1', "RU")
                # Загружаем произвольные фильтры
                if 'custom_filters' in settings:
                    for i, custom_data in enumerate(settings['custom_filters']):
                        if i < len(self.custom_filters):
                            self.custom_filters[i]['checkbox'].setChecked(custom_data['enabled'])
                            self.custom_filters[i]['line_edit'].setText(custom_data['text'])
                
                
                # Загружаем размеры окна
                if 'window_width' in settings and 'window_height' in settings:
                    self.resize(settings['window_width'], settings['window_height'])
                
                # Загружаем настройку синхронизации прокрутки
                self.sync_scroll = settings.get('sync_scroll', False)
                if hasattr(self, 'sync_scroll_toggle'):
                    self.sync_scroll_toggle.setChecked(self.sync_scroll)
                    self.toggle_sync_scroll()

                # Загружаем размеры сплиттеров
                if 'pane_splitter_sizes' in settings and hasattr(self, 'pane_splitter'):
                    self.pane_splitter.setSizes(settings['pane_splitter_sizes'])
                if 'main_vertical_splitter_sizes' in settings and hasattr(self, 'main_vertical_splitter'):
                    self.main_vertical_splitter.setSizes(settings['main_vertical_splitter_sizes'])

                # Загружаем настройки подсветки пустых полей
                self.highlight_empty_fields = settings.get('highlight_empty_fields', True)
                self.highlight_empty_color = settings.get('highlight_empty_color', '#434343')
                self.debug_logs_enabled = settings.get('debug_logs_enabled', True)

                # Загружаем позиции окон плеера и менеджера
                self.saved_audio_player_pos = settings.get('audio_player_pos')
                self.saved_files_window_pos = settings.get('files_window_pos')
                
                # Загружаем настройки темы (fallback — встроенные значения)
                self.theme_bg_even = settings.get('theme_bg_even', '#393939')
                self.theme_bg_odd = settings.get('theme_bg_odd', '#2f2f2f')

                # Загружаем громкость
                self.audio_volume = settings.get('audio_volume', 50)

                # Загружаем reference locale
                self.reference_locale = settings.get('reference_locale', 'DEFAULT')

                # Settings loaded successfully (silent)
                
            except Exception as e:
                ErrorLogger.log_error("SETTINGS_LOAD", f"Ошибка загрузки настроек: {e}")
                print(f"ERROR: Settings load failed: {e}")
        # If no settings file, defaults are already set in __init__
    
    def save_settings(self, force=False, update_preview=True):
        """Сохраняет настройки в файл"""
        try:
            # Debug logging: record every call to save_settings with stack trace
            try:
                import traceback
                log_path = os.path.join(os.path.dirname(__file__), 'settings_debug.log')
                with open(log_path, 'a', encoding='utf-8') as lf:
                    lf.write(f"--- save_settings called at {datetime.now().isoformat()} force={force} suppress={getattr(self, '_suppress_settings_save', False)}\n")
                    for line in traceback.format_stack():
                        lf.write(line)
                    lf.write('\n')
            except Exception:
                pass
            # If suppression flag is set and not forced, skip saving (prevents dialog autosave)
            if getattr(self, '_suppress_settings_save', False) and not force:
                return
            settings = {
                'version': VersionInfo.CURRENT,
                'language': self.current_language,
                'filter_action_text': self.filter_action_text.isChecked(),
                'filter_action_radio': self.filter_action_radio.isChecked(),
                'filter_description': self.filter_description.isChecked(),
                'filter_subtitle': self.filter_subtitle.isChecked(),
                'filter_sortie': self.filter_sortie.isChecked(),
                'filter_name': self.filter_name.isChecked(),
                'filter_empty': self.filter_empty_cb.isChecked(),
                'filter_empty_keys': self.filter_empty_keys_cb.isChecked() if hasattr(self, 'filter_empty_keys_cb') else getattr(self, 'filter_empty_keys', True),
                    'highlight_empty_fields': getattr(self, 'highlight_empty_fields', True),
                    'highlight_empty_color': getattr(self, 'highlight_empty_color', '#434343'),
                    'debug_logs_enabled': getattr(self, 'debug_logs_enabled', True),
                'create_backup': getattr(self, 'create_backup', False),
                'show_all_keys': getattr(self, 'show_all_keys', False),
                'last_open_folder': getattr(self, 'last_open_folder', ''),
                'last_save_folder': getattr(self, 'last_save_folder', ''),
                'last_audio_folder': getattr(self, 'last_audio_folder', ''),
                'window_width': self.width(),
                'window_height': self.height(),
                'add_context': self.add_context_toggle.isChecked() if hasattr(self, 'add_context_toggle') else self.add_context,
                'ai_context_1': getattr(self, 'ai_context_1', ""),
                'ai_context_2': getattr(self, 'ai_context_2', ""),
                'ai_context_lang_1': getattr(self, 'ai_context_lang_1', "RU"),
                'sync_scroll': self.sync_scroll,
                'pane_splitter_sizes': self.pane_splitter.sizes() if hasattr(self, 'pane_splitter') else [600, 600],
                'main_vertical_splitter_sizes': self.main_vertical_splitter.sizes() if hasattr(self, 'main_vertical_splitter') else [700, 300],
                'audio_player_pos': [self.audio_player.x(), self.audio_player.y()] if hasattr(self, 'audio_player') and self.audio_player else None,
                'files_window_pos': [self.files_manager_window.x(), self.files_manager_window.y()] if hasattr(self, 'files_manager_window') and self.files_manager_window else None,
                'audio_volume': getattr(self, 'audio_volume', 50),
                'theme_bg_even': getattr(self, 'theme_bg_even', '#393939'),
                'theme_bg_odd': getattr(self, 'theme_bg_odd', '#2f2f2f'),
                'reference_locale': getattr(self, 'reference_locale', 'DEFAULT'),
                'custom_filters': []
            }
            
            # Сохраняем произвольные фильтры
            for custom_filter in self.custom_filters:
                settings['custom_filters'].append({
                    'enabled': custom_filter['checkbox'].isChecked(),
                    'text': custom_filter['line_edit'].text()
                })
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            # Apply changes immediately (visual only)
            self.update_display(update_preview=update_preview)
            # Обновляем заголовки предпросмотра если reference_locale изменился
            try:
                self.update_preview_header_texts()
            except Exception:
                pass
            
            # Settings saved successfully (silent)
            
        except Exception as e:
            ErrorLogger.log_error("SETTINGS_SAVE", f"Ошибка сохранения настроек: {e}")
            print(f"ERROR: Settings save failed: {e}")

    
    def change_language(self, is_russian):
        """Обработчик смены языка"""
        self.current_language = 'ru' if is_russian else 'en'
        self.update_interface_language()
        self.save_settings()
    
    def update_interface_language(self):
        """Обновляет текст интерфейса на текущем языке"""
        # Обновляем статусную строку
        self.statusBar().showMessage(get_translation(self.current_language, 'status_ready'))
        
        """Обновляет текст интерфейса на текущем языке"""
        # Обновляем кнопки управления файлами
        self.open_btn.setText(get_translation(self.current_language, 'open_file_btn'))
        
        # Обновляем открытые окна
        if self.audio_player:
            self.audio_player.retranslate_ui(self.current_language)
            
        if hasattr(self, 'files_manager_window') and self.files_manager_window:
            self.files_manager_window.retranslate_ui(self.current_language)
        self.open_miz_btn.setText(get_translation(self.current_language, 'open_miz_btn'))
        self.save_file_btn.setText(get_translation(self.current_language, 'save_file_btn'))
        
        # Кнопка удаления локали
        if hasattr(self, 'delete_locale_btn'):
            self.delete_locale_btn.setText(get_translation(self.current_language, 'delete_locale_btn'))
        
        # Применяем фиксированный размер кнопок при переключении языков
        if hasattr(self, 'button_fixed_width'):
            for button in [self.open_btn, self.open_miz_btn, self.save_file_btn]:
                button.setMinimumWidth(self.button_fixed_width)
                button.setMaximumWidth(self.button_fixed_width)
        
        # Обновляем кнопки действий
        if hasattr(self, 'copy_all_btn'):
            self.copy_all_btn.setText(get_translation(self.current_language, 'copy_all_btn'))
        if hasattr(self, 'show_keys_btn'):
            self.show_keys_btn.setText(get_translation(self.current_language, 'show_keys_btn'))
        if hasattr(self, 'paste_btn'):
            self.paste_btn.setText(get_translation(self.current_language, 'paste_btn'))
        if hasattr(self, 'clear_btn'):
            self.clear_btn.setText(get_translation(self.current_language, 'clear_btn'))
        
        # Применяем фиксированные размеры для всех кнопок при переключении языков
        if hasattr(self, 'copy_btn_fixed_width'):
            self.copy_all_btn.setMinimumWidth(self.copy_btn_fixed_width)
            self.copy_all_btn.setMaximumWidth(self.copy_btn_fixed_width)
        if hasattr(self, 'keys_btn_fixed_width'):
            self.show_keys_btn.setMinimumWidth(self.keys_btn_fixed_width)
            self.show_keys_btn.setMaximumWidth(self.keys_btn_fixed_width)
        if hasattr(self, 'paste_btn_fixed_width'):
            self.paste_btn.setMinimumWidth(self.paste_btn_fixed_width)
            self.paste_btn.setMaximumWidth(self.paste_btn_fixed_width)
        if hasattr(self, 'clear_btn_fixed_width'):
            self.clear_btn.setMinimumWidth(self.clear_btn_fixed_width)
            self.clear_btn.setMaximumWidth(self.clear_btn_fixed_width)
        
        # Обновляем другие кнопки
        if hasattr(self, 'default_filters_btn'):
            self.default_filters_btn.setText(get_translation(self.current_language, 'default_filters_btn'))
        
        # Применяем фиксированный размер для кнопки фильтров
        if hasattr(self, 'filter_btn_fixed_width'):
            self.default_filters_btn.setMinimumWidth(self.filter_btn_fixed_width)
            self.default_filters_btn.setMaximumWidth(self.filter_btn_fixed_width)
        
        # Обновляем заголовок окна
        self.setWindowTitle(get_translation(self.current_language, 'window_title', version=VersionInfo.CURRENT))

        # Кнопка настроек
        if hasattr(self, 'btn_settings'):
            self.btn_settings.text = get_translation(self.current_language, 'settings_btn')
            try:
                self.btn_settings.update()
            except:
                pass

        # Обновляем открытую панель настроек
        if hasattr(self, 'settings_window') and self.settings_window:
            try:
                self.settings_window.retranslate_ui(self.current_language)
            except:
                pass
        
        # Обновляем группы фильтров
        if hasattr(self, 'filters_group'):
            self.filters_group.setTitle(get_translation(self.current_language, 'filters_group'))
        
        if hasattr(self, 'preview_group'):
            # Убираем заголовок группы предпросмотра — используем отдельную фиксированную шапку
            try:
                self.preview_group.setTitle("")
            except Exception:
                pass

        # Обновляем заголовки внутри панели предпросмотра (если созданы)
        self.update_preview_header_texts()

    def update_preview_header_texts(self):
        """Обновляет тексты заголовков шапки предпросмотра (локализованные и динамические)."""
        # Если установлен флаг подавления — не обновляем шапку/предпросмотр
        if getattr(self, '_suppress_preview_update', False):
            return
        try:
            if hasattr(self, 'preview_header_meta'):
                self.preview_header_meta.setText(get_translation(self.current_language, 'preview_header_meta'))

            if hasattr(self, 'preview_header_ref'):
                ref_locale = getattr(self, 'reference_locale', 'DEFAULT')
                ref_text = get_translation(self.current_language, 'preview_header_ref', locale=f"<span style='color:#ff9900'>{ref_locale}</span>")
                self.preview_header_ref.setText(ref_text)

            if hasattr(self, 'preview_header_editor'):
                editor_locale = (self.miz_locale_combo.currentText() if hasattr(self, 'miz_locale_combo') else getattr(self, 'current_miz_folder', ''))
                editor_text = get_translation(self.current_language, 'preview_header_editor', locale=f"<span style='color:#ff9900'>{editor_locale}</span>")
                self.preview_header_editor.setText(editor_text)
        except Exception:
            pass

        # Сделать рамку вокруг заголовков прозрачной (если необходимо)
        if hasattr(self, 'headers_container'):
            try:
                self.headers_container.setStyleSheet('background-color: transparent; border: none;')
            except Exception:
                pass
        
        # Обновляем ТОЛЬКО запрошенные статические метки
        if hasattr(self, 'additional_keys_label'):
            self.additional_keys_label.setText(get_translation(self.current_language, 'additional_keys_label'))
        if hasattr(self, 'skip_empty_label'):
            self.skip_empty_label.setText(get_translation(self.current_language, 'skip_empty_label'))
        if hasattr(self, 'original_text_header_label'):
            self.original_text_header_label.setText(get_translation(self.current_language, 'original_text_label'))
        if hasattr(self, 'translation_header_label'):
            self.translation_header_label.setText(get_translation(self.current_language, 'translation_label'))
        if hasattr(self, 'label_show_all'):
            self.label_show_all.setText(get_translation(self.current_language, 'show_all_keys_label'))
        if hasattr(self, 'label_skip_empty_keys'):
            self.label_skip_empty_keys.setText(get_translation(self.current_language, 'skip_empty_keys_label'))
        
        # Обновляем новые элементы (Контекст ИИ и кнопки)
        if hasattr(self, 'add_context_label_widget'):
            self.add_context_label_widget.setText(get_translation(self.current_language, 'add_context_label'))
        if hasattr(self, 'add_context_toggle'):
            self.register_custom_tooltip(self.add_context_toggle, get_translation(self.current_language, 'tooltip_add_context'))
            self.register_custom_tooltip(self.add_context_label_widget, get_translation(self.current_language, 'tooltip_add_context'))
        if hasattr(self, 'instructions_btn'):
            self.instructions_btn.setText(get_translation(self.current_language, 'instructions_btn'))
            if hasattr(self, 'instructions_btn_width'):
                self.instructions_btn.setFixedWidth(self.instructions_btn_width)
        if hasattr(self, 'ai_context_mgmt_btn'):
            self.ai_context_mgmt_btn.setText(get_translation(self.current_language, 'ai_context_mgmt_btn'))
            if hasattr(self, 'ai_context_btn_width'):
                self.ai_context_mgmt_btn.setFixedWidth(self.ai_context_btn_width)
        
        # Обновляем плейсхолдеры для произвольных фильтров

        if hasattr(self, 'custom_filters'):
            for i, custom_filter in enumerate(self.custom_filters):
                if 'line_edit' in custom_filter:
                    placeholder = get_translation(self.current_language, 'custom_filter_placeholder', index=i+1)
                    custom_filter['line_edit'].setPlaceholderText(placeholder)
        
        # Обновляем строку статуса, если файл еще не открыт
        if not self.current_file_path:
            self.statusBar().showMessage(get_translation(self.current_language, 'status_ready'))
        
        # Обновляем заголовки панелей текста
        if hasattr(self, 'english_count_label'):
            self.english_count_label.setText(get_translation(self.current_language, 'english_count_label', count=len(self.original_lines) if self.original_lines else 0))
        if hasattr(self, 'russian_count_label'):
            filled = sum(1 for line in self.original_lines if line['translated_text'].strip()) if self.original_lines else 0
            total = len(self.original_lines) if self.original_lines else 0
            self.russian_count_label.setText(get_translation(self.current_language, 'russian_count_label', filled=filled, total=total))
        if hasattr(self, 'stats_label'):
            self.update_translation_stats()
        if hasattr(self, 'preview_info'):
            self.preview_info.setText(get_translation(self.current_language, 'preview_info', count=len(self.original_lines) if self.original_lines else 0))
        
        # Обновляем метки поиска
        if hasattr(self, 'search_label'):
            self.search_label.setText(get_translation(self.current_language, 'search_label'))
        if hasattr(self, 'search_input'):
            self.search_input.setPlaceholderText(get_translation(self.current_language, 'search_placeholder'))
        if hasattr(self, 'search_matches_label'):
            self.update_search_matches_label()
        
        # Обновляем тултипы для кнопок и элементов (кастомный стиль)
        if hasattr(self, 'drag_label'):
            self.register_custom_tooltip(self.drag_label, get_translation(self.current_language, 'tooltip_drag'), side='right')
        
        if hasattr(self, 'logo_label'):
            self.register_custom_tooltip(self.logo_label, get_translation(self.current_language, 'tooltip_about_program'), side='left')
        
        if hasattr(self, 'open_btn'): self.unregister_custom_tooltip(self.open_btn)
        if hasattr(self, 'open_miz_btn'): self.unregister_custom_tooltip(self.open_miz_btn)
        if hasattr(self, 'save_file_btn'): self.unregister_custom_tooltip(self.save_file_btn)
        if hasattr(self, 'instructions_btn'): self.unregister_custom_tooltip(self.instructions_btn)
        if hasattr(self, 'ai_context_mgmt_btn'): self.unregister_custom_tooltip(self.ai_context_mgmt_btn)
        if hasattr(self, 'copy_all_btn'): self.unregister_custom_tooltip(self.copy_all_btn)
        if hasattr(self, 'show_keys_btn'): self.unregister_custom_tooltip(self.show_keys_btn)
        if hasattr(self, 'paste_btn'): self.unregister_custom_tooltip(self.paste_btn)
        if hasattr(self, 'clear_btn'): self.unregister_custom_tooltip(self.clear_btn)
        if hasattr(self, 'default_filters_btn'): self.unregister_custom_tooltip(self.default_filters_btn)
        if hasattr(self, 'view_log_btn'): self.unregister_custom_tooltip(self.view_log_btn)
        if hasattr(self, 'add_context_toggle'): 
            self.unregister_custom_tooltip(self.add_context_toggle)
            self.add_context_toggle.setToolTip("")
        
        # Обновляем тултипы для меток (кастомный стиль)
        if hasattr(self, 'add_context_label_widget'):
            self.register_custom_tooltip(self.add_context_label_widget, get_translation(self.current_language, 'tooltip_add_context'))
        
        # Обновление меток открытых файлов (белый/оранжевый стиль)
        if hasattr(self, 'file_prefix_label'):
            self.file_prefix_label.setText(get_translation(self.current_language, 'file_label'))
        if hasattr(self, 'mission_prefix_label'):
            self.mission_prefix_label.setText(get_translation(self.current_language, 'mission_label'))
        if hasattr(self, 'loc_prefix_label'):
            self.loc_prefix_label.setText(get_translation(self.current_language, 'localization_label'))

        # Обновление текста тоггла синхронизации
        if hasattr(self, 'sync_scroll_label_widget'):
            self.sync_scroll_label_widget.setText(get_translation(self.current_language, 'sync_scroll_label'))
            self.register_custom_tooltip(self.sync_scroll_label_widget, get_translation(self.current_language, 'tooltip_sync_scroll'))

        self.update_file_labels()
        
        # Обновляем новые кнопки инструментов
        if hasattr(self, 'btn_radio'):
            self.btn_radio.text = get_translation(self.current_language, 'btn_radio')
            self.btn_radio.update()
        if hasattr(self, 'btn_files'):
            self.btn_files.text = get_translation(self.current_language, 'btn_files')
            self.btn_files.update()

        # Принудительно переприменяем стили для всех кнопок, чтобы избежать "прямоугольного" бага
        for btn in [self.open_btn, self.open_miz_btn, self.save_file_btn]:
            btn.setStyleSheet(btn.styleSheet())
        
        if hasattr(self, 'copy_all_btn'): self.copy_all_btn.setStyleSheet(self.copy_all_btn.styleSheet())
        if hasattr(self, 'show_keys_btn'): self.show_keys_btn.setStyleSheet(self.show_keys_btn.styleSheet())
        if hasattr(self, 'paste_btn'): self.paste_btn.setStyleSheet(self.paste_btn.styleSheet())
        if hasattr(self, 'clear_btn'): self.clear_btn.setStyleSheet(self.clear_btn.styleSheet())
        if hasattr(self, 'instructions_btn'): self.instructions_btn.setStyleSheet(self.instructions_btn.styleSheet())
        if hasattr(self, 'ai_context_mgmt_btn'): self.ai_context_mgmt_btn.setStyleSheet(self.ai_context_mgmt_btn.styleSheet())

        # Переподключаем тултипы
        # if hasattr(self, 'open_btn'): self.register_custom_tooltip(self.open_btn, get_translation(self.current_language, 'tooltip_open_file'))
        # if hasattr(self, 'open_miz_btn'): self.register_custom_tooltip(self.open_miz_btn, get_translation(self.current_language, 'tooltip_open_miz'))
        # if hasattr(self, 'save_file_btn'): self.register_custom_tooltip(self.save_file_btn, get_translation(self.current_language, 'tooltip_save_file'))
        # if hasattr(self, 'instructions_btn'): self.register_custom_tooltip(self.instructions_btn, get_translation(self.current_language, 'tooltip_instructions'))
        # if hasattr(self, 'ai_context_mgmt_btn'): self.register_custom_tooltip(self.ai_context_mgmt_btn, get_translation(self.current_language, 'tooltip_ai_context'))
        # if hasattr(self, 'copy_all_btn'): self.register_custom_tooltip(self.copy_all_btn, get_translation(self.current_language, 'tooltip_copy_all'))
        # if hasattr(self, 'show_keys_btn'): self.register_custom_tooltip(self.show_keys_btn, get_translation(self.current_language, 'tooltip_show_keys'))
        # if hasattr(self, 'paste_btn'): self.register_custom_tooltip(self.paste_btn, get_translation(self.current_language, 'tooltip_paste'))
        # if hasattr(self, 'clear_btn'): self.register_custom_tooltip(self.clear_btn, get_translation(self.current_language, 'tooltip_clear'))
        # if hasattr(self, 'default_filters_btn'): self.register_custom_tooltip(self.default_filters_btn, get_translation(self.current_language, 'tooltip_default_filters'))
        # if hasattr(self, 'view_log_btn'): self.register_custom_tooltip(self.view_log_btn, get_translation(self.current_language, 'tooltip_view_log'))

        # Обновляем аудиоплеер, если он открыт
        if self.audio_player:
            self.audio_player.retranslate_ui(self.current_language)
            
        print(f"OK: Interface updated to {self.current_language.upper()}")
        
        
        # Принудительно обновляем отображение и предпросмотр
            
        # Принудительно обновляем отображение и предпросмотр
        self.update_display()
        self.update_preview()

    def update_file_labels(self):
        """Обновляет метки открытых файлов с сокращением длинных путей и тултипами"""
        if not hasattr(self, 'selected_file_label') or not hasattr(self, 'selected_miz_label'):
            return

        # Обновление метки обычного файла
        if self.current_file_path and self.selected_file_label.isVisible():
            filename = os.path.basename(self.current_file_path)
            self.file_prefix_label.setText(get_translation(self.current_language, 'file_label'))
            
            # Сокращаем только имя файла
            # Общая ширина контейнера 700px, вычитаем ширину префикса
            metrics = QFontMetrics(self.file_prefix_label.font())
            prefix_width = metrics.horizontalAdvance(self.file_prefix_label.text()) + 10 # + зазор
            name_max_width = max(100, 700 - prefix_width)
            
            elided_name = self.elide_label_text(self.file_name_label, filename, name_max_width)
            self.file_name_label.setText(elided_name)
            
            # Тултип на весь контейнер
            self.register_custom_tooltip(self.selected_file_label, self.current_file_path, side='bottom-left')

        # Обновление метки .miz файла
        if self.current_miz_path and self.selected_miz_label.isVisible():
            filename = os.path.basename(self.current_miz_path)
            folder = getattr(self, 'current_miz_folder', 'DEFAULT')
            
            self.mission_prefix_label.setText(get_translation(self.current_language, 'mission_label'))
            self.loc_prefix_label.setText(get_translation(self.current_language, 'localization_label'))
            
            # Обновление комбобокса
            self.miz_locale_combo.blockSignals(True)
            if self.miz_locale_combo.count() == 0 and self.current_miz_folder:
                 self.miz_locale_combo.addItem(self.current_miz_folder)
            
            if self.current_miz_folder:
                self.miz_locale_combo.setCurrentText(self.current_miz_folder)
            self.miz_locale_combo.blockSignals(False)

            # Обновим заголовок редактора перевода в шапке предпросмотра
            try:
                if hasattr(self, 'preview_header_editor'):
                    editor_locale = (self.miz_locale_combo.currentText() if hasattr(self, 'miz_locale_combo') else getattr(self, 'current_miz_folder', ''))
                    editor_text = get_translation(self.current_language, 'preview_header_editor', locale=f"<span style='color:#ff9900'>{editor_locale}</span>")
                    self.preview_header_editor.setText(editor_text)
            except Exception:
                pass
            
            # Рассчитываем ширины для сокращения
            metrics = QFontMetrics(self.mission_prefix_label.font())
            p1_w = metrics.horizontalAdvance(self.mission_prefix_label.text())
            p2_w = metrics.horizontalAdvance(self.loc_prefix_label.text())
            f_w = metrics.horizontalAdvance(self.miz_locale_combo.currentText())
            
            # Остаток для имени миссии (общий лимит 700)
            name_max_width = max(100, 700 - p1_w - p2_w - f_w - 30) # -30 на зазоры
            
            elided_name = self.elide_label_text(self.mission_name_label, filename, name_max_width)
            self.mission_name_label.setText(elided_name)
            
            # Единый тултип на весь контейнер (Миссия + Название)
            self.register_custom_tooltip(self.mission_info_container, self.current_miz_path, side='bottom-left')
            
            # Убираем лишние тултипы
            if hasattr(self, 'unregister_custom_tooltip'):
                self.unregister_custom_tooltip(self.selected_miz_label)
                self.unregister_custom_tooltip(self.mission_prefix_label)
                self.unregister_custom_tooltip(self.mission_name_label)
                self.unregister_custom_tooltip(self.miz_locale_combo)
                self.unregister_custom_tooltip(self.delete_locale_btn)

    def elide_label_text(self, label, text, max_width):
        """Вспомогательная функция для сокращения текста с многоточием"""
        metrics = QFontMetrics(label.font())
        if metrics.horizontalAdvance(text) <= max_width:
            return text
        return metrics.elidedText(text, Qt.ElideMiddle, max_width)
    
    def update_translation_stats(self):
        """Update translation statistics in the preview panel"""
        if not hasattr(self, 'stats_label') or not self.original_lines:
            return
        
        # Count non-empty original lines
        to_translate = sum(1 for line in self.original_lines if line.get('original_text', '').strip())
        
        # Count translated lines (non-empty translation)
        translated = sum(1 for line in self.original_lines 
                         if line.get('original_text', '').strip() and 
                            line.get('translated_text', '').strip())
        
        # Count untranslated lines
        not_translated = to_translate - translated
        
        # Dynamic color for "Not translated": green if 0, red if > 0
        not_translated_color = '#2ecc71' if not_translated == 0 else '#e74c3c'
        
        # Build colored HTML text
        stats_text = (
            f"<span style='color: white;'>{get_translation(self.current_language, 'stats_to_translate', count=to_translate)}</span>"
            f"<span style='color: #888;'> | </span>"
            f"<span style='color: #2ecc71;'>{get_translation(self.current_language, 'stats_translated', count=translated)}</span>"
            f"<span style='color: #888;'> | </span>"
            f"<span style='color: {not_translated_color};'>{get_translation(self.current_language, 'stats_not_translated', count=not_translated)}</span>"
        )
        
        self.stats_label.setText(stats_text)
    
    # [FILE_PARSING] - ПЕРЕРАБОТАННЫЙ ПАРСЕР
    def open_file(self):
        """Открывает файл для перевода (обычный файл, не .miz)"""
        try:
            start_folder = getattr(self, 'last_open_folder', '')
            file_path, _ = QFileDialog.getOpenFileName(
                self, 'Открыть файл', start_folder, 'Все поддерживаемые (*.txt *.lua *.cmp);;Текстовые файлы (*.txt);;Lua файлы (*.lua);;Файлы кампаний (*.cmp);;Все файлы (*)')
            
            if not file_path:
                return
            
            self.clear_current_data()
            self.last_open_folder = os.path.dirname(file_path)
            self.save_settings()
            self.current_miz_path = None
            self.current_file_path = file_path

            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.original_content = f.read()
                
                # Проверяем расширение файла
                is_cmp = file_path.lower().endswith('.cmp')
                
                # Проверяем, является ли это dictionary файлом или файлом кампании
                if is_cmp:
                    self.parse_cmp_file(self.original_content)
                elif '["' in self.original_content and '"] = "' in self.original_content:
                    self.parse_dictionary_file(self.original_content)
                else:
                    # Простой текстовый файл
                    self.parse_text_file(self.original_content)
                
                if self.original_lines:
                    self.apply_filters()
                    self.save_file_btn.setEnabled(True)
                    
                    # Обновляем надписи о файлах
                    self.selected_file_label.setVisible(True)
                    self.selected_miz_label.setVisible(False)
                    self.update_file_labels()
                    
                    # Инициализируем original_translated_text для отслеживания правок для ВСЕХ строк
                    for line in self.all_lines_data:
                        line['original_translated_text'] = line.get('translated_text', '')
                    
                    self.statusBar().showMessage(get_translation(self.current_language, 'status_lines_loaded', count=len(self.original_lines)))
                    self.has_unsaved_changes = False
                else:
                    # Используем кастомный диалог
                    self.show_custom_dialog(
                        get_translation(self.current_language, 'error_title'),
                        get_translation(self.current_language, 'error_no_lines_found'),
                        "info"
                    )
                    
            except UnicodeDecodeError as e:
                error_msg = f"Ошибка кодировки файла: {str(e)}"
                ErrorLogger.log_error("FILE_ENCODING", error_msg, f"Файл: {file_path}")
                
                self.show_custom_dialog(
                    get_translation(self.current_language, 'error_title_encoding'),
                    f"{get_translation(self.current_language, 'error_utf8_read')}\n\n"
                    f"{get_translation(self.current_language, 'error_utf8_convert')}\n\n"
                    f"{get_translation(self.current_language, 'error_details', details=str(e))}",
                    "error"
                )
            except Exception as e:
                error_msg = f"Ошибка чтения файла: {str(e)}"
                ErrorLogger.log_error("FILE_READ", error_msg, f"Файл: {file_path}")
                
                self.show_custom_dialog(
                    get_translation(self.current_language, 'error_title'),
                    f"{get_translation(self.current_language, 'file_read_error')}: {str(e)}\n\n"
                    f"{get_translation(self.current_language, 'tooltip_view_log')}: {ErrorLogger.LOG_FILE}",
                    "error"
                )
                
        except Exception as e:
            error_msg = f"Общая ошибка при открытии файла: {str(e)}"
            ErrorLogger.log_error("FILE_OPEN", error_msg)
            self.show_custom_dialog("Ошибка", error_msg, "error")
    
    def parse_dictionary_file(self, content):
        """Парсит dictionary используя новый парсер LuaDictionaryParser"""
        import tempfile

        # Создаем временный файл для парсера
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_file = f.name

        try:
            # Используем новый парсер
            self.dictionary_parser = LuaDictionaryParser()
            entries = self.dictionary_parser.parse_file(temp_file)

            # Подготавливаем данные для редактирования
            editing_dict = self.dictionary_parser.prepare_for_editing()

            # Формируем all_lines_data (сохраняя совместимость с остальным кодом)
            self.all_lines_data = []
            self.original_lines = []

            

            line_number = 0
            for key, (text_parts, file_lines, absolute_start_line) in entries.items():
                # Вычисляем, весь ли ключ пустой (все части пустые)
                key_all_empty = all(not (p and p.strip()) for p in text_parts)

                for part_index, part in enumerate(text_parts):
                    # Проверяем нужно ли переводить эту строку
                    should_translate = self._should_translate_key(key)

                    # Проверяем, пустая ли строка
                    is_empty = not part.strip()

                    line_data = {
                        'key': key,
                        'original_text': part,
                        'display_text': part,
                        'translated_text': part,
                        'full_match': file_lines[part_index] if part_index < len(file_lines) else '',
                        'indent': '',
                        'start_pos': line_number if should_translate else absolute_start_line + part_index,
                        'end_pos': (line_number + 1) if should_translate else (absolute_start_line + part_index + 1),
                        'file_line_index': absolute_start_line + part_index, # Абсолютный индекс для системы
                        'should_translate': should_translate,
                        'is_empty': is_empty,
                        'key_all_empty': key_all_empty,
                        'ends_with_backslash': part.endswith('\\') if part else False,
                        'is_multiline': False,
                        'display_line_index': 0,
                        'total_display_lines': 1,
                        'original_translated_text': '', # Будет заполнено при загрузке локали
                        'part_index': part_index  # Оригинальная позиция внутри ключа
                    }

                    self.all_lines_data.append(line_data)

                    # Решаем, включать ли строку в список отображения
                    has_reference_text = False
                    # Используем референс ТОЛЬКО если текущий файл — .miz (у него есть self.current_miz_path).
                    # Это предотвращает показ референсного текста из предыдущей миссии при открытии
                    # standalone dictionary (когда current_miz_path == None).
                    if getattr(self, 'current_miz_path', None) and hasattr(self, 'reference_data') and self.reference_data:
                        ref_parts = self.reference_data.get(key, [])
                        if ref_parts and part_index < len(ref_parts):
                             if ref_parts[part_index].strip():
                                 has_reference_text = True

                    # Если строка пустая - фильтруем (если включен фильтр)
                    should_filter = is_empty and self.filter_empty
                    include_in_original = should_translate and not should_filter
                    
                    # Если ключ полностью пустой и включен фильтр пропуска пустых ключей, не добавляем
                    if key_all_empty and getattr(self, 'filter_empty_keys', True):
                        include_in_original = False

                    if include_in_original:
                        self.original_lines.append(line_data)
                        line_number += 1

            print(f"[STAT] Found lines in file: {len(self.all_lines_data)}")
            print(f"[STAT] Lines for translation: {len(self.original_lines)}")

        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def parse_cmp_file(self, content):
        """Парсит файл кампании (.cmp) используя CampaignParser"""
        # Сначала очищаем данные
        self.all_lines_data = []
        self.original_lines = []
        
        # Получаем данные через новый парсер
        self.all_lines_data = self.campaign_parser.parse_content(content)
        
        # Проставляем индексы (так как парсер их не знает)
        for i, line in enumerate(self.all_lines_data):
            line['index'] = i + 1

        self.original_lines = self.all_lines_data[:]

    def save_cmp_file(self, target_path):
        """Сохраняет файл кампании (.cmp) со всеми локализациями по указанному пути"""
        # Сначала принудительно синхронизируем правки из предпросмотра
        self.apply_pending_preview_sync()
        
        if not self.current_file_path:
            return False

        try:
            # Читаем оригинал файла
            with open(self.current_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Получаем все переведенные строки из нашей структуры данных
            # Объединяем части с одинаковыми ключами (для многострочных description)
            translations = {}
            for line in self.all_lines_data:
                key = line['key']
                val = line.get('translated_text')
                if val is None:
                    val = line.get('original_text', '')
                
                # Если ключ уже есть - добавляем через newline (многострочное значение)
                if key in translations:
                    translations[key] = translations[key] + '\n' + val
                else:
                    translations[key] = val

            # Список поддерживаемых языков из парсера
            supported_languages = self.campaign_parser.supported_languages
            base_keys = self.campaign_parser.base_keys

            new_content = content
            processed_keys = set()
            
            # 1. Обновляем существующие ключи
            for lang in supported_languages:
                for b_key in base_keys:
                    full_key = f"{b_key}_{lang}"
                    val = translations.get(full_key, "")
                    
                    val_parts = val.split('\n')
                    # Ищем и заменяем: ["KEY"] = "VALUE" или [[VALUE]]
                    # re.DOTALL нужен для многострочных описаний
                    pattern = r'(\[\"' + re.escape(full_key) + r'\"\]\s*=\s*)(?:"(?:[^"\\]|\\.)*"|\[\[[\s\S]*?\]\])(,?)'
                    
                    match = re.search(pattern, new_content, re.DOTALL)
                    if match:
                        encoded_parts = [self.campaign_parser._encode_text(p) for p in val_parts]
                        if len(encoded_parts) == 1:
                            new_val_str = f'"{encoded_parts[0]}"'
                        else:
                            # Многострочный
                            new_val_str = f'"{encoded_parts[0]}\\'
                            for part in encoded_parts[1:-1]:
                                new_val_str += f'\n{part}\\'
                            new_val_str += f'\n{encoded_parts[-1]}"'
                            
                        replacement = f"{match.group(1)}{new_val_str}{match.group(2)}"
                        # Заменяем только первое вхождение (для надежности)
                        new_content = new_content.replace(match.group(0), replacement, 1)
                        processed_keys.add(full_key)
            
            # 2. Добавляем новые ключи (которых не было в файле)
            lines_to_add = []
            for lang in supported_languages:
                lang_block = []
                for b_key in base_keys:
                    full_key = f"{b_key}_{lang}"
                    # Проверяем: ключ не обработан И его нет в оригинальном файле
                    key_pattern = f'["{full_key}"]'
                    if full_key not in processed_keys and key_pattern not in content:
                        val = translations.get(full_key, "")
                        if val: # Добавляем только если есть значение
                             val_parts = val.split('\n')
                             lang_block.extend(self.campaign_parser.generate_lua_lines(full_key, val_parts))
                
                if lang_block:
                    lines_to_add.append(f"\n    -- Localization {lang}")
                    lines_to_add.extend(lang_block)

            if lines_to_add:
                # Вставляем перед последней скобкой
                last_brace_idx = new_content.rfind('}')
                if last_brace_idx != -1:
                    insertion = "\n" + "\n".join(lines_to_add) + "\n"
                    new_content = new_content[:last_brace_idx] + insertion + new_content[last_brace_idx:]
                else:
                    raise Exception("Не удалось найти структуру таблицы campaign в файле.")

            # Сохраняем по целевому пути
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Сбрасываем индикацию после успешного сохранения
            self.reset_modified_display_state()
            
            return True
            
        except Exception as e:
            ErrorLogger.log_error("SAVE_CMP", str(e))
            self.show_custom_dialog("Ошибка сохранения", str(e), "error")
            return False

    def handle_cmp_overwrite(self):
        """Перезапись CMP файла с бэкапом"""
        # Проверяем настройку
        should_backup = getattr(self, 'create_backup', True)
            
        backup_path = None
        if should_backup:
             backup_path = self.create_backup_file(self.current_file_path)
             
        if self.save_cmp_file(self.current_file_path):
             self.show_save_report(self.current_file_path, backup_path=backup_path)

    def save_cmp_as(self):
        """Сохранить .cmp как..."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить файл как", 
            os.path.dirname(self.current_file_path), 
            "Campaign Files (*.cmp)"
        )
        if file_path:
             if self.save_cmp_file(file_path):
                 self.show_custom_dialog(get_translation(self.current_language, 'success_title'), 
                                         f"Файл сохранен: {file_path}", "info")

    def show_cmp_save_dialog(self):
        """Показывает диалог сохранения CMP (Overwrite / Save As) в стиле .miz"""
        # --- НАСТРОЙКИ РАЗМЕРОВ КНОПОК ---
        miz_btn_width = 250       # Ширина основных кнопок
        miz_cancel_width = 100    # Ширина кнопки отмена
        # ---------------------------------
        
        dialog = CustomDialog(self)
        dialog.setWindowTitle(get_translation(self.current_language, 'save_file_btn'))
        dialog.setFixedWidth(450)
        
        # Стили (копия из show_miz_save_dialog)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: #404040;
                color: #ddd;
                border: 2px solid #ff9900;
                border-radius: 10px;
            }}
            QLabel {{
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                background-color: transparent;
            }}
            QPushButton {{
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 10px 20px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: {miz_btn_width}px;
                max-width: {miz_btn_width}px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: #e68a00;
            }}
            QPushButton:pressed {{
                background-color: #cc7a00;
            }}
            QPushButton#cancelBtn {{
                background-color: #ffffff;
                color: #000000;
                border-radius: 16px;
                min-width: {miz_cancel_width}px;
                max-width: {miz_cancel_width}px;
            }}
            QPushButton#cancelBtn:hover {{
                background-color: #a3a3a3;
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)
        
        # Заголовок
        title_container = QWidget()
        title_container.setStyleSheet('background-color: transparent; border: none;')
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        title_layout.setAlignment(Qt.AlignCenter)
        
        title_text = QLabel(get_translation(self.current_language, 'file_label'))
        title_text.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_text)
        
        # Имя файла
        full_filename = os.path.basename(self.current_file_path)
        name_part, ext_part = os.path.splitext(full_filename)
        if len(name_part) > 40:
            display_name = name_part[:40] + "..." + ext_part
        else:
            display_name = full_filename
            
        filename_label = QLabel(display_name)
        filename_label.setAlignment(Qt.AlignCenter)
        filename_label.setStyleSheet('color: #ff9900; background-color: transparent; border: none;')
        title_layout.addWidget(filename_label)
        
        layout.addWidget(title_container)
        
        # Инфо
        info_label = QLabel(get_translation(self.current_language, 'save_dialog_info'))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Кнопки
        btns_layout = QVBoxLayout()
        btns_layout.setAlignment(Qt.AlignCenter)
        
        # Frame для перезаписи (белая рамка)
        overwrite_frame = QFrame()
        overwrite_frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #ffffff;
                border-radius: 10px;
                background-color: transparent;
                margin: 5px;
            }}
            QPushButton {{ 
                margin: 5px; 
                min-width: {miz_btn_width}px;
                max-width: {miz_btn_width}px;
            }}
            QLabel {{
                border: none;
            }}
        """)
        overwrite_layout = QVBoxLayout(overwrite_frame)
        overwrite_layout.setContentsMargins(10, 10, 10, 10)
        overwrite_layout.setSpacing(5)
        overwrite_layout.setAlignment(Qt.AlignCenter)
        
        # Кнопка Перезаписать
        overwrite_btn = QPushButton(get_translation(self.current_language, 'overwrite_cmp_btn'))
        
        def on_overwrite():
            if hasattr(self, 'cmp_backup_cb'):
                self.create_backup = self.cmp_backup_cb.isChecked()
                self.save_settings()
            dialog.accept()
            self.handle_cmp_overwrite()
            
        overwrite_btn.clicked.connect(on_overwrite)
        overwrite_layout.addWidget(overwrite_btn)
        
        # Тоггл бэкапа
        backup_toggle_layout = QHBoxLayout()
        backup_toggle_layout.setAlignment(Qt.AlignCenter)
        backup_toggle_layout.setSpacing(10)
        
        self.cmp_backup_cb = ToggleSwitch()
        # Используем атрибут create_backup или по умолчанию True
        current_backup_setting = getattr(self, 'create_backup', True)
        self.cmp_backup_cb.setChecked(current_backup_setting)
        
        backup_toggle_layout.addWidget(self.cmp_backup_cb)
        
        backup_label = QLabel(get_translation(self.current_language, 'miz_backup_label'))
        backup_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: normal; background-color: transparent;")
        backup_toggle_layout.addWidget(backup_label)
        
        overwrite_layout.addLayout(backup_toggle_layout)
        
        btns_layout.addWidget(overwrite_frame)
        
        # Кнопка Сохранить как
        save_as_container = QHBoxLayout()
        save_as_container.addStretch()
        save_as_btn = QPushButton(get_translation(self.current_language, 'save_as_btn'))
        save_as_btn.setFixedWidth(miz_btn_width)
        save_as_btn.clicked.connect(lambda: [dialog.accept(), self.save_cmp_as()])
        save_as_container.addWidget(save_as_btn)
        save_as_container.addStretch()
        btns_layout.addLayout(save_as_container)
        
        # Кнопка Отмена
        cancel_container = QHBoxLayout()
        cancel_container.addStretch()
        cancel_btn = QPushButton(get_translation(self.current_language, 'cancel_btn'))
        cancel_btn.setObjectName("cancelBtn")
        
        def on_cancel():
            # Сохраняем состояние тоггла даже при отмене
            if hasattr(self, 'cmp_backup_cb'):
                self.create_backup = self.cmp_backup_cb.isChecked()
                self.save_settings()
            dialog.reject()
            
        cancel_btn.clicked.connect(on_cancel)
        cancel_container.addWidget(cancel_btn)
        cancel_container.addStretch()
        btns_layout.addLayout(cancel_container)
        
        layout.addLayout(btns_layout)
        dialog.exec_()

    def _should_translate_key(self, key):
        """Проверяет нужно ли переводить ключ по фильтрам"""
        if hasattr(self, 'show_all_keys_cb') and self.show_all_keys_cb.isChecked():
            return True

        if hasattr(self, 'filter_action_text') and self.filter_action_text.isChecked() and 'ActionText' in key:
            return True
        elif hasattr(self, 'filter_action_radio') and self.filter_action_radio.isChecked() and 'ActionRadioText' in key:
            return True
        elif hasattr(self, 'filter_description') and self.filter_description.isChecked() and 'description' in key:
            return True
        elif hasattr(self, 'filter_subtitle') and self.filter_subtitle.isChecked() and 'subtitle' in key:
            return True
        else:
            for custom_filter in self.custom_filters:
                if custom_filter['checkbox'].isChecked():
                    filter_text = custom_filter['line_edit'].text().strip()
                    if filter_text and filter_text in key:
                        return True
            return False

    def parse_lua_file(self, content):
        """Парсит Lua файл с dictionary (использует новый парсер)"""
        self.parse_dictionary_file(content)
    def load_miz_dictionary_data(self, miz_path, folder_name):
        """Helper to load dictionary file from specific l10n folder in miz"""
        try:
            with zipfile.ZipFile(miz_path, 'r') as miz_archive:
                dict_path = f'l10n/{folder_name}/dictionary'
                
                # Проверяем прямой путь
                if dict_path in miz_archive.namelist():
                     with miz_archive.open(dict_path, 'r') as dict_file:
                        return dict_file.read().decode('utf-8')

                # Поиск с учетом регистра (как в open_miz_file)
                dict_filename = 'dictionary'
                folder_prefix = f'l10n/{folder_name.lower()}/'
                
                for item in miz_archive.infolist():
                    name = item.filename
                    try:
                        name = name.encode('cp437').decode('utf-8')
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        pass
                        
                    if name.lower().startswith(folder_prefix) and name.lower().endswith(dict_filename):
                        with miz_archive.open(item.filename, 'r') as dict_file:
                            return dict_file.read().decode('utf-8')
                
                raise FileNotFoundError(f"Dictionary not found in {folder_name}")
        except Exception as e:
            raise e

    def change_miz_locale(self, index):
        """Switch current miz locale"""
        if self.is_switching_locale:
            return
            
        new_folder = self.miz_locale_combo.currentText()
        if not new_folder or new_folder == self.current_miz_folder:
            return
            
        # ПРОВЕРКА: Если локаль была удалена, но осталась в кэше UI (редкий случай)
        if new_folder not in self.current_miz_l10n_folders and not new_folder.startswith(("+", "[")):
            print(f"WARNING: Attempted to switch to deleted locale {new_folder}. Aborting.")
            self.update_miz_locale_combo() # Синхронизируем UI
            return

        print(f"DEBUG: Switching locale to {new_folder}")
        
        try:
            self.is_switching_locale = True
            
            # Обработка выбора "[ + ]"
            if new_folder == "[ + ]":
                self.is_expanding_plus = True
                try:
                    self.update_miz_locale_combo(show_all=True)
                    self.miz_locale_combo.showPopup()
                finally:
                    # Сбрасываем флаг чуть позже, чтобы таймер в eventFilter успел его увидеть
                    QTimer.singleShot(200, lambda: setattr(self, 'is_expanding_plus', False))
                return

            # Обработка создания новой локали
            if new_folder.startswith("+"):
                target_locale = new_folder[1:] # Убираем плюс
                print(f"DEBUG: Creating new locale {target_locale} from DEFAULT")
                
                # 1. Сначала сохраняем текущее состояние если есть
                if self.current_miz_folder:
                     self.miz_trans_memory[self.current_miz_folder] = {
                        'original_lines': copy.deepcopy(self.original_lines),
                        'all_lines_data': copy.deepcopy(self.all_lines_data),
                        'original_content': self.original_content
                    }
                
                # 2. Берем данные из DEFAULT
                default_data = None
                
                # Ищем в памяти
                if "DEFAULT" in self.miz_trans_memory:
                    default_data = self.miz_trans_memory["DEFAULT"]
                # Или загружаем из файла
                else:
                    try:
                        content = self.load_miz_dictionary_data(self.current_miz_path, "DEFAULT")
                        self.parse_dictionary_file(content) # Парсим чтобы получить структуры
                        default_data = {
                            'original_lines': copy.deepcopy(self.original_lines),
                            'all_lines_data': copy.deepcopy(self.all_lines_data),
                            'original_content': content
                        }
                    except Exception as e:
                        # Если DEFAULT нет (странно), берем текущее
                        print(f"WARNING: DEFAULT locale not found, copying current. Error: {e}")
                        default_data = {
                            'original_lines': copy.deepcopy(self.original_lines),
                            'all_lines_data': copy.deepcopy(self.all_lines_data),
                            'original_content': self.original_content
                        }

                # 3. Применяем данные к новой локали
                self.original_lines = copy.deepcopy(default_data['original_lines'])
                self.all_lines_data = copy.deepcopy(default_data['all_lines_data'])
                self.original_content = default_data['original_content']
                # При создании новой локали из DEFAULT сбрасываем все переводы,
                # чтобы в новой локали не появлялись правки, введённые в DEFAULT.
                try:
                    for ln in self.original_lines:
                        if isinstance(ln, dict):
                            ln['translated_text'] = ''
                            ln['original_translated_text'] = ''
                            # Отображаем в UI оригинальный текст, а не перевод
                            ln['display_text'] = ln.get('original_text', '')
                except Exception:
                    pass
                try:
                    for ln in self.all_lines_data:
                        if isinstance(ln, dict):
                            ln['translated_text'] = ''
                            ln['original_translated_text'] = ''
                            ln['display_text'] = ln.get('original_text', '')
                except Exception:
                    pass
                
                # 4. Обновляем списки и интерфейс
                if target_locale not in self.current_miz_l10n_folders:
                    self.current_miz_l10n_folders.append(target_locale)
                    self.current_miz_l10n_folders.sort()
                
                self.current_miz_folder = target_locale
                self.update_miz_locale_combo(show_all=False)
                
                # 4.1 Обновляем ресурсы для новой локали (синхронизация подсветки)
                try:
                    with zipfile.ZipFile(self.current_miz_path, 'r') as miz_archive:
                        self.miz_resource_manager.update_locale(miz_archive, target_locale)
                except Exception as e:
                    print(f"WARNING: Ошибка обновления ресурсов при создании локали: {e}")
                
                self.apply_filters()
                self.update_display()
                self.update_preview()
                self.update_file_labels()
                
                self.statusBar().showMessage(get_translation(self.current_language, 'status_locale_created', locale=target_locale))
                
                # Сбрасываем выбор в аудиоплеере при смене локали
                if self.audio_player is not None:
                     self.audio_player.reset_to_no_file()
                     
                return

            # Стандартное переключение
            # 1. Save current state to memory
            if self.current_miz_folder:
                self.miz_trans_memory[self.current_miz_folder] = {
                    'original_lines': copy.deepcopy(self.original_lines),
                    'all_lines_data': copy.deepcopy(self.all_lines_data),
                    'original_content': self.original_content
                }
            
            # 2. Load new state
            if new_folder in self.miz_trans_memory:
                memory = self.miz_trans_memory[new_folder]
                self.original_lines = memory['original_lines']
                self.all_lines_data = memory['all_lines_data']
                self.original_content = memory['original_content']
                print(f"DEBUG: Loaded {new_folder} from memory")
            else:
                # Load from file
                content = self.load_miz_dictionary_data(self.current_miz_path, new_folder)
                self.original_content = content
                self.parse_dictionary_file(content)
                print(f"DEBUG: Loaded {new_folder} from file")
                # Initialize original_translated_text for change tracking (file-load only)
                for line in self.all_lines_data:
                    line['original_translated_text'] = line.get('translated_text', '')
            
            # 3. Update current folder
            self.current_miz_folder = new_folder
            
            # 3.1 Обновляем mapResource для новой локали
            try:
                with zipfile.ZipFile(self.current_miz_path, 'r') as miz_archive:
                    self.miz_resource_manager.update_locale(miz_archive, new_folder)
            except Exception as e:
                print(f"WARNING: Ошибка обновления ресурсов при смене локали: {e}")
            
            # 4. Update display
            self.apply_filters()
            self.update_display()
            self.update_preview()
            self.update_file_labels() 
            
            self.statusBar().showMessage(get_translation(self.current_language, 'status_mission_lines_loaded', count=len(self.original_lines)))
            
            # Сбрасываем выбор в аудиоплеере при смене локали
            if self.audio_player is not None:
                 self.audio_player.reset_to_no_file()
            
        except Exception as e:
            error_msg = f"Error switching locale: {str(e)}"
            ErrorLogger.log_error("MIZ_LOCALE_SWITCH", error_msg)
            self.show_custom_dialog("Error", error_msg, "error")
            
            # Revert combo
            self.miz_locale_combo.blockSignals(True)
            self.miz_locale_combo.setCurrentText(self.current_miz_folder)
            self.miz_locale_combo.blockSignals(False)
            
        finally:
            self.is_switching_locale = False
            self.update_delete_button_visibility()

    def update_delete_button_visibility(self):
        """Обновляет видимость кнопки удаления в зависимости от выбранной локали"""
        if not hasattr(self, 'delete_locale_btn'):
            return
            
        curr = self.miz_locale_combo.currentText()
        is_valid = curr and curr != "DEFAULT" and not curr.startswith("[") and not curr.startswith("+")
        is_miz = self.current_file_path is not None and self.current_file_path.lower().endswith(".miz")
        self.delete_locale_btn.setVisible(bool(is_miz and is_valid))

    def confirm_delete_locale(self):
        """Вызывает диалог подтверждения удаления текущей локали"""
        current_locale = self.miz_locale_combo.currentText()
        if not current_locale or current_locale == "DEFAULT" or current_locale.startswith("[") or current_locale.startswith("+"):
            return
            
        dialog = DeleteConfirmDialog(current_locale, self.current_language, self)
        if dialog.exec_() == QDialog.Accepted:
            self.delete_selected_locale(current_locale)

    def delete_selected_locale(self, locale_name):
        """Удаляет локаль из памяти и списков, обновляет интерфейс"""
        # 1. Удаляем из памяти перевода
        if locale_name in self.miz_trans_memory:
            del self.miz_trans_memory[locale_name]
            
        # 2. Удаляем из списка папок локалей
        if hasattr(self, 'current_miz_l10n_folders') and locale_name in self.current_miz_l10n_folders:
            self.current_miz_l10n_folders.remove(locale_name)
            
        # 3. ПРИНУДИТЕЛЬНО обновляем комбобокс, чтобы удалить название из списка UI
        self.update_miz_locale_combo()
            
        # 4. Если мы удалили текущую открытую локаль, переключаемся на DEFAULT
        if self.current_miz_folder == locale_name:
            self.current_miz_folder = None # Сброс
            index = self.miz_locale_combo.findText("DEFAULT")
            if index >= 0:
                self.miz_locale_combo.setCurrentIndex(index)
            # Если DEFAULT нет, update_miz_locale_combo уже сбросил UI на первый элемент
            
        print(f"OK: Locale {locale_name} deleted and UI updated")

    def update_miz_locale_combo(self, show_all=False):
        """Обновляет содержимое комбобокса локалей"""
        self.miz_locale_combo.blockSignals(True)
        self.miz_locale_combo.clear()
        
        # 1. Существующие папки
        self.miz_locale_combo.addItems(self.current_miz_l10n_folders)
        
        # 2. Если нужно показать все доступные для создания
        if show_all:
            existing = set(self.current_miz_l10n_folders)
            for locale in self.STANDARD_LOCALES:
                if locale not in existing:
                    self.miz_locale_combo.addItem(f"+{locale}")
        else:
            # Иначе добавляем кнопку раскрытия, если есть что добавить
            existing = set(self.current_miz_l10n_folders)
            has_missing = any(l not in existing for l in self.STANDARD_LOCALES)
            if has_missing:
                self.miz_locale_combo.addItem("[ + ]")
                
        if self.current_miz_folder in self.current_miz_l10n_folders:
            self.miz_locale_combo.setCurrentText(self.current_miz_folder)
            
        self.miz_locale_combo.blockSignals(False)
        self.update_delete_button_visibility()

    def open_miz_file(self):
        """Открывает файл миссии .miz и извлекает dictionary"""
        progress = None
        try:
            start_folder = getattr(self, 'last_open_folder', '')
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                'Открыть файл миссии DCS (.miz)', 
                start_folder, 
                'Файлы миссий DCS (*.miz);;Все файлы (*)'
            )
            
            if not file_path:
                return
            
            self.clear_current_data()
            self.last_open_folder = os.path.dirname(file_path)
            self.save_settings()

                
            print(f"\n{'='*50}")
            print(f"ОТКРЫТИЕ .MIZ ФАЙЛА: {os.path.basename(file_path)}")
            print(f"{'='*50}")
            
            # Сохраняем путь к .miz файлу
            self.current_miz_path = file_path
            
            # Показываем прогресс-бар
            progress = MizProgressDialog(self)
            progress.show()
            progress.set_value(10)
            
            try:
                # Открываем .miz файл как ZIP-архив
                with zipfile.ZipFile(file_path, 'r') as miz_archive:
                    progress.set_value(20)
                    
                    # Парсим ресурсы миссии (связи audio↔subtitle, mapResource)
                    try:
                        self.miz_resource_manager.load_from_miz(miz_archive, 'DEFAULT')
                        # Показываем кнопку смещения эвристики
                        if hasattr(self, 'heuristic_toggle_btn'):
                            offset = self.miz_resource_manager.get_current_offset_label()
                            offset_str = f"+{offset}" if offset > 0 else str(offset)
                            self.heuristic_toggle_btn.setText(
                                get_translation(self.current_language, 'heuristic_toggle_btn', offset=offset_str)
                            )
                            # self.heuristic_toggle_btn.setVisible(True)  # Скрыта по просьбе пользователя
                    except Exception as e:
                        print(f"WARNING: Ошибка парсинга ресурсов миссии: {e}")
                    progress.set_value(30)
                    
                    # Сканируем доступные папки локализации в l10n/
                    l10n_folders = set()
                    for item in miz_archive.infolist():
                        # Исправляем кодировку имени файла (CP437 -> UTF-8), если нужно
                        name = item.filename
                        try:
                            name = name.encode('cp437').decode('utf-8')
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            pass
                            
                        if name.startswith('l10n/') and '/' in name[5:]:
                            folder_name = name[5:].split('/')[0]
                            l10n_folders.add(folder_name)
                    
                    l10n_folders = sorted(list(l10n_folders))
                    print(f"DEBUG: Found l10n folders: {l10n_folders}")
                    progress.set_value(40)
                    
                    # Путь по умолчанию
                    self.current_miz_folder = 'DEFAULT'
                    dict_path = f'l10n/{self.current_miz_folder}/dictionary'
                    
                    # Если найдено несколько папок, спрашиваем пользователя
                    if len(l10n_folders) > 1 or (len(l10n_folders) == 1 and "DEFAULT" not in l10n_folders):
                        dialog = MizFolderDialog(l10n_folders, self.current_language, self)
                        if dialog.exec_() == QDialog.Accepted:
                            self.current_miz_folder = dialog.selected_folder
                            dict_path = f'l10n/{self.current_miz_folder}/dictionary'
                            print(f"DEBUG: User selected folder: {self.current_miz_folder}")
                            # Обновляем mapResource для выбранной локали
                            try:
                                self.miz_resource_manager.update_locale(miz_archive, self.current_miz_folder)
                            except Exception as e:
                                print(f"WARNING: Ошибка обновления ресурсов для {self.current_miz_folder}: {e}")
                        else:
                            print("DEBUG: Folder selection cancelled")
                            self.current_miz_path = None
                            progress.close()
                            return
                    progress.set_value(50)
                    
                    # Проверяем наличие файла dictionary по выбранному пути
                    if dict_path not in miz_archive.namelist():
                        # Ищем альтернативные пути (на случай разных регистров)
                        found = False
                        dict_filename = os.path.basename(dict_path).lower()
                        folder_prefix = os.path.dirname(dict_path).lower() + '/'
                        
                        for item in miz_archive.infolist():
                            # Исправляем кодировку
                            name = item.filename
                            try:
                                name = name.encode('cp437').decode('utf-8')
                            except (UnicodeEncodeError, UnicodeDecodeError):
                                pass

                            if name.lower().startswith(folder_prefix) and name.lower().endswith(dict_filename):
                                dict_path = item.filename # Используем оригинальное имя из архива
                                print(f"⚠ Найден dictionary по альтернативному пути: {dict_path}")
                                found = True
                                break
                        
                        if not found:
                            raise FileNotFoundError(f"Файл dictionary не найден по пути {dict_path}")
                    progress.set_value(60)
                    
                    # Читаем содержимое dictionary
                    with miz_archive.open(dict_path, 'r') as dict_file:
                        self.original_content = dict_file.read().decode('utf-8')
                    
                    print(f"✅ Файл dictionary успешно извлечен из {dict_path}")
                    print(f"📏 Размер файла: {len(self.original_content)} байт")
                    progress.set_value(70)
                    
            except zipfile.BadZipFile:
                error_msg = get_translation(self.current_language, 'error_bad_zip', filename=os.path.basename(file_path))
                ErrorLogger.log_error("MIZ_BAD_ZIP", error_msg)
                self.show_custom_dialog(get_translation(self.current_language, 'error_title'), error_msg, "error")
                self.current_miz_path = None
                progress.close()
                return
            except FileNotFoundError as e:
                error_msg = f"{get_translation(self.current_language, 'file_not_found')}: {str(e)}"
                ErrorLogger.log_error("MIZ_NO_DICT", error_msg)
                self.show_custom_dialog(get_translation(self.current_language, 'error_title'), error_msg, "error")
                self.current_miz_path = None
                progress.close()
                self.has_unsaved_changes = False
                return
            except Exception as e:
                error_msg = f"{get_translation(self.current_language, 'miz_error')}: {str(e)}"
                ErrorLogger.log_error("MIZ_READ", error_msg)
                self.show_custom_dialog(get_translation(self.current_language, 'error_title'), error_msg, "error")
                self.current_miz_path = None
                progress.close()
                return
            
            # Обновляем метку файла
            self.current_file_path = file_path
            
            # Загружаем reference данные из .miz (с диска, read-only)
            # ВАЖНО: делаем это ДО parse_dictionary_file, чтобы фильтрация пустых строк знала о референсе
            try:
                self.reference_loader.clear_cache()
                self.reference_data = self.reference_loader.load_locale_from_miz(
                    file_path, getattr(self, 'reference_locale', 'DEFAULT')
                )
            except Exception as e:
                print(f"WARNING: Ошибка загрузки reference данных: {e}")
                self.reference_data = {}

            # Теперь парсим основной словарь
            self.parse_dictionary_file(self.original_content)
            progress.set_value(90)
            
            if self.original_lines:
                self.apply_filters()
                self.save_file_btn.setEnabled(True)
                self.selected_miz_label.setVisible(True)
                self.selected_file_label.setVisible(False)
                
                # Инициализация переключателя локалей
                self.current_miz_l10n_folders = l10n_folders
                self.miz_trans_memory = {} # Сброс памяти при открытии нового файла

                self.update_miz_locale_combo(show_all=False)
                
                self.update_file_labels()
                
                # Сохраняем начальное состояние ВСЕХ строк для отслеживания правок
                for line in self.all_lines_data:
                    line['original_translated_text'] = line.get('translated_text', '')
                
                lines_loaded_msg = get_translation(self.current_language, 'status_mission_lines_loaded', count=len(self.original_lines))
                self.statusBar().showMessage(lines_loaded_msg)
                
                # Если референс-локаль отсутствовала и был fallback на DEFAULT — показываем предупреждение
                if self.reference_loader.last_fallback:
                    fb = self.reference_loader.last_fallback
                    warn_msg = get_translation(self.current_language, 'status_ref_locale_fallback', locale=fb)
                    # Показываем предупреждение через 300мс (чтобы предыдущее сообщение успело отобразиться)
                    QTimer.singleShot(300, lambda: self.statusBar().showMessage(warn_msg))
                    # Через 5 секунд восстанавливаем сообщение о загруженных строках
                    QTimer.singleShot(5300, lambda: self.statusBar().showMessage(lines_loaded_msg))
                
                self.has_unsaved_changes = False
                progress.set_value(100)
            else:
                self.show_custom_dialog(
                    get_translation(self.current_language, 'error_title'),
                    get_translation(self.current_language, 'error_no_lines_found_miz'),
                    "info"
                )
            
        except Exception as e:
            error_msg = f"Общая ошибка при открытии .miz файла: {str(e)}"
            ErrorLogger.log_error("MIZ_OPEN", error_msg)
            self.show_custom_dialog("Ошибка", error_msg, "error")
            self.current_miz_path = None
        finally:
            if progress:
                progress.close()
    
    def parse_lua_file(self, content):
        """Парсит Lua файл с dictionary (старый метод, оставлен для обратной совместимости)"""
        print("⚠ Используется старый парсер Lua. Рекомендуется обновить файл.")
        self.parse_dictionary_file(content)
    
    def parse_text_file(self, content):
        """Парсит простой текстовый файл"""
        self.original_lines = []
        self.all_lines_data = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                line_data = {
                    'key': f'Line_{i+1:04d}',
                    'original_text': line,
                    'display_text': line,
                    'translated_text': line,
                    'full_match': line,
                    'indent': '',
                    'start_pos': 0,
                    'end_pos': len(line),
                    'should_translate': True,
                    'is_empty': False,
                    'ends_with_backslash': False,
                    'is_multiline': False,
                    'display_line_index': i,
                    'total_display_lines': 1,
                    'part_index': i
                }
                
                self.all_lines_data.append(line_data)
                self.original_lines.append(line_data)
    
    def apply_filters(self, full_rebuild=True):
        """Применяет выбранные фильтры к данным"""
        lines_before = len(self.original_lines)
        self.original_lines = []
        
        # Находим объект строки в original_lines, который сейчас в фокусе (чтобы не скрывать его во время ввода)
        focused_line_data = None
        try:
            focus_w = QApplication.focusWidget()
            from widgets import PreviewTextEdit
            if isinstance(focus_w, PreviewTextEdit) and 0 <= focus_w.index < len(self.original_lines):
                focused_line_data = self.original_lines[focus_w.index]
        except Exception:
            pass
        
        show_all = getattr(self, 'show_all_keys_cb', None) and self.show_all_keys_cb.isChecked()
        suppress_indices = getattr(self, 'suppress_empty_filter_for_indices', set())
        
        for idx, line_data in enumerate(self.all_lines_data):
            should_translate = False
            
            if show_all:
                should_translate = True
            elif self.filter_action_text.isChecked() and 'ActionText' in line_data['key']:
                should_translate = True
            elif self.filter_action_radio.isChecked() and 'ActionRadioText' in line_data['key']:
                should_translate = True
            elif self.filter_description.isChecked() and 'description' in line_data['key']:
                should_translate = True
            elif self.filter_subtitle.isChecked() and 'subtitle' in line_data['key']:
                should_translate = True
            elif self.filter_sortie.isChecked() and 'sortie' in line_data['key']:
                should_translate = True
            elif self.filter_name.isChecked() and 'name' in line_data['key']:
                should_translate = True
            else:
                # Проверяем произвольные фильтры
                for custom_filter in self.custom_filters:
                    if custom_filter['checkbox'].isChecked():
                        filter_text = custom_filter['line_edit'].text().strip()
                        if filter_text and filter_text in line_data['key']:
                            should_translate = True
                            break
            
            # Проверка пустых строк/ключей (учитываем наличие текста в референсе)
            has_ref = False
            # Используем референс только если открыт .miz (есть путь в current_miz_path)
            if getattr(self, 'current_miz_path', None) and hasattr(self, 'reference_data') and self.reference_data:
                rp = self.reference_data.get(line_data['key'], [])
                p_idx = line_data.get('part_index', 0)
                if rp and p_idx < len(rp) and rp[p_idx].strip():
                    has_ref = True

            # === Фильтр пустых строк: НЕ удаляем строку если есть референсный текст ===
            # collect diagnostics: reason why a line would be excluded
            exclude_reason = None
            if not show_all and should_translate and line_data['is_empty'] and self.filter_empty:
                # если для этой строки есть текст в reference (например при .miz), сохраняем её
                if has_ref:
                    pass
                else:
                    # НЕ скрываем строку, если она в фокусе прямо сейчас (защита от исчезновения поля под курсором)
                    if line_data is not focused_line_data:
                        # Проверяем, является ли эта строка окончательным индексом в original_lines
                        current_visual_idx = len(self.original_lines)
                        if current_visual_idx not in suppress_indices:
                            should_translate = False
                            exclude_reason = 'empty_filtered'
                    
            # Если включён фильтр пропуска пустых ключей и ключ полностью пуст, не переводим
            if not show_all and getattr(self, 'filter_empty_keys', True) and line_data.get('key_all_empty', False):
                should_translate = False
                exclude_reason = 'key_all_empty'
            
            if should_translate:
                self.original_lines.append(line_data)
            else:
                # Log diagnostic info for excluded lines when filtering is active
                try:
                    if self.filter_empty or getattr(self, 'filter_empty_keys', True):
                        # limit excessive logging
                        if not hasattr(self, '_filter_diagnostics'):
                            self._filter_diagnostics = []
                        if len(self._filter_diagnostics) < 200:
                            key = line_data.get('key')
                            part = line_data.get('part_index', 0)
                            is_empty = bool(line_data.get('is_empty', False))
                            has_reference = bool(has_ref)
                            reason = exclude_reason or 'no_match'
                            self._filter_diagnostics.append((idx, key, part, is_empty, has_reference, reason))
                except Exception:
                    pass
        
        # Очищаем флаг защиты после применения фильтра
        self.suppress_empty_filter_for_indices = set()
        
        lines_after = len(self.original_lines)
        log_msg = f"[APPLY_FILTERS] before={lines_before} after={lines_after} filter_empty={self.filter_empty} suppressed={len(suppress_indices)}"
        self._log_to_file(log_msg)
        # Dump diagnostics if collected
        try:
            if hasattr(self, '_filter_diagnostics') and self._filter_diagnostics:
                self._log_to_file(f"[FILTER_DIAG] Collected {len(self._filter_diagnostics)} entries (showing up to 200):")
                for entry in self._filter_diagnostics:
                    idx, key, part, is_empty, has_reference, reason = entry
                    self._log_to_file(f"[FILTER_DIAG] idx={idx} key={key} part={part} empty={is_empty} has_ref={has_reference} reason={reason}")
                # keep diagnostics for one run only
                self._filter_diagnostics = []
        except Exception:
            pass
        print(f"📊 После фильтрации строк для перевода: {len(self.original_lines)}")
        
        if full_rebuild:
            self.update_display()
        else:
            # Если количество видимых строк изменилось — нужно обновить и верхний редактор,
            # чтобы индексы блоков соответствовали новым индексам original_lines.
            if len(self.original_lines) != lines_before:
                self.update_display(update_preview=False)
            
            self.sync_preview_incremental()
            # Обновление основного окна (Top Editor) опционально, 
            # но обычно при наборе в превью оно не требуется немедленно
            # self.update_display(update_preview=False)
    
    def toggle_empty_filter(self):
        """Включает/выключает фильтр пустых строк - ИСПРАВЛЕНО: без параметра state"""
        # Используем isChecked() для получения состояния после анимации
        self.filter_empty = self.filter_empty_cb.isChecked()
        log_msg = f"[TOGGLE_EMPTY_FILTER] filter_empty={self.filter_empty} original_lines_before={len(self.original_lines)}"
        self._log_to_file(log_msg)
        self.apply_filters()
        self.save_settings()

    def toggle_empty_keys_filter(self):
        """Переключает фильтр: пропускать полностью пустые ключи"""
        self.filter_empty_keys = self.filter_empty_keys_cb.isChecked()
        self.apply_filters()
        self.save_settings()
    
    def toggle_show_all_keys(self):
        """Переключает отображение всех ключей"""
        self.show_all_keys = self.show_all_keys_cb.isChecked()
        self.apply_filters()
        self.save_settings()
    
    def toggle_keys_display(self, checked):
        """Переключает отображение ключей.
        Обновляем основное отображение без перестройки превью (preview уже соответствует оригиналу).
        """
        # Обновляем только основные панели — предотвращаем полную перерисовку превью
        self.update_display(update_preview=False)
        # Обновляем только визуальные цвета/заголовки в превью (не перестраивая виджеты)
        try:
            self.update_preview_theme_colors()
        except Exception:
            pass
    
    # [DISPLAY_METHODS]
    def update_display(self, update_preview=True):
        """Обновляет отображение в основных панелях"""
        # Если установлен флаг подавления — не обновляем отображение/предпросмотр
        if getattr(self, '_suppress_preview_update', False):
            return
        if self.is_updating_display:
            return
            
        self.is_updating_display = True
        self.prevent_text_changed = True
        
        try:
            if not self.original_lines:
                self.original_text_all.clear()
                self.translated_text_all.clear()
                self.update_translation_stats()
                self.english_count_label.setText(get_translation(self.current_language, 'english_count_label', count=0))
                self.russian_count_label.setText(get_translation(self.current_language, 'russian_count_label', filled=0, total=0))
                self.preview_info.setText(get_translation(self.current_language, 'preview_info', count=0))
                return
            
            # Формируем текст для левой панели (оригинал)
            english_lines = []
            show_keys = self.show_keys_btn.isChecked()
            
            for line_data in self.original_lines:
                # Удаляем переносы строк внутри текста
                clean_text = line_data['display_text'].replace('\n', ' ')
                
                # Добавляем индикатор слеша
                if line_data.get('ends_with_backslash', False):
                    # clean_text += " [\\]"  # Индикатор слеша удален по просьбе пользователя
                    pass
                
                if show_keys:
                    english_lines.append(f"[{line_data['key']}] {clean_text}")
                else:
                    english_lines.append(clean_text)
            
            # [BUFFER] Устанавливаем лимит номеров строк для оригинала
            self.original_text_all.max_line_count = len(self.original_lines)
            
            # Формируем текст для правой панели (перевод)
            russian_lines = []
            for line_data in self.original_lines:
                if line_data['translated_text']:
                    clean_text = line_data['translated_text'].replace('\n', ' ')
                    russian_lines.append(clean_text)
                else:
                    russian_lines.append('')
            
            # [BUFFER] Добавляем лишние строки в перевод
            if self.extra_translation_lines:
                russian_lines.extend(self.extra_translation_lines)
            
            # [BUFFER] Добавляем соответствующие пустые строки в оригинал
            if len(self.extra_translation_lines) > 0:
                english_lines.extend([''] * len(self.extra_translation_lines))
            
            # Обновляем оригинал
            self.original_text_all.setPlainText('\n'.join(english_lines))
            
            new_text = '\n'.join(russian_lines)
            
            # Обновляем перевод (если изменился)
            current_text = self.translated_text_all.toPlainText()
            if current_text != new_text:
                self.translated_text_all.setPlainText(new_text)
            
            # [LINE_PADDING] Добиваем пустыми строками до количества строк оригинала
            doc = self.translated_text_all.document()
            current_blocks = doc.blockCount()
            needed_blocks = len(self.original_lines)
            
            if current_blocks < needed_blocks:
                diff = needed_blocks - current_blocks
                cursor = QTextCursor(doc)
                cursor.movePosition(QTextCursor.End)
                cursor.insertText('\n' * diff)
            
            # Применяем цвета темы к редакторам
            if hasattr(self, 'original_text_all'):
                self.original_text_all.set_zebra_colors(self.theme_bg_even, self.theme_bg_odd)
            if hasattr(self, 'translated_text_all'):
                self.translated_text_all.set_zebra_colors(self.theme_bg_even, self.theme_bg_odd)

            # Обновляем статистику
            self.update_stats()
            
            # Обновляем предпросмотр
            if update_preview and not getattr(self, 'is_updating_from_preview', False):
                self.schedule_preview_update()
            elif not update_preview:
                # Если полная перерисовка подавлена, обновляем только цвета (визуально)
                self.update_preview_theme_colors()
            
            # Обновляем результаты поиска, если есть активный поиск
            if hasattr(self, 'search_input') and self.search_input.text():
                self.on_search_text_changed(self.search_input.text())
            
        except Exception as e:
            ErrorLogger.log_error("DISPLAY_UPDATE", f"Ошибка при обновлении отображения: {e}")
        finally:
            self.is_updating_display = False
            self.prevent_text_changed = False
    
    def update_stats(self):
        """Обновляет статистику перевода"""
        if not self.original_lines:
            self.update_translation_stats()
            self.english_count_label.setText(get_translation(self.current_language, 'english_count_label', count=0))
            self.russian_count_label.setText(get_translation(self.current_language, 'russian_count_label', filled=0, total=0))
            if hasattr(self, 'preview_info'):
                self.preview_info.setText(get_translation(self.current_language, 'preview_info', count=0))
            return
        
        self.update_translation_stats()
        count_all = len(self.original_lines)
        self.english_count_label.setText(get_translation(self.current_language, 'english_count_label', count=count_all))
        
        filled_translations = sum(1 for line in self.original_lines if line['translated_text'].strip())
        self.russian_count_label.setText(get_translation(self.current_language, 'russian_count_label', filled=filled_translations, total=count_all))
        
        # Обновляем "Показано строк XX" в превью
        if hasattr(self, 'preview_info'):
            self.preview_info.setText(get_translation(self.current_language, 'preview_info', count=count_all))

    def on_add_context_toggled(self, checked):
        """Handler for `add_context_toggle`: save setting without forcing preview rebuild."""
        try:
            # update internal flag
            self.add_context = bool(checked)
            # persist setting but avoid full preview rebuild
            self.save_settings(update_preview=False)
        except Exception:
            try:
                self.save_settings()
            except Exception:
                pass
    
    def toggle_sync_scroll(self):
        """Переключает режим синхронной прокрутки окон"""
        self.sync_scroll = self.sync_scroll_toggle.isChecked()
        
        # Отключаем старые вертикальные соединения
        try:
            self.original_text_all.verticalScrollBar().valueChanged.disconnect(self._sync_original_to_translated)
        except: pass
        try:
            self.translated_text_all.verticalScrollBar().valueChanged.disconnect(self._sync_translated_to_original)
        except: pass
            
        # Если включено — подключаем
        if self.sync_scroll:
            self.original_text_all.verticalScrollBar().valueChanged.connect(self._sync_original_to_translated)
            self.translated_text_all.verticalScrollBar().valueChanged.connect(self._sync_translated_to_original)
            
            # Сразу синхронизируем (правое к левому)
            val = self.original_text_all.verticalScrollBar().value()
            self.translated_text_all.verticalScrollBar().setValue(val)
        
        # Синхронизация горизонтального пространства (видимости) теперь работает ВСЕГДА 
        # (подключена в setup_translation_area), поэтому здесь ничего менять не нужно 
        # для сохранения высоты вьюпортов даже при выключенном вертикальном синхроне.
        self._sync_horizontal_scrollbar_visibility()
        
        # Save without forcing preview rebuild (no need to reconstruct preview when toggling scroll)
        try:
            self.save_settings(update_preview=False)
        except Exception:
            try:
                self.save_settings()
            except Exception:
                pass

    def _sync_horizontal_scrollbar_visibility(self):
        """Синхронизирует видимость (резервирование места) горизонтальных скроллбаров"""
        # Проверяем, нужен ли хоть один горизонтальный скроллбар
        range_orig = self.original_text_all.horizontalScrollBar().maximum()
        range_trans = self.translated_text_all.horizontalScrollBar().maximum()
        
        if range_orig > 0 or range_trans > 0:
            # Если хотя бы одному нужен — включаем у обоих (AlwaysOn + наш 'stealth' стиль)
            self.original_text_all.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.translated_text_all.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        else:
            # Если обоим не нужен — возвращаем авто-режим (оба скроются)
            self.original_text_all.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.translated_text_all.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def _sync_original_to_translated(self, value):
        """Синхронизация левого окна -> правое"""
        if self._is_syncing or not self.sync_scroll:
            return
        self._is_syncing = True
        self.translated_text_all.verticalScrollBar().setValue(value)
        self._is_syncing = False

    def _sync_translated_to_original(self, value):
        """Синхронизация правого окна -> левое"""
        if self._is_syncing or not self.sync_scroll:
            return
        self._is_syncing = True
        self.original_text_all.verticalScrollBar().setValue(value)
        self._is_syncing = False
    
    # [TEXT_PROCESSING]

    def count_slashes(self, text):
        """Считает количество слешей в тексте"""
        if not text:
            return 0
        return text.count('\\')

    def unescape_string(self, text):
        """Раскодирует экранированные символы в строке"""
        if not text:
            return ""
        
        # Сначала обрабатываем двойные слеши (один слеш в игре)
        result = text.replace('\\\\', '\\')
        
        # Затем обрабатываем другие escape-последовательности
        replacements = [
            ('\\"', '"'),
            ('\\n', '\n'),
            ('\\t', '\t'),
            ('\\r', '\r'),
        ]
        
        for old, new in replacements:
            result = result.replace(old, new)
        
        return result
    
    def generate_content_from_data(self, lines_data):
        """Generates lua dictionary content from specific lines data (for multi-locale save)
        Correctly handles multi-line entries by grouping them by key.
        """
        # Группируем строки по ключу
        translations = {}
        for item in lines_data:
            key = item['key']
            if key not in translations:
                translations[key] = []
            
            # Используем перевод, даже если он пустой ('')
            # Падаем на оригинал только если данных о переводе вообще нет (None)
            val = item.get('translated_text')
            if val is None:
                val = item.get('original_text', '')
            
            translations[key].append(val)
            
        content = "dictionary = \n{\n"
        
        for key, lines in translations.items():
            if not lines:
                continue
                
            if len(lines) == 1:
                # Обычная строка
                value = self.escape_string(lines[0])
                content += f'    ["{key}"] = "{value}",\n'
            else:
                # Многострочная запись
                # Первая строка
                val0 = self.escape_string(lines[0])
                content += f'    ["{key}"] = "{val0}\\\n'
                
                # Средние строки
                for i in range(1, len(lines) - 1):
                    val_i = self.escape_string(lines[i])
                    content += f'{val_i}\\\n'
                
                # Последняя строка
                val_last = self.escape_string(lines[-1])
                content += f'{val_last}",\n'
                
        content += "} -- end of dictionary\n"
        return content

    def escape_string(self, text):
        """Кодирует специальные символы для сохранения в файл"""
        if not text:
            return ""
        
        result = text
        
        # ВАЖНО: сначала экранируем обратные слеши
        result = result.replace('\\', '\\\\')
        
        # Затем экранируем кавычки
        result = result.replace('"', '\\"')
        
        # Затем другие управляющие символы
        result = result.replace('\n', '\\n')
        result = result.replace('\t', '\\t')
        result = result.replace('\r', '\\r')
        
        return result
    
    def copy_all_english(self):
        """Копирует весь английский текст в буфер обмена"""
        if not self.original_lines:
            self.statusBar().showMessage(get_translation(self.current_language, 'status_no_lines_to_copy'))
            return
        
        english_lines = []
        backslash_lines = []
        
        for i, line_data in enumerate(self.original_lines):
            # Без ключей при копировании
            clean_text = line_data['display_text'].replace('\n', ' ')
            
            # Отмечаем строки со слешами
            if line_data.get('ends_with_backslash', False):
                backslash_lines.append(i + 1)
                clean_text += " [добавьте \\ в конце]"
            
            english_lines.append(clean_text)
        
        english_text = '\n'.join(english_lines)
        
        # Проверяем, включено ли добавление контекста (через тоггл или переменную)
        is_context_enabled = self.add_context_toggle.isChecked() if hasattr(self, 'add_context_toggle') else getattr(self, 'add_context', True)
        
        # Добавляем контекст (только основной) если включено
        if is_context_enabled and hasattr(self, 'ai_context_1') and self.ai_context_1.strip():
            # Очищаем контекст от лишних пробелов в конце и добавляем двойной перенос для пустой строки
            english_text = self.ai_context_1.strip() + "\n\n" + english_text
            
        QApplication.clipboard().setText(english_text)
        
        # Показываем информацию внизу, без всплывающих окон
        if backslash_lines:
            shown = backslash_lines[:20]
            more = len(backslash_lines) - len(shown)
            tail = f" (+{more})" if more > 0 else ""
            self.statusBar().showMessage(
                f"✅ Скопировано {len(english_lines)} строк. ⚠ Строки со слешом: {', '.join(map(str, shown))}{tail}"
            )
        else:
            self.statusBar().showMessage(get_translation(self.current_language, 'status_copied', count=len(english_lines)))
    
    def paste_from_clipboard(self):
        """Вставляет текст из буфера обмена Windows"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if text:
            self.translated_text_all.setPlainText(text)
            self.statusBar().showMessage(get_translation(self.current_language, 'status_text_pasted'))
        else:
            self.statusBar().showMessage(get_translation(self.current_language, 'status_clipboard_empty'))
    
    def clear_current_data(self):
        """Полностью очищает текущие данные перед загрузкой нового файла"""
        self.original_lines = []
        self.all_lines_data = []
        self.extra_translation_lines = []
        self.search_matches = []
        self.current_match_index = -1
        self.audio_labels_map = {}
        
        if hasattr(self, 'miz_resource_manager'):
            self.miz_resource_manager.reset()
        
        self.miz_trans_memory = {}
        
        # Скрываем кнопку эвристики
        if hasattr(self, 'heuristic_toggle_btn'):
            self.heuristic_toggle_btn.setVisible(False)
        
        # Очищаем виджеты
        self.prevent_text_changed = True
        if hasattr(self, 'original_text_all'):
            self.original_text_all.clear()
        if hasattr(self, 'translated_text_all'):
            self.translated_text_all.clear()
        
        # СТОП отрисовки предпросмотра
        if hasattr(self, 'preview_batch_timer'):
            self.preview_batch_timer.stop()
        self.preview_groups_queue = []
        
        self.clear_preview_widgets()
        
        # Сброс статистики
        if hasattr(self, 'stats_label'):
            self.update_translation_stats()
        
        if hasattr(self, 'english_count_label'):
            self.english_count_label.setText(get_translation(self.current_language, 'english_count_label', count=0))
        if hasattr(self, 'russian_count_label'):
            self.russian_count_label.setText(get_translation(self.current_language, 'russian_count_label', filled=0, total=0))
        if hasattr(self, 'preview_info'):
            self.preview_info.setText(get_translation(self.current_language, 'preview_info', count=0))
            
        # Сбрасываем выбор в аудиоплеере при загрузке нового файла
        if hasattr(self, 'audio_player') and self.audio_player is not None:
             self.audio_player.reset_to_no_file()
             
        self.prevent_text_changed = False
        print("DEBUG: Current data cleared")
    
    # [PREVIEW_METHODS]
    def clear_preview_widgets(self):
        """Очищает все виджеты предпросмотра (оптимизировано)"""
        # Отключаем обновления для ускорения очистки
        if hasattr(self, 'preview_content'):
            self.preview_content.setUpdatesEnabled(False)
            
        try:
            # Сначала останавливаем таймеры, которые могут создавать новые виджеты
            if hasattr(self, 'preview_batch_timer'):
                self.preview_batch_timer.stop()
            
            # Очищаем три колонки
            layouts = [
                getattr(self, 'preview_meta_layout', None), 
                getattr(self, 'preview_orig_layout', None),
                getattr(self, 'preview_trans_layout', None)
            ]
            
            for layout in layouts:
                if not layout: continue
                
                # Удаляем растяжку в конце, если она есть
                count = layout.count()
                if count > 0:
                    item = layout.itemAt(count - 1)
                    if item and not item.widget() and not item.layout():
                         layout.removeItem(item)

                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        w = item.widget()
                        try:
                            # Логируем удаляемый виджет (полезно для диагностики рассинхронов)
                            self._log_to_file(f"[PREVIEW_DELETE_WIDGET] name={getattr(w, 'objectName', lambda: None)()} key={getattr(w, 'key', None)} part={getattr(w, 'part_index', None)} index={getattr(w, 'index', None)}")
                        except Exception:
                            pass
                        # Разрываем связи во избежание сюрпризов при удалении
                        if hasattr(w, 'partner'): w.partner = None
                        if hasattr(w, 'row_siblings'): w.row_siblings = None
                        w.deleteLater()
                    elif item.layout():
                        self.clear_layout(item.layout())
            # Логируем и очищаем маппинги (безопасно)
            if hasattr(self, 'preview_key_to_group_widget') and self.preview_key_to_group_widget:
                try:
                    for key, val in list(self.preview_key_to_group_widget.items()):
                        try:
                            mw, ow, tw = val
                            # подсчитываем количество дочерних редакторов в каждой колонке
                            o_count = len(ow.findChildren(type(ow))) if hasattr(ow, 'findChildren') else None
                            t_count = len(tw.findChildren(type(tw))) if hasattr(tw, 'findChildren') else None
                        except Exception:
                            o_count = t_count = None
                        try:
                            self._log_to_file(f"[PREVIEW_DELETE_GROUP] key={key} orig_count={o_count} trans_count={t_count}")
                        except Exception:
                            pass
                except Exception:
                    pass
            for attr in ['preview_key_to_group_widget', 'warning_icons_map', 
                         'audio_labels_map', 'quick_audio_buttons']:
                if hasattr(self, attr):
                    try:
                        getattr(self, attr).clear()
                    except Exception:
                        setattr(self, attr, {})
                else:
                    setattr(self, attr, {})

        except Exception as e:
            ErrorLogger.log_error("CLEAR_PREVIEW", f"Error clearing preview: {e}")
        finally:
            if hasattr(self, 'preview_content'):
                self.preview_content.setUpdatesEnabled(True)
                self.preview_content.update()

    def recursive_delete_widget(self, widget):
        """Рекурсивно удаляет виджет и все его дочерние элементы"""
        if hasattr(widget, 'layout'):
            if widget.layout():
                self.clear_layout(widget.layout())
        widget.deleteLater()

    def clear_layout(self, layout):
        """Рекурсивно очищает layout и все его элементы"""
        if layout is None:
            return
        
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def update_preview_theme_colors(self):
        """Обновляет цвета темы в предпросмотре без перерисовки виджетов"""
        if not hasattr(self, 'preview_meta_layout') or not self.preview_meta_layout:
            return
            
        self.preview_content.setUpdatesEnabled(False)
        try:
            # Итерируемся по всем строкам в превью (используем meta_layout как эталон количества)
            for i in range(self.preview_meta_layout.count()):
                item_meta = self.preview_meta_layout.itemAt(i)
                item_orig = self.preview_orig_layout.itemAt(i)
                item_trans = self.preview_trans_layout.itemAt(i)
                
                if not (item_meta and item_orig and item_trans):
                    continue
                    
                w_meta = item_meta.widget()
                w_orig = item_orig.widget()
                w_trans = item_trans.widget()
                
                # Пропускаем, если это не виджет (например, stretch в конце)
                if not (w_meta and w_orig and w_trans) or w_meta.objectName() != "preview_line_group":
                    continue
                    
                # Рассчитываем новый цвет
                bg_color = self.theme_bg_even if i % 2 == 0 else self.theme_bg_odd
                
                # Обновляем стили (сохраняя остальные параметры границы из render_preview_batch)
                # Meta column
                w_meta.setStyleSheet(f'''
                    QWidget#preview_line_group {{
                        background-color: {bg_color};
                        border-bottom: 1px solid #333;
                        border-right: 1px solid #333;
                        border-radius: 0px;
                    }}
                ''')
                # Original column
                w_orig.setStyleSheet(f'''
                    QWidget#preview_line_group {{
                        background-color: {bg_color};
                        border-bottom: 1px solid #333;
                        border-right: 1px solid #333;
                        border-radius: 0px;
                    }}
                ''')
                # Translated column
                w_trans.setStyleSheet(f'''
                    QWidget#preview_line_group {{
                        background-color: {bg_color};
                        border-bottom: 1px solid #333;
                        border-radius: 0px;
                    }}
                ''')
        except Exception as e:
            print(f"Error updating preview colors: {e}")
        finally:
            self.preview_content.setUpdatesEnabled(True)

    def update_preview(self):
        """Обновляет предварительный просмотр всех строк (версия с батчевой отрисовкой)"""
        # Если установлен флаг подавления — не перерисовываем предпросмотр
        if getattr(self, '_suppress_preview_update', False):
            return
        # If user is actively typing (pending edits) or a preview editor has focus, postpone rebuild
        try:
            from widgets import PreviewTextEdit
            focused = QApplication.focusWidget()
        except Exception:
            PreviewTextEdit = None
            focused = None

        if getattr(self, 'pending_sync_edits', None):
            # postpone to avoid destroying active editors while typing
            self.schedule_preview_update(300)
            return

        if PreviewTextEdit and isinstance(focused, PreviewTextEdit):
            # СОХРАНЯЕМ ФОКУС: запоминаем где был курсор перед обновлением
            try:
                cursor = focused.textCursor()
                self.last_focused_preview_info = {
                    'key': focused.key if hasattr(focused, 'key') else None,
                    'part_index': focused.part_index if hasattr(focused, 'part_index') else (focused.index if hasattr(focused, 'index') else None),
                    'position': cursor.position(),
                    'anchor': cursor.anchor()
                }
            except Exception:
                self.last_focused_preview_info = None
            
            # РАЗРЕШАЕМ: теперь мы не блокируем обновление полностью, 
            # так как научились восстанавливать фокус.
            pass

        if self.is_preview_updating:
            self.schedule_preview_update(300)
            return
            
        self.is_preview_updating = True
        try:
            # Останавливаем предыдущую отрисовку (если таймер инициализирован)
            if hasattr(self, 'preview_batch_timer'):
                self.preview_batch_timer.stop()
            self.preview_groups_queue = []
            
            # Очищаем предыдущий предпросмотр
            self.clear_preview_widgets()
            
            if not self.original_lines:
                self.preview_info.setText(get_translation(self.current_language, 'preview_info', count=0))
                return

            # Группировка строк по ключу
            groups = []
            if self.original_lines:
                current_group = [0]
                for i in range(1, len(self.original_lines)):
                    if self.original_lines[i]['key'] == self.original_lines[i-1]['key']:
                        current_group.append(i)
                    else:
                        groups.append(current_group)
                        current_group = [i]
                groups.append(current_group)

            # 2. Подготавливаем очередь
            self.preview_groups_queue = groups
            self.audio_labels_map = {}
            
            # Обновляем информацию (предварительно)
            self.preview_info.setText(get_translation(self.current_language, 'preview_info', count=len(self.original_lines)))
            
            # Запускаем батчевую отрисовку (увеличили интервал до 20мс для меньшей нагрузки)
            if hasattr(self, 'preview_batch_timer'):
                self.preview_batch_timer.start(20)
            
        except Exception as e:
            error_msg = f"Ошибка обновления предпросмотра: {str(e)}"
            ErrorLogger.log_error("PREVIEW_ERROR", error_msg)
            if hasattr(self, 'preview_info'):
                self.preview_info.setText(f'Ошибка: {error_msg[:50]}...')
        finally:
            self.is_preview_updating = False

    def sync_preview_incremental(self):
        """Эффективное обновление: скрывает/показывает имеющиеся виджеты без пересоздания.
        Используется для авто-обновлений (фильтров) во время ввода, чтобы избежать тормозов.
        """
        if not hasattr(self, 'preview_key_to_group_widget') or not self.preview_key_to_group_widget:
            return
        
        # Создаем маппинг (key, part_index) -> new_index для быстрого поиска
        visible_map = {}
        for i, line in enumerate(self.original_lines):
            # В original_lines у нас есть полные данные строки
            visible_map[(line['key'], line.get('part_index', 0))] = i
            
        # Отключаем обновления для ускорения
        self.preview_content.setUpdatesEnabled(False)
        try:
            from widgets import PreviewTextEdit
            # Проходим по всем группам (mw - meta, ow - orig, tw - trans)
            for key, (mw, ow, tw) in self.preview_key_to_group_widget.items():
                group_has_visible = False
                
                # Внутри каждой колонки группы (orig, trans)
                # Нам нужно проверить все PreviewTextEdit
                for col_w in (ow, tw):
                    edits = col_w.findChildren(PreviewTextEdit)
                    for edit in edits:
                        # part_index мы добавили ранее в render_preview_batch
                        match_key = (key, getattr(edit, 'part_index', 0))
                        
                        if match_key in visible_map:
                            edit.setVisible(True)
                            try:
                                self._log_to_file(f"[PREVIEW_SHOW] key={key} part={getattr(edit, 'part_index', 0)} index={getattr(edit, 'index', None)}")
                            except Exception:
                                pass
                            # Обновляем индекс для синхронизации, чтобы sync_pending_edits работал корректно
                            edit.index = visible_map[match_key]
                            group_has_visible = True
                        else:
                            edit.setVisible(False)
                            try:
                                self._log_to_file(f"[PREVIEW_HIDE] key={key} part={getattr(edit, 'part_index', 0)} reason=not_in_visible_map")
                            except Exception:
                                pass
                
                # Если в ключе не осталось ни одной видимой строки - скрываем всю группу
                # (метаданные и контейнеры колонок)
                mw.setVisible(group_has_visible)
                ow.setVisible(group_has_visible)
                tw.setVisible(group_has_visible)
                try:
                    self._log_to_file(f"[PREVIEW_GROUP_VIS] key={key} visible={group_has_visible}")
                except Exception:
                    pass
                
            # Обновляем счетчик
            self.preview_info.setText(get_translation(self.current_language, 'preview_info', count=len(self.original_lines)))
            
        except Exception as e:
            print(f"Error in sync_preview_incremental: {e}")
            # В случае ошибки fallback на полную перерисовку
            self.update_preview()
        finally:
            self.preview_content.setUpdatesEnabled(True)

    def render_preview_batch(self):
        """Отрисовывает одну пачку групп в предпросмотре для плавности"""
        if not self.preview_groups_queue or not self.original_lines:
            self.preview_batch_timer.stop()
            self.preview_layout.addStretch()
            self.last_focused_preview_info = None  # Сбрасываем, если так и не нашли
            return
            
        # Пачка по 10 групп за раз (было 15, уменьшили для плавности)
        batch_size = 10
        batch = self.preview_groups_queue[:batch_size]
        self.preview_groups_queue = self.preview_groups_queue[batch_size:]
        
        # Отключаем обновления на время массового добавления
        self.preview_content.setUpdatesEnabled(False)
        try:
            for group_indices in batch:
                if not group_indices: continue
                first_idx = group_indices[0]
                
                # ПРОВЕРКА ГРАНИЦ (Защита от IndexError при быстрой смене файлов)
                if first_idx >= len(self.original_lines):
                    continue
                    
                line_data = self.original_lines[first_idx]
                current_key = line_data['key']

                # part_index уже сохранён в line_data при парсинге — НЕ перезаписываем
                
                # Рассчитываем цвет зебры: чередуем по чётности
                current_count = self.preview_meta_layout.count()
                bg_color = self.theme_bg_even if current_count % 2 == 0 else self.theme_bg_odd
                
                # Создаём три строки (по одной для каждой колонки)
                meta_row_widget = QWidget()
                meta_row_widget.setObjectName("preview_line_group")
                meta_row_widget.setStyleSheet(f'''
                    QWidget#preview_line_group {{
                        background-color: {bg_color};
                        border-bottom: 1px solid #333;
                        border-right: 1px solid #333;
                        border-radius: 0px;
                    }}
                ''')
                meta_row_layout = QVBoxLayout(meta_row_widget)
                meta_row_layout.setContentsMargins(4, 1, 4, 1)
                meta_row_layout.setSpacing(2)

                orig_row_widget = QWidget()
                orig_row_widget.setObjectName("preview_line_group")
                orig_row_widget.setStyleSheet(f'''
                    QWidget#preview_line_group {{
                        background-color: {bg_color};
                        border-bottom: 1px solid #333;
                        border-right: 1px solid #333;
                        border-radius: 0px;
                    }}
                ''')
                orig_row_layout = QVBoxLayout(orig_row_widget)
                orig_row_layout.setContentsMargins(4, 1, 4, 1)
                orig_row_layout.setSpacing(0)

                trans_row_widget = QWidget()
                trans_row_widget.setObjectName("preview_line_group")
                trans_row_widget.setStyleSheet(f'''
                    QWidget#preview_line_group {{
                        background-color: {bg_color};
                        border-bottom: 1px solid #333;
                        border-radius: 0px;
                    }}
                ''')
                trans_row_layout = QVBoxLayout(trans_row_widget)
                trans_row_layout.setContentsMargins(4, 1, 4, 1)
                trans_row_layout.setSpacing(0)

                # Регистрируем группу для селективного апдейта по ключу (три компонента)
                try:
                    self.preview_key_to_group_widget[current_key] = (meta_row_widget, orig_row_widget, trans_row_widget)
                except Exception:
                    self.preview_key_to_group_widget = {current_key: (meta_row_widget, orig_row_widget, trans_row_widget)}
                try:
                    self._log_to_file(f"[PREVIEW_CREATE_GROUP] key={current_key} first_idx={first_idx} parts={len(group_indices)} current_count={current_count}")
                except Exception:
                    pass
                
                # Подсветка при наведении только для аудио меток, для строк убрана
                
                # 1. Содержимое метаданных (Номер, Ключ, Аудио)
                idx_label = f"#{first_idx+1}" if len(group_indices) == 1 else f"#{first_idx+1}-{group_indices[-1]+1}"
                header_line = QLabel(f"<span style='color: #cccccc; font-weight: bold;'>{idx_label}</span> <span style='color: #8f8f8f; font-size: 11px;'>{current_key}</span>")
                header_line.setStyleSheet('border: none; background: transparent;')
                header_line.setWordWrap(True)
                # Убрали setMaximumWidth(195) для динамического растяжения
                meta_row_layout.addWidget(header_line, 0, Qt.AlignTop)
                
                audio_info = self.miz_resource_manager.get_audio_for_key(current_key)
                if audio_info:
                    audio_filename, is_current_locale = audio_info
                    audio_color = '#00cc66' if self.miz_resource_manager.is_audio_replaced(current_key) else ('#ff9900' if is_current_locale else '#888888')
                    audio_label = ClickableLabel(audio_filename)
                    audio_label.clicked.connect(lambda k=current_key: self.open_audio_player(k, auto_play=False))
                    self.audio_labels_map[current_key] = audio_label
                    
                    # ЦВЕТ АУДИО: #ff6666 если заменен и не сохранен, иначе #2ecc71 (если в текущей папке) или #888888
                    is_audio_replaced = self.miz_resource_manager.is_audio_replaced(current_key)
                    if is_audio_replaced:
                         audio_color = '#ff6666'
                    elif is_current_locale:
                         audio_color = '#2ecc71'
                    else:
                         audio_color = '#cccccc'

                    # Возвращаем border-radius контролам
                    border_style = "border: 1px solid #ff9900; border-radius: 4px;" if current_key == self.active_audio_key else "border: 1px solid transparent;"
                    audio_label.setStyleSheet(f'''
                        QLabel {{
                            color: {audio_color};
                            font-size: 12px;
                            text-decoration: underline;
                            background-color: transparent;
                            {border_style}
                            padding: 2px;
                        }}
                        QLabel:hover {{
                            background-color: #3d4256;
                            border-radius: 2px;
                        }}
                    ''')
                    audio_label.setWordWrap(True)
                    # Убрали setMaximumWidth(195) для динамического растяжения
                    meta_row_layout.addWidget(audio_label, 0, Qt.AlignTop)
                    
                    # Мини-кнопки управления (Play/Stop)
                    audio_controls = QHBoxLayout()
                    audio_controls.setContentsMargins(0, 0, 0, 0)
                    audio_controls.setSpacing(10)
                    # Play/Pause (слева) - уменьшенные на 30%
                    play_btn = QPushButton("▶")
                    play_btn.setFixedSize(self.preview_btn_size, self.preview_btn_size)
                    play_btn.setCursor(Qt.PointingHandCursor)
                    # Apply style using current top offset
                    play_btn.setStyleSheet(self.preview_btn_base.format(size=self.preview_play_font, w=self.preview_btn_size, top=self.preview_play_top_offset))
                    play_btn.clicked.connect(lambda _, k=current_key, b=play_btn: self.quick_toggle_audio(k, b))

                    # Stop (справа) — иконка квадрата белая по требованию
                    stop_btn = QPushButton("■")
                    stop_btn.setFixedSize(self.preview_btn_size, self.preview_btn_size)
                    stop_btn.setCursor(Qt.PointingHandCursor)
                    stop_btn.setStyleSheet(self.preview_btn_base.format(size=self.preview_stop_font, w=self.preview_btn_size, top=self.preview_stop_top_offset))
                    stop_btn.clicked.connect(self.stop_quick_audio)
                    
                    audio_controls.addWidget(play_btn)
                    audio_controls.addWidget(stop_btn)
                    
                    # Значок ВНИМАНИЯ для файлов из DEFAULT - создаем ТОЛЬКО если нужен
                    warning_icon = None
                    audio_info = self.miz_resource_manager.get_audio_for_key(current_key)
                    if audio_info and not audio_info[1]:  # Если файл НЕ в текущей локали (из DEFAULT)
                        warning_icon = QLabel("⚠")
                        warning_icon.setStyleSheet("color: #ffcc00; background-color: transparent; font-size: 16px; margin-left: 3px;")
                        warning_icon.setCursor(Qt.PointingHandCursor)
                        audio_controls.addWidget(warning_icon)
                        
                        # Регистрируем кастомный тултип (красивый стиль как у "Информация о программе")
                        self.register_custom_tooltip(warning_icon, get_translation(self.current_language, 'file_from_default'), side='top')
                        
                        # Сохраняем ссылку на значок ВНИМАНИЯ
                        if not hasattr(self, 'warning_icons_map'):
                            self.warning_icons_map = {}
                        self.warning_icons_map[current_key] = warning_icon
                    
                    # Сохраняем ссылку на кнопку для быстрого обновления состояния
                    try:
                        self.quick_audio_buttons[current_key] = play_btn
                        # Если уже играет этот ключ, синхронизируем иконку
                        if self.quick_playing_key == current_key:
                            if self.quick_paused:
                                play_btn.setText("▶")
                            else:
                                play_btn.setText("\u23F8\uFE0E")
                    except Exception:
                        pass
                    audio_controls.addStretch()
                    meta_row_layout.addLayout(audio_controls)
                    # Stretch будет добавлен в конце функции для всей мета-строки
                
                # Добавляем содержимое в layout оригинала
                for idx in group_indices:
                    l_data = self.original_lines[idx]
                    # Используем reference данные (с диска) для оригинальной колонки
                    # Только если открыт .miz — в противном случае референс игнорируем
                    if getattr(self, 'current_miz_path', None) and getattr(self, 'reference_data', None):
                        ref_parts = self.reference_data.get(current_key, [])
                    else:
                        ref_parts = []
                    if ref_parts:
                        # Используем оригинальный part_index из данных строки (сохранён при парсинге)
                        original_part_idx = l_data.get('part_index', 0)
                        ref_text = ref_parts[original_part_idx] if original_part_idx < len(ref_parts) else ''
                    else:
                        # Если открыт .miz — показываем fallback (display_text), иначе — пустой референс
                        if getattr(self, 'current_miz_path', None):
                            ref_text = l_data['display_text']
                        else:
                            ref_text = ''
                    # part_index — оригинальная позиция внутри ключа (из парсинга)
                    original_part_idx = l_data.get('part_index', 0)
                    orig_edit = PreviewTextEdit(idx, ref_text, read_only=True)
                    orig_edit.part_index = original_part_idx
                    orig_edit.setStyleSheet("color: #ffffff; background-color: transparent; border: none; border-radius: 0px;")
                    orig_edit._original_style = "color: #ffffff; background-color: transparent; border: none; border-radius: 0px;"
                    try:
                        self._log_to_file(f"[PREVIEW_WIDGET] create orig idx={idx} key={current_key} part={original_part_idx} text_len={len(ref_text)}")
                    except Exception:
                        pass
                    
                    t_text = l_data['translated_text'] if l_data['translated_text'] else ""
                    # Проверяем 'original_translated_text' (исходный текст при загрузке)
                    is_modified = False
                    if 'original_translated_text' in l_data:
                        is_modified = t_text != l_data['original_translated_text']

                    trans_edit = PreviewTextEdit(idx, t_text, read_only=False)
                    trans_edit.key = current_key
                    trans_edit.part_index = original_part_idx
                    try:
                        self._log_to_file(f"[PREVIEW_WIDGET] create trans idx={idx} key={current_key} part={original_part_idx} text_len={len(t_text)} modified={is_modified}")
                    except Exception:
                        pass

                    # Цвет текста: #ff6666 если изменен (и не сохранен), иначе #2ecc71
                    text_color = "#ff6666" if is_modified else "#2ecc71"

                    # Фон поля перевода устанавливается через фокус (focusIn/Out) у PreviewTextEdit
                    original_style = f"color: {text_color}; background-color: transparent; border: none; border-radius: 0px;"
                    trans_edit.setStyleSheet(original_style)
                    trans_edit._original_style = original_style

                    # ВОССТАНОВЛЕНИЕ ФОКУСА
                    if self.last_focused_preview_info:
                        info = self.last_focused_preview_info
                        # Для PreviewTextEdit 'index' обычно соответствует 'part_index' внутри группы или глобальному индексу
                        # Но надежнее всего проверять по ключу (если есть) и индексу части
                        is_match = False
                        if info['key'] == current_key:
                            # Проверяем совпадение индекса
                            if info['part_index'] == idx:
                                is_match = True
                        
                        if is_match:
                            try:
                                trans_edit.setFocus()
                                cursor = trans_edit.textCursor()
                                cursor.setPosition(info['anchor'])
                                cursor.setPosition(info['position'], QTextCursor.KeepAnchor)
                                trans_edit.setTextCursor(cursor)
                                # Сбрасываем, чтобы не фокусировать повторно при батчевой отрисовке других групп
                                self.last_focused_preview_info = None
                            except Exception:
                                pass
                    # Исправлено: лямбда теперь использует динамический te.index и данные из оригинального списка.
                    # Это предотвращает перезапись чужих строк при вставке новых через Enter.
                    trans_edit.text_changed.connect(
                        lambda *args, te=trans_edit: 
                        self.on_preview_text_modified(te, te.index, self.original_lines[te.index])
                    )
                    # Подключаем вставку новой строки через Enter
                    trans_edit.line_inserted.connect(
                        lambda ins_idx, move_text, te=trans_edit,
                               orl=orig_row_layout, trl=trans_row_layout,
                               mw=meta_row_widget, orw=orig_row_widget, trw=trans_row_widget:
                        self.on_preview_line_inserted(ins_idx, move_text, te, orl, trl, mw, orw, trw)
                    )
                    # Подключаем удаление/слияние строки через Backspace
                    trans_edit.line_deleted.connect(lambda del_idx, merge_text, te=trans_edit: self.on_preview_line_deleted(del_idx, te, merge_text))
                    
                    orig_edit.set_partner(trans_edit)
                    trans_edit.set_partner(orig_edit)
                    
                    orig_row_layout.addWidget(orig_edit, 0, Qt.AlignTop)
                    trans_row_layout.addWidget(trans_edit, 0, Qt.AlignTop)
                
                
                # Подключаем row_siblings на каждый PreviewTextEdit для трёхсторонней синхронизации
                siblings_tuple = (meta_row_widget, orig_row_widget, trans_row_widget)
                for sub in (orig_row_widget, trans_row_widget):
                    for edit in sub.findChildren(PreviewTextEdit):
                        edit.row_siblings = siblings_tuple
                
                # Активируем layout'ы
                meta_row_widget.layout().activate()
                orig_row_widget.layout().activate()
                trans_row_widget.layout().activate()
                
                # Добавляем растяжку в концы layout-ов, чтобы прижать всё содержимое к ВЕРХУ
                meta_row_layout.addStretch(1)
                orig_row_layout.addStretch(1)
                trans_row_layout.addStretch(1)

                # Добавляем три row-виджета в их соответствующие колонки
                self.preview_meta_layout.addWidget(meta_row_widget)
                self.preview_orig_layout.addWidget(orig_row_widget)
                self.preview_trans_layout.addWidget(trans_row_widget)
        finally:
            self.preview_content.setUpdatesEnabled(True)

    def on_preview_text_changed(self, index, new_text):
        """Прямая синхронизация изменений из предпросмотра в буфер данных (с дебаунсом)"""
        if self.prevent_text_changed or getattr(self, 'is_updating_from_preview', False):
            return
            
        try:
            if 0 <= index < len(self.original_lines):
                # Сохраняем правку в очередь (сохраняем переносы строк для мульти-строчных записей)
                self.pending_sync_edits[index] = new_text
                
                # Перезапускаем таймер синхронизации
                self.preview_sync_timer.stop()
                self.preview_sync_timer.start()
                
                # Визуальный отклик (опционально)
                self.statusBar().showMessage(get_translation(self.current_language, 'status_waiting_sync'))
                
                # Помечаем, что есть несохраненные изменения
                self.has_unsaved_changes = True
                        
        except Exception as e:
            print(f"Error buffering preview edit: {e}")

    def apply_pending_preview_sync(self):
        """Применяет накопленные в очереди правки из предпросмотра к основному редактору"""
        if not self.pending_sync_edits or self.prevent_text_changed:
            return
            
        self.is_updating_from_preview = True
        self.prevent_text_changed = True
        
        try:
            # Сортируем по индексу для предсказуемого обновления
            indices = sorted(self.pending_sync_edits.keys())
            
            # Получаем документ основного редактора
            if hasattr(self, 'translated_text_all'):
                doc = self.translated_text_all.document()
                
                for index in indices:
                    new_text = self.pending_sync_edits[index]
                    
                    # 1. Обновляем данные буфера
                    if 0 <= index < len(self.original_lines):
                        self.original_lines[index]['translated_text'] = new_text
                        # Keep is_empty in sync so filters don't wrongly hide non-empty lines
                        self.original_lines[index]['is_empty'] = not bool(new_text.strip())
                    
                    # 2. Обновляем визуальный блок в редакторе
                    block = doc.findBlockByNumber(index)
                    if block.isValid():
                        cursor = QTextCursor(block)
                        # Надежный метод замены текста в блоке БЕЗ затрагивания символа новой строки
                        cursor.movePosition(QTextCursor.StartOfBlock)
                        cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                        cursor.insertText(new_text)
                
                self.has_unsaved_changes = True
                self.update_stats()
                
            # Очищаем очередь
            self.pending_sync_edits.clear()
            self.statusBar().showMessage(get_translation(self.current_language, 'status_sync_complete'))


            
        except Exception as e:
            print(f"Error in apply_pending_preview_sync: {e}")
            ErrorLogger.log_error("SYNC_ERROR", f"Ошибка пакетной синхронизации: {e}")
        finally:
            self.prevent_text_changed = False
            self.is_updating_from_preview = False

    # [SEARCH_METHODS]
    def on_search_text_changed(self, text):
        """Обработка ввода текста в поиск"""
        try:
            self.search_matches = []
            self.search_match_types = []  # Типы совпадений: 'text_original', 'text_translated' или 'audio'
            self.current_match_index = -1
            
            # Снимаем выделение файла, если поиск очищен
            if not text:
                self.clear_audio_highlight()
                self.update_search_matches_label()
                return

            text_lower = text.lower()
            if len(text_lower) < 1:  # Ищем от 1 символа
                self.clear_audio_highlight()
                self.update_search_matches_label()
                return

            # Ищем совпадения в тексте - РАЗЛИЧНЫЕ записи для одного ключа если совпадение в обоих полях
            found_keys_audio = set()  # Для отслеживания ключей с аудио совпадениями (они приоритетные)
            
            for i, line in enumerate(self.original_lines):
                original = str(line.get('display_text', '')).lower()
                translated = str(line.get('translated_text', '')).lower()
                key = str(line.get('key', '')).lower()
                current_key = line.get('key')
                
                # Если найдено в оригинале - добавляем эту запись
                if text_lower in original:
                    self.search_matches.append(i)
                    self.search_match_types.append('text_original')
                
                # Если найдено в переводе - добавляем ОТДЕЛЬНУЮ запись (даже если уже есть из оригинала)
                if text_lower in translated:
                    self.search_matches.append(i)
                    self.search_match_types.append('text_translated')
                
                # Если найдено в ключе (и еще ничего не нашли) - добавляем запись
                if text_lower in key and not (text_lower in original or text_lower in translated):
                    self.search_matches.append(i)
                    self.search_match_types.append('text_original')  # Ключ выделяем как оригинал
            
            # Ищем совпадения в названиях аудиофайлов (независимо от текста)
            for i, line in enumerate(self.original_lines):
                current_key = line.get('key')
                audio_info = self.miz_resource_manager.get_audio_for_key(current_key)
                if audio_info:
                    audio_filename = audio_info[0].lower()
                    if text_lower in audio_filename:
                        # Добавляем аудио совпадение НЕЗАВИСИМО от текстовых совпадений (как и для text_original/text_translated)
                        if current_key not in found_keys_audio:
                            self.search_matches.append(i)
                            self.search_match_types.append('audio')
                            found_keys_audio.add(current_key)
            
            # Сортируем по индексу для поддержания порядка
            if self.search_matches:
                sorted_indices = sorted(range(len(self.search_matches)), key=lambda i: self.search_matches[i])
                self.search_matches = [self.search_matches[i] for i in sorted_indices]
                self.search_match_types = [self.search_match_types[i] for i in sorted_indices]
            
            if self.search_matches:
                self.current_match_index = 0
                match_index = self.search_matches[0]
                match_type = self.search_match_types[0]
                self.highlight_search_match(match_index, match_type, text_lower)
                
                # Если первое совпадение в файле, выделяем его
                if match_type == 'audio':
                    line = self.original_lines[match_index]
                    current_key = line.get('key')
                    self.highlight_audio_file(current_key)
                else:
                    self.clear_audio_highlight()
            else:
                self.clear_audio_highlight()
            
            self.update_search_matches_label()
        except Exception as e:
            ErrorLogger.log_error("SEARCH_ERROR", f"Error in search text changed: {e}")
            self.clear_audio_highlight()

    def search_next(self):
        """Переход к следующему совпадению"""
        try:
            if not self.search_matches:
                if self.search_input.text():
                    self.on_search_text_changed(self.search_input.text())
                if not self.search_matches:
                    return
                
            self.current_match_index += 1
            if self.current_match_index >= len(self.search_matches):
                self.current_match_index = 0
            
            match_index = self.search_matches[self.current_match_index]
            match_type = self.search_match_types[self.current_match_index] if self.current_match_index < len(self.search_match_types) else 'text'
            search_text = self.search_input.text()
            self.highlight_search_match(match_index, match_type, search_text)
            
            # Обновляем счетчик совпадений
            self.update_search_matches_label()
            
            # Обновляем выделение файла
            if match_type == 'audio':
                line = self.original_lines[match_index]
                current_key = line.get('key')
                self.highlight_audio_file(current_key)
            else:
                self.clear_audio_highlight()
        except Exception as e:
            ErrorLogger.log_error("SEARCH_ERROR", f"Error in search next: {e}")

    def search_prev(self):
        """Переход к предыдущему совпадению"""
        try:
            if not self.search_matches:
                if self.search_input.text():
                    self.on_search_text_changed(self.search_input.text())
                if not self.search_matches:
                    return
                
            self.current_match_index -= 1
            if self.current_match_index < 0:
                self.current_match_index = len(self.search_matches) - 1
            
            match_index = self.search_matches[self.current_match_index]
            match_type = self.search_match_types[self.current_match_index] if self.current_match_index < len(self.search_match_types) else 'text'
            search_text = self.search_input.text()
            self.highlight_search_match(match_index, match_type, search_text)
            
            # Обновляем счетчик совпадений
            self.update_search_matches_label()
            
            # Обновляем выделение файла
            if match_type == 'audio':
                line = self.original_lines[match_index]
                current_key = line.get('key')
                self.highlight_audio_file(current_key)
            else:
                self.clear_audio_highlight()
        except Exception as e:
            ErrorLogger.log_error("SEARCH_ERROR", f"Error in search prev: {e}")

    def highlight_search_match(self, line_index, match_type='text_original', search_text=''):
        """Скролл к строке в предпросмотре и синхронизация"""
        try:
            # Основной скролл к строке в превью
            if hasattr(self, 'preview_key_to_group_widget') and line_index < len(self.original_lines):
                current_key = self.original_lines[line_index].get('key')
                if current_key in self.preview_key_to_group_widget:
                    widget_data = self.preview_key_to_group_widget[current_key]
                    # Определяем правильный layout для скролла в зависимости от типа совпадения
                    scroll_area = None
                    # У нас один общий scroll_area для всего сплиттера
                    scroll_area = getattr(self, 'preview_scroll', None)
                    if match_type == 'text_original':
                        widget_to_scroll = widget_data[1] if isinstance(widget_data, (tuple, list)) else widget_data.get('orig')
                    elif match_type == 'text_translated':
                        widget_to_scroll = widget_data[2] if isinstance(widget_data, (tuple, list)) else widget_data.get('trans')
                    else:
                        # Для аудио скроллим к метаданным
                        widget_to_scroll = widget_data[0] if isinstance(widget_data, (tuple, list)) else widget_data.get('meta')
                    
                    if scroll_area and widget_to_scroll:
                        try:
                            scroll_area.ensureWidgetVisible(widget_to_scroll, xMargin=0, yMargin=100)
                        except Exception:
                            pass
                
            # Если это совпадение за текст - синхронизируем редакторы БЕЗ предварительной очистки
            # (sync_editors_to_line сам переопределит форматирование)
            if match_type in ('text_original', 'text_translated'):
                self.sync_editors_to_line(line_index, match_type, search_text)
            else:
                # Если это совпадение за файл - снимаем выделение с редакторов
                self.clear_editors_selection()
        except Exception as e:
            ErrorLogger.log_error("SEARCH_ERROR", f"Error in highlight match: {e}")

    def clear_editors_selection(self):
        """Снимает выделение со строк в редакторах оригинала и перевода"""
        try:
            # Очищаем ВСЕ выделения
            if hasattr(self, 'original_text_all') and self.original_text_all:
                self.original_text_all.setExtraSelections([])
                cursor = self.original_text_all.textCursor()
                cursor.clearSelection()
                self.original_text_all.setTextCursor(cursor)
            
            if hasattr(self, 'translated_text_all') and self.translated_text_all:
                self.translated_text_all.setExtraSelections([])
                cursor = self.translated_text_all.textCursor()
                cursor.clearSelection()
                self.translated_text_all.setTextCursor(cursor)
            
            # Снимаем выделение и в preview окне
            try:
                from widgets import PreviewTextEdit
                if hasattr(self, 'preview_layout') and self.preview_layout is not None:
                    for i in range(self.preview_layout.count()):
                        item = self.preview_layout.itemAt(i)
                        if item:
                            group_widget = item.widget()
                            if group_widget:
                                edits = group_widget.findChildren(PreviewTextEdit)
                                for edit in edits:
                                    edit.setExtraSelections([])
                                    cursor = edit.textCursor()
                                    cursor.clearSelection()
                                    edit.setTextCursor(cursor)
            except Exception:
                pass
        except Exception as e:
            ErrorLogger.log_error("SEARCH_ERROR", f"Error clearing editors selection: {e}")

    def sync_editors_to_line(self, line_index, match_type='text_original', search_text=''):
        """Синхронизация редакторов с выбранной строкой - выделяет только найденный текст"""
        try:
            if line_index < 0 or line_index >= len(self.original_lines):
                return
            
            search_text_lower = search_text.lower() if search_text else ''

            # Очищаем все прежние extra selections в основных редакторах и превью
            try:
                if hasattr(self, 'original_text_all') and self.original_text_all:
                    self.original_text_all.setExtraSelections([])
                if hasattr(self, 'translated_text_all') and self.translated_text_all:
                    self.translated_text_all.setExtraSelections([])

                from widgets import PreviewTextEdit
                # Очищаем все PreviewTextEdit в трёх layout'ах (вместо старого preview_layout)
                for layout in [getattr(self, 'preview_meta_layout', None),
                               getattr(self, 'preview_orig_layout', None),
                               getattr(self, 'preview_trans_layout', None)]:
                    if layout:
                        for i in range(layout.count()):
                            widget = layout.itemAt(i).widget() if layout.itemAt(i) else None
                            if widget:
                                edits = widget.findChildren(PreviewTextEdit)
                                for edit in edits:
                                    try:
                                        edit.setExtraSelections([])
                                    except Exception:
                                        pass
            except Exception:
                pass

            # Синхронизация оригинала - ТОЛЬКО если совпадение в оригинальном тексте
            if match_type == 'text_original':
                if hasattr(self, 'original_text_all') and self.original_text_all and self.original_text_all.document():
                    # Очищаем ВСЕ выделения
                    self.original_text_all.setExtraSelections([])
                    
                    block = self.original_text_all.document().findBlockByNumber(line_index)
                    if block.isValid():
                        block_text = block.text()
                        block_text_lower = block_text.lower()
                        
                        # Находим позицию найденного текста в строке
                        pos = block_text_lower.find(search_text_lower)
                        if pos >= 0:
                            # Снимаем все прежние extra selections
                            try:
                                self.original_text_all.setExtraSelections([])
                            except Exception:
                                pass

                            # Создаём QExtraSelection для правильного выделения
                            selection = QTextEdit.ExtraSelection()
                            selection.cursor = QTextCursor(block)
                            selection.cursor.setPosition(block.position() + pos)
                            selection.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(search_text))

                            # Форматирование
                            selection.format.setBackground(QColor('#ff9900'))
                            selection.format.setForeground(QColor('#000000'))

                            # Устанавливаем видимый курсор без выделения (чтобы не показывался стандартный серый фон)
                            cursor_for_view = QTextCursor(block)
                            cursor_for_view.setPosition(block.position() + pos)
                            cursor_for_view.clearSelection()
                            self.original_text_all.setTextCursor(cursor_for_view)

                            # Применяем выделение через ExtraSelection и обновляем вид
                            self.original_text_all.setExtraSelections([selection])
                            self.original_text_all.centerCursor()
                            try:
                                self.original_text_all.viewport().update()
                            except Exception:
                                pass
                
            # Синхронизация перевода - ТОЛЬКО если совпадение в переведенном тексте
            if match_type == 'text_translated':
                if hasattr(self, 'translated_text_all') and self.translated_text_all and self.translated_text_all.document():
                    # Очищаем ВСЕ выделения
                    self.translated_text_all.setExtraSelections([])
                    
                    if line_index < self.translated_text_all.blockCount():
                        block_trans = self.translated_text_all.document().findBlockByNumber(line_index)
                        if block_trans.isValid():
                            block_text = block_trans.text()
                            block_text_lower = block_text.lower()
                            
                            # Находим позицию найденного текста в строке
                            pos = block_text_lower.find(search_text_lower)
                            if pos >= 0:
                                # Снимаем все прежние extra selections
                                try:
                                    self.translated_text_all.setExtraSelections([])
                                except Exception:
                                    pass

                                # Создаём QExtraSelection для правильного выделения
                                selection = QTextEdit.ExtraSelection()
                                selection.cursor = QTextCursor(block_trans)
                                selection.cursor.setPosition(block_trans.position() + pos)
                                selection.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(search_text))

                                # Форматирование
                                selection.format.setBackground(QColor('#ff9900'))
                                selection.format.setForeground(QColor('#000000'))

                                # Устанавливаем видимый курсор без выделения
                                cursor_for_view = QTextCursor(block_trans)
                                cursor_for_view.setPosition(block_trans.position() + pos)
                                cursor_for_view.clearSelection()
                                self.translated_text_all.setTextCursor(cursor_for_view)

                                # Применяем выделение через ExtraSelection и обновляем вид
                                self.translated_text_all.setExtraSelections([selection])
                                self.translated_text_all.centerCursor()
                                try:
                                    self.translated_text_all.viewport().update()
                                except Exception:
                                    pass
            
            # Синхронизация превью - ТОЛЬКО для текстовых совпадений
            if match_type in ('text_original', 'text_translated') and search_text_lower:
                try:
                    if line_index < len(self.original_lines):
                        current_key = self.original_lines[line_index].get('key')
                        if hasattr(self, 'preview_key_to_group_widget') and current_key in self.preview_key_to_group_widget:
                            group_widget = self.preview_key_to_group_widget[current_key]
                            
                            # Найти все PreviewTextEdit в этой группе и выделить нужный индекс
                            from widgets import PreviewTextEdit
                            edits = []
                            # group_widget может быть кортежом (meta_row, orig_row, trans_row),
                            # либо старой dict-структурой, либо одиночным QWidget
                            try:
                                if isinstance(group_widget, (tuple, list)):
                                    for sub in group_widget:
                                        if hasattr(sub, 'findChildren'):
                                            edits.extend(sub.findChildren(PreviewTextEdit))
                                elif isinstance(group_widget, dict):
                                    for key in ('meta', 'orig', 'trans'):
                                        sub = group_widget.get(key)
                                        if sub and hasattr(sub, 'findChildren'):
                                            edits.extend(sub.findChildren(PreviewTextEdit))
                                elif hasattr(group_widget, 'findChildren'):
                                    edits = group_widget.findChildren(PreviewTextEdit)
                            except Exception:
                                edits = []

                            for edit in edits:
                                # Очищаем выделения у всех редакторов превью
                                edit.setExtraSelections([])
                                
                                if hasattr(edit, 'index') and edit.index == line_index:
                                    # Выделяем ТОЛЬКО нужное поле в зависимости от match_type
                                    # read_only=True для оригинала, read_only=False для перевода
                                    should_highlight = False
                                    if match_type == 'text_original' and edit.isReadOnly():
                                        should_highlight = True
                                    elif match_type == 'text_translated' and not edit.isReadOnly():
                                        should_highlight = True
                                    
                                    if should_highlight and edit.document():
                                        # В превью выделяем только найденное слово
                                        doc_text = edit.toPlainText()
                                        doc_text_lower = doc_text.lower()
                                        pos = doc_text_lower.find(search_text_lower)
                                        if pos >= 0:
                                            # Снимаем прежние extra selections
                                            try:
                                                edit.setExtraSelections([])
                                            except Exception:
                                                pass

                                            # Создаём QExtraSelection для правильного выделения
                                            selection = QTextEdit.ExtraSelection()
                                            selection.cursor = QTextCursor(edit.document())
                                            selection.cursor.setPosition(pos)
                                            selection.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(search_text))
                                            selection.format.setBackground(QColor('#ff9900'))
                                            selection.format.setForeground(QColor('#000000'))

                                            # Устанавливаем видимый курсор без выделения
                                            cursor_for_view = QTextCursor(edit.document())
                                            cursor_for_view.setPosition(pos)
                                            cursor_for_view.clearSelection()
                                            edit.setTextCursor(cursor_for_view)

                                            edit.setExtraSelections([selection])
                                            try:
                                                edit.viewport().update()
                                            except Exception:
                                                pass
                except Exception:
                    pass
        except Exception as e:
            ErrorLogger.log_error("SYNC_ERROR", f"Error syncing editors: {e}")

    def highlight_audio_file(self, audio_key):
        """Выделяет аудиофайл с цветом #ff9900 при поиске"""
        try:
            # Если выделенный файл уже совпадает с новым - ничего не делаем
            if self.highlighted_audio_key == audio_key:
                return
            
            # Снимаем выделение со старого файла
            if self.highlighted_audio_key and self.highlighted_audio_key in self.audio_labels_map:
                old_label = self.audio_labels_map[self.highlighted_audio_key]
                # Восстанавливаем обычный стиль
                is_audio_replaced = self.miz_resource_manager.is_audio_replaced(self.highlighted_audio_key)
                audio_info = self.miz_resource_manager.get_audio_for_key(self.highlighted_audio_key)
                is_current_locale = audio_info[1] if audio_info else False
                
                if is_audio_replaced:
                    audio_color = '#ff6666'
                elif is_current_locale:
                    audio_color = '#2ecc71'
                else:
                    audio_color = '#cccccc'
                
                border_style = "border: 1px solid #ff9900; border-radius: 4px;" if self.highlighted_audio_key == self.active_audio_key else "border: 1px solid transparent;"
                old_label.setStyleSheet(f'''
                    QLabel {{
                        color: {audio_color};
                        font-size: 12px;
                        text-decoration: underline;
                        background-color: transparent;
                        {border_style}
                        padding: 2px;
                    }}
                    QLabel:hover {{
                        background-color: #3d4256;
                        border-radius: 2px;
                    }}
                ''')
            
            # Применяем выделение к новому файлу
            if audio_key in self.audio_labels_map:
                new_label = self.audio_labels_map[audio_key]
                new_label.setStyleSheet(f'''
                    QLabel {{
                        color: #000000;
                        font-size: 12px;
                        text-decoration: underline;
                        background-color: #ff9900;
                        border: 1px solid transparent;
                        padding: 2px;
                    }}
                    QLabel:hover {{
                        background-color: #ff9900;
                        border-radius: 2px;
                    }}
                ''')
                self.highlighted_audio_key = audio_key
                
                # Скролл к выделенному файлу в превью
                if hasattr(self, 'preview_key_to_group_widget') and audio_key in self.preview_key_to_group_widget:
                    widgets_dict = self.preview_key_to_group_widget[audio_key]
                    # widgets_dict это кортеж (meta_row, orig_row, trans_row)
                    if isinstance(widgets_dict, (tuple, list)) and len(widgets_dict) > 0:
                        meta_widget = widgets_dict[0]
                        # Используем preview_meta_scroll для скролла к метаданным (аудио там)
                        if hasattr(self, 'preview_meta_scroll') and self.preview_meta_scroll:
                            try:
                                self.preview_meta_scroll.ensureWidgetVisible(meta_widget, xMargin=0, yMargin=100)
                            except Exception:
                                pass
                    elif isinstance(widgets_dict, dict):
                        # На случай если это dict (старая структура)
                        meta_widget = widgets_dict.get('meta')
                        if meta_widget and hasattr(self, 'preview_meta_scroll') and self.preview_meta_scroll:
                            try:
                                self.preview_meta_scroll.ensureWidgetVisible(meta_widget, xMargin=0, yMargin=100)
                            except Exception:
                                pass
        except Exception as e:
            ErrorLogger.log_error("AUDIO_HIGHLIGHT", f"Error highlighting audio: {e}")

    def clear_audio_highlight(self):
        """Снимает выделение с аудиофайла"""
        try:
            if self.highlighted_audio_key and self.highlighted_audio_key in self.audio_labels_map:
                label = self.audio_labels_map[self.highlighted_audio_key]
                # Восстанавливаем обычный стиль
                is_audio_replaced = self.miz_resource_manager.is_audio_replaced(self.highlighted_audio_key)
                audio_info = self.miz_resource_manager.get_audio_for_key(self.highlighted_audio_key)
                is_current_locale = audio_info[1] if audio_info else False
                
                if is_audio_replaced:
                    audio_color = '#ff6666'
                elif is_current_locale:
                    audio_color = '#2ecc71'
                else:
                    audio_color = '#cccccc'
                
                border_style = "border: 1px solid #ff9900; border-radius: 4px;" if self.highlighted_audio_key == self.active_audio_key else "border: 1px solid transparent;"
                label.setStyleSheet(f'''
                    QLabel {{
                        color: {audio_color};
                        font-size: 12px;
                        text-decoration: underline;
                        background-color: transparent;
                        {border_style}
                        padding: 2px;
                    }}
                    QLabel:hover {{
                        background-color: #3d4256;
                        border-radius: 2px;
                    }}
                ''')
                self.highlighted_audio_key = None
        except Exception as e:
            ErrorLogger.log_error("AUDIO_HIGHLIGHT", f"Error clearing audio highlight: {e}")

    def update_search_matches_label(self):
        """Обновляет label с количеством совпадений и текущим индексом"""
        try:
            if hasattr(self, 'search_matches_label'):
                count = len(self.search_matches)
                if count > 0 and self.current_match_index >= 0:
                    # Показываем счетчик "X из Y"
                    current_num = self.current_match_index + 1
                    label_text = f"{current_num} из {count}"
                else:
                    # Только общее количество
                    label_text = get_translation(self.current_language, 'search_matches', count=count)
                self.search_matches_label.setText(label_text)
        except Exception as e:
            ErrorLogger.log_error("SEARCH_ERROR", f"Error updating matches label: {e}")

    def schedule_preview_update(self, delay_ms: int = 200):
        """Планирует обновление предпросмотра с задержкой (debounce)"""
        if self.preview_update_timer is None:
            return
            
        # [PERFORMANCE] Адаптивная задержка в зависимости от количества строк
        line_count = len(self.original_lines)
        if line_count > 1000:
            effective_delay = 2000 # 2 секунды для огромных файлов
        elif line_count > 300:
            effective_delay = 1000 # 1 секунда для больших файлов
        else:
            effective_delay = delay_ms # Стандартные 200мс для малых файлов
            
        self.preview_update_timer.start(effective_delay)
    
    # [SAVE_METHODS]
    def save_file(self):
        """Сохраняет переведенный файл"""
        if not self.current_file_path:
            return
        
        # Проверяем расширение файла
        is_cmp = self.current_file_path.lower().endswith('.cmp')
        
        # Проверяем, открыт ли .miz файл или .cmp
        if self.current_miz_path:
            # Показываем диалог с опциями сохранения для .miz
            self.show_miz_save_dialog()
        elif is_cmp:
            # Показываем диалог сохранения для .cmp
            self.show_cmp_save_dialog()
        else:
            # Используем старую логику сохранения для обычных файлов
            self.save_regular_file()

    def save_regular_file(self):
        """Сохраняет обычный файл (не .miz)"""
        # Сначала принудительно синхронизируем правки из предпросмотра
        self.apply_pending_preview_sync()
        
        try:
            # Определяем начальную папку и имя файла
            if self.current_file_path:
                default_dir = self.last_save_folder if self.last_save_folder else os.path.dirname(self.current_file_path)
                default_name = os.path.basename(self.current_file_path)
            else:
                default_dir = self.last_save_folder
                default_name = "translated.txt"
            
            initial_path = os.path.join(default_dir, default_name)

            # Сохраняем настройки перед сохранением файла
            self.save_settings()

            print(f"\n{'='*50}")
            print(f"НАЧАЛО СОХРАНЕНИЯ ОБЫЧНОГО ФАЙЛА")
            print(f"{'='*50}")
            print(f"Всего строк в файле: {len(self.all_lines_data)}")
            print(f"Строк для перевода: {len(self.original_lines)}")

            # Используем новый метод generate_translated_content для получения переведённого контента
            result_content = self.generate_translated_content()

            # Сохраняем файл
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                get_translation(self.current_language, 'save_file_btn'),
                initial_path,
                'Text files (*.txt);;All files (*)'
            )
            if not save_path:
                return
            
            self.last_save_folder = os.path.dirname(save_path)
            self.save_settings()

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(result_content)

            filename = os.path.basename(save_path)
            self.statusBar().showMessage(get_translation(self.current_language, 'status_file_saved', filename=filename))
            
            # Сбрасываем индикацию после успешного сохранения
            self.reset_modified_display_state()
            
            self.show_save_report(save_path)
            print(f"✅ Файл сохранен: {filename}")

        except Exception as e:
            error_msg = f"Ошибка сохранения файла: {str(e)}"
            ErrorLogger.log_error("FILE_SAVE", error_msg)
            self.show_custom_dialog(
                get_translation(self.current_language, 'error_title'),
                error_msg,
                "error"
            )

    def save_dictionary_as_txt(self):
        """Сохраняет переведенный словарь как отдельный .txt файл"""
        try:
            # Определяем начальную папку и имя файла
            default_dir = self.last_save_folder if self.last_save_folder else os.path.dirname(self.current_file_path) if self.current_file_path else ""
            default_name = 'dictionary.txt'
            initial_path = os.path.join(default_dir, default_name)

            # Диалог выбора места сохранения
            save_path, _ = QFileDialog.getSaveFileName(
                self, 
                get_translation(self.current_language, 'save_file_btn'), 
                initial_path, 
                'Text files (*.txt);;All files (*)'
            )
            
            if not save_path:
                return
            
            self.last_save_folder = os.path.dirname(save_path)
            self.save_settings()

            print(f"\n{'='*50}")
            print(f"ЭКСПОРТ СЛОВАРЯ В .TXT: {os.path.basename(save_path)}")
            print(f"{'='*50}")
            
            # Используем generate_translated_content для получения переведённого контента
            result_content = self.generate_translated_content()
            
            # Сохраняем файл
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(result_content)
            
            # Показываем успех
            filename = os.path.basename(save_path)
            self.statusBar().showMessage(get_translation(self.current_language, 'status_file_saved', filename=filename))
            
            self.show_save_report(save_path)
            print(f"✅ Словарь успешно экспортирован в {filename}")
                
        except Exception as e:
            error_msg = f"Ошибка сохранения словаря: {str(e)}"
            ErrorLogger.log_error("DICT_SAVE_AS_TXT", error_msg)
            self.show_custom_dialog(get_translation(self.current_language, 'error_title'), error_msg, "error")
    
    def show_save_report(self, save_path, missing_slashes=None, backup_path=None):
        """Показывает отчет о сохранении"""
        dialog = CustomDialog(self)
        dialog.setWindowTitle(get_translation(self.current_language, 'save_report_title'))
        
        # Устанавливаем собственные стили для окна отчета о сохранении (тёмный фон + оранжевая рамка)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #404040;
                border: 2px solid #ff9900;
                border-radius: 10px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                background-color: transparent;
                border: none;
            }
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 10px 20px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        
        # 1. Заголовок "Файл сохранен"
        title_text = get_translation(self.current_language, 'save_report_title')
        title_label = QLabel(title_text)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 2. Имя файла (ОРАНЖЕВЫЙ)
        filename_label = QLabel(os.path.basename(save_path))
        filename_label.setAlignment(Qt.AlignCenter)
        filename_label.setStyleSheet("color: #ff9900; font-size: 14px; font-weight: bold;")
        filename_label.setWordWrap(True)
        layout.addWidget(filename_label)
        
        # 3. Статистика
        total_keys = len(self.all_lines_data)
        # Count non-empty original lines
        translatable_lines = sum(1 for line in self.original_lines if line.get('original_text', '').strip())
        # Count translated lines (where original is non-empty and translation is non-empty)
        translated_lines = sum(1 for line in self.original_lines 
                                if line.get('original_text', '').strip() and 
                                   line.get('translated_text', '').strip())
        
        stats_text = (
            f"{get_translation(self.current_language, 'save_stats')}\n"
            f"{get_translation(self.current_language, 'total_lines', count=total_keys)}\n"
            f"{get_translation(self.current_language, 'translatable_lines', count=translatable_lines)}\n"
            f"{get_translation(self.current_language, 'translated_lines', count=translated_lines)}\n"
            f"{get_translation(self.current_language, 'remaining_lines', count=max(0, translatable_lines - translated_lines))}"
        )
        
        stats_label = QLabel(stats_text)
        stats_label.setAlignment(Qt.AlignCenter)
        stats_label.setStyleSheet("color: #ffffff; font-size: 12px;")
        layout.addWidget(stats_label)
        
        # 4. Предупреждение о слешах
        if missing_slashes:
            warning_text = get_translation(self.current_language, 'slash_warning', count=len(missing_slashes))
            warning_label = QLabel(warning_text)
            warning_label.setAlignment(Qt.AlignCenter)
            warning_label.setStyleSheet("color: #ffff00; font-weight: bold;")
            warning_label.setWordWrap(True)
            layout.addWidget(warning_label)
            
        # 5. Бэкап (ЗЕЛЕНЫЙ)
        if backup_path:
            backup_title = QLabel(get_translation(self.current_language, 'backup_created'))
            backup_title.setAlignment(Qt.AlignCenter)
            backup_title.setStyleSheet("color: #ffffff; margin-top: 10px;")
            layout.addWidget(backup_title)
            
            backup_name = QLabel(os.path.basename(backup_path))
            backup_name.setAlignment(Qt.AlignCenter)
            backup_name.setStyleSheet("color: #00ff00; font-size: 14px; font-weight: bold;")
            backup_name.setWordWrap(True)
            layout.addWidget(backup_name)
        
        # Кнопка OK (центрированная)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton(get_translation(self.current_language, 'ok_btn'))
        ok_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.exec_()
        
        self.statusBar().showMessage(get_translation(self.current_language, 'status_file_saved', filename=os.path.basename(save_path)))

    def show_miz_save_dialog(self):
        """Показывает диалог с опциями сохранения для .miz файлов с темной темой"""
        # --- НАСТРОЙКИ РАЗМЕРОВ КНОПОК ---
        miz_btn_width = 250       # Ширина основных кнопок
        miz_cancel_width = 100    # Ширина кнопки отмена
        # ---------------------------------
        
        dialog = CustomDialog(self)
        dialog.setWindowTitle(get_translation(self.current_language, 'save_dialog_title'))
        dialog.setFixedWidth(450)  # Фиксированная ширина
        
        # Устанавливаем собственные стили для окна сохранения .miz
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: #404040;
                color: #ddd;
                border: 2px solid #ff9900;
                border-radius: 10px;
            }}
            QLabel {{
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                background-color: transparent;
            }}
            QPushButton {{
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 10px 20px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: {miz_btn_width}px;
                max-width: {miz_btn_width}px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: #e68a00;
            }}
            QPushButton:pressed {{
                background-color: #cc7a00;
            }}
            QPushButton#cancelBtn {{
                background-color: #ffffff;
                color: #000000;
                border-radius: 16px;
                min-width: {miz_cancel_width}px;
                max-width: {miz_cancel_width}px;
            }}
            QPushButton#cancelBtn:hover {{
                background-color: #a3a3a3;
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)
        
        # Заголовок (разделенный на две части)
        title_container = QWidget()
        title_container.setStyleSheet('background-color: transparent; border: none;')
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        title_layout.setAlignment(Qt.AlignCenter)
        
        # Текст "Миссия:"
        title_text = QLabel(get_translation(self.current_language, 'mission_file_label'))
        title_text.setAlignment(Qt.AlignCenter)
        title_text.setStyleSheet('''
            color: #ffffff;
            background-color: transparent;
            border: none;
        ''')
        title_layout.addWidget(title_text)
        
        # Имя файла (оранжевым цветом) с обрезкой до 40 символов
        full_filename = os.path.basename(self.current_miz_path)
        name_part, ext_part = os.path.splitext(full_filename)
        if len(name_part) > 40:
            display_name = name_part[:40] + "..." + ext_part
        else:
            display_name = full_filename
            
        filename_label = QLabel(display_name)
        filename_label.setAlignment(Qt.AlignCenter)
        filename_label.setStyleSheet('''
            color: #ff9900;
            background-color: transparent;
            border: none;
        ''')
        title_layout.addWidget(filename_label)
        
        layout.addWidget(title_container)
        
        # Информация
        info_label = QLabel(get_translation(self.current_language, 'save_dialog_info'))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Контейнер для кнопок (для центрирования)
        btns_layout = QVBoxLayout()
        btns_layout.setAlignment(Qt.AlignCenter)
        
        # Группа для перезаписи (с рамкой)
        overwrite_frame = QFrame()
        overwrite_frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #777;
                border-radius: 10px;
                background-color: transparent;
                margin: 5px;
            }}
            QPushButton {{ 
                margin: 5px; 
                min-width: {miz_btn_width}px;
                max-width: {miz_btn_width}px;
            }}
            QLabel {{
                border: none;
            }}
        """)
        overwrite_layout = QVBoxLayout(overwrite_frame)
        overwrite_layout.setContentsMargins(10, 10, 10, 10)
        overwrite_layout.setSpacing(5)
        overwrite_layout.setAlignment(Qt.AlignCenter)
        
        # Кнопка ПЕРЕЗАПИСАТЬ (основная)
        overwrite_btn = QPushButton(get_translation(self.current_language, 'overwrite_btn'))
        overwrite_btn.clicked.connect(lambda: self.handle_miz_save(dialog, 'overwrite'))
        overwrite_layout.addWidget(overwrite_btn)
        
        # Тоггл бэкапа
        backup_toggle_layout = QHBoxLayout()
        backup_toggle_layout.setAlignment(Qt.AlignCenter)
        backup_toggle_layout.setSpacing(10)
        
        self.miz_backup_cb = ToggleSwitch()
        self.miz_backup_cb.setChecked(getattr(self, 'create_backup', False))
        backup_toggle_layout.addWidget(self.miz_backup_cb)
        
        backup_label = QLabel(get_translation(self.current_language, 'miz_backup_label'))
        backup_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: normal; background-color: transparent;")
        backup_toggle_layout.addWidget(backup_label)
        
        overwrite_layout.addLayout(backup_toggle_layout)
        
        btns_layout.addWidget(overwrite_frame)
        
        # Кнопки "Сохранить как" и ".txt" помещаем в горизонтальные контейнеры для центрирования
        
        save_as_container = QHBoxLayout()
        save_as_container.addStretch()
        save_as_btn = QPushButton(get_translation(self.current_language, 'save_as_btn'))
        save_as_btn.setFixedWidth(miz_btn_width)
        save_as_btn.clicked.connect(lambda: self.handle_miz_save(dialog, 'save_as'))
        save_as_container.addWidget(save_as_btn)
        save_as_container.addStretch()
        
        # НОВАЯ КНОПКА: Сохранить отдельно в .txt
        save_txt_container = QHBoxLayout()
        save_txt_container.addStretch()
        save_txt_btn = QPushButton(get_translation(self.current_language, 'save_txt_separately_btn'))
        save_txt_btn.setFixedWidth(miz_btn_width)
        save_txt_btn.clicked.connect(lambda: [dialog.accept(), self.save_dictionary_as_txt()])
        save_txt_container.addWidget(save_txt_btn)
        save_txt_container.addStretch()
        
        # Отмена (центрированная и укороченная)
        cancel_container = QHBoxLayout()
        cancel_container.addStretch()
        cancel_btn = QPushButton(get_translation(self.current_language, 'cancel_btn'))
        cancel_btn.setObjectName("cancelBtn")
        # Обработчик отмены с сохранением состояния тоггла резервной копии
        def cancel_with_backup_save():
            # Сохраняем состояние тоггла резервной копии
            if hasattr(self, 'miz_backup_cb'):
                self.create_backup = self.miz_backup_cb.isChecked()
                self.save_settings()
            dialog.reject()
        
        cancel_btn.clicked.connect(cancel_with_backup_save)
        cancel_container.addWidget(cancel_btn)
        cancel_container.addStretch()
        
        btns_layout.addLayout(save_as_container)
        btns_layout.addLayout(save_txt_container)
        btns_layout.addLayout(cancel_container)
        
        layout.addLayout(btns_layout)
        
        dialog.exec_()



    def handle_miz_save(self, dialog, action):
        """Обработчик выбора действия сохранения"""
        # Сохраняем состояние бэкапа
        if hasattr(self, 'miz_backup_cb'):
            self.create_backup = self.miz_backup_cb.isChecked()
            self.save_settings()
            
        dialog.accept()
        
        if action == 'overwrite':
            self.save_miz_overwrite() # Больше не просит папку
        elif action == 'save_as':
            self.save_miz_as() # Больше не просит папку, только файл


    def create_backup_file(self, file_path):
        """Создает инкрементальную резервную копию файла (.backup, .backup1, ...)"""
        if not os.path.exists(file_path):
            return None
            
        base_backup_path = file_path + '.backup'
        backup_path = base_backup_path
        
        counter = 1
        while os.path.exists(backup_path):
            backup_path = f"{base_backup_path}{counter}"
            counter += 1
            
        try:
            shutil.copy2(file_path, backup_path)
            print(f"✅ Создана резервная копия: {os.path.basename(backup_path)}")
            return backup_path
        except Exception as e:
            ErrorLogger.log_error("BACKUP", f"Не удалось создать резервную копию: {e}")
            return None

    def save_miz_overwrite(self):
        """Перезаписывает исходный .miz файл (сохраняет ВСЕ локали)"""
        # Сначала принудительно синхронизируем правки из предпросмотра
        self.apply_pending_preview_sync()
        
        progress = MizProgressDialog(self)
        try:
            print(f"\n{'='*50}")
            print(f"ПЕРЕЗАПИСЬ .MIZ ФАЙЛА (ALL LOCALES)")
            print(f"{'='*50}")
            
            # 1. Сначала сохраняем текущее состояние в память
            if self.current_miz_folder:
                 self.miz_trans_memory[self.current_miz_folder] = {
                    'original_lines': copy.deepcopy(self.original_lines),
                    'all_lines_data': copy.deepcopy(self.all_lines_data),
                    'original_content': self.original_content
                }
            
            progress.show()
            progress.set_value(10)
            
            # Создаем резервную копия если нужно
            backup_path = None
            if getattr(self, 'create_backup', False):
                progress.set_value(20)
                backup_path = self.create_backup_file(self.current_miz_path)
            
            progress.set_value(70)
            
            # Переменная для отслеживания успеха
            success = False
            
            # Временный файл для записи изменений
            temp_miz = self.current_miz_path + '.tmp'
            
            try:
                # Читаем оригинал и пишем в темп
                with zipfile.ZipFile(self.current_miz_path, 'r') as zin:
                    with zipfile.ZipFile(temp_miz, 'w', compression=zin.compressionlevel if hasattr(zin, 'compressionlevel') else zipfile.ZIP_DEFLATED) as zout:
                        progress.set_value(50)
                        
                        # Собираем данные для всех локалей из памяти
                        locales_data = {} # {folder: binary_content}
                        
                        # Список разрешенных папок локалей (для удаления мусора из удаленных локалей)
                        allowed_folders = [f.lower() for f in self.current_miz_l10n_folders]
                        
                        for locale, data in self.miz_trans_memory.items():
                             # Генерируем контент для каждой локали
                             # ВРЕМЕННЫЙ ХАК: Используем вспомогательный метод генерации
                             # который принимает данные, а не берет self.*
                             content = self.generate_content_from_data(data['all_lines_data'])
                             locales_data[locale] = content.encode('utf-8')

                        # Список файлов, которые мы заменили
                        replaced_files = []

                        for item in zin.infolist():
                            # Сохраняем оригинальное имя
                            original_filename_for_read = item.filename
                            
                            try:
                                fixed_name = item.filename.encode('cp437').decode('utf-8')
                                item.filename = fixed_name
                                item.flag_bits |= 0x800  # UTF-8 flag
                            except (UnicodeEncodeError, UnicodeDecodeError):
                                pass

                            is_handled = False
                            # Нормализуем путь для надежной проверки
                            # Нормализуем путь (убираем лишние слеши и приводим к нижнему регистру для сравнения)
                            path_norm = item.filename.replace('\\', '/').strip('/')
                            path_norm_lower = path_norm.lower()
                            
                            for locale in locales_data:
                                # 1. Проверка словаря
                                if path_norm_lower == f'l10n/{locale}/dictionary'.lower():
                                    zout.writestr(item, locales_data[locale])
                                    replaced_files.append(path_norm)
                                    is_handled = True
                                    print(f"DEBUG: Updated dictionary: {item.filename}")
                                    break
                                
                                # 2. Проверка mapResource
                                if path_norm_lower == f'l10n/{locale}/mapResource'.lower():
                                    updated_map = self.miz_resource_manager.get_updated_map_resource_content(zin, locale)
                                    zout.writestr(item, updated_map.encode('utf-8'))
                                    replaced_files.append(path_norm)
                                    is_handled = True
                                    print(f"DEBUG: Updated mapResource: {item.filename}")
                                    break
                            
                            if not is_handled:
                                # Проверяем, не принадлежит ли этот файл удаленной локали (робастно)
                                if path_norm.lower().startswith("l10n/"):
                                    parts = path_norm.split('/')
                                    if len(parts) > 1:
                                        folder_part = parts[1].lower()
                                        # Проверяем наличие в списке разрешенных локалей (регистронезависимо)
                                        if folder_part not in allowed_folders:
                                            print(f"DEBUG: REMOVING residual file from deleted locale: {item.filename}")
                                            continue
                                        
                                # Проверяем, не заменен ли этот файл (pending_files)
                                path_norm_lower = path_norm.lower()
                                is_replaced = False
                                for pending_path in self.miz_resource_manager.get_pending_files():
                                    if pending_path.lower() == path_norm_lower:
                                        is_replaced = True
                                        break
                                # Проверяем, не помечен ли файл на удаление (старый аудиофайл)
                                if not is_replaced:
                                    for del_path in self.miz_resource_manager.get_files_to_delete():
                                        if del_path.lower() == path_norm_lower:
                                            is_replaced = True
                                            print(f"DEBUG: DELETING old audio file: {item.filename}")
                                            break
                                if is_replaced:
                                    continue

                                zout.writestr(item, zin.read(original_filename_for_read))
                        
                        # Добавляем новые словари и mapResource (созданные локали), которых не было в архиве
                        for locale, content in locales_data.items():
                             # Dictionary
                             dict_path = f'l10n/{locale}/dictionary'
                             already_replaced = any(f.lower() == dict_path.lower() for f in replaced_files)
                             if not already_replaced:
                                  zout.writestr(dict_path, content)
                                  print(f"DEBUG: Created new dictionary {dict_path}")
                                  
                             # mapResource
                             map_path = f'l10n/{locale}/mapResource'
                             already_replaced_map = any(f.lower() == map_path.lower() for f in replaced_files)
                             if not already_replaced_map:
                                  updated_map = self.miz_resource_manager.get_updated_map_resource_content(zin, locale)
                                  zout.writestr(map_path, updated_map.encode('utf-8'))
                                  print(f"DEBUG: Created new mapResource {map_path}")

                        # Записываем новые/замененные файлы ресурсов
                        for target_path, source_path in self.miz_resource_manager.get_pending_files().items():
                            if os.path.exists(source_path):
                                zout.write(source_path, arcname=target_path)
                                print(f"DEBUG: Wrote pending file: {target_path}")

                
                # Atomic replace: заменяем оригинал новым файлом (без отдельного удаления)
                try:
                    print(f"DEBUG: Replacing {self.current_miz_path} with {temp_miz}")
                    # os.replace атомарно заменит файл в той же файловой системе
                    os.replace(temp_miz, self.current_miz_path)
                    print(f"DEBUG: Replace successful")
                except Exception as re:
                    print(f"ERROR: Failed to replace archive: {re}")
                    # Если замена не удалась — удаляем temp (чтобы не оставлять мусор)
                    try:
                        if os.path.exists(temp_miz):
                            os.remove(temp_miz)
                    except Exception:
                        pass
                    raise
                # self.current_miz_folder = target_folder # FIX: Не меняем текущую рабочую папку при сохранении
                self.update_file_labels()
                
                # Сбрасываем индикацию после успешного сохранения
                # (Обновляем референс до вызова reset_modified, так как он вызовет apply_filters)
                if hasattr(self, 'reference_loader'):
                    self.reference_loader.clear_cache()
                    try:
                        self.reference_data = self.reference_loader.load_locale_from_miz(
                            self.current_miz_path, getattr(self, 'reference_locale', 'DEFAULT')
                        )
                    except Exception:
                        pass
                
                self.reset_modified_display_state()
                
                success = True
                progress.set_value(100)
                
            except Exception as e:
                if os.path.exists(temp_miz):
                    os.remove(temp_miz)
                raise e
            finally:
                progress.close()
            
            if success:
                # Фиксируем замены в кэшах (файлы уже в архиве)
                self.miz_resource_manager.commit_pending_changes()
                # Обновляем предпросмотр (зелёный → оранжевый, замены зафиксированы)
                self.update_preview()
                # Показываем отчет
                self.show_save_report(self.current_miz_path, backup_path=backup_path)
                
        except Exception as e:
            error_msg = get_translation(self.current_language, 'error_miz_save', error=str(e))
            ErrorLogger.log_error("MIZ_OVERWRITE", error_msg)
            self.show_custom_dialog(get_translation(self.current_language, 'error_title'), error_msg, "error")

    def save_miz_as(self):
        """Сохраняет перевод в новый .miz файл (все локали)"""
        # Сначала принудительно синхронизируем правки из предпросмотра
        self.apply_pending_preview_sync()
        
        progress = None
        try:
            # Определяем начальную папку и имя файла
            default_dir = self.last_save_folder if self.last_save_folder else os.path.dirname(self.current_miz_path) if self.current_miz_path else ""
            default_name = os.path.splitext(os.path.basename(self.current_miz_path))[0] + f"_translated.miz" if self.current_miz_path else f"mission_translated.miz"
            initial_path = os.path.join(default_dir, default_name)

            # Диалог выбора файла (стандартный)
            save_path, _ = QFileDialog.getSaveFileName(self, get_translation(self.current_language, 'save_dialog_title'), initial_path, "DCS Mission (*.miz)")
            
            if not save_path:
                return

            self.last_save_folder = os.path.dirname(save_path)
            
            # 1. Сначала сохраняем текущее состояние в память
            if self.current_miz_folder:
                 self.miz_trans_memory[self.current_miz_folder] = {
                    'original_lines': copy.deepcopy(self.original_lines),
                    'all_lines_data': copy.deepcopy(self.all_lines_data),
                    'original_content': self.original_content
                }

            progress = MizProgressDialog(self)
            progress.show()
            progress.set_value(10)
            
            # --- ВНУТРЕННЯЯ ЛОГИКА СОХРАНЕНИЯ (ДУБЛИРУЕТ SAVE_OVERWRITE НО В ДРУГОЙ ФАЙЛ) ---
            # ... можно было бы вынести в отдельный метод, но пока дублируем с адаптацией под другой save_path
            
            # Временный файл не нужен, пишем сразу в save_path (но читаем из current)
            try:
                with zipfile.ZipFile(self.current_miz_path, 'r') as zin:
                    with zipfile.ZipFile(save_path, 'w', compression=zin.compressionlevel if hasattr(zin, 'compressionlevel') else zipfile.ZIP_DEFLATED) as zout:
                        # ... та же логика копирования и замены ...
                        progress.set_value(50)
                        locales_data = {} 
                        
                        # Список разрешенных папок локалей
                        allowed_folders = [f.lower() for f in self.current_miz_l10n_folders]
                        
                        for locale, data in self.miz_trans_memory.items():
                             content = self.generate_content_from_data(data['all_lines_data'])
                             locales_data[locale] = content.encode('utf-8')

                        replaced_files = []
                        for item in zin.infolist():
                            original_filename_for_read = item.filename
                            try:
                                fixed_name = item.filename.encode('cp437').decode('utf-8')
                                item.filename = fixed_name
                                item.flag_bits |= 0x800 
                            except: pass

                            is_handled = False
                            # Нормализуем путь (убираем лишние слеши и приводим к нижнему регистру для сравнения)
                            path_norm = item.filename.replace('\\', '/').strip('/')
                            path_norm_lower = path_norm.lower()
                            
                            for locale in locales_data:
                                # 1. Проверка словаря
                                if path_norm_lower == f'l10n/{locale}/dictionary'.lower():
                                    zout.writestr(item, locales_data[locale])
                                    replaced_files.append(path_norm)
                                    is_handled = True
                                    print(f"DEBUG: Updated dictionary: {item.filename}")
                                    break
                                
                                # 2. Проверка mapResource
                                if path_norm_lower == f'l10n/{locale}/mapResource'.lower():
                                    updated_map = self.miz_resource_manager.get_updated_map_resource_content(zin, locale)
                                    zout.writestr(item, updated_map.encode('utf-8'))
                                    replaced_files.append(path_norm)
                                    is_handled = True
                                    print(f"DEBUG: Updated mapResource: {item.filename}")
                                    break
                            
                            if not is_handled:
                                # Проверяем, не принадлежит ли этот файл удаленной локали (робастно)
                                if path_norm.lower().startswith("l10n/"):
                                    parts = path_norm.split('/')
                                    if len(parts) > 1:
                                        folder_part = parts[1].lower()
                                        if folder_part not in allowed_folders:
                                            print(f"DEBUG: REMOVING residual file from deleted locale: {item.filename}")
                                            continue
                                            
                                # Проверяем, не заменен ли этот файл (pending_files)
                                path_norm_lower = path_norm.lower()
                                is_replaced = False
                                for pending_path in self.miz_resource_manager.get_pending_files():
                                    if pending_path.lower() == path_norm_lower:
                                        is_replaced = True
                                        break
                                # Проверяем, не помечен ли файл на удаление (старый аудиофайл)
                                if not is_replaced:
                                    for del_path in self.miz_resource_manager.get_files_to_delete():
                                        if del_path.lower() == path_norm_lower:
                                            is_replaced = True
                                            print(f"DEBUG: DELETING old audio file: {item.filename}")
                                            break
                                if is_replaced:
                                    continue
                                    
                                zout.writestr(item, zin.read(original_filename_for_read))
                        
                        # Добавляем новые словари и mapResource (созданные локали), которых не было в архиве
                        for locale, content in locales_data.items():
                             # Dictionary
                             dict_path = f'l10n/{locale}/dictionary'
                             already_replaced = any(f.lower() == dict_path.lower() for f in replaced_files)
                             if not already_replaced:
                                  zout.writestr(dict_path, content)
                                  print(f"DEBUG: Created new dictionary {dict_path}")
                                  
                             # mapResource
                             map_path = f'l10n/{locale}/mapResource'
                             already_replaced_map = any(f.lower() == map_path.lower() for f in replaced_files)
                             if not already_replaced_map:
                                  updated_map = self.miz_resource_manager.get_updated_map_resource_content(zin, locale)
                                  zout.writestr(map_path, updated_map.encode('utf-8'))
                                  print(f"DEBUG: Created new mapResource {map_path}")

                        # Записываем новые/замененные файлы ресурсов
                        for target_path, source_path in self.miz_resource_manager.get_pending_files().items():
                            if os.path.exists(source_path):
                                zout.write(source_path, arcname=target_path)
                                print(f"DEBUG: Wrote pending file: {target_path}")

                success = True
                progress.set_value(100)
                
                # Обновляем текущий путь к миссии
                self.current_miz_path = save_path
                self.update_stats()
                self.update_file_labels()

            except Exception as e:
                if os.path.exists(save_path):
                    os.remove(save_path)
                raise e
            
            if success:
                # Фиксируем замены в кэшах (файлы уже в архиве)
                self.miz_resource_manager.commit_pending_changes()
                
                # РЕФРЕШ: Сбрасываем кэш референса для нового файла
                if hasattr(self, 'reference_loader'):
                    self.reference_loader.clear_cache()
                    try:
                        self.reference_data = self.reference_loader.load_locale_from_miz(
                            self.current_miz_path, getattr(self, 'reference_locale', 'DEFAULT')
                        )
                    except Exception:
                        pass
                        
                # Сбрасываем индикацию и фиксируем изменения как новые оригинальные данные
                self.reset_modified_display_state()
            # ----------------------------------------------------------------------------------

        except Exception as e:
            error_msg = get_translation(self.current_language, 'error_miz_save', error=str(e))
            ErrorLogger.log_error("MIZ_SAVE_AS", error_msg)
            self.show_custom_dialog("Error", error_msg, "error")
        finally:
             if progress: progress.close()



    def replace_file_in_zip(self, zip_path, file_path_within_zip, new_content):
        """Безопасная замена файла в ZIP-архиве"""
        temp_zip = None
        try:
            print(f"🔄 Начинаю замену файла в архиве: {file_path_within_zip}")
            
            # Создаем временный файл
            temp_zip = zip_path + ".temp"
            
            # Создаем новый архив с замененным файлом
            with zipfile.ZipFile(zip_path, 'r') as zin, \
                 zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zout:
                
                # Копируем все файлы из старого архива
                for item in zin.infolist():
                    if item.filename != file_path_within_zip:
                        # Копируем без изменений
                        data = zin.read(item.filename)
                        zout.writestr(item, data)
                        print(f"   📋 Скопирован: {item.filename}")
                    else:
                        print(f"   ⏩ Пропускаем старую версию: {item.filename}")
                
                # Добавляем новый/обновленный файл dictionary
                zout.writestr(file_path_within_zip, new_content.encode('utf-8'))
                print(f"   📝 Добавлен новый файл: {file_path_within_zip}")
            
            # Заменяем оригинальный архив
            os.remove(zip_path)
            os.rename(temp_zip, zip_path)
            
            print(f"✅ Файл {file_path_within_zip} успешно заменен в архиве")
            return True
            
        except Exception as e:
            error_msg = f"Ошибка при замене файла в ZIP-архиве: {str(e)}"
            ErrorLogger.log_error("ZIP_REPLACE", error_msg, f"Путь: {zip_path}, файл: {file_path_within_zip}")
            print(f"⚠ {error_msg}")
            
            # Очищаем временный файл при ошибке
            if temp_zip and os.path.exists(temp_zip):
                try:
                    os.remove(temp_zip)
                    print(f"🧹 Удален временный файл: {temp_zip}")
                except:
                    pass
                    
            return False
        
    def generate_translated_content(self):
        """Генерирует переведенное содержимое для dictionary с помощью нового парсера"""
        import tempfile
        import os

        # Создаем временный файл для парсера
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False, encoding='utf-8') as f:
            f.write(self.original_content)
            temp_file = f.name

        try:
            # Собираем переводы в словарь для парсера
            # Формат: ключ -> список переведённых строк (каждая строка файла - отдельный элемент)
            translations = {}

            # Группируем переводы по ключу
            for line_data in self.all_lines_data:
                key = line_data['key']

                if key not in translations:
                    translations[key] = []

                # Используем translated_text, даже если он пустой ('')
                # Падаем назад на оригинал только если перевода вообще нет (None)
                raw_translated = line_data.get('translated_text')
                if raw_translated is None:
                    raw_translated = line_data.get('original_text', '')
                
                if raw_translated:
                    parts = raw_translated.split('\n')
                    translations[key].extend(parts)
                else:
                    # Пустая строка
                    translations[key].append('')

            # Используем новый парсер для сохранения
            # Сначала парсим файл для получения структуры
            self.dictionary_parser.entries = {}
            self.dictionary_parser.parse_file(temp_file)

            # Сохраняем переводы
            self.dictionary_parser.save_translations(temp_file + '_out', translations)

            # Читаем результат
            with open(temp_file + '_out', 'r', encoding='utf-8') as f:
                result_content = f.read()

            return result_content

        finally:
            # Удаляем временные файлы
            for temp_file_path in [temp_file, temp_file + '_out']:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

    def get_line_data_by_key(self, key):
        """Вспомогательный метод для поиска данных по ключу"""
        for line_data in self.all_lines_data:
            if line_data['key'] == key:
                return line_data
        return None

    def register_custom_tooltip(self, widget, text, side='bottom'):
        """Регистрирует виджет для показа кастомного тултипа (QLabel-based)."""
        if not hasattr(self, '_custom_tooltip_map'):
            self._custom_tooltip_map = {}
        # Сохраняем текст и сторону появления
        self._custom_tooltip_map[widget] = {'text': text, 'side': side}
        try:
            widget.setToolTip('')
        except Exception:
            pass
        try:
            widget.installEventFilter(self)
        except Exception:
            pass

    def unregister_custom_tooltip(self, widget):
        """Удаляет регистрацию кастомного тултипа и возвращает виджет в исходное состояние."""
        try:
            if hasattr(self, '_custom_tooltip_map') and widget in self._custom_tooltip_map:
                del self._custom_tooltip_map[widget]
        except Exception:
            pass
        try:
            widget.removeEventFilter(self)
        except Exception:
            pass
        try:
            widget.setToolTip('')
        except Exception:
            pass
    
    # [EVENT_HANDLERS]
    def on_translation_changed(self):
        """Обработчик изменения текста перевода"""
        if self.prevent_text_changed or self.is_updating_display:
            return
        
        # Получаем все строки перевода
        raw_text = self.translated_text_all.toPlainText()
        translation_lines = raw_text.split('\n')
        
        # Исправление: если текст заканчивается переносом строки, split('\n') 
        # добавляет лишнюю пустую строку в конце. Удаляем её, если она пустая.
        if translation_lines and not translation_lines[-1] and raw_text.endswith('\n'):
            translation_lines.pop()

        # [SMART PASTE] Попытка обнаружить и удалить контекст AI
        context_stripped = False
        ai_context = getattr(self, 'ai_context_1', '').strip()
        
        if ai_context and len(translation_lines) > len(self.original_lines):
            context_lines = ai_context.split('\n')
            # Проверяем, совпадают ли первые строки с контекстом
            if len(translation_lines) >= len(context_lines):
                # Сравниваем строки
                match = True
                for i in range(len(context_lines)):
                    if translation_lines[i] != context_lines[i]:
                        match = False
                        break
                
                if match:
                    # Контекст найден, удаляем его
                    print("DEBUG: Context detected in paste, stripping...")
                    
                    # Определяем, сколько удалять (контекст + отступ)
                    lines_to_remove = len(context_lines)
                    
                    # Проверяем пустую строку после контекста (которую добавляет copy_all_english как \n\n)
                    if len(translation_lines) > lines_to_remove and not translation_lines[lines_to_remove].strip():
                        lines_to_remove += 1
                        
                    translation_lines = translation_lines[lines_to_remove:]
                    context_stripped = True
                    self.statusBar().showMessage(get_translation(self.current_language, 'status_context_stripped'))

        # [BUFFER] Мы больше не обрезаем строки принудительно здесь,
        # чтобы пользователь мог свободно нажимать Enter.
        # Теперь translation_lines может быть длиннее, чем self.original_lines.
        
        # [BUFFER SYNC] Синхронизируем количество строк в левом окне (оригинал)
        # чтобы скроллбары всегда совпадали по высоте
        current_trans_count = len(translation_lines)
        required_orig_count = len(self.original_lines)
        
        # Определяем, сколько строк должно быть в оригинальном окне
        target_orig_window_count = max(required_orig_count, current_trans_count)
        
        # Получаем текущее количество строк в виджете оригинала
        actual_orig_window_lines = self.original_text_all.toPlainText().split('\n')
        
        if len(actual_orig_window_lines) != target_orig_window_count:
            # Обновляем оригинал, добавляя или убирая пустые "буферные" строки
            self.prevent_text_changed = True # На всякий случай, хотя оригинал ReadOnly
            
            # Сохраняем позицию скролла оригинала
            orig_scroll = self.original_text_all.verticalScrollBar().value()
            
            # Формируем новый текст для окна оригинала
            new_orig_lines = [line['original_text'] for line in self.original_lines]
            if target_orig_window_count > len(new_orig_lines):
                new_orig_lines.extend([''] * (target_orig_window_count - len(new_orig_lines)))
            
            self.original_text_all.setPlainText('\n'.join(new_orig_lines))
            self.original_text_all.verticalScrollBar().setValue(orig_scroll)
            
            self.prevent_text_changed = False

        if context_stripped:
             # Если контекст удалили, обновляем виджет
            self.prevent_text_changed = True
            
            cursor = self.translated_text_all.textCursor()
            scroll_pos = self.translated_text_all.verticalScrollBar().value()
            
            self.translated_text_all.setPlainText('\n'.join(translation_lines))
            
            self.translated_text_all.verticalScrollBar().setValue(scroll_pos)
            self.translated_text_all.setTextCursor(cursor)
            
            self.prevent_text_changed = False

        
        # Обновляем переводы в данных (только для реальных строк оригинала!)
        # Сначала сохраним старые значения для вычисления diff'а
        old_texts = [line.get('translated_text', '') for line in self.original_lines]

        changed_indices = set()
        for i, line_data in enumerate(self.original_lines):
            if i < len(translation_lines):
                new_text = translation_lines[i].rstrip('\r')
            else:
                new_text = ''

            # Сравнение старого и нового значения
            try:
                if old_texts[i] != new_text:
                    changed_indices.add(i)
            except Exception:
                # В случае проблем с индексами — пометим индекс на обновление
                changed_indices.add(i)

            line_data['translated_text'] = new_text

        # [BUFFER] Сохраняем "лишние" строки буфера отдельно
        if len(translation_lines) > len(self.original_lines):
            self.extra_translation_lines = translation_lines[len(self.original_lines):]
        else:
            self.extra_translation_lines = []

        self.update_stats()

        # [LIVE FILTER] Если включен фильтр пустых строк, запускаем отложенное обновление
        if self.filter_empty or getattr(self, 'filter_empty_keys', True):
            # Задержка 1500мс, чтобы не дергать список прямо во время ввода
            self.filter_debounce_timer.start(1500)

        # Если есть изменившиеся индексы — пытаемся селективно обновить только соответствующие группы
        if changed_indices:
            try:
                updated = self.update_preview_for_indices(changed_indices)
            except Exception:
                updated = False

            if not updated:
                # fallback: полная перестройка (debounced)
                self.schedule_preview_update(1500)
        else:
            # Нет изменений — ничего не делаем
            pass

        if changed_indices:
            self.has_unsaved_changes = True
        self.statusBar().showMessage(get_translation(self.current_language, 'status_translation_updated'))
    
    def clear_translation(self):
        """Очищает весь перевод"""
        if not self.original_lines:
            return
        
        # Используем кастомный диалог
        dialog = CustomDialog(self)
        dialog.setWindowTitle(get_translation(self.current_language, 'clear_dialog_title'))
        
        # Устанавливаем собственные стили для окна подтверждения очистки (тёмный фон + оранжевая рамка)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #404040;
                border: 2px solid #ff9900;
                border-radius: 10px;
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                background-color: transparent;
                border: none;
            }
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 10px 20px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
            QPushButton#cancelBtn {
                background-color: #ffffff;
                color: #000000;
                border-radius: 16px;
            }
            QPushButton#cancelBtn:hover {
                background-color: #a3a3a3;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Текст вопроса
        question_label = QLabel(get_translation(self.current_language, 'clear_question'))
        question_label.setAlignment(Qt.AlignCenter)
        question_label.setWordWrap(True)
        
        # Кнопки
        button_layout = QHBoxLayout()
        yes_btn = QPushButton(get_translation(self.current_language, 'yes_btn'))
        yes_btn.clicked.connect(lambda: self.handle_clear_confirmation(dialog, True))
        no_btn = QPushButton(get_translation(self.current_language, 'no_btn'))
        no_btn.setObjectName("cancelBtn")
        no_btn.clicked.connect(lambda: self.handle_clear_confirmation(dialog, False))
        
        button_layout.addStretch()
        button_layout.addWidget(yes_btn)
        button_layout.addWidget(no_btn)
        button_layout.addStretch()
        
        layout.addWidget(question_label)
        layout.addLayout(button_layout)
        
        # Показываем диалог
        dialog.exec_()
    
    def handle_clear_confirmation(self, dialog, confirmed):
        """Обработчик подтверждения очистки перевода"""
        dialog.accept()
        if confirmed:
            # Очищаем перевод
            changed_indices = []
            for i, line_data in enumerate(self.original_lines):
                if line_data.get('translated_text', ''):
                    line_data['translated_text'] = ''
                    changed_indices.append(i)

            self.extra_translation_lines = []

            # Обновляем основное отображение БЕЗ перестройки превью
            self.update_display(update_preview=False)

            # Если были реальные изменения — пытаемся селективно обновить превью
            if changed_indices:
                try:
                    updated = self.update_preview_for_indices(changed_indices)
                except Exception:
                    updated = False

                # Если селективный апдейт не сработал — планируем перестроение (debounced)
                if not updated:
                    try:
                        self.schedule_preview_update(200)
                    except Exception:
                        try:
                            self.update_preview()
                        except Exception:
                            pass

                self.has_unsaved_changes = True
            else:
                # Ничего не изменилось — не трогаем превью и не планируем перестройку
                pass

            self.statusBar().showMessage(get_translation(self.current_language, 'status_translation_cleared'))

    def show_custom_dialog(self, title, message, dialog_type="info"):
        """Показывает кастомный диалог с указанным типом"""
        dialog = CustomDialog(self)
        dialog.setWindowTitle(title)
        
        # Устанавливаем фиксированный размер для диалога
        dialog.setFixedSize(400, 200)
        
        # Вместо установки глобального стиля для QDialog, устанавливаем только для содержимого
        content_style = """
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                background-color: transparent;
                border: none;
            }
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 10px 20px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        """
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # Создаем контейнер для содержимого
        content_widget = QWidget()
        content_widget.setStyleSheet(content_style)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        error_label = QLabel(message)
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setWordWrap(True)
        error_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        ok_btn = QPushButton(get_translation(self.current_language, 'ok_btn'))
        ok_btn.clicked.connect(dialog.accept)
        
        # Контейнер для кнопки (чтобы не растягивалась)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        
        content_layout.addWidget(error_label)
        content_layout.addLayout(btn_layout)
        
        layout.addWidget(content_widget)
        
        dialog.exec_()

    def show_question_dialog(self, title, message):
        """Показывает кастомный диалог с кнопками Да/Нет в стиле приложения"""
        dialog = CustomDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(440, 200)
        
        content_style = """
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                background-color: transparent;
                border: none;
            }
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 10px 20px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
            QPushButton#noBtn {
                background-color: #ffffff;
                color: #000000;
            }
            QPushButton#noBtn:hover {
                background-color: #a3a3a3;
            }
        """
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 30, 30, 30)
        
        content_widget = QWidget()
        content_widget.setStyleSheet(content_style)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        
        yes_btn = QPushButton(get_translation(self.current_language, 'yes_btn'))
        no_btn = QPushButton(get_translation(self.current_language, 'no_btn'))
        no_btn.setObjectName("noBtn")
        
        yes_btn.clicked.connect(dialog.accept)
        no_btn.clicked.connect(dialog.reject)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(yes_btn)
        btn_layout.addWidget(no_btn)
        btn_layout.addStretch()
        
        content_layout.addWidget(msg_label)
        content_layout.addLayout(btn_layout)
        
        layout.addWidget(content_widget)
        
        # Возвращает True, если нажато ДА (accept), иначе False
        return dialog.exec_() == QDialog.Accepted

    def show_exit_confirmation_dialog(self):
        """Показывает стилизованное окно подтверждения выхода при наличии несохраненных изменений"""
        dialog = CustomDialog(self)
        dialog.bg_color = QColor("#333333")  # Устанавливаем тёмный фон для родителя
        dialog.setWindowTitle(get_translation(self.current_language, 'confirm_exit_title'))
        dialog.setFixedSize(440, 220)
        
        # Стилизация согласно пожеланиям пользователя
        content_style = """
            QWidget#ConfirmContent {
                background-color: #333333;
                border: none;
                border-radius: 9px;  /* Чуть меньше радиус из-за 1px отступа */
            }
            QLabel {
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
                background-color: transparent;
                border: none;
            }
            QPushButton#yesBtn {
                background-color: #ff3333;  /* Красный для Да */
                color: #ffffff;
                border: none;
                padding: 10px 25px;
                border-radius: 18px;  /* Пилюля */
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
                margin: 5px;
            }
            QPushButton#yesBtn:hover {
                background-color: #cc1111;
            }
            QPushButton#yesBtn:pressed {
                background-color: #990000;
            }
            QPushButton#noBtn {
                background-color: #ffffff;  /* Белый для Отмена */
                color: #000000;
                border: none;
                padding: 10px 25px;
                border-radius: 18px;  /* Пилюля */
                font-weight: bold;
                font-size: 13px;
                min-width: 100px;
                margin: 5px;
            }
            QPushButton#noBtn:hover {
                background-color: #cccccc;
            }
            QPushButton#noBtn:pressed {
                background-color: #aaaaaa;
            }
        """
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(1, 1, 1, 1)  # Отступ 1px для отображения оранжевой рамки
        
        container = QWidget()
        container.setObjectName("ConfirmContent")
        container.setStyleSheet(content_style)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 30, 30, 30)

        container_layout.setSpacing(20)
        
        msg_label = QLabel(get_translation(self.current_language, 'confirm_exit_msg'))
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        
        yes_btn = QPushButton(get_translation(self.current_language, 'yes_exit_btn'))
        yes_btn.setObjectName("yesBtn")
        yes_btn.setCursor(Qt.PointingHandCursor)
        
        no_btn = QPushButton(get_translation(self.current_language, 'cancel_exit_btn'))
        no_btn.setObjectName("noBtn")
        no_btn.setCursor(Qt.PointingHandCursor)
        
        yes_btn.clicked.connect(dialog.accept)
        no_btn.clicked.connect(dialog.reject)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(yes_btn)
        btn_layout.addWidget(no_btn)
        btn_layout.addStretch()
        
        container_layout.addWidget(msg_label)
        container_layout.addLayout(btn_layout)
        
        layout.addWidget(container)
        
        return dialog.exec_() == QDialog.Accepted

    def open_audio_player(self, key, auto_play=False):
        """Открывает окно аудиоплеера для прослушивания аудио по ключу"""
        if not self.current_miz_path:
            return
            
        try:
            # 1. Получаем информацию об аудио для данного ключа
            audio_info = self.miz_resource_manager.get_audio_for_key(key)
            if not audio_info:
                self.show_custom_dialog("Audio Error", f"No audio resource found for key: {key}", "error")
                return
                
            filename, is_current_locale = audio_info
            
            # 2. Извлекаем файл во временную папку (используем key, менеджер сам найдет файл)
            temp_path = self.miz_resource_manager.extract_audio_to_temp(self.current_miz_path, key)
            
            if not temp_path or not os.path.exists(temp_path):
                self.show_custom_dialog("Audio Error", f"Could not extract audio file: {filename}", "error")
                return

            def handle_replace(key, new_path):
                self.handle_audio_replacement(key, new_path)

            # 3. Если плеер уже открыт — обновляем его (Синглтон)
            if self.audio_player is not None:
                try:
                    is_heuristic = self.miz_resource_manager.is_heuristic_match(key)
                    # ВАЖНО: Передаём callback при синглтон обновлении!
                    self.audio_player.update_audio(temp_path, filename, key, self.last_audio_folder, is_heuristic=is_heuristic, on_replace_callback=handle_replace)
                    if auto_play:
                        self.audio_player.toggle_play_pause()
                    return
                except Exception as e:
                    print(f"DEBUG: Recreating audio player due to error: {e}")
                    self.audio_player = None

            # 4. Создаем новое окно плеера (немодальное)
            from dialogs import AudioPlayerDialog
            is_heuristic = self.miz_resource_manager.is_heuristic_match(key)
            self.audio_player = AudioPlayerDialog(
                temp_path, 
                filename, 
                self.current_language, 
                key=key, 
                on_replace_callback=handle_replace, 
                parent=self,
                last_audio_folder=self.last_audio_folder,
                is_heuristic=is_heuristic
            )
            # Обнуляем ссылку при закрытии окна
            self.audio_player.finished.connect(lambda: [setattr(self, 'audio_player', None), self.set_active_audio_key(None)])
            self.set_active_audio_key(key)
            self.audio_player.show()
            if auto_play:
                self.audio_player.toggle_play_pause()
            
        except Exception as e:
            error_msg = f"Error opening audio player: {str(e)}"
            ErrorLogger.log_error("AUDIO_PLAYER_OPEN", error_msg)
            self.show_custom_dialog("Error", error_msg, "error")

    def on_heuristic_toggle(self):
        """Переключает смещение эвристики и обновляет отображение аудио."""
        if not hasattr(self, 'miz_resource_manager') or not self.miz_resource_manager:
            return
        
        success = self.miz_resource_manager.toggle_heuristic_offset()
        if not success:
            return
        
        # Обновляем текст кнопки
        new_offset = self.miz_resource_manager.get_current_offset_label()
        offset_str = f"+{new_offset}" if new_offset > 0 else str(new_offset)
        self.heuristic_toggle_btn.setText(
            get_translation(self.current_language, 'heuristic_toggle_btn', offset=offset_str)
        )
        
        # Сбрасываем аудиоплеер (если открыт)
        if self.audio_player is not None:
            self.audio_player.reset_to_no_file()
        
        # Обновляем отображение (аудио-метки обновятся)
        self.update_preview()

    def reset_modified_display_state(self):
        """Сбрасывает индикацию правок (красный -> зеленый) после сохранения.
        Устанавливает текущий перевод как новый 'оригинал'.
        """
        try:
            self.prevent_text_changed = True
            
            # 1. Сначала сбрасываем текущую активную локаль (все списки)
            # Обновляем all_lines_data (мастер-список)
            processed_refs = set()
            for line in self.all_lines_data:
                current_trans = line.get('translated_text', '')
                line['original_translated_text'] = current_trans
                # Option B: Всегда обновляем оригинал, даже если он пустой (clear)
                if current_trans is not None:
                    line['original_text'] = current_trans
                    line['display_text'] = current_trans
                    line['is_empty'] = not (current_trans and current_trans.strip())
                processed_refs.add(id(line))
            
            # На всякий случай обновляем original_lines (если там другие ссылки, хотя обычно те же)
            for line in self.original_lines:
                if id(line) not in processed_refs:
                    current_trans = line.get('translated_text', '')
                    line['original_translated_text'] = current_trans
                    if current_trans is not None:
                        line['original_text'] = current_trans
                        line['display_text'] = current_trans
                        line['is_empty'] = not (current_trans and current_trans.strip())
            
            # 2. Теперь сбрасываем ВСЕ локали в памяти
            for folder, memory in self.miz_trans_memory.items():
                for list_key in ['all_lines_data', 'original_lines']:
                    if list_key in memory:
                        for line in memory[list_key]:
                            current_trans = line.get('translated_text', '')
                            line['original_translated_text'] = current_trans
                            if current_trans is not None:
                                line['original_text'] = current_trans
                                line['display_text'] = current_trans
                                line['is_empty'] = not (current_trans and current_trans.strip())

            # 3. Рекалькуляция key_all_empty (для Lua словарей)
            keys_with_content = set()
            for line in self.all_lines_data:
                if not line.get('is_empty', True):
                    keys_with_content.add(line.get('key'))
            
            for line in self.all_lines_data:
                line['key_all_empty'] = line.get('key') not in keys_with_content
            
            # Переприменяем фильтры (это скроет строки, которые стали пустыми и обновит все окна)
            self.apply_filters()
            
            # Сбрасываем флаг несохраненных изменений
            self.has_unsaved_changes = False
            
        except Exception as e:
            print(f"DEBUG: Error in reset_modified_display_state: {e}")
        finally:
            self.prevent_text_changed = False

    def on_preview_text_modified(self, edit_widget, index, line_data):
        """Вызывается мгновенно при вводе текста в предпросмотре для смены цвета"""
        try:
            current_text = edit_widget.toPlainText()
            original_text = line_data.get('original_translated_text', '')
            
            # Если текст пустой при загрузке, сравниваем со значением по умолчанию
            is_modified = current_text != original_text
            new_color = "#ff6666" if is_modified else "#2ecc71"
            
            # Update only text color, preserving existing background (hover) using widget helper if available
            try:
                if hasattr(edit_widget, 'set_text_color'):
                    edit_widget.set_text_color(new_color)
                else:
                    # fallback: preserve background-color if present
                    existing = edit_widget.styleSheet() or ''
                    import re
                    m = re.search(r'background-color:\s*([^;]+);', existing)
                    bg = m.group(1).strip() if m else None
                    bg_part = f' background-color: {bg};' if bg else ' background-color: transparent;'
                    edit_widget.setStyleSheet(f"color: {new_color}; font-family: 'Consolas'; font-size: 10pt; border: none;{bg_part}")
            except Exception:
                edit_widget.setStyleSheet(f"color: {new_color}; font-family: 'Consolas'; font-size: 10pt; background-color: transparent; border: none;")
            
            # Запускаем основной таймер синхронизации (через 1.5 сек сохранит в данные и редактор)
            self.on_preview_text_changed(index, current_text)
        except Exception as e:
            print(f"DEBUG: Error in on_preview_text_modified: {e}")

    def on_preview_line_inserted(self, after_index, move_text, trans_edit_widget,
                                  orig_row_layout, trans_row_layout,
                                  meta_row_widget, orig_row_widget, trans_row_widget):
        """Вставляет новую пустую строку в данные и в UI превью при нажатии Enter."""
        try:
            # === ЛОГИРОВАНИЕ ===
            log_msg = f"[INSERT_START] after_index={after_index} move_text={repr(move_text)[:40]} original_lines_count={len(self.original_lines)}"
            self._log_to_file(log_msg)
            
            if after_index < 0 or after_index >= len(self.original_lines):
                return

            source_line = self.original_lines[after_index]
            key = source_line['key']
            new_index = after_index + 1

            # Текущая (левая) часть текста после разделения — читаем из виджета отправителя
            try:
                before_text = trans_edit_widget.toPlainText()
            except Exception:
                before_text = self.original_lines[after_index].get('translated_text', '')

            # --- 1. Вставка в модель данных ---
            new_line_data = {
                'key': key,
                'original_text': '',
                'display_text': '',
                'translated_text': move_text or '',
                'original_translated_text': '',
                'should_translate': True,
                # помечаем пустой только когда нет текста (и без пробелов)
                'is_empty': not (bool(move_text) and bool(str(move_text).strip())),
                'key_all_empty': False,
                'full_match': '',
                'is_multiline': False,
                'display_line_index': 0,
                'total_display_lines': 1
            }
            # Копируем необязательные поля чтобы не сломать остальной код
            for field in ('file_index', 'entry_start_line'):
                if field in source_line:
                    new_line_data[field] = source_line[field]

            # Обновляем исходную запись текущей строки (левая часть)
            try:
                self.original_lines[after_index]['translated_text'] = before_text
                self.original_lines[after_index]['is_empty'] = (before_text == '')
            except Exception:
                pass

            # Shift pending_sync_edits: keys >= new_index must be incremented by +1
            # (must happen BEFORE any on_preview_text_modified calls that queue new edits)
            try:
                if getattr(self, 'pending_sync_edits', None):
                    new_pending = {}
                    for k, v in list(self.pending_sync_edits.items()):
                        if k >= new_index:
                            new_pending[k + 1] = v
                        else:
                            new_pending[k] = v
                    self.pending_sync_edits = new_pending
            except Exception:
                pass

            # Обновим цвет/статус текущего виджета (чтобы цвет отражал изменение сразу)
            try:
                self.on_preview_text_modified(trans_edit_widget, after_index, self.original_lines[after_index])
            except Exception:
                pass

            # Находим реальный "физический" индекс текущей строки в мастер-списке (для мастер-редакторов)
            # ИСПОЛЬЗУЕМ identity (is), а не ==, чтобы не путать одинаковые пустые строки
            physical_idx = -1
            if hasattr(self, 'all_lines_data'):
                for i, item in enumerate(self.all_lines_data):
                    if item is source_line:
                        physical_idx = i
                        break
            
            master_new_index = physical_idx + 1 if physical_idx != -1 else new_index

            # --- 1. Вставка в модель данных ---
            self.original_lines.insert(new_index, new_line_data)

            # ВАЖНО: Синхронизируем all_lines_data. 
            if hasattr(self, 'all_lines_data') and self.all_lines_data is not self.original_lines:
                self.all_lines_data.insert(master_new_index, new_line_data)
            
            # === ЛОГИРОВАНИЕ: успешно добавили в модель ===
            log_msg = f"  [INSERT_MODEL] new_index={new_index} key={key} text={repr(new_line_data.get('translated_text', ''))[:40]} | moved_to_next={repr(move_text)[:40]}"
            self._log_to_file(log_msg)

            # --- 2. Обновление индексов в существующих виджетах превью ---
            # Все PreviewTextEdit с index >= new_index нужно сдвинуть на +1
            for col_widget in (orig_row_widget, trans_row_widget):
                for edit in col_widget.findChildren(PreviewTextEdit):
                    if edit.index >= new_index:
                        edit.index += 1

            # Сдвигаем также во всех остальных группах (обходим preview_key_to_group_widget)
            try:
                for k, (mw, ow, tw) in self.preview_key_to_group_widget.items():
                    if k == key:
                        continue  # эту группу уже обработали выше
                    for col_w in (ow, tw):
                        for edit in col_w.findChildren(PreviewTextEdit):
                            if edit.index >= new_index:
                                edit.index += 1
            except Exception:
                pass

            # --- 3. Добавляем виджеты в превью (без полного перерендера) ---
            # Находим позицию вставки в layout (после виджета trans_edit_widget)
            # Layout содержит: виджет0, виджет1 ... виджетN, Stretch
            # Нам нужно вставить новый виджет строго ПОСЛЕ trans_edit_widget

            # Оригинал: пустая строка (readonly)
            new_orig = PreviewTextEdit(new_index, '', read_only=True)
            new_orig.setStyleSheet("color: #ffffff; background-color: transparent; border: none; border-radius: 0px;")
            new_orig._original_style = "color: #ffffff; background-color: transparent; border: none; border-radius: 0px;"

            # Перевод: редактируемая строка, заполняем её правой частью
            new_trans = PreviewTextEdit(new_index, move_text or '', read_only=False)
            # Начний цвет зависит от того, изменилась ли строка относительно original_translated_text
            is_new_modified = (new_line_data['translated_text'] != new_line_data.get('original_translated_text', ''))
            new_trans_color = "#ff6666" if is_new_modified else "#2ecc71"
            new_trans_style = f"color: {new_trans_color}; background-color: transparent; border: none; border-radius: 0px;"
            new_trans.setStyleSheet(new_trans_style)
            new_trans._original_style = new_trans_style

            # Подключаем сигналы для нового виджета
            # Исправлено: используем динамический te.index для защиты от порчи данных при вставках
            new_trans.text_changed.connect(
                lambda *args, te=new_trans:
                self.on_preview_text_modified(te, te.index, self.original_lines[te.index])
            )
            new_trans.line_inserted.connect(
                lambda ins_idx, move_text, te=new_trans,
                       orl=orig_row_layout, trl=trans_row_layout,
                       mw=meta_row_widget, orw=orig_row_widget, trw=trans_row_widget:
                self.on_preview_line_inserted(ins_idx, move_text, te, orl, trl, mw, orw, trw)
            )
            # Подключаем удаление/слияние строки для динамически вставленной строки
            new_trans.line_deleted.connect(lambda del_idx, merge_text, te=new_trans: self.on_preview_line_deleted(del_idx, te, merge_text))

            # Немедленно обновим цвет и состояние новой строки (если она уже содержит текст после split)
            try:
                # Обновляем модельную запись, чтобы on_preview_text_modified мог её прочитать
                self.original_lines[new_index] = new_line_data
                self.on_preview_text_modified(new_trans, new_index, new_line_data)
            except Exception:
                pass

            new_orig.set_partner(new_trans)
            new_trans.set_partner(new_orig)

            # Определяем позицию вставки в orig_row_layout
            insert_pos = -1
            for i in range(orig_row_layout.count()):
                item = orig_row_layout.itemAt(i)
                if item and item.widget() is trans_edit_widget.partner:
                    insert_pos = i + 1
                    break

            if insert_pos == -1:
                # Фолбэк: вставляем перед stretch
                insert_pos = orig_row_layout.count() - 1

            # Удаляем stretch, вставляем виджеты, добавляем stretch обратно
            # orig
            stretch_item_o = orig_row_layout.takeAt(orig_row_layout.count() - 1)
            orig_row_layout.insertWidget(insert_pos, new_orig, 0, Qt.AlignTop)
            orig_row_layout.addStretch(1)

            # trans — находим позицию после trans_edit_widget
            trans_insert_pos = -1
            for i in range(trans_row_layout.count()):
                item = trans_row_layout.itemAt(i)
                if item and item.widget() is trans_edit_widget:
                    trans_insert_pos = i + 1
                    break
            if trans_insert_pos == -1:
                trans_insert_pos = trans_row_layout.count() - 1

            stretch_item_t = trans_row_layout.takeAt(trans_row_layout.count() - 1)
            trans_row_layout.insertWidget(trans_insert_pos, new_trans, 0, Qt.AlignTop)
            trans_row_layout.addStretch(1)

            # row_siblings для новых виджетов
            siblings_tuple = (meta_row_widget, orig_row_widget, trans_row_widget)
            new_orig.row_siblings = siblings_tuple
            new_trans.row_siblings = siblings_tuple

            # --- Обновляем part_index для всех виджетов в этой группе (после вставки)
            try:
                indices = [i for i, ld in enumerate(self.original_lines) if ld['key'] == key]
                if key in self.preview_key_to_group_widget:
                    _, ow, tw = self.preview_key_to_group_widget[key]
                    for col_w in (ow, tw):
                        for edit in col_w.findChildren(PreviewTextEdit):
                            idx_val = getattr(edit, 'index', None)
                            if idx_val is None:
                                continue
                            try:
                                edit.part_index = indices.index(idx_val)
                            except ValueError:
                                # widget may belong to another group instance; ignore
                                pass
            except Exception:
                pass

            # Обновим part_index в модели original_lines для этой группы
            try:
                for pos, idx in enumerate([i for i, ld in enumerate(self.original_lines) if ld['key'] == key]):
                    try:
                        self.original_lines[idx]['part_index'] = pos
                    except Exception:
                        pass
            except Exception:
                pass

            # --- 4. Обновляем idx_label текущей группы ---
            self._update_group_header_label(key)

            # --- 5. Обновляем idx_label всех ПОСЛЕДУЮЩИХ групп ---
            self._renumber_groups_after(new_index)

            # --- 6. Синхронизируем верхний редактор (translated_text_all) ---
            # ВАЖНО: Устанавливаем флаг, чтобы apply_filters() не удалил новую пустую строку
            self.suppress_empty_filter_for_indices = {new_index}
            log_msg = f"  [INSERT_SUPPRESS_FILTER] index={new_index}"
            self._log_to_file(log_msg)
            self._insert_line_in_upper_editor(new_index, trans_text=move_text)
            
            # === ЛОГИРОВАНИЕ: завершение вставки ===
            log_msg = f"[INSERT_END] new_index={new_index} completed_successfully | original_lines_count={len(self.original_lines)}"
            self._log_to_file(log_msg)

            # --- 7. Обновляем общую статистику и счетчики ---
            self.update_stats()
            self.has_unsaved_changes = True

            # --- 8. Принудительно обновляем высоту блока ---
            new_trans.adjust_height()

            # --- 9. Фокус на новое поле ---
            try:
                new_trans.setFocus()
            except Exception:
                pass

        except Exception as e:
            import traceback
            print(f"ERROR in on_preview_line_inserted: {e}")
            traceback.print_exc()

    # ─── Вспомогательные методы для вставки строки ─────────────────────────────

    def _update_group_header_label(self, key):
        """Обновляет метку #X-Y в meta_row_widget для заданного ключа по текущим данным."""
        try:
            map_ = getattr(self, 'preview_key_to_group_widget', {})
            if key not in map_:
                return
            meta_w, orig_w, trans_w = map_[key]

            # Собираем все индексы этого ключа из original_lines
            indices = [i for i, ld in enumerate(self.original_lines) if ld['key'] == key]
            if not indices:
                return

            first_i = indices[0]
            last_i = indices[-1]
            if first_i == last_i:
                label_text = f"#{first_i + 1}"
            else:
                label_text = f"#{first_i + 1}-{last_i + 1}"

            # Находим QLabel (первый дочерний) в meta_w
            from PyQt5.QtWidgets import QLabel
            for child in meta_w.findChildren(QLabel):
                if child.text().startswith('<span') and '#' in child.text():
                    current_key_fragment = key[:30]
                    child.setText(
                        f"<span style='color: #cccccc; font-weight: bold;'>{label_text}</span> "
                        f"<span style='color: #8f8f8f; font-size: 11px;'>{key}</span>"
                    )
                    break
        except Exception as e:
            print(f"DEBUG _update_group_header_label: {e}")

    def _renumber_groups_after(self, after_index):
        """Обновляет #X-Y метки всех групп, чьи индексы >= after_index (сдвиг +1)."""
        try:
            map_ = getattr(self, 'preview_key_to_group_widget', {})
            from PyQt5.QtWidgets import QLabel

            for key, (meta_w, orig_w, trans_w) in map_.items():
                # Собираем индексы этой группы
                indices = [i for i, ld in enumerate(self.original_lines) if ld['key'] == key]
                if not indices:
                    continue
                # Если группа затронута (хотя бы один индекс >= after_index), перерисовываем её метку
                if indices[-1] < after_index:
                    continue  # группа полностью ДО вставленной строки

                first_i = indices[0]
                last_i = indices[-1]
                if first_i == last_i:
                    label_text = f"#{first_i + 1}"
                else:
                    label_text = f"#{first_i + 1}-{last_i + 1}"

                for child in meta_w.findChildren(QLabel):
                    if child.text().startswith('<span') and '#' in child.text():
                        child.setText(
                            f"<span style='color: #cccccc; font-weight: bold;'>{label_text}</span> "
                            f"<span style='color: #8f8f8f; font-size: 11px;'>{key}</span>"
                        )
                        break
        except Exception as e:
            print(f"DEBUG _renumber_groups_after: {e}")

    def _insert_line_in_upper_editor(self, new_index, trans_text=None):
        """Вставляет пустую строку в верхние редакторы (оригинал и перевод) на позицию new_index.
        Если `trans_text` задан — вставляет его в `translated_text_all` для новой строки."""
        try:
            log_msg = f"    [UPPER_INSERT_START] new_index={new_index} trans_text={repr(trans_text)[:40] if trans_text else None}"
            self._log_to_file(log_msg)
            
            prev_flag = getattr(self, 'prevent_text_changed', False)
            self.prevent_text_changed = True

            try:
                # Синхронизируем оба окна: и оригинал, и перевод
                for attr in ('original_text_all', 'translated_text_all'):
                    editor = getattr(self, attr, None)
                    if not editor:
                        continue
                    
                    editor_name = 'original' if attr == 'original_text_all' else 'translated'
                    log_msg = f"      [UPPER_INSERT] editor={editor_name} index={new_index}"
                    self._log_to_file(log_msg)

                    # Если у редактора есть лимит строк для нумерации, увеличиваем его
                    if hasattr(editor, 'max_line_count') and editor.max_line_count is not None:
                        editor.max_line_count += 1

                    doc = editor.document()
                    block_count = doc.blockCount()

                    # new_index — позиция новой строки (0-based)
                    insert_at = min(new_index, block_count)

                    cursor = editor.textCursor()

                    # Position cursor at the END of the previous block so that
                    # insertBlock() creates a clean empty block without
                    # contaminating the next block's text.
                    if insert_at > 0:
                        prev_block = doc.findBlockByNumber(insert_at - 1)
                        if prev_block.isValid():
                            cursor.setPosition(prev_block.position() + prev_block.length() - 1)
                        else:
                            cursor.movePosition(cursor.End)
                    else:
                        # Inserting at position 0 — place cursor at start
                        cursor.setPosition(0)

                    cursor.beginEditBlock()
                    cursor.insertBlock()
                    # Cursor is now at the start of the newly inserted empty block
                    if attr == 'translated_text_all' and trans_text:
                        try:
                            cursor.insertText(trans_text)
                        except Exception:
                            pass
                    cursor.endEditBlock()
            finally:
                self.prevent_text_changed = prev_flag

        except Exception as e:
            print(f"DEBUG _insert_line_in_upper_editor: {e}")

    def _delete_line_from_upper_editor(self, index):
        """Удаляет строку с указанным индексом из верхних редакторов оригинала и перевода."""
        log_msg = f"    [UPPER_DELETE_START] index={index}"
        self._log_to_file(log_msg)
        
        prev_flag = getattr(self, 'prevent_text_changed', False)
        self.prevent_text_changed = True
        try:
            editors = []
            if hasattr(self, 'original_text_all'):
                editors.append(('original', self.original_text_all))
            if hasattr(self, 'translated_text_all'):
                editors.append(('translated', self.translated_text_all))
            
            for editor_name, editor in editors:
                log_msg = f"      [UPPER_DELETE] editor={editor_name} index={index}"
                self._log_to_file(log_msg)
                
                doc = editor.document()
                block = doc.findBlockByNumber(index)
                if block.isValid():
                    cursor = QTextCursor(block)
                    cursor.beginEditBlock()
                    
                    # Если это не последний блок, удаляем его и идущий за ним \n
                    if block.next().isValid():
                        cursor.setPosition(block.position())
                        cursor.setPosition(block.next().position(), QTextCursor.KeepAnchor)
                    else:
                        # Это последний блок. Пытаемся захватить \n перед ним
                        if block.previous().isValid():
                            # Становимся в конец ПРЕДЫДУЩЕГО блока (перед \n последнего блока)
                            cursor.setPosition(block.previous().position() + block.previous().length() - 1)
                            # Выделяем до конца документа (который и есть наш последний блок)
                            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                        else:
                            # Единственный блок в документе
                            cursor.select(QTextCursor.BlockUnderCursor)
                    
                    cursor.removeSelectedText()
                    cursor.endEditBlock()
        finally:
            self.prevent_text_changed = prev_flag

    def on_preview_line_deleted(self, index, trans_edit_widget, merge_text=''):
        """Удаляет строку из данных и UI при нажатии Backspace в пустом поле.
        Если `merge_text` задан — объединяет текущую строку с предыдущей перед удалением."""
        try:
            # === ЛОГИРОВАНИЕ ===
            log_msg = f"[DELETE_START] index={index} merge_text={repr(merge_text)[:40]} original_lines_count={len(self.original_lines)}"
            self._log_to_file(log_msg)
            
            if index < 0 or index >= len(self.original_lines):
                return

            source_line = self.original_lines[index]
            key = source_line['key']

            # --- Защита: нельзя удалить последнюю строку в группе (ключе) ---
            group_lines = [line for line in self.original_lines if line['key'] == key]
            if len(group_lines) <= 1:
                self.statusBar().showMessage(get_translation(self.current_language, 'status_cannot_delete_last'), 3000)
                return

            # --- Если требуется объединение с предыдущей строкой ---
            merge_cursor_pos = -1  # cursor position at merge join point
            if merge_text:
                prev_index = index - 1
                if prev_index >= 0 and self.original_lines[prev_index]['key'] == key:
                    try:
                        prev_text = self.original_lines[prev_index].get('translated_text', '') or ''
                        merge_cursor_pos = len(prev_text)
                        new_prev = prev_text + merge_text
                        self.original_lines[prev_index]['translated_text'] = new_prev
                        
                        # === ЛОГИРОВАНИЕ: успешное объединение ===
                        log_msg = f"  [MERGE] prev_index={prev_index} | prev={repr(prev_text)[:30]} + current={repr(merge_text)[:30]} = {repr(new_prev)[:50]}"
                        self._log_to_file(log_msg)
                        # Обновляем виджет предыдущей строки в превью
                        try:
                            if key in self.preview_key_to_group_widget:
                                _, ow, tw = self.preview_key_to_group_widget[key]
                                for edit in tw.findChildren(PreviewTextEdit):
                                    if getattr(edit, 'index', None) == prev_index:
                                        edit.blockSignals(True)
                                        edit.setPlainText(new_prev)
                                        edit.blockSignals(False)
                                        edit.adjust_height()
                                        # Обновляем цвет сразу (новый текст отличается от original_translated_text)
                                        try:
                                            self.on_preview_text_modified(edit, prev_index, self.original_lines[prev_index])
                                        except Exception:
                                            pass
                                        # И буферно синхронизируем данные в основной редактор
                                        try:
                                            self.on_preview_text_changed(prev_index, new_prev)
                                        except Exception:
                                            pass
                                        break
                        except Exception:
                            pass
                    except Exception:
                        pass

            # --- 1. Удаление из модели данных ---
            # Находим физический индекс в all_lines_data через identity
            physical_idx = -1
            if hasattr(self, 'all_lines_data'):
                for i, item in enumerate(self.all_lines_data):
                    if item is source_line:
                        physical_idx = i
                        break

            # === ЛОГИРОВАНИЕ: удаляем из модели ===
            log_msg = f"  [DELETE_MODEL] index={index} physical_idx={physical_idx} text_before_delete={repr(source_line.get('translated_text', ''))[:40]}"
            self._log_to_file(log_msg)
            
            # Удаляем из обоих списков
            self.original_lines.pop(index)
            if physical_idx != -1 and self.all_lines_data is not self.original_lines:
                self.all_lines_data.pop(physical_idx)
            
            # === ЛОГИРОВАНИЕ: успешное удаление ===
            log_msg = f"  [DELETE_MODEL_DONE] original_lines_count_after={len(self.original_lines)}"
            self._log_to_file(log_msg)

            # Сдвигаем pending_sync_edits: удаляем текущий индекс и сдвигаем большие на -1
            try:
                if getattr(self, 'pending_sync_edits', None):
                    new_pending = {}
                    for k, v in list(self.pending_sync_edits.items()):
                        if k == index:
                            continue
                        if k > index:
                            new_pending[k - 1] = v
                        else:
                            new_pending[k] = v
                    self.pending_sync_edits = new_pending
            except Exception:
                pass

            # --- 2. Обновление индексов в существующих виджетах превью ---
            # Все PreviewTextEdit с index > deleted_index нужно сдвинуть на -1 (идем по всем группам)
            try:
                for k, (mw, ow, tw) in self.preview_key_to_group_widget.items():
                    for col_w in (ow, tw):
                        for edit in col_w.findChildren(PreviewTextEdit):
                            if edit.index > index:
                                edit.index -= 1
                # После смещения индексов — пересчитаем part_index для группы ключа
                try:
                    if key in self.preview_key_to_group_widget:
                        indices = [i for i, ld in enumerate(self.original_lines) if ld['key'] == key]
                        _, ow, tw = self.preview_key_to_group_widget[key]
                        for col_w in (ow, tw):
                            for edit in col_w.findChildren(PreviewTextEdit):
                                idx_val = getattr(edit, 'index', None)
                                if idx_val is None:
                                    continue
                                try:
                                    edit.part_index = indices.index(idx_val)
                                except ValueError:
                                    pass
                except Exception:
                    pass
            except Exception:
                pass

            # После удаления — обновим part_index в модели для этого ключа
            try:
                for pos, idx in enumerate([i for i, ld in enumerate(self.original_lines) if ld['key'] == key]):
                    try:
                        self.original_lines[idx]['part_index'] = pos
                    except Exception:
                        pass
            except Exception:
                pass

            # --- 3. Удаление виджетов из UI превью ---
            # Находим и удаляем виджет из трансляции и его партнера из оригинала
            partner_widget = trans_edit_widget.partner

            # Find the previous PreviewTextEdit to focus after deletion
            focus_target = None
            try:
                if key in self.preview_key_to_group_widget:
                    _, _, tw = self.preview_key_to_group_widget[key]
                    prev_widgets = [e for e in tw.findChildren(PreviewTextEdit)
                                   if not e.isReadOnly() and e is not trans_edit_widget]
                    candidates = [e for e in prev_widgets if e.index < index]
                    if candidates:
                        focus_target = max(candidates, key=lambda e: e.index)
                    elif prev_widgets:
                        focus_target = min(prev_widgets, key=lambda e: e.index)
            except Exception:
                pass

            # Удаляем из layout-ов
            if trans_edit_widget.row_siblings:
                _, orig_row_w, trans_row_w = trans_edit_widget.row_siblings

                # Удаляем из оригинала
                orig_layout = orig_row_w.layout()
                orig_layout.removeWidget(partner_widget)
                partner_widget.deleteLater()

                # Удаляем из перевода
                trans_layout = trans_row_w.layout()
                trans_layout.removeWidget(trans_edit_widget)
                trans_edit_widget.deleteLater()

                # Принудительно обновляем высоты оставшихся виджетов в группе
                for edit in trans_row_w.findChildren(PreviewTextEdit):
                    edit.adjust_height()

            # --- 4. Обновляем заголовки ---
            self._update_group_header_label(key)
            self._renumber_groups_after(index)

            # --- 5. Синхронизируем верхние редакторы ---
            log_msg = f"  [DELETE_UPPER_EDITOR] index={index}"
            self._log_to_file(log_msg)
            self._delete_line_from_upper_editor(index)

            # === ЛОГИРОВАНИЕ: завершение удаления ===
            log_msg = f"[DELETE_END] index={index} completed_successfully | original_lines_count={len(self.original_lines)}"
            self._log_to_file(log_msg)

            # --- 6. Restore focus to previous widget ---
            if focus_target is not None:
                try:
                    focus_target.setFocus()
                    cursor = focus_target.textCursor()
                    if merge_cursor_pos >= 0:
                        cursor.setPosition(merge_cursor_pos)
                    else:
                        cursor.movePosition(cursor.End)
                    focus_target.setTextCursor(cursor)
                except Exception:
                    pass

            self.has_unsaved_changes = True
            self.update_stats()
            self.statusBar().showMessage(get_translation(self.current_language, 'status_line_deleted'), 2000)

        except Exception as e:
            print(f"DEBUG: Error in on_preview_line_deleted: {e}")
            log_msg = f"[DELETE_ERROR] {str(e)}"
            self._log_to_file(log_msg)

    def quick_play_audio(self, key):
        """Проигрывает аудио в фоне без открытия диалога"""
        try:
            # Используем правильный метод извлечения из архива
            path = self.miz_resource_manager.extract_audio_to_temp(self.current_miz_path, key)
            if path and os.path.exists(path):
                pygame.mixer.music.load(path)
                # Применяем сохраненную громкость
                pygame.mixer.music.set_volume(self.audio_volume / 100.0)
                pygame.mixer.music.play()
                self.statusBar().showMessage(f"Playing: {os.path.basename(path)}")
            else:
                self.statusBar().showMessage(f"Audio not found: {key}")
        except Exception as e:
            print(f"DEBUG: Quick Play Error: {e}")

    def stop_quick_audio(self):
        """Останавливает фоновое воспроизведение"""
        try:
            pygame.mixer.music.stop()
            self.statusBar().showMessage("Audio stopped")
        except:
            pass
        # Сбрасываем состояние быстрой игры и обновляем иконку кнопки, если она есть
        try:
            if self.quick_playing_key and self.quick_playing_key in self.quick_audio_buttons:
                btn = self.quick_audio_buttons.get(self.quick_playing_key)
                if btn:
                    btn.setText("▶")
                    try:
                        btn.setStyleSheet(self.preview_play_style)
                    except Exception:
                        pass
        except Exception:
            pass
        self.quick_playing_key = None
        self.quick_paused = False

    def handle_audio_replacement(self, key, new_path):
        """Обрабатывает замену аудиофайла из аудиоплеера."""
        try:

            # Обновляем путь к последней папке аудио
            if new_path:
                self.last_audio_folder = os.path.dirname(new_path)
                # Сохраняем настройки, но не триггерим полную перерисовку превью
                try:
                    self.save_settings(update_preview=False)
                except Exception:
                    try:
                        self.save_settings()
                    except Exception:
                        pass

            result = self.miz_resource_manager.replace_audio(key, new_path)
            
            if result:
                # Обновляем название файла в предпросмотре
                label = self.audio_labels_map.get(key)
                if label is not None:
                    old_text = label.text()
                    label.setText(result)
                    label.update()
                    label.repaint()
                    new_text = label.text()
                    self._update_audio_label_style(key)

                # Обновляем плеер с новым файлом (если он открыт)
                if self.audio_player is not None:
                    try:
                        self.audio_player.update_audio(new_path, result, key, self.last_audio_folder)
                    except Exception as e:
                        pass

                # Обновляем только группу превью, связанную с этим ключом,
                # чтобы не перерисовывать весь превью (более эффективный путь).
                try:
                    updated = self.update_preview_for_key(key)
                except Exception:
                    updated = False

                if not updated:
                    # fallback: полная перерисовка если локальное обновление не сработало
                    try:
                        if hasattr(self, 'schedule_preview_update'):
                            self.schedule_preview_update(200)
                        else:
                            self.update_preview()
                    except Exception:
                        pass
        except Exception as e:
            error_msg = f"Error replacing audio: {str(e)}"
            ErrorLogger.log_error("AUDIO_REPLACE", error_msg)
            try:
                self.show_custom_dialog("Error", error_msg, "error")
            except Exception:
                pass

    def quick_toggle_audio(self, key, btn):
        """Toggle play/pause for a quick preview button linked to `key`."""
        try:
            # Если уже играет этот же ключ
            if self.quick_playing_key == key:
                # Если играет прямо сейчас -> пауза
                if pygame.mixer.music.get_busy() and not self.quick_paused:
                    try:
                        pygame.mixer.music.pause()
                        self.quick_paused = True
                        btn.setText("▶")
                        try:
                            btn.setStyleSheet(self.preview_play_style)
                        except Exception:
                            pass
                    except Exception:
                        pass
                elif self.quick_paused:
                    try:
                        pygame.mixer.music.unpause()
                        self.quick_paused = False
                        btn.setText("\u23F8\uFE0E")
                        try:
                            btn.setStyleSheet(self.preview_pause_style)
                        except Exception:
                            pass
                    except Exception:
                        pass
                else:
                    # Не играет, запустим заново
                    path = self.miz_resource_manager.extract_audio_to_temp(self.current_miz_path, key)
                    if path and os.path.exists(path):
                        try:
                            pygame.mixer.music.load(path)
                            pygame.mixer.music.set_volume(self.audio_volume / 100.0)
                            pygame.mixer.music.play()
                            self.quick_paused = False
                            btn.setText("\u23F8\uFE0E")
                            try:
                                btn.setStyleSheet(self.preview_pause_style)
                            except Exception:
                                pass
                        except Exception as e:
                            print(f"DEBUG: Quick restart error: {e}")
            else:
                # Останавливаем предыдущую (если была)
                if self.quick_playing_key and self.quick_playing_key in self.quick_audio_buttons:
                    prev_btn = self.quick_audio_buttons.get(self.quick_playing_key)
                    if prev_btn:
                        prev_btn.setText("▶")

                # Попробуем извлечь и проиграть
                path = self.miz_resource_manager.extract_audio_to_temp(self.current_miz_path, key)
                if path and os.path.exists(path):
                    try:
                        pygame.mixer.music.load(path)
                        pygame.mixer.music.set_volume(self.audio_volume / 100.0)
                        pygame.mixer.music.play()
                        self.statusBar().showMessage(f"Playing: {os.path.basename(path)}")
                        btn.setText("\u23F8\uFE0E")
                        try:
                            btn.setStyleSheet(self.preview_pause_style)
                        except Exception:
                            pass
                        self.quick_playing_key = key
                        self.quick_paused = False
                        self.quick_audio_buttons[key] = btn
                    except Exception as e:
                        print(f"DEBUG: Quick Toggle Play Error: {e}")
                else:
                    self.statusBar().showMessage(f"Audio not found: {key}")
        except Exception as e:
            print(f"DEBUG: quick_toggle_audio error: {e}")

    def set_active_audio_key(self, key):
        """Устанавливает активный аудио-ключ и обновляет рамки в предпросмотре"""
        old_key = self.active_audio_key
        self.active_audio_key = key
        
        # Обновляем старый виджет (убираем рамку)
        if old_key and old_key in self.audio_labels_map:
            self._update_audio_label_style(old_key)
            
        # Обновляем новый виджет (добавляем рамку)
        if key and key in self.audio_labels_map:
            self._update_audio_label_style(key)

    def _update_audio_label_style(self, key):
        """Вспомогательный метод для динамического обновления стиля метки аудио"""
        if key not in self.audio_labels_map:
            return
            
        label = self.audio_labels_map[key]
        audio_info = self.miz_resource_manager.get_audio_for_key(key)
        if not audio_info:
            return
            
        _, is_current_locale = audio_info
        
        # Определяем цвет
        if self.miz_resource_manager.is_audio_replaced(key):
            audio_color = '#ff6666' # Красный для замененных (несохраненных)
        elif is_current_locale:
            audio_color = '#2ecc71' # Зеленый для текущей локали
        else:
            audio_color = '#cccccc' # Тултипы и отсутствующие файлы теперь светлее
            
        # Определяем рамку (прозрачная по умолчанию, чтобы не прыгал размер)
        border_style = "border: 1px solid #ff9900; border-radius: 4px;" if key == self.active_audio_key else "border: 1px solid transparent;"
        
        label.setStyleSheet(f'''
            QLabel {{
                color: {audio_color};
                font-size: 12px;
                text-decoration: underline;
                background-color: transparent;
                {border_style}
                padding: 2px;
            }}
            QLabel:hover {{
                background-color: #3d4256;
                border-radius: 2px;
            }}
        ''')

    def update_preview_for_key(self, key):
        """
        Точечно обновляет виджеты в превью для конкретного ключа.
        Позволяет избежать перерисовки всего списка при замене аудио.
        """
        if not key:
            return
            
        try:
            # 1. Обновляем стиль текста/лейбла аудио
            self._update_audio_label_style(key)
            
            # 2. Обновляем видимость значка предупреждения (⚠)
            if hasattr(self, 'warning_icons_map') and key in self.warning_icons_map:
                warning_icon = self.warning_icons_map[key]
                audio_info = self.miz_resource_manager.get_audio_for_key(key)
                if audio_info:
                    _, is_current_locale = audio_info
                    # Если файл теперь в текущей локали (был заменен), скрываем варнинг
                    if is_current_locale or self.miz_resource_manager.is_audio_replaced(key):
                        warning_icon.setVisible(False)
                    else:
                        warning_icon.setVisible(True)
            
            # 3. Обновляем текст в лейбле
            if hasattr(self, 'audio_labels_map') and key in self.audio_labels_map:
                label = self.audio_labels_map[key]
                audio_info = self.miz_resource_manager.get_audio_for_key(key)
                if audio_info:
                    label.setText(audio_info[0])

            # 4. Пересчитываем высоты (если нужно)
            if hasattr(self, 'preview_key_to_group_widget') and key in self.preview_key_to_group_widget:
                widgets = self.preview_key_to_group_widget[key]
                from widgets import PreviewTextEdit
                
                # widgets это кортеж (meta, orig, trans)
                if isinstance(widgets, (tuple, list)):
                    for w in widgets[1:]: # orig и trans колонки
                        edits = w.findChildren(PreviewTextEdit)
                        if edits:
                            # Достаточно вызвать для одного, так как они синхронны внутри группы
                            edits[0].adjust_height()
                            break
        except Exception as e:
            # Log full traceback to help diagnose why selective update fails
            try:
                import traceback
                tb = traceback.format_exc()
                ErrorLogger.log_error("PREVIEW_UPDATE_KEY", f"Exception in update_preview_for_key for key={key}: {e}\n{tb}")
                # also write to debug file for immediate inspection
                try:
                    log_path = os.path.join(os.path.dirname(__file__), 'settings_debug.log')
                    with open(log_path, 'a', encoding='utf-8') as lf:
                        lf.write(f"[PREVIEW_UPDATE_KEY] {datetime.now().isoformat()} key={key} ERROR: {e}\n{tb}\n")
                except Exception:
                    pass
            except Exception:
                try:
                    ErrorLogger.log_error("PREVIEW_UPDATE_KEY", f"Exception while logging error for key={key}: {e}")
                except Exception:
                    pass
            # Do not re-raise — return False so callers won't trigger full rebuild fallback
            return False
        return True

    def _check_quick_audio(self):
        """Проверяет состояние фонового воспроизведения и сбрасывает кнопку по окончании трека."""
        try:
            if not getattr(self, 'quick_playing_key', None):
                return

            busy = False
            try:
                busy = pygame.mixer.music.get_busy()
            except Exception:
                busy = False

            # Если трек не играет (не busy) и не на паузе => завершился
            if not busy and not getattr(self, 'quick_paused', False):
                try:
                    btn = self.quick_audio_buttons.get(self.quick_playing_key)
                    if btn:
                        btn.setText("▶")
                        try:
                            btn.setStyleSheet(self.preview_play_style)
                        except Exception:
                            pass
                except Exception:
                    pass
                self.quick_playing_key = None
                self.quick_paused = False
        except Exception:
            pass
    def update_preview_for_indices(self, indices):
        """Обновляет группы предпросмотра, которые содержат хотя бы один индекс из `indices`.
        Возвращает True если были найдены и обновлены группы, иначе False.
        """
        try:
            from widgets import PreviewTextEdit
            updated = False
            if not hasattr(self, 'preview_layout') or self.preview_layout is None:
                return False

            # Проходим по всем группам в layout и ищем в них PreviewTextEdit с нужными индексами
            count = self.preview_layout.count()
            for i in range(count):
                item = self.preview_layout.itemAt(i)
                if not item:
                    continue
                group_widget = item.widget()
                if not group_widget:
                    continue

                try:
                    edits = group_widget.findChildren(PreviewTextEdit)
                except Exception:
                    edits = []

                group_matches = False
                for e in edits:
                    try:
                        if e.index in indices:
                            group_matches = True
                            break
                    except Exception:
                        continue

                if group_matches:
                    # Обновляем все редактируемые поля в группе
                    # Блокируем синхронизацию из превью в главный редактор
                    try:
                        prev_flag = getattr(self, 'prevent_text_changed', False)
                        self.prevent_text_changed = True
                    except Exception:
                        prev_flag = False

                    for e in edits:
                        try:
                            # Обновляем текст в превью из текущих данных буфера
                            try:
                                idx = getattr(e, 'index', None)
                                if idx is not None and 0 <= idx < len(self.original_lines):
                                    desired = self.original_lines[idx].get('translated_text', '') or ''
                                    # Обновляем ТОЛЬКО редактируемые поля перевода
                                    try:
                                        if not e.isReadOnly():
                                            if e.toPlainText() != desired:
                                                e.setPlainText(desired)
                                    except Exception:
                                        # Если метод отсутствует — безопасный fallback: обновляем
                                        if e.toPlainText() != desired:
                                            e.setPlainText(desired)
                            except Exception:
                                pass

                            # Подстраиваем высоту/геометрию
                            e.adjust_height()
                        except Exception:
                            try:
                                e.updateGeometry()
                            except Exception:
                                pass

                    # Восстанавливаем флаг
                    try:
                        self.prevent_text_changed = prev_flag
                    except Exception:
                        pass

                    try:
                        group_widget.updateGeometry()
                        group_widget.update()
                    except Exception:
                        pass

                    updated = True

            if updated and hasattr(self, 'preview_content'):
                try:
                    self.preview_content.updateGeometry()
                    self.preview_content.update()
                except Exception:
                    pass

            return updated
        except Exception:
            return False

    def closeEvent(self, event):
        """Проверка несохраненных изменений перед закрытием"""
        try:
            if getattr(self, 'has_unsaved_changes', False):
                if not self.show_exit_confirmation_dialog():
                    event.ignore()
                    return
            
            self.save_settings()
        except Exception as e:
            ErrorLogger.log_error("APP_CLOSE", f"Ошибка при закрытии программы: {e}")
        event.accept()

# [CUSTOM_DIALOG]


# [MAIN_FUNCTION]
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = TranslationApp()
    window.show()

    sys.exit(app.exec_())
