from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QProgressBar, QGridLayout, QWidget, QPlainTextEdit, QTextBrowser
import os
from PyQt5.QtCore import Qt, QPoint, QRectF, QEvent
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath, QRegion, QDesktopServices, QFont, QFontMetrics, QMovie
from localization import get_translation
import sys

def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсу, работает в dev и в PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class CustomDialog(QDialog):
    """Кастомный диалог без заголовка окна с поддержкой перетаскивания и закруглёнными углами"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.drag_position = QPoint()
        self.dragging = False
        self.border_radius = 10

    def update_mask(self):
        """Обновляет маску для закруглённых углов"""
        try:
            path = QPainterPath()
            rect = QRectF(0, 0, self.width(), self.height())
            path.addRoundedRect(rect, self.border_radius, self.border_radius)
            region = QRegion(path.toFillPolygon().toPolygon())
            self.setMask(region)
        except Exception as e:
            from error_logger import ErrorLogger
            ErrorLogger.log_error("DIALOG_MASK", f"Ошибка установки маски: {e}")

    def paintEvent(self, event):
        """Рисует фон диалога с закруглёнными углами"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_color = QColor(64, 64, 64)

        rect = self.rect()

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self.border_radius, self.border_radius)

        pen = QPen(QColor(255, 153, 0), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(
            rect.adjusted(1, 1, -1, -1),
            self.border_radius,
            self.border_radius
        )

        super().paintEvent(event)

    def resizeEvent(self, event):
        """Обработка изменения размера диалога"""
        super().resizeEvent(event)
        self.update_mask()

    def showEvent(self, event):
        """Обработка показа диалога"""
        super().showEvent(event)
        self.update_mask()

    def mousePressEvent(self, event):
        """Обработка нажатия мыши для перетаскивания окна"""
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self.dragging = True
            self.drag_position = event.globalPos() - self.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Обработка движения мыши для перетаскивания окна"""
        if self.dragging and (event.buttons() & (Qt.LeftButton | Qt.RightButton)):
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Обработка отпускания кнопки мыши"""
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self.dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class MizFolderDialog(CustomDialog):
    """Диалог выбора папки локализации в .miz файле"""
    def __init__(self, folders, current_language, parent=None):
        super().__init__(parent)
        self.selected_folder = "DEFAULT"
        self.folders = folders
        self.current_language = current_language

        self.setWindowTitle(get_translation(self.current_language, 'miz_select_folder_title'))
        self.setFixedSize(450, 250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        combo_style = """
            QComboBox {
                background-color: #606060;
                color: #ffffff;
                border: 1px solid #777;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 200px;
                font-size: 13px;
            }
            QComboBox:focus {
                border-color: #ff9900;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: #ffffff;
                selection-background-color: #ff9900;
                selection-color: #000000;
                border: 1px solid #ff9900;
            }
        """

        title_label = QLabel(get_translation(self.current_language, 'miz_select_folder_title'))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px; background-color: transparent;")

        desc_label = QLabel(get_translation(self.current_language, 'miz_select_folder_desc'))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #bbbbbb; font-size: 11px; background-color: transparent;")

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addSpacing(5)

        self.combo = QComboBox()
        self.combo.addItems(folders)
        if "DEFAULT" in folders:
            self.combo.setCurrentText("DEFAULT")
        self.combo.setStyleSheet(combo_style)

        combo_layout = QHBoxLayout()
        combo_layout.addStretch()
        combo_layout.addWidget(self.combo)
        combo_layout.addStretch()
        layout.addLayout(combo_layout)

        btn_style_open = """
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 8px 30px;
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
        """
        btn_style_cancel = """
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                padding: 8px 30px;
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #a3a3a3;
            }
        """

        open_btn = QPushButton(get_translation(self.current_language, 'open_btn'))
        open_btn.setStyleSheet(btn_style_open)
        open_btn.clicked.connect(self.handle_accept)

        cancel_btn = QPushButton(get_translation(self.current_language, 'cancel_btn'))
        cancel_btn.setStyleSheet(btn_style_cancel)
        cancel_btn.clicked.connect(self.reject)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignCenter)

        open_row = QHBoxLayout()
        open_row.addStretch()
        open_row.addWidget(open_btn)
        open_row.addStretch()

        cancel_row = QHBoxLayout()
        cancel_row.addStretch()
        cancel_row.addWidget(cancel_btn)
        cancel_row.addStretch()

        btn_layout.addLayout(open_row)
        btn_layout.addLayout(cancel_row)
        layout.addLayout(btn_layout)

    def handle_accept(self):
        self.selected_folder = self.combo.currentText()
        self.accept()


class MizSaveAsDialog(CustomDialog):
    """Диалог выбора папки для сохранения перевода в .miz"""
    def __init__(self, current_language, action='save_as', parent=None):
        super().__init__(parent)
        self.selected_folder = "DEFAULT"
        self.current_language = current_language
        self.parent_window = parent
        self.action = action

        self.setWindowTitle(get_translation(self.current_language, 'miz_save_folder_title'))
        self.setFixedSize(450, 320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(10)

        # Заголовок с файлом миссии (две строки)
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
            font-size: 13px;
            font-weight: bold;
            background-color: transparent;
            border: none;
        ''')
        title_layout.addWidget(title_text)

        # Имя файла (оранжевым цветом) с обрезкой до 40 символов
        filename = os.path.basename(parent.current_miz_path) if parent and hasattr(parent, 'current_miz_path') else ""
        name_part, ext_part = os.path.splitext(filename)
        if len(name_part) > 40:
            display_name = name_part[:40] + "..." + ext_part
        else:
            display_name = filename
            
        filename_label = QLabel(display_name)
        filename_label.setAlignment(Qt.AlignCenter)
        filename_label.setStyleSheet('''
            color: #ff9900;
            font-size: 13px;
            font-weight: bold;
            background-color: transparent;
            border: none;
        ''')
        title_layout.addWidget(filename_label)

        layout.addWidget(title_container)

        # Разделитель
        layout.addSpacing(10)

        title_label = QLabel(get_translation(self.current_language, 'miz_save_folder_title'))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px; background-color: transparent;")

        desc_label = QLabel(get_translation(self.current_language, 'miz_save_folder_desc'))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #bbbbbb; font-size: 11px; background-color: transparent;")

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addSpacing(5)

        all_langs = ["CN", "CS", "DE", "DEFAULT", "EN", "ES", "FR", "JP", "KO", "RU"]

        self.combo = QComboBox()
        self.combo.addItems(all_langs)
        self.combo.setCurrentText("DEFAULT")
        self.combo.setStyleSheet("""
            QComboBox {
                background-color: #606060;
                color: #ffffff;
                border: 1px solid #777;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 200px;
                font-size: 13px;
            }
            QComboBox:focus { border-color: #ff9900; }
            QComboBox::drop-down { border: none; background-color: transparent; }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: #ffffff;
                selection-background-color: #ff9900;
                selection-color: #000000;
                border: 1px solid #ff9900;
            }
        """)

        combo_layout = QHBoxLayout()
        combo_layout.addStretch()
        combo_layout.addWidget(self.combo)
        combo_layout.addStretch()
        layout.addLayout(combo_layout)

        btn_style_save = """
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 8px 30px;
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover { background-color: #e68a00; }
        """
        btn_style_cancel = """
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                padding: 8px 30px;
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover { background-color: #a3a3a3; }
        """

        # Выбираем ключ локализации в зависимости от действия
        btn_key = 'save_btn' if self.action == 'overwrite' else 'save_as_btn'
        save_btn = QPushButton(get_translation(self.current_language, btn_key))
        save_btn.setStyleSheet(btn_style_save)
        save_btn.clicked.connect(self.handle_accept)

        cancel_btn = QPushButton(get_translation(self.current_language, 'cancel_btn'))
        cancel_btn.setStyleSheet(btn_style_cancel)
        cancel_btn.clicked.connect(self.reject)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignCenter)

        for btn in [save_btn, cancel_btn]:
            row = QHBoxLayout()
            row.addStretch()
            row.addWidget(btn)
            row.addStretch()
            btn_layout.addLayout(row)

        layout.addLayout(btn_layout)

    def handle_accept(self):
        self.selected_folder = self.combo.currentText()
        self.accept()


class MizProgressDialog(CustomDialog):
    """Кастомный диалог прогресс-бара для операций с .miz"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("")
        self.setFixedSize(300, 100)

        lang = 'ru'
        if parent and hasattr(parent, 'current_language'):
            lang = parent.current_language
        elif self.parent() and hasattr(self.parent(), 'current_language'):
            lang = self.parent().current_language

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.label = QLabel(get_translation(lang, 'miz_executing'))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px; background-color: transparent;")
        layout.addWidget(self.label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #ffffff;
                border: none;
                border-radius: 12px;
                text-align: center;
                color: #000000;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #ff9900;
                border-radius: 12px;
            }
        """)
        layout.addWidget(self.progress_bar)

    def set_value(self, value):
        from PyQt5.QtWidgets import QApplication
        self.progress_bar.setValue(int(value))
        QApplication.processEvents()


class AboutWindow(CustomDialog):
    """Окно 'Об авторе' (About)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        lang = 'ru'
        if parent and hasattr(parent, 'current_language'):
            lang = parent.current_language
        elif self.parent() and hasattr(self.parent(), 'current_language'):
            lang = self.parent().current_language

        self.setWindowTitle(get_translation(lang, 'about_title'))
        self.setFixedSize(854, 420)

        self.main_grid = QGridLayout(self)
        self.main_grid.setContentsMargins(0, 0, 0, 0)
        self.main_grid.setSpacing(0)

        self.content_area = QWidget()
        self.content_area.setFixedWidth(527)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(40, 20, 20, 80)

        from PyQt5.QtWidgets import QTextBrowser
        self.about_text_edit = QTextBrowser()
        self.about_text_edit.setReadOnly(True)
        self.about_text_edit.setUndoRedoEnabled(False)
        self.about_text_edit.setOpenLinks(False)
        self.about_text_edit.setOpenExternalLinks(False)
        self.about_text_edit.anchorClicked.connect(self.handle_link_click)
        self.about_text_edit.setStyleSheet("""
            QTextBrowser {
                background-color: transparent;
                color: #ffffff;
                border:1px solid #777;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                selection-background-color: #ff9900;
                selection-color: #000000;
            }
        """)
        self.about_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.about_text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.content_layout.addWidget(self.about_text_edit)

        self.update_content()
 
        self.cat_label = QLabel()
        self.cat_label.setFixedSize(327, 346)
        self.cat_label.setStyleSheet("background-color: transparent; border: none;")
        self.cat_label.setAttribute(Qt.WA_TranslucentBackground)
 
        cat_path = resource_path("cat.png")
        if os.path.exists(cat_path):
            from PyQt5.QtGui import QPixmap
            cat_pixmap = QPixmap(cat_path)
            from PyQt5.QtCore import Qt as QtCore
            scaled_cat = cat_pixmap.scaled(327, 346, QtCore.KeepAspectRatio, QtCore.SmoothTransformation)
            self.cat_label.setPixmap(scaled_cat)
        else:
            self.cat_label.setStyleSheet("color: #555; background-color: transparent;")
            self.cat_label.setText("cat.png\nnot found")
            self.cat_label.setAlignment(Qt.AlignCenter)



        self.exit_btn = QPushButton(get_translation(lang, 'exit_btn'))
        self.exit_btn.setFixedSize(120, 35)
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.clicked.connect(self.accept)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 17px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #a3a3a3;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)

        self.main_grid.addWidget(self.content_area, 0, 0)
        self.main_grid.addWidget(self.cat_label, 0, 1, Qt.AlignRight | Qt.AlignBottom)

        self.btn_container = QWidget()
        self.btn_container.setAttribute(Qt.WA_TranslucentBackground)
        self.btn_layout = QVBoxLayout(self.btn_container)
        self.btn_layout.setContentsMargins(0, 0, 0, 20)
        self.btn_layout.addWidget(self.exit_btn, 0, Qt.AlignHCenter | Qt.AlignBottom)

        self.main_grid.addWidget(self.btn_container, 0, 0, 1, 2, Qt.AlignBottom)

        self.main_grid.setContentsMargins(0, 0, 0, 0)

        self.exit_btn.raise_()

    def update_content(self):
        """Обновляет содержимое с поддержкой ссылок"""
        try:
            lang = self.parent().current_language if self.parent() else 'ru'
            text = get_translation(lang, 'about_text')

            import re
            text = re.sub(r'(https?://[^\s<>]+)', r'<a href="\1" style="color: #ff9900;">\1</a>', text)

            addr = "TKLcwmrNmwXFgwbpS66UnAGsB3Lvnqpwv5"
            if addr in text:
                copy_link = f' <a href="copy:{addr}" style="text-decoration: none; color: #ff9900;">📋</a>'
                text = text.replace(addr, f"{addr}{copy_link}")

            html = text.replace('\n', '<br>')
            self.about_text_edit.setHtml(f'<div style="color: #ffffff; font-family: sans-serif;">{html}</div>')
        except Exception as e:
            print(f"DEBUG: Error in update_content: {e}")
            self.about_text_edit.setPlainText("Error loading content")

    def handle_link_click(self, url):
        """Обработчик нажатия на ссылки"""
        from PyQt5.QtCore import QUrl
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtWidgets import QApplication
        url_str = url.toString()
        if url_str.startswith("copy:"):
            addr = url_str.split(":")[1]
            QApplication.clipboard().setText(addr)
            return

        lang = self.parent().current_language if self.parent() else 'ru'
        title = get_translation(lang, 'open_btn')
        msg = "Вы действительно хотите открыть ссылку в браузере?\n\n" + url_str if lang == 'ru' else "Do you really want to open this link in your browser?\n\n" + url_str

        if self.parent().show_question_dialog(title, msg):
            QDesktopServices.openUrl(url)


class AIContextWindow(CustomDialog):
    """Окно управления контекстом для ИИ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        lang = 'ru'
        if parent and hasattr(parent, 'current_language'):
            lang = parent.current_language
        self.lang = lang
            
        self.setWindowTitle(get_translation(lang, 'ai_context_title'))
        
        # --- ПАРАМЕТРЫ ДЛЯ РУЧНОЙ ПОДГОНКИ (ОФФСЕТЫ) ---
        self.window_width = 700
        self.setFixedSize(self.window_width, 860)
        
        # Поля ввода
        self.fields_width_percent = 0.75 # Увеличено относительно новой ширины окна
        self.fields_left_margin = 25
        self.fields_y_start = 100
        self.fields_spacing = 350 # Расстояние между началом 1-го и началом 2-го поля
        self.fields_height = 300
        
        # Метки (Используемый/Запасной контекст)
        self.label_1_x_offset = 10
        self.label_1_y_offset = -15
        self.label_2_x_offset = 10
        self.label_2_y_offset = -15
        
        # Кнопки "Поменять местами" (GIF)
        self.gif_swap_x_offset = 0 # Смещение по горизонтали (относительно центра между полями)
        self.gif_swap_y_offset = 0 # Смещение по вертикали
        
        # Кнопка "Контекст по умолчанию" (GIF)
        self.gif_default_x_offset = 0
        self.gif_default_y_offset = 50 # Смещение относительно базового Y (50)
        
        # Заголовок окна
        self.title_label_y_offset = 15
        self.title_label_font_size = 14

        # Кнопки "Сохранить"
        self.btn_save_x_offset = 10 # Отступ вправо от поля ввода
        self.btn_save_height = 32
        self.btn_save_width = 120    # <--- ШИРИНА КНОПКИ "СОХРАНИТЬ"
        self.btn_save_font_size = 11
        
        # Индикаторы (желтые треугольники)
        self.warn_y_offset = 45 # Отступ вниз от кнопки Сохранить
        self.warn_x_offset = 50 # Центрирование под кнопкой

        # Кнопка "Назад"
        self.btn_back_y_bottom_offset = 55 # Отступ от низа окна
        self.btn_back_width = 120    # <--- ШИРИНА КНОПКИ "НАЗАД"
        self.btn_back_x_offset = 0 # Добавлен для гибкости
        self.btn_back_y_offset = 0 # Добавлен для гибкости
        # -----------------------------------------------

        # Рассчитываем общую фиксированную ширину для всех кнопок на основе русского текста
        # Это предотвращает изменение размера кнопок при смене языка
        font = QFont()
        font.setBold(True)
        font.setPixelSize(12) # Используем пиксели (px), так как в стилях указаны px
        metrics = QFontMetrics(font)
        
        # Список всех русских названий кнопок для расчета
        ru_texts = [
            'Контекст по умолчанию',
            'Поменять местами',
            'Сохранить',
            'Назад'
        ]
        
        # Находим максимальную ширину с учетом иконок и отступов (примерно как в главном окне + 40-50px)
        max_text_w = 0
        for text in ru_texts:
            w_text = metrics.horizontalAdvance(text)
            if w_text > max_text_w:
                max_text_w = w_text
        
        # Лишний отступ для фиксации ширины ПОБОЧНЫХ кнопок (padding слева + справа)
        self.common_btn_padding_extra = 0 
        # self.common_btn_fixed_width = max_text_w + self.common_btn_padding_extra # This was used before, now using explicit widths

        # Тексты из настроек (будут установлены родителем)
        self.context_1 = ""
        self.context_2 = ""
        
        # Флаги изменений
        self.changed_1 = False
        self.changed_2 = False

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        # Поле 1: Используемый контекст
        self.label_1 = QLabel(get_translation(self.lang, 'context_label_1'), self)
        self.label_1.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")
        
        self.edit_1 = QPlainTextEdit(self)
        self.setup_edit_style(self.edit_1)
        self.edit_1.textChanged.connect(self.on_text_1_changed)
        
        # Поле 2: Запасной контекст
        self.label_2 = QLabel(get_translation(self.lang, 'context_label_2'), self)
        self.label_2.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")
        
        self.edit_2 = QPlainTextEdit(self)
        self.setup_edit_style(self.edit_2)
        self.edit_2.textChanged.connect(self.on_text_2_changed)

        # Заголовок окна
        self.title_label = QLabel(get_translation(self.lang, 'ai_context_title'), self)
        self.title_label.setStyleSheet(f"color: #ff9900; font-weight: bold; font-size: {self.title_label_font_size}px;")
        self.title_label.setAlignment(Qt.AlignCenter)

        # Кнопка "Контекст по умолчанию" (GIF)
        self.btn_default = QLabel(self)
        self.btn_default.setFixedSize(32, 32)
        self.btn_default.setCursor(Qt.PointingHandCursor)
        self.btn_default.installEventFilter(self)
        
        # Попытка загрузить GIF
        default_gif_path = resource_path("arrow2.gif")
        if os.path.exists(default_gif_path):
            self.movie_default = QMovie(default_gif_path)
            self.movie_default.setScaledSize(self.btn_default.size())
            self.btn_default.setMovie(self.movie_default)
            if self.movie_default.jumpToFrame(0):
                self.movie_default.stop()
        else:
            self.btn_default.setText("🔄")
            self.btn_default.setStyleSheet("color: #ff9900; font-size: 20px;")
            self.btn_default.setAlignment(Qt.AlignCenter)
            
        # Тултип для кнопки (кастомный оранжевый)
        if self.parent() and hasattr(self.parent(), 'register_custom_tooltip'):
            self.parent().register_custom_tooltip(self.btn_default, get_translation(self.lang, 'tooltip_default_context'), side='bottom-right')

        # Кнопки "Сохранить"
        self.btn_save_1 = QPushButton(get_translation(self.lang, 'context_save_btn'), self)
        self.setup_orange_button(self.btn_save_1)
        self.btn_save_1.clicked.connect(lambda: self.save_field(1))
        
        self.btn_save_2 = QPushButton(get_translation(self.lang, 'context_save_btn'), self)
        self.setup_orange_button(self.btn_save_2)
        self.btn_save_2.clicked.connect(lambda: self.save_field(2))

        # Предупреждения (желтые треугольники)
        self.warn_1 = QLabel("⚠️", self)
        self.warn_1.setStyleSheet("font-size: 30px; color: #ffcc00;")
        self.warn_1.setToolTip(get_translation(self.lang, 'context_unsaved_warning'))
        self.warn_1.hide()

        self.warn_2 = QLabel("⚠️", self)
        self.warn_2.setStyleSheet("font-size: 30px; color: #ffcc00;")
        self.warn_2.setToolTip(get_translation(self.lang, 'context_unsaved_warning'))
        self.warn_2.hide()

        # Кнопка "Поменять местами" (GIF)
        self.btn_swap = QLabel(self)
        self.btn_swap.setFixedSize(64, 32)
        self.btn_swap.setCursor(Qt.PointingHandCursor)
        self.btn_swap.installEventFilter(self)
        
        swap_gif_path = resource_path("arrow1.gif")
        if os.path.exists(swap_gif_path):
            self.movie_swap = QMovie(swap_gif_path)
            self.movie_swap.setScaledSize(self.btn_swap.size())
            self.btn_swap.setMovie(self.movie_swap)
            if self.movie_swap.jumpToFrame(0):
                self.movie_swap.stop()
        else:
            self.btn_swap.setText("⇅")
            self.btn_swap.setStyleSheet("color: #ff9900; font-size: 24px;")
            self.btn_swap.setAlignment(Qt.AlignCenter)

        # Кнопка "Назад"
        self.btn_back = QPushButton(get_translation(self.lang, 'context_back_btn'), self)
        self.setup_white_button(self.btn_back)
        self.btn_back.clicked.connect(self.close)

        self.update_positions()

    def setup_edit_style(self, edit):
        edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #505050;
                color: #ffffff;
                border: 1px solid #777;
                border-radius: 4px;
                padding: 5px;
            }
            QPlainTextEdit:focus {
                border: 1px solid #ff9900;
            }
        """)
        # С задержкой импорта для CustomScrollBar если нужно, но здесь используем из widgets через парент или напрямую
        try:
            from widgets import CustomScrollBar
            edit.setVerticalScrollBar(CustomScrollBar(Qt.Vertical))
        except:
            pass
        edit.setLineWrapMode(QPlainTextEdit.WidgetWidth)

    def setup_orange_button(self, btn):
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(self.btn_save_height)
        btn.setFixedWidth(self.btn_save_width) # Use the exposed width
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ff9900;
                color: #000000;
                border-radius: {self.btn_save_height // 2}px;
                padding: 0px 5px;
                font-weight: bold;
                font-size: {self.btn_save_font_size}px;
            }}
            QPushButton:hover {{ background-color: #e68a00; }}
            QPushButton:pressed {{ background-color: #cc7a00; }}
        """)

    def setup_white_button(self, btn):
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(self.btn_save_height)
        btn.setFixedWidth(self.btn_back_width) # Use the exposed width for back button
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: #000000;
                border-radius: {self.btn_save_height // 2}px;
                padding: 0px 5px;
                font-weight: bold;
                font-size: {self.btn_save_font_size}px;
            }}
            QPushButton:hover {{ background-color: #e0e0e0; }}
            QPushButton:pressed {{ background-color: #d0d0d0; }}
        """)

    def update_positions(self):
        w = self.width()
        h = self.height()
        fw = int(w * self.fields_width_percent)
        fh = self.fields_height
        
        mx = self.fields_left_margin
        y1 = self.fields_y_start
        y2 = y1 + self.fields_spacing
        
        # Позиционирование заголовка
        title_w = self.title_label.sizeHint().width()
        self.title_label.setGeometry((w - title_w) // 2, self.title_label_y_offset, title_w, 30)

        # Позиционирование полей и меток
        self.label_1.setFixedWidth(fw)
        self.label_1.move(mx + self.label_1_x_offset, y1 + self.label_1_y_offset)
        self.edit_1.setGeometry(mx, y1, fw, fh)
        
        self.label_2.setFixedWidth(fw)
        self.label_2.move(mx + self.label_2_x_offset, y2 + self.label_2_y_offset)
        self.edit_2.setGeometry(mx, y2, fw, fh)
        
        # Кнопки "Сохранить" (справа от полей)
        bx = mx + fw + self.btn_save_x_offset
        self.btn_save_1.move(bx, y1 + (fh - self.btn_save_1.height()) // 2)
        self.btn_save_2.move(bx, y2 + (fh - self.btn_save_2.height()) // 2)
        
        # Индикаторы (желтые треугольники) под кнопками сохранить
        self.warn_1.adjustSize()
        self.warn_2.adjustSize()
        self.warn_1.move(bx + (self.btn_save_1.width() - self.warn_1.width()) // 2, 
                         self.btn_save_1.y() + self.warn_y_offset)
        self.warn_2.move(bx + (self.btn_save_2.width() - self.warn_2.width()) // 2, 
                         self.btn_save_2.y() + self.warn_y_offset)
        
        # Кнопка "Контекст по умолчанию" (GIF) - СВЕРХУ
        def_x = bx + self.gif_default_x_offset
        def_y = 50 + self.gif_default_y_offset
        self.btn_default.move(def_x, def_y)

        # Кнопка "Поменять местами" (GIF) - между полями
        mid_y = (y1 + fh + y2) // 2
        swap_x = mx + (fw // 2) - (self.btn_swap.width() // 2) + self.gif_swap_x_offset
        swap_y = mid_y - (self.btn_swap.height() // 2) + self.gif_swap_y_offset
        self.btn_swap.move(swap_x, swap_y)
        
        # Кнопка "Назад"
        self.btn_back.move(w // 2 - self.btn_back_width // 2 + self.btn_back_x_offset, 
                          h - self.btn_back_y_bottom_offset + self.btn_back_y_offset)

    def eventFilter(self, obj, event):
        # Предотвращаем падение, если кнопки еще не созданы
        if not hasattr(self, 'btn_swap') or not hasattr(self, 'btn_default'):
            return super().eventFilter(obj, event)
            
        # Обработка GIF кнопок (arrow1.gif и arrow2.gif)
        if obj in [self.btn_swap, self.btn_default]:
            movie = None
            if obj == self.btn_swap and hasattr(self, 'movie_swap'):
                movie = self.movie_swap
            elif obj == self.btn_default and hasattr(self, 'movie_default'):
                movie = self.movie_default
            
            if movie:
                if event.type() == QEvent.Enter:
                    # Переход на 2-й кадр (индекс 1)
                    if movie.jumpToFrame(1):
                        movie.stop()
                    return False # <--- ВАЖНО: возвращаем False, чтобы тултип сработал
                elif event.type() == QEvent.Leave:
                    # Переход на 1-й кадр (индекс 0)
                    if movie.jumpToFrame(0):
                        movie.stop()
                    return False # <--- ВАЖНО: возвращаем False
                elif event.type() == QEvent.MouseMove:
                    return False # <--- ВАЖНО: возвращаем False
                elif event.type() == QEvent.MouseButtonRelease:
                    if event.button() == Qt.LeftButton:
                        if obj == self.btn_swap:
                            self.swap_contexts()
                        else:
                            self.set_default_context()
                        return True
        
        return super().eventFilter(obj, event)

    def load_data(self):
        # Будет вызвано извне после установки context_1/2 родителем
        self.edit_1.setPlainText(self.context_1)
        self.edit_2.setPlainText(self.context_2)
        self.changed_1 = False
        self.changed_2 = False
        self.warn_1.hide()
        self.warn_2.hide()

    def on_text_1_changed(self):
        if self.edit_1.toPlainText() != self.context_1:
            self.changed_1 = True
            self.warn_1.show()
        else:
            self.changed_1 = False
            self.warn_1.hide()

    def on_text_2_changed(self):
        if self.edit_2.toPlainText() != self.context_2:
            self.changed_2 = True
            self.warn_2.show()
        else:
            self.changed_2 = False
            self.warn_2.hide()

    def set_default_context(self):
        default_text = get_translation(self.lang, 'default_context_text')
        self.edit_1.setPlainText(default_text)

    def swap_contexts(self):
        t1 = self.edit_1.toPlainText()
        t2 = self.edit_2.toPlainText()
        self.edit_1.setPlainText(t2)
        self.edit_2.setPlainText(t1)

    def save_field(self, field_id):
        if field_id == 1:
            self.context_1 = self.edit_1.toPlainText()
            self.changed_1 = False
            self.warn_1.hide()
        else:
            self.context_2 = self.edit_2.toPlainText()
            self.changed_2 = False
            self.warn_2.hide()
        
        # Вызываем метод сохранения в родителе
        if self.parent() and hasattr(self.parent(), 'save_ai_context_settings'):
            self.parent().save_ai_context_settings(self.context_1, self.context_2)


class InstructionsWindow(CustomDialog):
    """Окно с инструкцией по переводу"""
    def __init__(self, parent=None):
        super().__init__(parent)
        lang = 'ru'
        if parent and hasattr(parent, 'current_language'):
            lang = parent.current_language
            
        self.setWindowTitle(get_translation(lang, 'instructions_btn'))
        self.setFixedSize(700, 800)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Текст заголовка
        title_label = QLabel(get_translation(lang, 'instructions_btn'))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #ff9900; font-weight: bold; font-size: 18px; background-color: transparent;")
        layout.addWidget(title_label)
        
        # Область просмотра текста
        from PyQt5.QtWidgets import QTextBrowser
        self.text_browser = QTextBrowser()
        self.text_browser.setReadOnly(True)
        # Фон как в Preview (#505050), серая рамка (1px solid #777)
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #505050;
                color: #ffffff;
                border: 1px solid #777;
                border-radius: 6px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        
        # Устанавливаем кастомный скроллбар (как в приложении)
        try:
            from widgets import CustomScrollBar
            self.text_browser.setVerticalScrollBar(CustomScrollBar())
        except Exception:
            pass
            
        # Получаем текст из локализации
        content = get_translation(lang, 'instruction_content')
        self.text_browser.setText(content)
        
        layout.addWidget(self.text_browser)
        
        # Кнопка закрытия
        self.close_btn = QPushButton(get_translation(lang, 'exit_btn'))
        self.close_btn.setFixedSize(120, 32)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #a3a3a3;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
