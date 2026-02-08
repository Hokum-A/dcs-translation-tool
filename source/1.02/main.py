"""
================================================================================
DCS TRANSLATION TOOL v1.02
================================================================================

КОНТЕКСТ ДЛЯ НОВОГО ЧАТА (обязательно прочитай перед началом работы!):

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
from PyQt5.QtGui import QFont, QTextCursor, QColor, QPalette, QPainter, QBrush, QPixmap, QPen, QMovie, QPainterPath, QRegion, QDesktopServices, QFontInfo, QFontMetrics, QIcon
from PyQt5.QtCore import QRectF

# Импорты модулей
from widgets import (LineNumberArea, NumberedTextEdit, CustomScrollBar,
                    ToggleSwitch, LanguageToggleSwitch, CustomToolTip)
from dialogs import (CustomDialog, MizFolderDialog, MizSaveAsDialog,
                    MizProgressDialog, AboutWindow, InstructionsWindow, AIContextWindow)
from error_logger import ErrorLogger
from version import VersionInfo
from parser import LuaDictionaryParser
from parserCMP import CampaignParser
from Context import AI_CONTEXTS

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
        
        # Инициализация данных
        self.current_file_path = None
        self.current_miz_path = None  # Новый атрибут для хранения пути к .miz файлу
        self.current_miz_folder = "DEFAULT"  # Текущая папка локализации в .miz
        self.original_lines = []
        self.all_lines_data = []
        self.filter_empty = True
        self.is_updating_display = False
        self.prevent_text_changed = False
        self.settings_file = "translation_tool_settings.json"
        self.preview_update_timer = None
        self.logo_pixmap_original = None
        self.is_resizing = False  # Флаг для отслеживания изменения размера
        self.current_language = 'ru'  # По умолчанию русский язык
        
        # Инциализация кастомного тултипа (без родителя для стабильности на Windows)
        from widgets import CustomToolTip
        self.custom_tooltip = CustomToolTip()
        
        # Запоминание последних папок
        self.last_open_folder = ''  # Последняя папка для открытия файлов
        self.last_save_folder = ''  # Последняя папка для сохранения файлов
        
        # Настройки контекста ИИ
        self.add_context = True    # Добавлять контекст по умолчанию
        self.ai_context_1 = AI_CONTEXTS.get('RU', get_translation(self.current_language, 'default_context_text')) 
        self.ai_context_2 = ""     # Дополнительный контекст ИИ
        self.ai_context_lang_1 = "RU" # Сохраненный язык шаблона

        # Настройки фильтров
        self.show_all_keys = False  # Показывать все ключи (по умолчанию выключено)
        self.sync_scroll = False    # Синхронизация прокрутки (по умолчанию выключено)
        self._is_syncing = False    # Флаг для предотвращения рекурсии при синхронизации

        # Пользовательские фильтры (3 штуки)
        self.custom_filters = []

        # Парсер dictionary (новый)
        self.dictionary_parser = LuaDictionaryParser()
        self.campaign_parser = CampaignParser()

        # Вывод информации о версии
        VersionInfo.print_version()
        
        # Инициализация UI
        self.init_ui()
        
        # Загружаем сохраненные настройки
        self.load_settings()
        
        # Центрируем окно после применения всех настроек (включая размер)
        self.center_on_screen()

    
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
        
        # Устанавливаем eventFilter для перетаскивания окна
        central_widget.installEventFilter(self)
        central_widget.setMouseTracking(True)
        
        # Подключение сигналов
        self.translated_text_all.textChanged.connect(self.on_translation_changed)

        # Debounce для предпросмотра (иначе тяжело перерисовывать на каждый символ)
        self.preview_update_timer = QTimer(self)
        self.preview_update_timer.setSingleShot(True)
        self.preview_update_timer.timeout.connect(self.update_preview)
        
        # Таймер для отложенного обновления после ресайза
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.finish_resize)
        
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
        """Рисует фон окна (без оранжевой рамки)"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Рисуем закруглённый фон окна, чтобы углы были плавными
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(64, 64, 64)))  # #404040
        rect = self.rect()
        radius = 12
        painter.drawRoundedRect(rect, radius, radius)
        
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
        '''
        self.translated_text_all.setStyleSheet(translated_style)
        
        # Предпросмотр
        preview_style = '''
            background-color: #505050; 
            border: 1px solid #777; 
            border-radius: 6px;
        '''
        self.preview_content.setStyleSheet(preview_style)
    
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
    
    # [UI_SETUP]
    def setup_ui_components(self, main_layout):
        """Настройка всех компонентов пользовательского интерфейса"""
        
        # 1. Верхняя панель с кнопками управления файлами (слева) и логотипом/статистикой (справа)
        self.setup_top_panel(main_layout)
        
        # 2. Группа фильтров
        self.setup_filter_group(main_layout)
        
        # 3. Основная область перевода (две панели)
        self.setup_translation_area(main_layout)
        
        # 4. Панель предварительного просмотра
        self.setup_preview_panel(main_layout)
    
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
        
        self.mission_prefix_label = QLabel()
        self.mission_prefix_label.setStyleSheet("color: white; font-weight: bold; background: transparent; border: none;")
        self.mission_prefix_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.mission_name_label = QLabel()
        self.mission_name_label.setStyleSheet("color: #ff9900; font-weight: bold; background: transparent; border: none;")
        self.mission_name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.loc_prefix_label = QLabel()
        self.loc_prefix_label.setStyleSheet("color: white; font-weight: bold; background: transparent; border: none;")
        self.loc_prefix_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.loc_folder_label = QLabel()
        self.loc_folder_label.setStyleSheet("color: #ff9900; font-weight: bold; background: transparent; border: none;")
        self.loc_folder_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        selected_miz_inner_layout.addWidget(self.mission_prefix_label)
        selected_miz_inner_layout.addWidget(self.mission_name_label)
        selected_miz_inner_layout.addWidget(self.loc_prefix_label)
        selected_miz_inner_layout.addWidget(self.loc_folder_label)
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
        for button in [self.open_btn, self.open_miz_btn, self.save_file_btn]:
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
        
        # Обработка клика по логотипу
        if hasattr(self, 'logo_label') and obj == self.logo_label:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.show_about_window()
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
        # Изменили фон заголовка на прозрачный
        self.filters_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #505050;
                color: #fff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #fff;
                background-color: transparent;  /* Изменено с #505050 на transparent */
                border: none;
            }
        """)
        
        filter_layout = QVBoxLayout()
        filter_layout.setContentsMargins(10, 10, 10, 10)
        
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
        filter_row1.addStretch()
        
        filter_layout.addLayout(filter_row1)
        
        # Вторая строка - произвольные фильтры
        filter_row2 = QHBoxLayout()
        filter_row2.setContentsMargins(0, 0, 0, 0)
        filter_row2.setSpacing(10)

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
            custom_layout.setSpacing(6)
            
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
        
        container_all, self.label_show_all = create_toggle_container(self.show_all_keys_cb, 
                                                                    get_translation(self.current_language, 'show_all_keys_label'))
        filter_row2.addSpacing(10)
        filter_row2.addWidget(container_all)
        
        # Пропускать пустые строки
        filter_row2.addStretch()
        self.filter_empty_cb = ToggleSwitch()
        self.filter_empty_cb.setChecked(True)
        self.filter_empty_cb.animation.finished.connect(self.toggle_empty_filter)
        
        empty_container = QWidget()
        empty_container.setStyleSheet('background-color: #505050; border: none;')  # Добавили фон
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
        
        # Отключаем "Показывать все ключи"
        if hasattr(self, 'show_all_keys_cb'):
            self.show_all_keys_cb.setChecked(False)
        
        # Отключаем произвольные фильтры
        for custom_filter in self.custom_filters:
            custom_filter['checkbox'].setChecked(False)
            custom_filter['line_edit'].clear()
        
        # Обновляем интерфейс
        self.filter_empty = True
        self.apply_filters()
        
        self.statusBar().showMessage(get_translation(self.current_language, 'status_default_filters'))
    
    def setup_translation_area(self, main_layout):
        """Настройка основной области перевода"""
        translation_frame = QFrame()
        translation_frame.setFrameShape(QFrame.StyledPanel)
        # Восстанавливаем полутемный фон для области перевода БЕЗ РАМКИ
        translation_frame.setStyleSheet("background-color: #505050; border: none;")
        translation_layout = QVBoxLayout(translation_frame)
        translation_layout.setContentsMargins(0, 0, 0, 0)
        translation_layout.setSpacing(0)
        
        # Разделитель для двух панелей
        splitter = QSplitter(Qt.Horizontal)
        
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
                background-color: transparent;  /* Прозрачный фон для "зебры" */
                border: 2px solid #777;  /* Светло-серая рамка по умолчанию */
                border-radius: 6px;
            }
            QPlainTextEdit:focus {
                border: 2px solid #ff9900;  /* Оранжевая рамка при фокусе */
                border-radius: 6px;
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
        self.add_context_toggle.toggled.connect(self.save_settings)
        
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
                background-color: transparent;  /* Прозрачный фон для "зебры" */
                border: 2px solid #777;  /* Светло-серая рамка по умолчанию */
                border-radius: 6px;
            }
            QPlainTextEdit:focus {
                border: 2px solid #ff9900;  /* Оранжевая рамка при фокусе */
                border-radius: 6px;
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
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 600])
        
        translation_layout.addWidget(splitter)
        main_layout.addWidget(translation_frame, 1)
    
    def setup_preview_panel(self, main_layout):
        """Настройка панели предварительного просмотра"""
        self.preview_group = QGroupBox(get_translation(self.current_language, 'preview_group'))
        # Изменили фон заголовка на прозрачный
        self.preview_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #505050;
                color: #fff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #fff;
                background-color: transparent;  /* Изменено с #505050 на transparent */
                border: none;
            }
        """)
        
        preview_layout = QVBoxLayout(self.preview_group)
        preview_layout.setContentsMargins(5, 15, 5, 5)
        
        # Поле предпросмотра с прокруткой
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setVerticalScrollBar(CustomScrollBar())
        self.preview_scroll.setHorizontalScrollBar(CustomScrollBar())
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setMinimumHeight(300)  # Увеличиваем высоту предпросмотра
        self.preview_scroll.setStyleSheet('''
            background-color: #505050; 
            border: none;
        ''')
        
        self.preview_content = QWidget()
        # Добавили светло-серую рамку внутрь предпросмотра
        self.preview_content.setStyleSheet('''
            background-color: #505050; 
            border: 1px solid #777; 
            border-radius: 6px;
        ''')
        self.preview_layout = QVBoxLayout(self.preview_content)
        self.preview_layout.setSpacing(0)
        self.preview_layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        self.preview_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.preview_scroll.setWidget(self.preview_content)
        preview_layout.addWidget(self.preview_scroll)
        
        # Информация о предпросмотре с предупреждением о слешах и статистикой
        preview_info_layout = QHBoxLayout()
        preview_info_layout.setContentsMargins(0, 5, 0, 0)
        
        # Значок предупреждения о несовпадении слешей
        self.slash_warning_label = QLabel()
        # Увеличиваем значок предупреждения примерно в 1.5 раза
        self.slash_warning_label.setFixedSize(30, 30)
        self.slash_warning_label.setVisible(False)
        self.slash_warning_label.setCursor(Qt.PointingHandCursor)
        
        # Кастомный тултип для предупреждения о слешах
        
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
        self.stats_label.setTextFormat(Qt.RichText)  # Enable HTML formatting
        
        self.preview_info = QLabel(get_translation(self.current_language, 'preview_info', count=0))
        self.preview_info.setStyleSheet('''
            color: #aaa;
            background-color: transparent;
            border: none;
        ''')
        
        preview_info_layout.addWidget(self.slash_warning_label)
        preview_info_layout.addWidget(self.preview_info)
        preview_info_layout.addStretch()
        preview_info_layout.addWidget(self.stats_label)
        
        preview_layout.addLayout(preview_info_layout)
        
        main_layout.addWidget(self.preview_group)
    
    # [SETTINGS_METHODS]
    def load_settings(self):
        """Загружает настройки из файла"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
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

                # Settings loaded successfully (silent)
                
            except Exception as e:
                ErrorLogger.log_error("SETTINGS_LOAD", f"Ошибка загрузки настроек: {e}")
                print(f"ERROR: Settings load failed: {e}")
        # If no settings file, defaults are already set in __init__
    
    def save_settings(self):
        """Сохраняет настройки в файл"""
        try:
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
                'create_backup': getattr(self, 'create_backup', False),
                'show_all_keys': getattr(self, 'show_all_keys', False),
                'last_open_folder': getattr(self, 'last_open_folder', ''),
                'last_save_folder': getattr(self, 'last_save_folder', ''),
                'window_width': self.width(),
                'window_height': self.height(),
                'add_context': self.add_context_toggle.isChecked() if hasattr(self, 'add_context_toggle') else self.add_context,
                'ai_context_1': getattr(self, 'ai_context_1', ""),
                'ai_context_2': getattr(self, 'ai_context_2', ""),
                'ai_context_lang_1': getattr(self, 'ai_context_lang_1', "RU"),
                'sync_scroll': self.sync_scroll,
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
        self.open_miz_btn.setText(get_translation(self.current_language, 'open_miz_btn'))
        self.save_file_btn.setText(get_translation(self.current_language, 'save_file_btn'))
        
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
        
        # Обновляем группы фильтров
        if hasattr(self, 'filters_group'):
            self.filters_group.setTitle(get_translation(self.current_language, 'filters_group'))
        
        if hasattr(self, 'preview_group'):
            self.preview_group.setTitle(get_translation(self.current_language, 'preview_group'))
        
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
        
        print(f"OK: Interface updated to {self.current_language.upper()}")
        
        # Обновляем тултип предупреждения о слешах (всегда, чтобы при появлении он был на нужном языке)
        if hasattr(self, 'slash_warning_label'):
            tooltip_text = get_translation(self.current_language, 'tooltip_warning_slash')
            self.register_custom_tooltip(self.slash_warning_label, tooltip_text, side='right')
            
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
            self.loc_folder_label.setText(f"[{folder}]")
            
            # Рассчитываем ширины для сокращения
            metrics = QFontMetrics(self.mission_prefix_label.font())
            p1_w = metrics.horizontalAdvance(self.mission_prefix_label.text())
            p2_w = metrics.horizontalAdvance(self.loc_prefix_label.text())
            f_w = metrics.horizontalAdvance(self.loc_folder_label.text())
            
            # Остаток для имени миссии (общий лимит 700)
            name_max_width = max(100, 700 - p1_w - p2_w - f_w - 30) # -30 на зазоры
            
            elided_name = self.elide_label_text(self.mission_name_label, filename, name_max_width)
            self.mission_name_label.setText(elided_name)
            
            self.register_custom_tooltip(self.selected_miz_label, self.current_miz_path, side='bottom-left')

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
                    
                    self.statusBar().showMessage(get_translation(self.current_language, 'status_lines_loaded', count=len(self.original_lines)))
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
            for key, (text_parts, file_lines) in entries.items():
                for part_index, part in enumerate(text_parts):
                    # Проверяем нужно ли переводить эту строку
                    should_translate = self._should_translate_key(key)

                    # Проверяем, пустая ли строка
                    is_empty = not part.strip()

                    line_data = {
                        'key': key,
                        'original_text': part,
                        'display_text': part,
                        'translated_text': '',
                        'full_match': file_lines[part_index] if part_index < len(file_lines) else '',
                        'indent': '',
                        'start_pos': line_number,
                        'end_pos': line_number + 1,
                        'should_translate': should_translate,
                        'is_empty': is_empty,
                        'ends_with_backslash': part.endswith('\\') if part else False,
                        'is_multiline': False,
                        'display_line_index': 0,
                        'total_display_lines': 1
                    }

                    self.all_lines_data.append(line_data)

                    if should_translate and not (is_empty and self.filter_empty):
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
                val = line.get('translated_text', '').strip()
                if not val:
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
                    pattern = r'(\[\"' + re.escape(full_key) + r'\"\]\s*=\s*)(?:"(?:[^"\\]|\\.)*"|\[\[[\s\S]*?\]\])(,?)'
                    
                    match = re.search(pattern, new_content)
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
                        new_content = new_content.replace(match.group(0), replacement)
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
        overwrite_btn = QPushButton(get_translation(self.current_language, 'overwrite_btn'))
        
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
            
            # Парсим содержимое dictionary
            self.parse_dictionary_file(self.original_content)
            progress.set_value(85)
            
            if self.original_lines:
                self.apply_filters()
                self.save_file_btn.setEnabled(True)
                progress.set_value(90)
                
                # Обновляем надписи о файлах
                self.selected_miz_label.setVisible(True)
                self.selected_file_label.setVisible(False)
                self.update_file_labels()
                
                self.statusBar().showMessage(get_translation(self.current_language, 'status_mission_lines_loaded', count=len(self.original_lines)))
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
                    'translated_text': '',
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
    
    def apply_filters(self):
        """Применяет выбранные фильтры к данным"""
        self.original_lines = []
        
        show_all = getattr(self, 'show_all_keys_cb', None) and self.show_all_keys_cb.isChecked()
        
        for line_data in self.all_lines_data:
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
            
            if not show_all and should_translate and line_data['is_empty'] and self.filter_empty:
                should_translate = False
            
            if should_translate:
                self.original_lines.append(line_data)
        
        print(f"📊 После фильтрации строк для перевода: {len(self.original_lines)}")
        self.update_display()
    
    def toggle_empty_filter(self):
        """Включает/выключает фильтр пустых строк - ИСПРАВЛЕНО: без параметра state"""
        # Используем isChecked() для получения состояния после анимации
        self.filter_empty = self.filter_empty_cb.isChecked()
        self.apply_filters()
        self.save_settings()
    
    def toggle_show_all_keys(self):
        """Переключает отображение всех ключей"""
        self.show_all_keys = self.show_all_keys_cb.isChecked()
        self.apply_filters()
        self.save_settings()
    
    def toggle_keys_display(self, checked):
        """Переключает отображение ключей"""
        self.update_display()
    
    # [DISPLAY_METHODS]
    def update_display(self):
        """Обновляет отображение в основных панелях"""
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
            
            self.original_text_all.setPlainText('\n'.join(english_lines))
            
            # Формируем текст для правой панели (перевод)
            russian_lines = []
            
            for line_data in self.original_lines:
                if line_data['translated_text']:
                    clean_text = line_data['translated_text'].replace('\n', ' ')
                    russian_lines.append(clean_text)
                else:
                    russian_lines.append('')
            
            new_text = '\n'.join(russian_lines)
            
            # Удаляем лишние пустые строки в конце
            while new_text.endswith('\n\n'):
                new_text = new_text.rstrip('\n')
            
            # Обновляем только если текст изменился
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
            
            # Обновляем статистику
            self.update_stats()
            
            # Обновляем предпросмотр
            self.schedule_preview_update()
            
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
            return
        
        self.update_translation_stats()
        self.english_count_label.setText(get_translation(self.current_language, 'english_count_label', count=len(self.original_lines)))
        
        filled_translations = sum(1 for line in self.original_lines if line['translated_text'].strip())
        self.russian_count_label.setText(get_translation(self.current_language, 'russian_count_label', filled=filled_translations, total=len(self.original_lines)))
    
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
        
        self.save_settings()

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
    
    # [PREVIEW_METHODS]
    def clear_preview_widgets(self):
        """Полностью очищает все виджеты предпросмотра с освобождением памяти"""
        # Удаляем все дочерние виджеты из контейнера предпросмотра
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                # Рекурсивно очищаем все вложенные виджеты
                self.recursive_delete_widget(widget)
            elif item.layout():
                # Если есть вложенный layout, очищаем и его
                self.clear_layout(item.layout())
        
        # Принудительное обновление
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

    def update_preview(self):
        """Обновляет предварительный просмотр всех строк"""
        try:
            # Очищаем предыдущий предпросмотр
            self.clear_preview_widgets()
            
            if not self.original_lines:
                self.preview_info.setText(get_translation(self.current_language, 'preview_info', count=0))
                self.slash_warning_label.setVisible(False)
                return
            
            # Переменные для подсчета строк с несовпадением слешей
            mismatch_count = 0
            mismatch_lines = []
            
            # Показываем ВСЕ строки
            for i, line_data in enumerate(self.original_lines):
                # Контейнер для строки
                line_widget = QWidget()
                line_widget.setMinimumHeight(40)  # Минимальная высота строки, может увеличиваться для многострочного текста
                line_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                
                # Проверяем совпадение количества слешей
                original_slashes = self.count_slashes(line_data['display_text'])
                translated_slashes = self.count_slashes(line_data['translated_text']) if line_data['translated_text'] else 0
                has_slash_mismatch = original_slashes != translated_slashes
                
                # Проверяем опасные комбинации (Rule 2/3)
                danger_found = False
                danger_msg = ""
                
                text_to_check = line_data['translated_text'] if line_data['translated_text'] else line_data['display_text']
                
                if text_to_check:
                    if text_to_check.endswith('\\ '):
                        danger_found = True
                        danger_msg = "Rule 3: Слеш с пробелом в конце вызывает зависание"
                    elif text_to_check.endswith('\\"'):
                        danger_found = True
                        danger_msg = "Rule 2: Слеш перед кавычкой в конце может быть опасен"
                
                # Подсвечиваем опасные строки
                if danger_found:
                    line_widget.setStyleSheet('''
                        QWidget {
                            background-color: #432222;
                            border-bottom: 2px solid #ff4444;
                        }
                    ''')
                elif line_data.get('ends_with_backslash', False):
                    # Мягкая подсветка для обычных слешей (пользователь может захотеть видеть их)
                    line_widget.setStyleSheet('''
                        QWidget {
                            background-color: #353535;
                            border-bottom: 1px solid #555;
                        }
                    ''')
                else:
                    line_widget.setStyleSheet('''
                        QWidget {
                            background-color: #404040;
                            border-bottom: 1px solid #555;
                        }
                    ''')
            
                line_layout = QHBoxLayout(line_widget)
                line_layout.setContentsMargins(8, 3, 8, 3)
                
                # Номер строки с индикатором слеша
                num_widget = QWidget()
                num_layout = QHBoxLayout(num_widget)
                num_layout.setContentsMargins(0, 0, 0, 0)
                num_layout.setSpacing(2)
                
                # Место для значка предупреждения (20px слева)
                warning_icon_label = QLabel()
                warning_icon_label.setFixedWidth(20)
                warning_icon_label.setStyleSheet('background-color: transparent; border: none;')
                
                # Номер строки
                num_label = QLabel(f"{i+1:4d}")
                num_label.setFixedWidth(35)
                num_label.setStyleSheet('color: #aaa; font-weight: bold; background-color: transparent; border: none;')
                
                # Индикатор несовпадения слешей или опасности
                if danger_found or has_slash_mismatch:
                    warning_icon_label.setText("⚠")
                    warning_color = "#ff4444" if danger_found else "#ff9900"
                    warning_icon_label.setStyleSheet(f'''
                        color: {warning_color}; 
                        font-weight: bold; 
                        font-size: 14px;
                        background-color: transparent;
                        border: none;
                    ''')
                    
                    # Добавляем тултип с описанием проблемы
                    tip = ""
                    if danger_found:
                        tip = danger_msg
                        if has_slash_mismatch:
                            tip += f"\n{get_translation(self.current_language, 'slash_warning', count=original_slashes, trans=translated_slashes)}"
                    else:
                        tip = get_translation(self.current_language, 'slash_warning', count=original_slashes, trans=translated_slashes)
                    
                    self.register_custom_tooltip(warning_icon_label, tip)
                else:
                    warning_icon_label.clear()
                    self.unregister_custom_tooltip(warning_icon_label)
                
                num_layout.addWidget(warning_icon_label)
                num_layout.addWidget(num_label)
                
                num_widget.setFixedWidth(60)  # Увеличили ширину из-за добавленного поля
                num_widget.setStyleSheet('background-color: transparent; border: none;')
                
                # Ключ
                key_label = QLabel(f"[{line_data['key']}]")
                key_label.setStyleSheet('''
                    color: #aaa; 
                    font-size: 9px;
                    background-color: transparent;
                    border: none;
                ''')
                key_label.setFixedWidth(150)
                
                # Оригинальный текст - ИЗМЕНЕНО: белый цвет
                original_text = line_data['display_text'].replace('\n', ' ')
                original_label = QLabel(original_text)
                if line_data.get('ends_with_backslash', False):
                    original_label.setStyleSheet('''
                        color: #ffffff; 
                        font-weight: bold;
                        background-color: transparent;
                        border: none;
                    ''')
                else:
                    original_label.setStyleSheet('''
                        color: #ffffff;
                        background-color: transparent;
                        border: none;
                    ''')
                original_label.setWordWrap(True)
                
                # Перевод с индикатором
                trans_widget = QWidget()
                trans_widget.setStyleSheet('background-color: transparent; border: none;')
                
                trans_layout = QHBoxLayout(trans_widget)
                trans_layout.setContentsMargins(0, 0, 0, 0)
                trans_layout.setSpacing(5)
                
                translated_text = line_data['translated_text'].replace('\n', ' ') if line_data['translated_text'] else ""
                
                # Проверяем слеш в переводе
                has_backslash_in_translation = line_data['translated_text'] and line_data['translated_text'].endswith('\\')
                has_backslash_in_original = line_data.get('ends_with_backslash', False)
                
                if translated_text:
                    trans_text_label = QLabel(translated_text)
                    
                    # Индикатор статуса слеша
                    status_indicator = QLabel()
                    status_indicator.setFixedWidth(20)
                    
                    if has_backslash_in_original:
                        if has_backslash_in_translation:
                            # ✓ Слеш сохранен
                            status_indicator.setText("✓")
                            status_indicator.setStyleSheet('''
                                color: #27ae60; 
                                font-weight: bold; 
                                font-size: 14px;
                                background-color: transparent;
                                border: none;
                            ''')
                            trans_text_label.setStyleSheet('''
                                color: #2ecc71;
                                background-color: transparent;
                                border: none;
                            ''')
                        else:
                            # ⚠ Слеш потерян
                            status_indicator.setText("⚠")
                            status_indicator.setStyleSheet('''
                                color: #e74c3c; 
                                font-weight: bold; 
                                font-size: 14px;
                                background-color: transparent;
                                border: none;
                            ''')
                            trans_text_label.setStyleSheet('''
                                color: #e74c3c; 
                                font-weight: bold;
                                background-color: transparent;
                                border: none;
                            ''')
                    else:
                        if has_backslash_in_translation:
                            # ! Лишний слеш
                            status_indicator.setText("!")
                            status_indicator.setStyleSheet('''
                                color: #f39c12; 
                                font-weight: bold; 
                                font-size: 12px;
                                background-color: transparent;
                                border: none;
                            ''')
                            trans_text_label.setStyleSheet('''
                                color: #2ecc71;
                                background-color: transparent;
                                border: none;
                            ''')
                        else:
                            # · Все ок
                            status_indicator.setText("·")
                            status_indicator.setStyleSheet('''
                                color: #777; 
                                font-size: 10px;
                                background-color: transparent;
                                border: none;
                            ''')
                            trans_text_label.setStyleSheet('''
                                color: #2ecc71;
                                background-color: transparent;
                                border: none;
                            ''')
                    
                    trans_text_label.setWordWrap(True)
                    trans_layout.addWidget(trans_text_label, 1)
                    trans_layout.addWidget(status_indicator)
                    
                else:
                    # Нет перевода
                    # Если оригинал тоже пустой, не пишем "не переведено"
                    if not line_data['original_text'].strip():
                         trans_text_label = QLabel("")
                         trans_text_label.setStyleSheet("background-color: transparent; border: none;")
                    else:
                        not_translated_text = get_translation(self.current_language, 'not_translated')
                        trans_text_label = QLabel(not_translated_text)
                        trans_text_label.setAlignment(Qt.AlignCenter)
                        trans_text_label.setStyleSheet('''
                            color: #e74c3c; 
                            font-size: 12px;
                            font-style: italic;
                            background-color: transparent;
                            border: none;
                        ''')
                    
                    trans_text_label.setWordWrap(True)
                    
                    status_indicator = QLabel("...")
                    status_indicator.setStyleSheet('''
                        color: #777; 
                        font-size: 10px;
                        background-color: transparent;
                        border: none;
                    ''')
                    status_indicator.setFixedWidth(20)
                    
                    trans_layout.addWidget(trans_text_label, 1)
                    trans_layout.addWidget(status_indicator)
        
                # Добавляем виджеты
                line_layout.addWidget(num_widget)  # Номер с индикатором
                line_layout.addWidget(key_label)
                line_layout.addWidget(original_label, 2)
                line_layout.addWidget(trans_widget, 2)  # Перевод с индикатором
                
                self.preview_layout.addWidget(line_widget)
            
            # Добавляем растягивающийся spacer для правильной работы скроллинга
            self.preview_layout.addStretch()
             
            # Обновляем информацию о предпросмотре
            self.preview_info.setText(get_translation(self.current_language, 'preview_info', count=len(self.original_lines)))
            
            # Обновляем значок предупреждения о несовпадении слешей
            if mismatch_count > 0:
                self.slash_warning_label.setVisible(True)
                self.slash_warning_label.setStyleSheet("""
                    QLabel {
                        color: #ff9900;
                        font-weight: bold;
                        font-size: 20px;
                        qproperty-alignment: AlignCenter;
                        background-color: transparent;
                        border: none;
                    }
                """)
                self.slash_warning_label.setText("⚠")
                
                # Формируем текст подсказки
                if len(mismatch_lines) <= 5:
                    lines_text = ', '.join(map(str, mismatch_lines))
                else:
                    lines_text = ', '.join(map(str, mismatch_lines[:5]))
                
                # Устанавливаем тултип у метки (появляться будет при наведении, не как всплывашка при каждом обновлении)
                # Используем короткий, однозначный текст тултипа с одним обратным слешем
                tooltip_text = get_translation(self.current_language, 'tooltip_warning_slash')
                # Регистрируем кастомный тултип для этой метки
                try:
                    self.register_custom_tooltip(self.slash_warning_label, tooltip_text, side='right')
                except Exception:
                    try:
                        self.register_custom_tooltip(self.slash_warning_label, tooltip_text, side='right')
                    except Exception:
                        pass
            else:
                # Скрываем метку и убираем тултип
                QToolTip.hideText()
                self.slash_warning_label.setVisible(False)
                # Убираем регистрацию кастомного тултипа, если была
                try:
                    self.unregister_custom_tooltip(self.slash_warning_label)
                except Exception:
                    try:
                        if hasattr(self, '_custom_tooltip_map') and self.slash_warning_label in self._custom_tooltip_map:
                            del self._custom_tooltip_map[self.slash_warning_label]
                    except Exception:
                        pass
            
        except Exception as e:
            error_msg = f"Ошибка при обновлении предпросмотра: {str(e)}"
            ErrorLogger.log_error("PREVIEW_ERROR", error_msg)
            self.preview_info.setText(f'Ошибка: {error_msg[:50]}...')

    def schedule_preview_update(self, delay_ms: int = 200):
        """Планирует обновление предпросмотра с задержкой (debounce)"""
        if self.preview_update_timer is None:
            return
        self.preview_update_timer.start(delay_ms)
    
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
        
        btns_layout.addWidget(overwrite_frame)
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
        
        # Сначала всегда спрашиваем папку локализации
        save_dialog = MizSaveAsDialog(self.current_language, action=action, parent=self)
        if save_dialog.exec_() == QDialog.Accepted:
            selected_folder = save_dialog.selected_folder
            if action == 'overwrite':
                self.save_miz_overwrite(selected_folder)
            elif action == 'save_as':
                self.save_miz_as(selected_folder)

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

    def save_miz_overwrite(self, target_folder):
        """Перезаписывает исходный .miz файл в выбранную папку локализации"""
        progress = MizProgressDialog(self)
        try:
            print(f"\n{'='*50}")
            print(f"ПЕРЕЗАПИСЬ .MIZ ФАЙЛА")
            print(f"{'='*50}")
            
            progress.show()
            progress.set_value(10)
            
            # Создаем резервную копия если нужно
            backup_path = None
            if getattr(self, 'create_backup', False):
                progress.set_value(20)
                backup_path = self.create_backup_file(self.current_miz_path)
            
            progress.set_value(40)
            # Готовим содержимое для замены
            new_content = self.generate_translated_content()
            progress.set_value(70)
            
            # Переменная для отслеживания успеха
            success = False
            
            # Временный файл для записи изменений
            temp_miz = self.current_miz_path + '.tmp'
            
            try:
                # Читаем оригинал и пишем в темп
                with zipfile.ZipFile(self.current_miz_path, 'r') as zin:
                    with zipfile.ZipFile(temp_miz, 'w', compression=zin.compressionlevel if hasattr(zin, 'compressionlevel') else zipfile.ZIP_DEFLATED) as zout:
                        progress.set_value(80)
                        dict_replaced = False
                        for item in zin.infolist():
                            # Сохраняем оригинальное имя для чтения данных, 
                            # но исправляем имя в объекте ZipInfo для правильной записи в новый архив
                            original_filename_for_read = item.filename
                            
                            try:
                                # Если имя было декодировано как CP437, но на самом деле это UTF-8
                                # (характерно для спецсимволов вроде LRM, которые превращаются в ΓÇÄ)
                                fixed_name = item.filename.encode('cp437').decode('utf-8')
                                item.filename = fixed_name
                                item.flag_bits |= 0x800  # Устанавливаем бит UTF-8
                            except (UnicodeEncodeError, UnicodeDecodeError):
                                # Если не получается, оставляем как есть
                                pass

                            if item.filename == f'l10n/{target_folder}/dictionary':
                                # Заменяем только dictionary в выбранной папке
                                zout.writestr(item, new_content.encode('utf-8')) # Ensure content is bytes
                                dict_replaced = True
                                print(f"DEBUG: Replaced dictionary in {item.filename}")
                            else:
                                # Остальное копируем без изменений
                                zout.writestr(item, zin.read(original_filename_for_read))
                        
                        # Если папки/файла не существовало в этом архиве, добавляем его
                        if not dict_replaced:
                            target_dict_path = f'l10n/{target_folder}/dictionary'
                            zout.writestr(target_dict_path, new_content.encode('utf-8'))
                            print(f"DEBUG: Created new dictionary at {target_dict_path}")
                
                # Удаляем оригинал и переименовываем темп
                os.remove(self.current_miz_path)
                os.rename(temp_miz, self.current_miz_path)
                self.current_miz_folder = target_folder
                self.update_file_labels()
                success = True
                progress.set_value(100)
                
            except Exception as e:
                if os.path.exists(temp_miz):
                    os.remove(temp_miz)
                raise e
            finally:
                progress.close()
            
            if success:
                # Показываем отчет
                self.show_save_report(self.current_miz_path, backup_path=backup_path)
                
        except Exception as e:
            error_msg = get_translation(self.current_language, 'error_miz_save', error=str(e))
            ErrorLogger.log_error("MIZ_OVERWRITE", error_msg)
            self.show_custom_dialog(get_translation(self.current_language, 'error_title'), error_msg, "error")

    def save_miz_as(self, target_folder):
        """Сохраняет перевод в новый .miz файл с выбором папки локализации"""
        progress = None
        try:
            # Определяем начальную папку и имя файла
            default_dir = self.last_save_folder if self.last_save_folder else os.path.dirname(self.current_miz_path) if self.current_miz_path else ""
            default_name = os.path.splitext(os.path.basename(self.current_miz_path))[0] + f"_{target_folder}.miz" if self.current_miz_path else f"mission_{target_folder}.miz"
            initial_path = os.path.join(default_dir, default_name)

            # Диалог выбора места сохранения
            save_path, _ = QFileDialog.getSaveFileName(
                self, 
                get_translation(self.current_language, 'save_as_btn'), 
                initial_path, 
                'Файлы миссий DCS (*.miz);;Все файлы (*)'
            )
            
            if not save_path:
                return
            
            self.last_save_folder = os.path.dirname(save_path)
            self.save_settings()
            
            # Проверяем, что пользователь не пытается сохранить в тот же файл
            if os.path.abspath(save_path) == os.path.abspath(self.current_miz_path):
                error_msg = get_translation(self.current_language, 'error_truncated_header')
                self.show_custom_dialog(get_translation(self.current_language, 'error_title'), error_msg, "error")
                return
            
            progress = MizProgressDialog(self)
            progress.show()
            progress.set_value(10)
            
            # Готовим содержимое для замены
            new_content = self.generate_translated_content()
            progress.set_value(40)
            
            # Безопасное сохранение через временный файл
            temp_save_path = save_path + '.tmp'
            
            # Создаем новый файл из оригинала
            with zipfile.ZipFile(self.current_miz_path, 'r') as zin:
                # Проверяем, что исходный файл корректен
                try:
                    zin.testzip()
                except zipfile.BadZipFile as e:
                    raise zipfile.BadZipFile(f"Source file is corrupted: {str(e)}")
                
                # Создаем временный файл
                compression = zipfile.ZIP_DEFLATED
                if hasattr(zin, 'compressionlevel'):
                    compression = zin.compressionlevel
                
                with zipfile.ZipFile(temp_save_path, 'w', compression=compression) as zout:
                    progress.set_value(60)
                    target_dict_path = f'l10n/{target_folder}/dictionary'
                    
                    dict_replaced = False
                    for item in zin.infolist():
                        # Сохраняем оригинальное имя для чтения данных, 
                        # но исправляем имя в объекте ZipInfo для правильной записи в новый архив
                        original_filename_for_read = item.filename
                        
                        try:
                            # Если имя было декодировано как CP437, но на самом деле это UTF-8
                            # (характерно для спецсимволов вроде LRM, которые превращаются в ΓÇÄ)
                            fixed_name = item.filename.encode('cp437').decode('utf-8')
                            item.filename = fixed_name
                            item.flag_bits |= 0x800  # Устанавливаем бит UTF-8
                        except (UnicodeEncodeError, UnicodeDecodeError):
                            # Если не получается, оставляем как есть
                            pass

                        if item.filename == target_dict_path:
                            # Заменяем существующий файл
                            zout.writestr(item, new_content.encode('utf-8'))
                            dict_replaced = True
                            print(f"DEBUG: Replaced existing dictionary at {target_dict_path}")
                        else:
                            # Копируем остальные файлы
                            zout.writestr(item, zin.read(original_filename_for_read))
                    
                    # Если папки/файла не существовало, добавляем его
                    if not dict_replaced:
                        zout.writestr(target_dict_path, new_content.encode('utf-8'))
                        print(f"DEBUG: Created new dictionary at {target_dict_path}")
            
            # Атомарно заменяем временный файл на целевой
            if os.path.exists(save_path):
                os.remove(save_path)
            os.rename(temp_save_path, save_path)
            
            progress.set_value(100)
            
            # Показываем отчет
            self.show_save_report(save_path)
            
        except zipfile.BadZipFile as e:
            error_msg = get_translation(self.current_language, 'error_truncated_header')
            ErrorLogger.log_error("MIZ_SAVE_AS_BADZIP", f"{error_msg}\nDetails: {str(e)}")
            self.show_custom_dialog(get_translation(self.current_language, 'error_title'), error_msg, "error")
        except Exception as e:
            error_msg = get_translation(self.current_language, 'error_miz_save', error=str(e))
            ErrorLogger.log_error("MIZ_SAVE_AS", error_msg)
            self.show_custom_dialog(get_translation(self.current_language, 'error_title'), error_msg, "error")
        finally:
            if progress:
                progress.close()

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

                # Добавляем переведённый текст или оригинал
                translated = line_data['translated_text'] if line_data['translated_text'] else line_data['original_text']
                translations[key].append(translated)

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
        translation_lines = self.translated_text_all.toPlainText().split('\n')
        
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

        # Ограничиваем количество строк до количества оригинальных строк
        if len(translation_lines) > len(self.original_lines):
            translation_lines = translation_lines[:len(self.original_lines)]
            
            # Обновляем текст в виджете (если обрезали или удалили контекст)
            self.prevent_text_changed = True
            
            # Сохраняем позицию курсора
            cursor = self.translated_text_all.textCursor()
            scroll_pos = self.translated_text_all.verticalScrollBar().value()
            
            self.translated_text_all.setPlainText('\n'.join(translation_lines))
            
            # Восстанавливаем позицию (по возможности)
            self.translated_text_all.setVerticalScrollBar(CustomScrollBar()) # Re-apply style if needed or just restore val
            self.translated_text_all.verticalScrollBar().setValue(scroll_pos)
            self.translated_text_all.setTextCursor(cursor)
            
            self.prevent_text_changed = False
            # ВАЖНО: Убрали return, чтобы данные сохранились в self.original_lines!
            
        elif context_stripped:
             # Если контекст удалили, но длина в норме, тоже обновляем виджет
            self.prevent_text_changed = True
            self.translated_text_all.setPlainText('\n'.join(translation_lines))
            self.prevent_text_changed = False

        
        # Обновляем переводы в данных
        for i, line_data in enumerate(self.original_lines):
            if i < len(translation_lines):
                line_data['translated_text'] = translation_lines[i].rstrip('\r')
            else:
                line_data['translated_text'] = ''
        
        self.update_stats()
        self.schedule_preview_update()
        
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
            for line_data in self.original_lines:
                line_data['translated_text'] = ''
            
            # Обновляем отображение
            self.update_display()
            
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

    def closeEvent(self, event):
        """Сохраняем настройки при закрытии окна"""
        try:
            self.save_settings()
        except Exception as e:
            ErrorLogger.log_error("APP_CLOSE", f"Ошибка при сохранении настроек при закрытии: {e}")
        event.accept()

# [CUSTOM_DIALOG]


# [MAIN_FUNCTION]
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = TranslationApp()
    window.show()

    sys.exit(app.exec_())
