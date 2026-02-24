import os
import pygame
import traceback
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QProgressBar, QGridLayout, QWidget, QPlainTextEdit, QTextBrowser, QSlider, QStyle, QFileDialog, QFrame, QLineEdit, QLayout, QSizePolicy, QScrollArea
from PyQt5.QtCore import Qt, QPoint, QRectF, QRect, QEvent, QUrl, QTimer, QSize, pyqtSignal
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath, QRegion, QDesktopServices, QFont, QFontMetrics, QMovie, QPixmap
from localization import get_translation
from widgets import ToggleSwitch
from version import VersionInfo
from Context import AI_CONTEXTS
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

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.drag_position = QPoint()
        self.dragging = False
        self.border_radius = 10
        self.offset = None
        self.is_active = True # Флаг активности окна
        self.bg_color = QColor(64, 64, 64)  # Цвет фона по умолчанию

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
        """Рисует фон диалога с закруглёнными углами и динамической рамкой"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_color = self.bg_color


        rect = self.rect()

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self.border_radius, self.border_radius)

        # Рамка: Оранжевая если активно (#ff9900), серая если нет (#8f8f8f)
        # Используем QRectF и смещение 0.5 для четкой отрисовки в 1 пиксель без размытия
        border_color = QColor(255, 153, 0) if self.is_active else QColor("#8f8f8f")
        pen = QPen(border_color, 1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(
            QRectF(0.5, 0.5, rect.width() - 1, rect.height() - 1),
            self.border_radius, self.border_radius
        )

        super().paintEvent(event)

    def resizeEvent(self, event):
        """Обработка изменения размера диалога"""
        super().resizeEvent(event)
        self.update_mask()

    def showEvent(self, event):
        # Обработка показа диалога
        self.update_mask()
        self.is_active = True # Устанавливаем статус активным при показе
        super().showEvent(event)

    def changeEvent(self, event):
        """Отслеживает изменение состояния окна (фокус/активность)"""
        if event.type() == QEvent.ActivationChange:
            self.is_active = self.isActiveWindow()
            self.update() # Принудительно перерисовываем рамку
        super().changeEvent(event)

    def mousePressEvent(self, event):
        """Обработка нажатия мыши для перетаскивания окна (ЛКМ и ПКМ)"""
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Обработка движения мыши для перетаскивания окна (ЛКМ и ПКМ)"""
        if self.dragging:
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


class LocaleButton(QPushButton):
    """Кнопка локали с обработкой двойного щелчка"""
    locale_double_clicked = pyqtSignal(str)
    
    def __init__(self, locale, parent=None):
        super().__init__(locale, parent)
        self.locale = locale
    
    def mouseDoubleClickEvent(self, event):
        """Испускаем сигнал двойного щелчка"""
        self.locale_double_clicked.emit(self.locale)
        event.accept()


class LocaleSelectorWidget(QWidget):
    """Горизонтальный селектор локалей, заменяет QComboBox в выборе папки .miz"""
    locale_activated = pyqtSignal()
    
    def __init__(self, folders, parent=None):
        super().__init__(parent)
        self.folders = self._sort_locales(list(folders))
        self.selected_locale = "DEFAULT" if "DEFAULT" in self.folders else (self.folders[0] if self.folders else None)
        self.locale_buttons = {}

        # FlowLayout позволяет кнопкам переноситься на следующую строку
        # если не помещаются в ширину окна.
        class FlowLayout(QLayout):
            def __init__(self, parent=None, margin=0, spacing=10, max_per_row=None):
                super().__init__(parent)
                self.itemList = []
                if parent is not None:
                    self.setContentsMargins(margin, margin, margin, margin)
                self._spacing = spacing
                self._max_per_row = max_per_row

            def addItem(self, item):
                self.itemList.append(item)

            def count(self):
                return len(self.itemList)

            def itemAt(self, index):
                if 0 <= index < len(self.itemList):
                    return self.itemList[index]
                return None

            def takeAt(self, index):
                if 0 <= index < len(self.itemList):
                    return self.itemList.pop(index)
                return None

            def expandingDirections(self):
                return Qt.Orientations(0)

            def hasHeightForWidth(self):
                return True

            def heightForWidth(self, width):
                return self.doLayout(QRect(0, 0, width, 0), True)

            def setGeometry(self, rect):
                super().setGeometry(rect)
                self.doLayout(rect, False)

            def sizeHint(self):
                return self.minimumSize()

            def minimumSize(self):
                size = QSize()
                for item in self.itemList:
                    size = size.expandedTo(item.minimumSize())
                left, top, right, bottom = self.getContentsMargins()
                return size + QSize(left + right, top + bottom)

            def spacing(self):
                return self._spacing

            def doLayout(self, rect, testOnly):
                spaceX = self.spacing()
                spaceY = self.spacing()

                # Collect items for each line to center-align them
                lines = []
                current_line_items = []
                current_line_width = 0

                for item in self.itemList:
                    widgetSize = item.sizeHint()
                    item_width = widgetSize.width()
                    nextX = current_line_width + item_width + spaceX

                    wrap_by_width = (nextX - spaceX > rect.width() and current_line_items)
                    wrap_by_count = (self._max_per_row is not None and len(current_line_items) >= self._max_per_row)

                    if wrap_by_width or wrap_by_count:
                        lines.append(current_line_items)
                        current_line_items = []
                        current_line_width = 0
                        nextX = item_width + spaceX

                    current_line_items.append((item, widgetSize))
                    current_line_width = nextX

                if current_line_items:
                    lines.append(current_line_items)

                # Now layout items with center alignment
                y = rect.y()
                lineHeight = 0

                for line_items in lines:
                    # Calculate total width of this line
                    line_width = sum(item[1].width() for item in line_items) + spaceX * (len(line_items) - 1)
                    # Center offset
                    offset = max(0, (rect.width() - line_width) // 2)

                    line_x = rect.x() + offset
                    lineHeight = 0
                    for item, widgetSize in line_items:
                        if not testOnly:
                            item.setGeometry(QRect(QPoint(line_x, y), widgetSize))
                        line_x += widgetSize.width() + spaceX
                        lineHeight = max(lineHeight, widgetSize.height())

                    y += lineHeight + spaceY

                return y - rect.y() - spaceY if lines else 0

        layout = FlowLayout(self, margin=0, spacing=10, max_per_row=5)

        font = QFont()
        font.setPointSize(14)

        # Ограничение: максимум локалей в строке
        max_per_row = 5
        # Ширина диалога задана в MizFolderDialog: 450, отступы layout: 30+30
        content_width = 450 - 30 - 30
        spacing = 10
        # Вычисляем полную ширину кнопки, помещающуюся по 5 штук,
        # затем уменьшаем ширину всех кнопок (кроме DEFAULT) вдвое.
        button_width_full = max(60, (content_width - spacing * (max_per_row - 1)) // max_per_row)
        button_width = max(40, button_width_full // 2)

        for locale in self.folders:
            btn = LocaleButton(locale)
            btn.setFont(font)
            btn.setCursor(Qt.PointingHandCursor)
            # DEFAULT оставляем полной ширины, остальные — уменьшенные
            if locale == "DEFAULT":
                btn.setFixedWidth(button_width_full)
            else:
                btn.setFixedWidth(button_width)
            btn.setFixedHeight(28)  # 7px top + 14px font + 7px bottom

            # inactive style
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #5a5a5a;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 4px;
                    padding: 0px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #454545;
                }
            """)

            btn.clicked.connect(lambda _, l=locale: self._select_locale(l))
            btn.locale_double_clicked.connect(lambda l: self._on_locale_double_clicked(l))
            self.locale_buttons[locale] = btn
            layout.addWidget(btn)

        # Allow the selector widget to expand to available width so FlowLayout
        # can wrap items horizontally into rows of up to `max_per_row`.
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # Ensure selector occupies dialog content width so wrapping is horizontal.
        self.setMinimumWidth(content_width)
        self.setLayout(layout)

        # select default
        if self.selected_locale:
            self._select_locale(self.selected_locale)

    def _sort_locales(self, locales):
        ordered = []
        if "DEFAULT" in locales:
            ordered.append("DEFAULT"); locales.remove("DEFAULT")
        if "RU" in locales:
            ordered.append("RU"); locales.remove("RU")
        locales.sort()
        ordered.extend(locales)
        return ordered

    def _select_locale(self, locale):
        # reset previous
        if self.selected_locale in self.locale_buttons:
            old = self.locale_buttons[self.selected_locale]
            old.setStyleSheet("""
                QPushButton {
                    background-color: #5a5a5a;
                    color: #ffffff;
                    border: 1px solid #ffffff;
                    border-radius: 4px;
                    padding: 0px;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #454545; }
            """)
        self.selected_locale = locale
        btn = self.locale_buttons.get(locale)
        if btn:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #5a5a5a;
                    color: #ff9900;
                    border: 1px solid #ff9900;
                    border-radius: 4px;
                    padding: 0px;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #454545; }
            """)

    def get_selected_locale(self):
        return self.selected_locale

    def _on_locale_double_clicked(self, locale):
        """Обработка двойного щелчка на локаль"""
        self._select_locale(locale)
        self.locale_activated.emit()


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

        # Вместо QComboBox используем горизонтальный селектор локалей
        try:
            self.locale_selector = LocaleSelectorWidget(folders)
            combo_layout = QHBoxLayout()
            combo_layout.addStretch()
            combo_layout.addWidget(self.locale_selector)
            combo_layout.addStretch()
            layout.addLayout(combo_layout)
            # Подключаем сигнал двойного щелчка к закрытию диалога с выбранной локалью
            self.locale_selector.locale_activated.connect(self.handle_accept)
        except Exception:
            # fallback на QComboBox если что-то пошло не так
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
        # Берём выбранную локаль из нового селектора, либо из combo как fallback
        try:
            self.selected_folder = self.locale_selector.get_selected_locale()
        except Exception:
            self.selected_folder = self.combo.currentText() if hasattr(self, 'combo') else "DEFAULT"
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
            text = get_translation(lang, 'about_text').format(version=VersionInfo.CURRENT)

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


class AudioPlayerDialog(CustomDialog):
    """Диалог аудиоплеера с возможностью замены файла (Pygame version)"""
    def __init__(self, audio_path, filename, current_language, key=None, on_replace_callback=None, parent=None, last_audio_folder=None, is_heuristic=False):
        super().__init__(parent)
        self.audio_path = audio_path # Временный путь к файлу для воспроизведения
        self.filename = filename     # Оригинальное имя файла
        self.current_language = current_language
        self.key = key               # Ключ (DictKey), для которого открыт плеер
        self.on_replace_callback = on_replace_callback # Callback для сохранения замены
        self.new_file_path = None    # Путь к новому файлу, если выбрали замену
        self.last_audio_folder = last_audio_folder # Последняя папка для выбора аудиофайлов
        self.is_heuristic = is_heuristic  # Аудио связано эвристически
        
        self.duration_sec = 0
        self.is_playing = False
        self.is_paused = False
        self.is_slider_dragged = False
        self.play_start_offset = 0 # Смещение для корректного отображения времени при перемотке
        self.audio_loaded = False
        
        self.setWindowTitle(get_translation(current_language, 'audio_player_title'))
        self.setFixedSize(550, 285)
        
        # Загрузка начального трека
        if audio_path and os.path.exists(audio_path):
            self.load_audio_file(audio_path)

        self.setup_ui()
        
        # Таймер для обновления UI
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100) # каждые 100 мс для плавного обновления

    def retranslate_ui(self, current_language):
        """Обновляет переводы интерфейса"""
        self.current_language = current_language
        self.setWindowTitle(get_translation(self.current_language, 'audio_player_title'))
        self.stop_btn.setToolTip(get_translation(self.current_language, 'stop_btn'))
        # Обновляем тултип для play/pause в зависимости от состояния
        tooltip_key = 'pause_btn' if self.is_playing and not self.is_paused else 'play_btn'
        self.play_pause_btn.setToolTip(get_translation(self.current_language, tooltip_key))
        self.replace_btn.setText(get_translation(self.current_language, 'replace_audio_btn'))
        
        # Если файл не выбран, обновляем надпись "Файл не выбран"
        if not self.audio_path:
            self.file_label.setText(get_translation(self.current_language, 'no_audio_file'))

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 10, 30, 10)
        layout.setSpacing(-10)

        # Кнопка закрытия (крестик) - абсолютное позиционирование (15px от краев)
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaaaaa;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff9900;
            }
        """)
        self.close_btn.move(550 - 30 - 15, 15)

        # 1. Название файла
        self.file_label = QLabel(self.filename)
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setWordWrap(True)
        # Добавляем padding-right: 45px, чтобы текст не залезал под абсолютно позиционированный крестик справа
        self.file_label.setStyleSheet("color: #ff9900; font-weight: bold; font-size: 14px; background-color: transparent; padding-right: 45px;")
        self.file_label.setAttribute(Qt.WA_TransparentForMouseEvents) 
        self.file_label.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.file_label)
        
        # 2. Группирующая рамка для управления и картинки
        self.controls_frame = QFrame()
        self.controls_frame.setObjectName("controlsFrame")
        self.controls_frame.setFixedSize(490, 125)
        self.controls_frame.setStyleSheet("""
            QFrame#controlsFrame {
                border: 1px solid #777;
                border-radius: 5px;
                background-color: transparent;
            }
        """)
        
        # Общий горизонтальный слой внутри рамки
        frame_outer_hbox = QHBoxLayout(self.controls_frame)
        frame_outer_hbox.setContentsMargins(15, 5, 15, 5)
        frame_outer_hbox.setSpacing(10)

        # Левая часть рамки - управление
        controls_vbox = QVBoxLayout()
        controls_vbox.setSpacing(5)

        # Инфо времени
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #aaaaaa; font-size: 12px; background-color: transparent;")
        self.time_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        controls_vbox.addWidget(self.time_label)

        # 3. Слайдер
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #777;
                height: 4px;
                background: #b0b0b0;
                margin: 2px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 1px solid #ffffff;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #ff9900;
                border-radius: 2px;
            }
        """)
        # Диапазон слайдера: от 0 до duration_ms
        self.position_slider.setRange(0, int(self.duration_sec * 1000))
        self.position_slider.sliderPressed.connect(self.on_slider_pressed)
        self.position_slider.sliderReleased.connect(self.on_slider_released)
        controls_vbox.addWidget(self.position_slider)

        # 4. Кнопки управления + громкость
        controls_row = QHBoxLayout()
        controls_row.setAlignment(Qt.AlignCenter)
        controls_row.setSpacing(15)

        btn_style_base = """
            QPushButton {{
                background-color: transparent;
                color: #ffffff;
                border: none;
                font-family: 'Segoe UI Symbol', Consolas, 'Segoe UI', sans-serif;
                font-weight: bold;
                font-size: {size}px;
                min-width: 40px;
                min-height: 40px;
                max-width: 40px;
                max-height: 40px;
                padding-top: {top}px;
                text-align: center;
            }}
            QPushButton:hover {{
                color: #ff9900;
            }}
        """

        # (no extra pressed/focus rules — keep base style minimal)

        # Play/Pause toggle button (слева)
        self.play_pause_btn = QPushButton("▶")
        self.play_pause_btn.setToolTip(get_translation(self.current_language, 'play_btn'))
        self.btn_style_base = btn_style_base  # сохраняем для смены стиля при переключении
        # Vertical offsets for fine-tuning position (edit these to nudge icon vertically)
        self.play_btn_top_offset = -4
        self.stop_btn_top_offset = 0
        # standard play icon size (use consistent top offset)
        self.play_pause_btn.setStyleSheet(btn_style_base.format(size=28, top=self.play_btn_top_offset))
        self.play_pause_btn.setFixedSize(40, 40)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        controls_row.addWidget(self.play_pause_btn)

        # Stop (справа)
        self.stop_btn = QPushButton("■")
        self.stop_btn.setToolTip(get_translation(self.current_language, 'stop_btn'))
        self.stop_btn.setStyleSheet(btn_style_base.format(size=24, top=self.stop_btn_top_offset))
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.clicked.connect(self.stop_audio)
        controls_row.addWidget(self.stop_btn)

        controls_row.addStretch()

        # Громкость
        vol_label = QLabel("🔊")
        vol_label.setStyleSheet("color: #aaa; background-color: transparent; font-size: 18px; padding-top: -2px;")
        vol_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        controls_row.addWidget(vol_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setRange(0, 100)
        # Устанавливаем громкость из настроек родителя (main.py)
        initial_vol = 50
        if self.parent() and hasattr(self.parent(), 'audio_volume'):
            initial_vol = self.parent().audio_volume
        self.volume_slider.setValue(initial_vol)
        
        # Применяем громкость сразу при инициализации
        pygame.mixer.music.set_volume(initial_vol / 100.0)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #777;
                height: 4px;
                background: #b0b0b0;
                margin: 2px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 10px;
                height: 10px;
                margin: -3px 0;
                border-radius: 5px;
            }
            QSlider::sub-page:horizontal {
                background: #ff9900;
                border-radius: 2px;
            }
        """)
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls_row.addWidget(self.volume_slider)
        
        controls_vbox.addLayout(controls_row)
        frame_outer_hbox.addLayout(controls_vbox)
        frame_outer_hbox.addSpacing(130) # Резервируем место под кота справа

        # 5. Картинка radiocat.png (правая часть рамки)
        # Мы используем абсолютное позиционирование .move(), чтобы картинка не обрезалась лейаутом
        img_x = 14  # <--- СМЕЩЕНИЕ ПО ГОРИЗОНТАЛИ (влево/вправо)
        img_y = 7  # <--- СМЕЩЕНИЕ ПО ВЕРТИКАЛИ (вверх/вниз)

        self.img_label = QLabel(self.controls_frame) # Указываем родителя напрямую
        self.img_label.setFixedSize(121, 110)
        
        img_path = os.path.join(os.path.dirname(__file__), "radiocat.png")
        if os.path.exists(img_path):
            pix = QPixmap(img_path)
            self.img_label.setPixmap(pix.scaled(121, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Placeholder if not found
            self.img_label.setStyleSheet("border: 1px dashed #777; color: #777; font-size: 10px;")
            self.img_label.setText("radiocat.png\n(121x110)")
            self.img_label.setAlignment(Qt.AlignCenter)

        # Устанавливаем положение (базовые координаты 354, 7 + оффсеты)
        self.img_label.move(354 + img_x, 7 + img_y)
        self.img_label.show() # Важно для виджетов без лейаута

        # Центрируем рамку в основном лайауте
        frame_centered_hbox = QHBoxLayout()
        frame_centered_hbox.setContentsMargins(0, 0, 0, 0)
        frame_centered_hbox.addStretch()
        frame_centered_hbox.addWidget(self.controls_frame)
        frame_centered_hbox.addStretch()
        layout.addLayout(frame_centered_hbox)

        # 5. Замена (теперь внизу)
        self.replace_btn = QPushButton(get_translation(self.current_language, 'replace_audio_btn'))
        self.replace_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 8px 20px;
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
        """)
        self.replace_btn.clicked.connect(self.replace_audio)
        replace_layout = QHBoxLayout()
        replace_layout.setContentsMargins(0, 10, 0, 15)
        replace_layout.addStretch()
        replace_layout.addWidget(self.replace_btn)
        replace_layout.addStretch()
        layout.addLayout(replace_layout)

        # Initial label update
        self.update_time_labels(0)
        
        # Поднимаем кнопку закрытия на самый верхний слой
        self.close_btn.raise_()

    def load_audio_file(self, audio_path):
        """Вспомогательный метод для загрузки файла в миксер"""
        try:
            if audio_path and os.path.exists(audio_path):
                # Сначала Sound для длительности
                sound = pygame.mixer.Sound(audio_path)
                self.duration_sec = sound.get_length()
                del sound
                
                # Потом music для стриминга
                pygame.mixer.music.load(audio_path)
                self.audio_loaded = True
                # Используем сохраненную громкость вместо 0.5
                current_vol = 50
                if self.parent() and hasattr(self.parent(), 'audio_volume'):
                    current_vol = self.parent().audio_volume
                pygame.mixer.music.set_volume(current_vol / 100.0)
        except Exception as e:
            print(f"Error loading audio file: {e}")
            self.duration_sec = 0
            self.audio_loaded = False

    def update_audio(self, audio_path, filename, key, last_audio_folder=None, is_heuristic=False, on_replace_callback=None):
        """Обновляет плеер для нового файла без пересоздания окна"""
        # Обновляем callback при каждом использовании синглтона!
        if on_replace_callback is not None:
            self.on_replace_callback = on_replace_callback
        
        self.stop_audio()
        self.audio_path = audio_path
        self.filename = filename
        self.key = key
        self.is_heuristic = is_heuristic
        if last_audio_folder is not None:
            self.last_audio_folder = last_audio_folder
        
        # Обновляем UI
        self.file_label.setText(self.filename)
        self.load_audio_file(audio_path)
        
        # Обновляем индикатор в главном окне
        if self.parent() and hasattr(self.parent(), 'set_active_audio_key'):
            self.parent().set_active_audio_key(key)
        
        # Включаем управление (так как могло быть выключено через reset_to_no_file)
        self.position_slider.setEnabled(True)
        self.play_pause_btn.setEnabled(True)
        self.replace_btn.setEnabled(True)
        
        # Сбрасываем прогресс
        self.position_slider.setRange(0, int(self.duration_sec * 1000))
        self.position_slider.setValue(0)
        self.play_start_offset = 0
        self.update_time_labels(0)
        
        # Высвечиваем окно если оно было скрыто
        if self.isHidden():
            self.show()
        self.raise_()
        self.activateWindow()

        self.activateWindow()

    def reset_to_no_file(self):
        """Сбрасывает плеер в состояние 'Файл не выбран'."""
        self.stop_audio()
        self.audio_path = None
        self.filename = None
        self.key = None
        self.is_heuristic = False
        self.audio_loaded = False
        
        # Сбрасываем индикатор в главном окне
        if self.parent() and hasattr(self.parent(), 'set_active_audio_key'):
            self.parent().set_active_audio_key(None)

        self.file_label.setText(get_translation(self.current_language, 'no_audio_file'))
        if hasattr(self, 'heuristic_label'):
            self.heuristic_label.setVisible(False)
            
        self.position_slider.setValue(0)
        self.position_slider.setEnabled(False)
        self.play_pause_btn.setEnabled(False)
        self.replace_btn.setEnabled(False)
        self.time_label.setText("00:00 / 00:00")
        
    def toggle_play_pause(self):
        """Переключение между воспроизведением и паузой"""
        # Проверка наличия файла перед воспроизведением
        if not hasattr(self, 'audio_path') or not self.audio_path or not os.path.exists(self.audio_path):
            return
            
        if self.is_playing:
            # Сейчас играет -> ставим на паузу
            pygame.mixer.music.pause()
            self.is_playing = False
            self.is_paused = True
            self.play_pause_btn.setText("▶")
            self.play_pause_btn.setStyleSheet(self.btn_style_base.format(size=28, top=self.play_btn_top_offset))
            self.play_pause_btn.setToolTip(get_translation(self.current_language, 'play_btn'))
        else:
            # Сейчас не играет
            if self.is_paused:
                # Было на паузе -> продолжаем с того же места
                try:
                    pygame.mixer.music.unpause()
                except Exception:
                    # Попытка перезагрузить трек и стартовать
                    try:
                        if hasattr(self, 'audio_path') and self.audio_path and os.path.exists(self.audio_path):
                            pygame.mixer.music.load(self.audio_path)
                            self.audio_loaded = True
                            pygame.mixer.music.play()
                    except Exception as e:
                        print(f"Audio unpause/load error: {e}")
            else:
                # Остановлено или ещё не играло -> запускаем сначала
                self.play_start_offset = 0
                try:
                    if not getattr(self, 'audio_loaded', False):
                        if hasattr(self, 'audio_path') and self.audio_path and os.path.exists(self.audio_path):
                            pygame.mixer.music.load(self.audio_path)
                            self.audio_loaded = True
                    pygame.mixer.music.play()
                except Exception as e:
                    print(f"Audio play error: {e}")
            self.is_playing = True
            self.is_paused = False
            self.play_pause_btn.setText("\u23F8\uFE0E")
            # pause bars size (slightly larger)
            self.play_pause_btn.setStyleSheet(self.btn_style_base.format(size=26, top=self.play_btn_top_offset))
            self.play_pause_btn.setToolTip(get_translation(self.current_language, 'pause_btn'))

    def stop_audio(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.play_pause_btn.setText("▶")
        self.play_pause_btn.setStyleSheet(self.btn_style_base.format(size=28, top=self.play_btn_top_offset))
        self.play_pause_btn.setToolTip(get_translation(self.current_language, 'play_btn'))
        # Перезагружаем трек, чтобы play начал сначала
        try:
            if self.audio_path:
                pygame.mixer.music.load(self.audio_path)
                self.audio_loaded = True
            self.position_slider.setValue(0)
            self.update_time_labels(0)
            self.play_start_offset = 0
        except: pass

    def set_volume(self, value):
        # Pygame volume is 0.0 to 1.0
        vol = value / 100.0
        pygame.mixer.music.set_volume(vol)
        
        # Сохраняем в основной класс и вызываем сохранение настроек
        if self.parent() and hasattr(self.parent(), 'audio_volume'):
            self.parent().audio_volume = value
            # Сохраняем настройки при каждом изменении ползунка (с учетом дебаунса, если бы он был, но тут просто сохранение)
            if hasattr(self.parent(), 'save_settings'):
                self.parent().save_settings()

    def on_slider_pressed(self):
        self.is_slider_dragged = True
        
    def on_slider_released(self):
        # Перемотка
        val_ms = self.position_slider.value()
        start_pos = val_ms / 1000.0
        
        try:
            # Ensure track is loaded before seek-play
            try:
                if not getattr(self, 'audio_loaded', False):
                    if hasattr(self, 'audio_path') and self.audio_path and os.path.exists(self.audio_path):
                        pygame.mixer.music.load(self.audio_path)
                        self.audio_loaded = True
            except Exception:
                pass
            pygame.mixer.music.play(start=start_pos)
            self.play_start_offset = val_ms
            self.is_playing = True
            self.is_paused = False
            self.play_pause_btn.setText("\u23F8\uFE0E")
            self.play_pause_btn.setStyleSheet(self.btn_style_base.format(size=26, top=self.play_btn_top_offset))
            self.play_pause_btn.setToolTip(get_translation(self.current_language, 'pause_btn'))
        except Exception as e:
            print(f"Seek error: {e}")
            
        self.is_slider_dragged = False

    def update_progress(self):
        if self.is_slider_dragged:
            return
            
        if pygame.mixer.music.get_busy():
            # get_pos returns ms played since last play(). 
            current_ms = pygame.mixer.music.get_pos() + self.play_start_offset
            
            self.position_slider.blockSignals(True)
            self.position_slider.setValue(current_ms)
            self.position_slider.blockSignals(False)
            
            self.update_time_labels(current_ms)
        elif self.is_playing:
            # Трек закончился сам — сбрасываем в начало
            self.is_playing = False
            self.is_paused = False
            self.play_start_offset = 0
            self.play_pause_btn.setText("▶")
            self.play_pause_btn.setStyleSheet(self.btn_style_base.format(size=28, top=self.play_btn_top_offset))
            self.play_pause_btn.setToolTip(get_translation(self.current_language, 'play_btn'))
            self.position_slider.blockSignals(True)
            self.position_slider.setValue(0)
            self.position_slider.blockSignals(False)
            self.update_time_labels(0)
            # Перезагружаем трек чтобы повторный play() шёл сначала
            try:
                pygame.mixer.music.load(self.audio_path)
            except: pass
            
    def update_time_labels(self, current_ms):
        def fmt(ms):
            s = int(ms // 1000) % 60
            m = int(ms // 60000)
            return f"{m:02}:{s:02}"
        
        dur_ms = int(self.duration_sec * 1000)
        self.time_label.setText(f"{fmt(current_ms)} / {fmt(dur_ms)}")

    def replace_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            get_translation(self.current_language, 'select_new_audio_title'),
            self.last_audio_folder or "",
            get_translation(self.current_language, 'audio_file_filter')
        )
        
        if file_path:
            self.new_file_path = file_path
            new_name = os.path.basename(file_path)
            self.filename = new_name
            
            # Обновляем текст заголовка в плеере
            self.file_label.setText(new_name)
            
            # 1. Сначала полностью освобождаем предыдущий файл в Pygame
            try:
                pygame.mixer.music.stop()
                if hasattr(pygame.mixer.music, 'unload'):
                    pygame.mixer.music.unload()
            except: pass

            # 2. Вызываем внешнюю функцию для "тихой" замены в менеджере и обновления превью
            # ВНИМАНИЕ: handle_audio_replacement внутри себя вызовет self.update_audio(file_path, ...)
            # поэтому локальное обновление здесь может быть избыточным, но мы оставляем 
            # безопасный вариант.
            if self.on_replace_callback and self.key:
                self.on_replace_callback(self.key, file_path)
            else:
                # Показываем ошибку пользователю
                error_msg = "⚠️ Cannot replace audio:\n"
                if not self.key:
                    error_msg += "• No audio file is currently loaded\n• Open an audio file from the mission first"
                if not self.on_replace_callback:
                    error_msg += "• Audio player callback is not initialized\n• Try closing and reopening the audio player"
                
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, get_translation(self.current_language, 'error'), error_msg)
            
            # 3. Обновляем локальные параметры плеера (на случай если callback не обновил)
            try:
                self.audio_path = file_path # Теперь играем новый файл, если нажмут Play
                
                # Сбрасываем слайдер и время
                self.position_slider.setValue(0)
                self.play_start_offset = 0
                self.is_playing = False
                self.is_paused = False
                # Обновляем прогресс слайдера
                self.position_slider.setRange(0, int(self.duration_sec * 1000))
                self.update_time_labels(0)
            except Exception as e:
                print(f"Error updating player after replace: {e}")

    def closeEvent(self, event):
        try:
            if hasattr(pygame.mixer.music, 'stop'):
                pygame.mixer.music.stop()
            if hasattr(pygame.mixer.music, 'unload'):
                pygame.mixer.music.unload()
        except:
            pass
        try:
            self.audio_loaded = False
        except Exception:
            pass
        
        # Сбрасываем индикатор в главном окне
        if self.parent() and hasattr(self.parent(), 'set_active_audio_key'):
            self.parent().set_active_audio_key(None)

        super().closeEvent(event)


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
        self.fields_y_start = 125
        self.fields_spacing = 330 # Расстояние между началом 1-го и началом 2-го поля
        self.fields_height = 280
        
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
        self.context_lang_1 = "RU"
        
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

        # Выпадающий список языков
        self.lang_label = QLabel(get_translation(self.lang, 'context_select_lang'), self)
        self.lang_label.setStyleSheet("color: #bbbbbb; font-size: 11px;")
        
        self.lang_combo = QComboBox(self)
        from PyQt5.QtWidgets import QListView
        self.lang_combo.setView(QListView())
        self.lang_combo.setMaxVisibleItems(15)
        # Сортируем языки: RU, EN, затем остальные по алфавиту
        all_langs = sorted(AI_CONTEXTS.keys())
        if 'EN' in all_langs: all_langs.remove('EN')
        if 'RU' in all_langs: all_langs.remove('RU')
        final_langs = ['EN', 'RU'] + all_langs
        self.lang_combo.addItems(final_langs)
        self.lang_combo.setCurrentText('RU')
        self.setup_combo_style(self.lang_combo)
        self.lang_combo.currentTextChanged.connect(self.on_lang_template_changed)
        
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
            
        self.btn_default.hide() # Скрываем кнопку, но оставляем в коде
            
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

    def setup_combo_style(self, combo):
        # Настройка чтобы список открывался ТОЛЬКО вниз
        combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # Это заставляет Qt использовать классический popup вместо "центрованного" списка на некоторых системах
        combo.setStyleSheet("""
            QComboBox {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #777;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
                combobox-popup: 0;
            }
            QComboBox:focus {
                border: 1px solid #ff9900;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ff9900;
                margin-right: 5px;
            }
            /* Стилизация выпадающего списка */
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: #ffffff;
                selection-background-color: #ff9900;
                selection-color: #000000;
                border: 1px solid #ff9900;
                outline: none;
            }
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
        
        # Позиционирование выпадающего списка (справа сверху над полем)
        combo_w = 120
        combo_x = mx + fw - combo_w
        combo_y = y1 - 29 # На 29 пикселей выше начала текстового поля
        self.lang_combo.setGeometry(combo_x, combo_y, combo_w, 24)
        
        self.lang_label.adjustSize()
        self.lang_label.move(combo_x - self.lang_label.width() - 10, combo_y + 4)

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
        
        # Устанавливаем сохраненный язык в выпадающем списке
        self.lang_combo.blockSignals(True)
        self.lang_combo.setCurrentText(self.context_lang_1)
        self.lang_combo.blockSignals(False)
        
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
        # Сбрасываем комбобокс на RU, так как дефолт совпадает с RU (для русского интерфейса)
        self.lang_combo.blockSignals(True)
        self.lang_combo.setCurrentText('RU')
        self.lang_combo.blockSignals(False)

    def on_lang_template_changed(self, lang):
        if lang in AI_CONTEXTS:
            self.edit_1.setPlainText(AI_CONTEXTS[lang])

    def swap_contexts(self):
        t1 = self.edit_1.toPlainText()
        t2 = self.edit_2.toPlainText()
        self.edit_1.setPlainText(t2)
        self.edit_2.setPlainText(t1)

    def save_field(self, field_id):
        if field_id == 1:
            self.context_1 = self.edit_1.toPlainText()
            self.context_lang_1 = self.lang_combo.currentText()
            self.changed_1 = False
            self.warn_1.hide()
        else:
            self.context_2 = self.edit_2.toPlainText()
            self.changed_2 = False
            self.warn_2.hide()
        
        # Вызываем метод сохранения в родителе
        if self.parent() and hasattr(self.parent(), 'save_ai_context_settings'):
            self.parent().save_ai_context_settings(
                self.context_1, 
                self.context_2, 
                self.context_lang_1 if field_id == 1 else None
            )


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
        self.text_browser.setHtml(content)
        
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


class DeleteConfirmDialog(CustomDialog):
    """Диалог подтверждения удаления локали с красной кнопкой ДА"""
    def __init__(self, locale_name, current_language, parent=None):
        super().__init__(parent)
        self.current_language = current_language
        self.locale_name = locale_name

        self.setWindowTitle(get_translation(self.current_language, 'delete_confirm_title'))
        self.setFixedSize(400, 180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        # Формируем сообщение (разбиваем на части для оранжевого выделения без HTML)
        full_msg = get_translation(self.current_language, 'delete_confirm_msg')
        parts = full_msg.split('{locale}')
        
        msg_container = QWidget()
        msg_container.setStyleSheet("background: transparent; border: none;")
        msg_h_layout = QHBoxLayout(msg_container)
        msg_h_layout.setContentsMargins(0, 0, 0, 0)
        msg_h_layout.setSpacing(0) # Убираем зазоры, чтобы текст выглядел единым
        msg_h_layout.addStretch()

        # Текст ДО названия
        if parts[0]:
            label_before = QLabel(parts[0])
            label_before.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px; background: transparent;")
            msg_h_layout.addWidget(label_before)
            
        # Само НАЗВАНИЕ (Оранжевое)
        label_name = QLabel(self.locale_name)
        label_name.setStyleSheet("color: #ff9900; font-weight: bold; font-size: 13px; background: transparent;")
        msg_h_layout.addWidget(label_name)
        
        # Текст ПОСЛЕ названия
        if len(parts) > 1 and parts[1]:
            label_after = QLabel(parts[1])
            label_after.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px; background: transparent;")
            msg_h_layout.addWidget(label_after)
            
        msg_h_layout.addStretch()
        layout.addWidget(msg_container)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        # Красная кнопка ДА
        self.yes_btn = QPushButton(get_translation(self.current_language, 'yes_btn'))
        self.yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #e53935;
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #c62828;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.yes_btn.clicked.connect(self.accept)

        # Белая кнопка Отмена
        self.no_btn = QPushButton(get_translation(self.current_language, 'cancel_btn'))
        self.no_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                padding: 10px 20px;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #a3a3a3;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        self.no_btn.clicked.connect(self.reject)

        # Добавляем кнопки в ряд по центру
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.yes_btn)
        row.addWidget(self.no_btn)
        row.addStretch()
        btn_layout.addLayout(row)

        layout.addLayout(btn_layout)


class FilesWindow(CustomDialog):
    """Окно менеджера файлов"""
    def __init__(self, current_language, parent=None):
        super().__init__(parent)
        self.current_language = current_language
        self.setWindowTitle(get_translation(current_language, 'files_window_title'))
        self.setFixedSize(800, 1100)
        
        # Основной layout
        layout = QVBoxLayout(self)
        # Устанавливаем небольшие отступы, чтобы рамка CustomDialog не перекрывалась
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        # Верхняя панель (Заголовок + Кнопка закрытия)
        top_bar = QWidget()
        # Reduced top bar height to lift content row closer to the top
        top_bar.setFixedHeight(36)
        top_bar.setStyleSheet("background-color: #3d4256; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        # Заголовок
        self.title_label = QLabel(self.windowTitle())
        self.title_label.setStyleSheet("color: #ff9900; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents) # Пропускает клики (для перетаскивания за бар)
        top_layout.addWidget(self.title_label)
        
        top_layout.addStretch()
        
        # Кнопка закрытия (крестик) - внутри top_bar для надежности
        self.close_btn = QPushButton("✕", top_bar)
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaaaaa;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff9900;
            }
        """)
        # Ширина окна 800, отступы лейаута 2. Ширина top_bar = 796.
        # Ставим 15px от правого края top_bar (796 - 30 - 15 = 751)
        # И 10px сверху (отцентрировано в высоте 50: (50-30)/2 = 10)
        self.close_btn.move(751, 10)
        
        layout.addWidget(top_bar)
        
        # Основная область контента
        content_area = QWidget()
        content_area.setStyleSheet("background-color: transparent; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Placeholder для контента (Кастомная отрисовка для сохранения длины штрихов)
        from PyQt5.QtGui import QPen
        class DashedPlaceholderLabel(QLabel):
            def paintEvent(self, event):
                super().paintEvent(event)
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing)
                pen = QPen(QColor("#8f8f8f"), 1, Qt.DashLine)
                # Настраиваем паттерн: 4 пикселя штрих, 4 пикселя пробел (можно варьировать)
                pen.setDashPattern([6, 4]) 
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                # Используем QRectF и смещение 0.5 для четкой отрисовки в 1 пиксель без размытия
                rect_f = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
                painter.drawRoundedRect(rect_f, 10, 10)

        self.placeholder_label = DashedPlaceholderLabel(get_translation(current_language, 'files_window_placeholder'))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #666; font-size: 14px; border: none; background: transparent;")
        self.placeholder_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        content_layout.addWidget(self.placeholder_label)
        
        layout.addWidget(content_area)
        
        # Поднимаем кнопку закрытия на самый верхний слой
        self.close_btn.raise_()

    def retranslate_ui(self, current_language):
        """Обновляет переводы интерфейса"""
        self.current_language = current_language
        self.setWindowTitle(get_translation(self.current_language, 'files_window_title'))
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.windowTitle())
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.setText(get_translation(self.current_language, 'files_window_placeholder'))


class SettingsWindow(CustomDialog):
    """Окно Настроек (минималистичный вариант)"""
    def __init__(self, current_language, parent=None):
        super().__init__(parent)
        self.current_language = current_language
        self.parent_window = parent
        self.setWindowTitle(get_translation(self.current_language, 'settings_window_title'))
        # Увеличиваем высоту в 2 раза, делаем окно растягиваемым, но с минимальным размером
        self.setMinimumSize(520, 720)
        self.resize(520, 720)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        # Top bar
        top_bar = QWidget()
        top_bar.setFixedHeight(36)
        top_bar.setStyleSheet("background-color: #3d4256; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)

        self.title_label = QLabel(self.windowTitle())
        self.title_label.setStyleSheet("color: #ff9900; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()

        # place close button as child of dialog to ensure exact distance from window edges
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #aaaaaa; border: none; font-size: 18px; font-weight: bold; }
            QPushButton:hover { color: #ff9900; }
        """)
        self.close_btn.raise_()


        layout.addWidget(top_bar)

        # === Область прокрутки (Scroll Area) ===
        from widgets import CustomScrollBar
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBar(CustomScrollBar())
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        # Content widget inside scroll area
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(scroll_content)
        # верхний отступ увеличен до 10px, боковые 15px для линий
        content_layout.setContentsMargins(15, 10, 15, 15)
        content_layout.setSpacing(12)
        content_layout.setAlignment(Qt.AlignTop)

        # === Ряд 1: Цвет фона 1 ===
        row_even = QWidget()
        row_even_layout = QHBoxLayout(row_even)
        row_even_layout.setContentsMargins(5, 0, 5, 0)
        row_even_layout.setSpacing(10)
        
        self.theme_bg_even_label = QLabel(get_translation(self.current_language, 'theme_bg_even_label'))
        self.theme_bg_even_label.setStyleSheet('color: #ddd; background: transparent;')
        row_even_layout.addWidget(self.theme_bg_even_label)
        row_even_layout.addStretch()
        
        self.theme_bg_even_preview = QLabel()
        self.theme_bg_even_preview.setFixedSize(22, 22)
        self.theme_bg_even_preview.setCursor(Qt.PointingHandCursor)
        self.theme_bg_even_preview.mousePressEvent = lambda e: self.open_color_dialog('even')
        row_even_layout.addWidget(self.theme_bg_even_preview)
        
        row_even.setFixedHeight(28)
        content_layout.addWidget(row_even, 0, Qt.AlignTop)

        # === Ряд 2: Цвет фона 2 ===
        row_odd = QWidget()
        row_odd_layout = QHBoxLayout(row_odd)
        row_odd_layout.setContentsMargins(5, 0, 5, 0)
        row_odd_layout.setSpacing(10)
        
        self.theme_bg_odd_label = QLabel(get_translation(self.current_language, 'theme_bg_odd_label'))
        self.theme_bg_odd_label.setStyleSheet('color: #ddd; background: transparent;')
        row_odd_layout.addWidget(self.theme_bg_odd_label)
        row_odd_layout.addStretch()
        
        self.theme_bg_odd_preview = QLabel()
        self.theme_bg_odd_preview.setFixedSize(22, 22)
        self.theme_bg_odd_preview.setCursor(Qt.PointingHandCursor)
        self.theme_bg_odd_preview.mousePressEvent = lambda e: self.open_color_dialog('odd')
        row_odd_layout.addWidget(self.theme_bg_odd_preview)
        
        row_odd.setFixedHeight(28)
        content_layout.addWidget(row_odd, 0, Qt.AlignTop)

        # --- Разделитель между фоном и шрифтами ---
        line_fonts = QFrame()
        line_fonts.setFrameShape(QFrame.HLine)
        line_fonts.setFrameShadow(QFrame.Plain)
        line_fonts.setFixedHeight(1)
        line_fonts.setStyleSheet("background-color: #555555; border: none;")
        content_layout.addWidget(line_fonts)

        # === Ряд: Цвет изменённого шрифта ===
        row_text_mod = QWidget()
        row_text_mod_layout = QHBoxLayout(row_text_mod)
        row_text_mod_layout.setContentsMargins(5, 0, 5, 0)
        row_text_mod_layout.setSpacing(10)
        
        mod_font_label = 'Цвет изменённого текста' if self.current_language == 'ru' else 'Modified text color'
        self.theme_text_modified_label = QLabel(mod_font_label)
        self.theme_text_modified_label.setStyleSheet('color: #ddd; background: transparent;')
        row_text_mod_layout.addWidget(self.theme_text_modified_label)
        row_text_mod_layout.addStretch()
        
        self.theme_text_modified_preview = QLabel()
        self.theme_text_modified_preview.setFixedSize(22, 22)
        self.theme_text_modified_preview.setCursor(Qt.PointingHandCursor)
        self.theme_text_modified_preview.mousePressEvent = lambda e: self.open_color_dialog('text_modified')
        row_text_mod_layout.addWidget(self.theme_text_modified_preview)
        
        row_text_mod.setFixedHeight(28)
        content_layout.addWidget(row_text_mod, 0, Qt.AlignTop)

        # === Ряд: Цвет сохранённого шрифта ===
        row_text_saved = QWidget()
        row_text_saved_layout = QHBoxLayout(row_text_saved)
        row_text_saved_layout.setContentsMargins(5, 0, 5, 0)
        row_text_saved_layout.setSpacing(10)
        
        saved_font_label = 'Цвет сохранённого текста' if self.current_language == 'ru' else 'Saved text color'
        self.theme_text_saved_label = QLabel(saved_font_label)
        self.theme_text_saved_label.setStyleSheet('color: #ddd; background: transparent;')
        row_text_saved_layout.addWidget(self.theme_text_saved_label)
        row_text_saved_layout.addStretch()
        
        self.theme_text_saved_preview = QLabel()
        self.theme_text_saved_preview.setFixedSize(22, 22)
        self.theme_text_saved_preview.setCursor(Qt.PointingHandCursor)
        self.theme_text_saved_preview.mousePressEvent = lambda e: self.open_color_dialog('text_saved')
        row_text_saved_layout.addWidget(self.theme_text_saved_preview)
        
        row_text_saved.setFixedHeight(28)
        content_layout.addWidget(row_text_saved, 0, Qt.AlignTop)

        # === Ряд: Шрифт предпросмотра ===
        row_font = QWidget()
        row_font_layout = QHBoxLayout(row_font)
        row_font_layout.setContentsMargins(5, 0, 5, 0)
        row_font_layout.setSpacing(10)
        
        font_label_text = get_translation(self.current_language, 'preview_font_family_label')
        self.preview_font_label = QLabel(font_label_text)
        self.preview_font_label.setStyleSheet('color: #ddd; background: transparent;')
        row_font_layout.addWidget(self.preview_font_label)
        row_font_layout.addStretch()
        
        # Общий стиль для комбобоксов
        combo_style = """
            QComboBox {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #ff9900;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #ffffff;
                selection-background-color: #ff9900;
                selection-color: #000000;
                border: 1px solid #555;
            }
        """
        
        # Выбор семейства шрифта
        self.preview_font_family_combo = QComboBox()
        self.preview_font_family_combo.addItems(['Consolas', 'Courier New', 'Lucida Console', 'Monospace', 'Arial', 'Roboto', 'Verdana'])
        self.preview_font_family_combo.setFixedWidth(130)
        self.preview_font_family_combo.setStyleSheet(combo_style)
        row_font_layout.addWidget(self.preview_font_family_combo)
        
        # Выбор размера шрифта
        self.preview_font_size_combo = QComboBox()
        self.preview_font_size_combo.addItems([str(x) for x in [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24]])
        self.preview_font_size_combo.setFixedWidth(65)
        self.preview_font_size_combo.setStyleSheet(combo_style)
        row_font_layout.addWidget(self.preview_font_size_combo)
        
        row_font.setFixedHeight(28)
        content_layout.addWidget(row_font, 0, Qt.AlignTop)

        # --- Разделитель перед остальными настройками ---
        line0 = QFrame()
        line0.setFrameShape(QFrame.HLine)
        line0.setFrameShadow(QFrame.Plain)
        line0.setFixedHeight(1)
        line0.setStyleSheet("background-color: #555555; border: none;")
        content_layout.addWidget(line0)

        # Compact row: Toggle + label + color preview (clickable)
        row = QWidget()
        row_layout = QHBoxLayout(row)
        # Боковой отступ 5px, чтобы текст был в 20px от края окна (15+5=20)
        row_layout.setContentsMargins(5, 0, 5, 0)
        row_layout.setSpacing(10)

        self.highlight_toggle = ToggleSwitch()
        # connect for debug logging when user toggles
        try:
            self.highlight_toggle.toggled.connect(self._on_highlight_toggled)
        except Exception:
            pass
        row_layout.addWidget(self.highlight_toggle)

        self.highlight_label = QLabel(get_translation(self.current_language, 'highlight_empty_label'))
        self.highlight_label.setStyleSheet('color: #ddd; background: transparent;')
        row_layout.addWidget(self.highlight_label)

        # color preview square (click to open color dialog)
        row_layout.addStretch()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(22, 22)
        self.color_preview.setCursor(Qt.PointingHandCursor)
        self.color_preview.setToolTip(get_translation(self.current_language, 'highlight_color_label'))
        self.color_preview.mousePressEvent = lambda e: self.open_color_dialog()
        row_layout.addWidget(self.color_preview)

        # Ограничим высоту строки настроек, чтобы она не центрировалась вертикально
        row.setFixedHeight(28)
        content_layout.addWidget(row, 0, Qt.AlignTop)

        # --- Разделитель после первой строки ---
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Plain)
        line1.setFixedHeight(1)
        line1.setStyleSheet("background-color: #555555; border: none;")
        content_layout.addWidget(line1)

        # === Второй ряд: Включить логи ===
        row2 = QWidget()
        row2_layout = QHBoxLayout(row2)
        # Боковой отступ 5px, чтобы текст был в 20px от края окна (15+5=20)
        row2_layout.setContentsMargins(5, 0, 5, 0)
        row2_layout.setSpacing(10)

        self.enable_logs_toggle = ToggleSwitch()
        row2_layout.addWidget(self.enable_logs_toggle)

        self.enable_logs_label = QLabel(get_translation(self.current_language, 'enable_logs_label'))
        self.enable_logs_label.setStyleSheet('color: #ddd; background: transparent;')
        row2_layout.addWidget(self.enable_logs_label)
        
        # Кнопка "Очистить логи" (как кликабельный QLabel для кастомного стиля)
        clear_logs_text = "Очистить логи" if self.current_language == 'ru' else "Clear logs"
        self.clear_logs_label = QLabel(f"<span style='color: white;'>|</span> <span style='color: white;'>{clear_logs_text}</span> <span style='color: white;'>|</span>")
        self.clear_logs_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                padding: 2px 5px;
                font-size: 11px;
            }
        """)
        self.clear_logs_label.setCursor(Qt.PointingHandCursor)
        self.clear_logs_label._hovered = False
        
        # Сохраняю оригинальный текст для восстановления
        self.clear_logs_label._original_text = f"<span style='color: white;'>|</span> <span style='color: white;'>{clear_logs_text}</span> <span style='color: white;'>|</span>"
        self.clear_logs_label._hovered_text = f"<span style='color: white;'>|</span> <span style='color: #ff9900;'>{clear_logs_text}</span> <span style='color: white;'>|</span>"
        
        # Переопределяю события мыши
        def on_enter(event):
            self.clear_logs_label._hovered = True
            self.clear_logs_label.setText(self.clear_logs_label._hovered_text)
        
        def on_leave(event):
            self.clear_logs_label._hovered = False
            self.clear_logs_label.setText(self.clear_logs_label._original_text)
        
        def on_click(event):
            if event.button() == Qt.LeftButton:
                self.clear_logs()
        
        self.clear_logs_label.enterEvent = on_enter
        self.clear_logs_label.leaveEvent = on_leave
        self.clear_logs_label.mousePressEvent = on_click
        
        row2_layout.addWidget(self.clear_logs_label)

        row2.setFixedHeight(28)
        row2_layout.addStretch()
        content_layout.addWidget(row2, 0, Qt.AlignTop)

        # --- Разделитель после второй строки ---
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Plain)
        line2.setFixedHeight(1)
        line2.setStyleSheet("background-color: #555555; border: none;")
        content_layout.addWidget(line2)

        # === Ряд 3: Reference locale ===
        row3 = QWidget()
        row3_layout = QHBoxLayout(row3)
        row3_layout.setContentsMargins(5, 0, 5, 0)
        row3_layout.setSpacing(10)

        ref_label_text = get_translation(self.current_language, 'reference_locale_label')
        self.reference_locale_label = QLabel(ref_label_text)
        self.reference_locale_label.setStyleSheet('color: #ddd; background: transparent;')
        row3_layout.addWidget(self.reference_locale_label)

        row3_layout.addStretch()

        self.reference_locale_combo = QComboBox()
        standard_locales = ['DEFAULT', 'EN', 'RU', 'FR', 'DE', 'CN', 'CS', 'ES', 'IT', 'JP', 'KO']
        self.reference_locale_combo.addItems(standard_locales)
        self.reference_locale_combo.setFixedWidth(120)
        self.reference_locale_combo.setStyleSheet(combo_style)
        row3_layout.addWidget(self.reference_locale_combo)

        row3.setFixedHeight(28)
        content_layout.addWidget(row3, 0, Qt.AlignTop)

        # --- Разделитель после третьей строки ---
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Plain)
        line3.setFixedHeight(1)
        line3.setStyleSheet("background-color: #555555; border: none;")
        content_layout.addWidget(line3)

        # Заполняем пустое пространство в скролле, чтобы настройки были сверху
        content_layout.addStretch()
        
        self.scroll_area.setWidget(scroll_content)
        layout.addWidget(self.scroll_area)

        # === Нижняя панель с кнопками (Всегда видна) ===
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(60)
        # Используем чуть более темный фон для отделения кнопок от контента
        bottom_bar.setStyleSheet("background-color: #2b2b2b; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
        bottom_layout = QVBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 0, 20, 0)
        
        action_row = QHBoxLayout()

        # Reset button (left-aligned) — same size/radius as Cancel, transparent background, thin white border
        # Label: Russian and English explicit variants
        if getattr(self, 'current_language', 'ru') == 'ru':
            reset_label = 'Сбросить настройки'
        else:
            reset_label = 'Reset settings'
        self.reset_btn = QPushButton(reset_label)
        self.reset_btn.setFixedHeight(32)
        # adjust width to fit russian label
        fm = self.reset_btn.fontMetrics()
        text_w = fm.horizontalAdvance(reset_label)
        btn_w = max(120, text_w + 36)
        self.reset_btn.setMinimumWidth(btn_w)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #ffffff;
                border: 1px solid #ffffff;
                border-radius: {32 // 2}px;
                padding: 0px 5px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{ border-color: #ff9900; }}
            QPushButton:pressed {{ background-color: rgba(255,255,255,0.04); }}
        """)
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        action_row.addWidget(self.reset_btn)

        action_row.addStretch()

        # Use same visual parameters as Save/Back buttons in AIContextWindow
        save_text = get_translation(self.current_language, 'save_btn')
        # strip any leading disk icon from translation for this dialog
        save_text = save_text.replace('💾 ', '').replace('💾', '').strip()

        self.cancel_btn = QPushButton(get_translation(self.current_language, 'cancel_btn'))
        self.cancel_btn.setFixedHeight(32)
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: #000000;
                border-radius: {32 // 2}px;
                padding: 0px 5px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #e0e0e0; }}
            QPushButton:pressed {{ background-color: #d0d0d0; }}
        """)
        self.cancel_btn.clicked.connect(self.cancel_and_restore)
        action_row.addWidget(self.cancel_btn)

        self.save_btn = QPushButton(save_text)
        self.save_btn.setFixedHeight(32)
        self.save_btn.setFixedWidth(120)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ff9900;
                color: #000000;
                border-radius: {32 // 2}px;
                padding: 0px 5px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #e68a00; }}
            QPushButton:pressed {{ background-color: #cc7a00; }}
        """)
        self.save_btn.clicked.connect(self.save_and_close)
        action_row.addWidget(self.save_btn)

        bottom_layout.addLayout(action_row)
        layout.addWidget(bottom_bar)

        # Initialize values from parent (will be reloaded on showEvent)
        try:
            self._log_debug(f"SettingsWindow.__init__: Creating dialog")
            self.load_values_from_parent()
            self._log_debug(f"SettingsWindow.__init__: Initial values loaded")
        except Exception as e:
            self._log_debug(f"SettingsWindow.__init__: ERROR loading initial values: {e}")

    def load_values_from_parent(self):
        if self.parent_window:
            val = getattr(self.parent_window, 'highlight_empty_fields', True)
            col = getattr(self.parent_window, 'highlight_empty_color', '#555555')
            logs = getattr(self.parent_window, 'debug_logs_enabled', True)
            self.highlight_toggle.setChecked(val)
            self.enable_logs_toggle.setChecked(logs)
            self.color_preview.setStyleSheet(f'background-color: {col}; border: 1px solid #777;')
            
            # Загружаем цвета темы (fallback — встроенные значения)
            c_even = getattr(self.parent_window, 'theme_bg_even', '#393939')
            c_odd = getattr(self.parent_window, 'theme_bg_odd', '#2f2f2f')
            self.theme_bg_even_preview.setStyleSheet(f'background-color: {c_even}; border: 1px solid #777;')
            self.theme_bg_odd_preview.setStyleSheet(f'background-color: {c_odd}; border: 1px solid #777;')

            # Загружаем шрифт (fallback — встроенные значения)
            c_mod = getattr(self.parent_window, 'theme_text_modified', '#ff6666')
            c_saved = getattr(self.parent_window, 'theme_text_saved', '#2ecc71')
            self.theme_text_modified_preview.setStyleSheet(f'background-color: {c_mod}; border: 1px solid #777;')
            self.theme_text_saved_preview.setStyleSheet(f'background-color: {c_saved}; border: 1px solid #777;')

            # Загружаем reference locale
            ref_locale = getattr(self.parent_window, 'reference_locale', 'DEFAULT')
            idx = self.reference_locale_combo.findText(ref_locale)
            if idx >= 0:
                self.reference_locale_combo.setCurrentIndex(idx)
            else:
                self.reference_locale_combo.setCurrentText(ref_locale)

            # Загружаем шрифт предпросмотра
            f_family = getattr(self.parent_window, 'preview_font_family', 'Consolas')
            f_size = str(getattr(self.parent_window, 'preview_font_size', 10))
            
            idx_f = self.preview_font_family_combo.findText(f_family)
            if idx_f >= 0: self.preview_font_family_combo.setCurrentIndex(idx_f)
            
            idx_s = self.preview_font_size_combo.findText(f_size)
            if idx_s >= 0: self.preview_font_size_combo.setCurrentIndex(idx_s)

            # save snapshot of parent's current values so Cancel can restore them
            try:
                self._orig_parent_values = {
                    'highlight_empty_fields': bool(getattr(self.parent_window, 'highlight_empty_fields', True)),
                    'highlight_empty_color': str(getattr(self.parent_window, 'highlight_empty_color', '#555555')),
                    'debug_logs_enabled': bool(getattr(self.parent_window, 'debug_logs_enabled', True)),
                    'theme_bg_even': str(getattr(self.parent_window, 'theme_bg_even', '#393939')),
                    'theme_bg_odd': str(getattr(self.parent_window, 'theme_bg_odd', '#2f2f2f')),
                    'theme_text_modified': str(getattr(self.parent_window, 'theme_text_modified', '#ff6666')),
                    'theme_text_saved': str(getattr(self.parent_window, 'theme_text_saved', '#2ecc71')),
                    'reference_locale': str(getattr(self.parent_window, 'reference_locale', 'DEFAULT')),
                    'preview_font_family': str(getattr(self.parent_window, 'preview_font_family', 'Consolas')),
                    'preview_font_size': int(getattr(self.parent_window, 'preview_font_size', 10))
                }
            except Exception:
                self._orig_parent_values = None
        # log loaded values
        try:
            if self.parent_window:
                v_h = getattr(self.parent_window, 'highlight_empty_fields', True)
                v_c = getattr(self.parent_window, 'highlight_empty_color', '#555555')
                v_l = getattr(self.parent_window, 'debug_logs_enabled', True)
                self._log_debug(f"load_values_from_parent: LOADED: highlight={v_h}, col={v_c}, logs={v_l} || SNAPSHOT: {self._orig_parent_values}")
        except Exception as e:
            self._log_debug(f"load_values_from_parent: ERROR logging: {e}")

    def reset_to_defaults(self):
        """Сбрасывает все настройки этого окна к значениям по умолчанию (не сохраняет в parent до Save)."""
        try:
            # Defaults: highlight enabled, color #555555, logs enabled
            # Block signals to avoid emitting toggled and triggering any external handlers
            try:
                self.highlight_toggle.blockSignals(True)
                self.enable_logs_toggle.blockSignals(True)
            except Exception:
                pass
            try:
                self.highlight_toggle.setChecked(True)
                self.enable_logs_toggle.setChecked(True)
            finally:
                try:
                    self.highlight_toggle.blockSignals(False)
                    self.enable_logs_toggle.blockSignals(False)
                except Exception:
                    pass
            # Update color preview (no signals expected)
            self.color_preview.setStyleSheet('background-color: #434343; border: 1px solid #777;')
            self.theme_bg_even_preview.setStyleSheet('background-color: #393939; border: 1px solid #777;')
            self.theme_bg_odd_preview.setStyleSheet('background-color: #2f2f2f; border: 1px solid #777;')
            self.theme_text_modified_preview.setStyleSheet('background-color: #ff6666; border: 1px solid #777;')
            self.theme_text_saved_preview.setStyleSheet('background-color: #2ecc71; border: 1px solid #777;')
            # Reset reference locale to DEFAULT
            idx = self.reference_locale_combo.findText('DEFAULT')
            if idx >= 0:
                self.reference_locale_combo.setCurrentIndex(idx)
            
            # Reset preview font to Consolas 10
            idx_f = self.preview_font_family_combo.findText('Consolas')
            if idx_f >= 0: self.preview_font_family_combo.setCurrentIndex(idx_f)
            idx_s = self.preview_font_size_combo.findText('10')
            if idx_s >= 0: self.preview_font_size_combo.setCurrentIndex(idx_s)
            try:
                self._log_debug('reset_to_defaults: applied defaults in dialog')
            except Exception:
                pass
        except Exception:
            pass

    def clear_logs(self):
        """Очищает все файлы логов."""
        try:
            from error_logger import ErrorLogger
            import os
            
            log_files = [
                'translation_tool_errors.log',
                'translation_tool_audio_changes.log',
                'settings_debug.log',
            ]
            
            cleared_count = 0
            for log_file in log_files:
                try:
                    if os.path.exists(log_file):
                        # Очищаем содержимое файла
                        with open(log_file, 'w', encoding='utf-8') as f:
                            f.write('')
                        cleared_count += 1
                except Exception as e:
                    pass
            
            # Показываем сообщение об успехе
            from PyQt5.QtWidgets import QMessageBox
            msg = f"✓ Логи очищены ({cleared_count} файлов)" if cleared_count > 0 else "✓ Нет файлов логов для очистки"
            if self.current_language != 'ru':
                msg = f"✓ Logs cleared ({cleared_count} files)" if cleared_count > 0 else "✓ No log files to clear"
            
            QMessageBox.information(self, "Success", msg)
        except Exception:
            pass

    def open_color_dialog(self, target='highlight'):
        from PyQt5.QtWidgets import QColorDialog
        
        if target == 'even':
            initial = self.theme_bg_even_preview.styleSheet()
        elif target == 'odd':
            initial = self.theme_bg_odd_preview.styleSheet()
        elif target == 'text_modified':
            initial = self.theme_text_modified_preview.styleSheet()
        elif target == 'text_saved':
            initial = self.theme_text_saved_preview.styleSheet()
        else:
            initial = self.color_preview.styleSheet()

        # extract color from stylesheet if present
        import re
        m = re.search(r'background-color:\s*([^;]+);', initial)
        init_col = m.group(1).strip() if m else '#555555'
        qc = QColorDialog(self)
        qc.setCurrentColor(QColor(init_col))
        if qc.exec_():
            c = qc.currentColor().name()
            if target == 'even':
                self.theme_bg_even_preview.setStyleSheet(f'background-color: {c}; border: 1px solid #777;')
            elif target == 'odd':
                self.theme_bg_odd_preview.setStyleSheet(f'background-color: {c}; border: 1px solid #777;')
            elif target == 'text_modified':
                self.theme_text_modified_preview.setStyleSheet(f'background-color: {c}; border: 1px solid #777;')
            elif target == 'text_saved':
                self.theme_text_saved_preview.setStyleSheet(f'background-color: {c}; border: 1px solid #777;')
            else:
                self.color_preview.setStyleSheet(f'background-color: {c}; border: 1px solid #777;')
            try:
                self._log_debug(f'color selected for {target}: {c}')
            except Exception:
                pass

    def save_and_close(self):
        # Apply to parent and save settings
        if self.parent_window:
            self.parent_window.highlight_empty_fields = self.highlight_toggle.isChecked()
            self.parent_window.debug_logs_enabled = self.enable_logs_toggle.isChecked()
            # extract color from preview stylesheet
            import re
            ss = self.color_preview.styleSheet()
            m = re.search(r'background-color:\s*([^;]+);', ss)
            c = m.group(1).strip() if m else '#555555'
            self.parent_window.highlight_empty_color = c
            
            # extract theme colors
            import re
            m_even = re.search(r'background-color:\s*([^;]+);', self.theme_bg_even_preview.styleSheet())
            self.parent_window.theme_bg_even = m_even.group(1).strip() if m_even else '#505050'
            
            m_odd = re.search(r'background-color:\s*([^;]+);', self.theme_bg_odd_preview.styleSheet())
            self.parent_window.theme_bg_odd = m_odd.group(1).strip() if m_odd else '#4a4a4a'

            m_mod = re.search(r'background-color:\s*([^;]+);', self.theme_text_modified_preview.styleSheet())
            self.parent_window.theme_text_modified = m_mod.group(1).strip() if m_mod else '#ff6666'
            
            m_saved = re.search(r'background-color:\s*([^;]+);', self.theme_text_saved_preview.styleSheet())
            self.parent_window.theme_text_saved = m_saved.group(1).strip() if m_saved else '#2ecc71'

            # Save font settings
            self.parent_window.preview_font_family = self.preview_font_family_combo.currentText()
            try:
                self.parent_window.preview_font_size = int(self.preview_font_size_combo.currentText())
            except:
                self.parent_window.preview_font_size = 10
            
            # Apply font changes
            if hasattr(self.parent_window, 'apply_preview_font_settings'):
                self.parent_window.apply_preview_font_settings()

            # Save reference locale and reload reference data if changed
            new_ref_locale = self.reference_locale_combo.currentText()
            old_ref_locale = getattr(self.parent_window, 'reference_locale', 'DEFAULT')
            self.parent_window.reference_locale = new_ref_locale
            if new_ref_locale != old_ref_locale and hasattr(self.parent_window, 'current_miz_path') and self.parent_window.current_miz_path:
                try:
                    self.parent_window.reference_data = self.parent_window.reference_loader.load_locale_from_miz(
                        self.parent_window.current_miz_path, new_ref_locale
                    )
                    # Показываем предупреждение если локаль не найдена и использован DEFAULT
                    if self.parent_window.reference_loader.last_fallback:
                        fb = self.parent_window.reference_loader.last_fallback
                        lang = getattr(self.parent_window, 'current_language', 'en')
                        warn_msg = get_translation(lang, 'status_ref_locale_fallback', locale=fb)
                        self.parent_window.statusBar().showMessage(warn_msg)
                        # Через 5 секунд восстанавливаем сообщение о строках
                        try:
                            restore_msg = get_translation(lang, 'status_mission_lines_loaded', count=len(self.parent_window.original_lines))
                            QTimer.singleShot(5000, lambda: self.parent_window.statusBar().showMessage(restore_msg))
                        except Exception:
                            QTimer.singleShot(5000, lambda: self.parent_window.statusBar().clearMessage())
                except Exception:
                    self.parent_window.reference_data = {}

            # allow parent to save (force) and clear suppression
            try:
                if hasattr(self.parent_window, '_suppress_settings_save'):
                    self.parent_window._suppress_settings_save = False
            except Exception:
                pass
            try:
                self.parent_window.save_settings(force=True, update_preview=False)
            except TypeError:
                # fallback if signature hasn't been updated
                self.parent_window.save_settings()

            # Rebuild preview if reference locale changed
            if new_ref_locale != old_ref_locale:
                try:
                    self.parent_window.update_display()
                except Exception:
                    pass
        self.close()

    def cancel_and_restore(self):
        """Restore parent's previous values (do not save) and close dialog."""
        self._log_debug(f"cancel_and_restore START: snapshot={getattr(self, '_orig_parent_values', None)}, parent={self.parent_window is not None}")
        try:
            if self.parent_window and getattr(self, '_orig_parent_values', None):
                vals = self._orig_parent_values
                # Suppress parent's preview updates while restoring values
                try:
                    self.parent_window._suppress_preview_update = True
                except Exception:
                    pass
                self._log_debug(f"cancel_and_restore: RESTORING from snapshot: {vals}")
                try:
                    old_val = self.parent_window.highlight_empty_fields
                    self.parent_window.highlight_empty_fields = vals.get('highlight_empty_fields', True)
                    self._log_debug(f"  - highlight_empty_fields: {old_val} -> {vals.get('highlight_empty_fields', True)}")
                except Exception as e:
                    self._log_debug(f"  - ERROR setting highlight_empty_fields: {e}")
                try:
                    old_col = self.parent_window.highlight_empty_color
                    self.parent_window.highlight_empty_color = vals.get('highlight_empty_color', '#555555')
                    self._log_debug(f"  - highlight_empty_color: {old_col} -> {vals.get('highlight_empty_color', '#555555')}")
                except Exception as e:
                    self._log_debug(f"  - ERROR setting highlight_empty_color: {e}")
                try:
                    old_logs = self.parent_window.debug_logs_enabled
                    self.parent_window.debug_logs_enabled = vals.get('debug_logs_enabled', True)
                    self._log_debug(f"  - debug_logs_enabled: {old_logs} -> {vals.get('debug_logs_enabled', True)}")
                except Exception as e:
                    self._log_debug(f"  - ERROR setting debug_logs_enabled: {e}")
                
                try:
                    self.parent_window.theme_bg_even = vals.get('theme_bg_even', '#505050')
                    self.parent_window.theme_bg_odd = vals.get('theme_bg_odd', '#4a4a4a')
                    self._log_debug(f"  - theme colors restored")
                except Exception as e:
                    self._log_debug(f"  - ERROR restoring theme colors: {e}")
                
                try:
                    self.parent_window.reference_locale = vals.get('reference_locale', 'DEFAULT')
                    self.parent_window.preview_font_family = vals.get('preview_font_family', 'Consolas')
                    self.parent_window.preview_font_size = vals.get('preview_font_size', 10)
                    if hasattr(self.parent_window, 'apply_preview_font_settings'):
                        self.parent_window.apply_preview_font_settings()
                    self._log_debug(f"  - reference_locale and font restored")
                except Exception as e:
                    self._log_debug(f"  - ERROR restoring reference_locale: {e}")
            else:
                self._log_debug(f"cancel_and_restore: NO VALUES TO RESTORE")
        except Exception as e:
            self._log_debug(f"cancel_and_restore: EXCEPTION: {e}")
        # clear suppression flag and close
        try:
            if self.parent_window:
                try:
                    self.parent_window._suppress_preview_update = False
                except Exception:
                    pass
                if hasattr(self.parent_window, '_suppress_settings_save'):
                    self.parent_window._suppress_settings_save = False
        except Exception:
            pass
        self.close()

    def showEvent(self, event):
        """Reload parent values every time dialog is shown (in case parent changed)"""
        self._log_debug(f"showEvent: Dialog shown, reloading parent values")
        super().showEvent(event)
        try:
            self.load_values_from_parent()
            self._log_debug(f"showEvent: Reloaded parent values")
        except Exception as e:
            self._log_debug(f"showEvent: ERROR reloading parent values: {e}")

    def closeEvent(self, event):
        # Ensure suppression flag cleared if dialog closed by other means
        try:
            if self.parent_window and hasattr(self.parent_window, '_suppress_settings_save'):
                self.parent_window._suppress_settings_save = False
        except Exception:
            pass
        super().closeEvent(event)

    def _log_debug(self, message: str):
        try:
            log_path = os.path.join(os.path.dirname(__file__), 'settings_debug.log')
            with open(log_path, 'a', encoding='utf-8') as lf:
                lf.write(f"[{datetime.now().isoformat()}] {message}\n")
                # include short stack trace for context
                for line in traceback.format_stack()[-8:]:
                    lf.write(line)
                lf.write('\n')
        except Exception:
            pass

    def _on_highlight_toggled(self, value: bool):
        try:
            self._log_debug(f'highlight_toggle toggled -> {value}')
        except Exception:
            pass

    def retranslate_ui(self, current_language):
        self.current_language = current_language
        self.setWindowTitle(get_translation(self.current_language, 'settings_window_title'))
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.windowTitle())
        # update labels/buttons
        try:
            if hasattr(self, 'highlight_toggle'):
                # update highlight label text
                if hasattr(self, 'highlight_label'):
                    self.highlight_label.setText(get_translation(self.current_language, 'highlight_empty_label'))
            if hasattr(self, 'enable_logs_label'):
                self.enable_logs_label.setText(get_translation(self.current_language, 'enable_logs_label'))
            if hasattr(self, 'clear_logs_label'):
                # Обновляем текст "Очистить логи" при смене языка
                clear_logs_text = "Очистить логи" if self.current_language == 'ru' else "Clear logs"
                self.clear_logs_label._original_text = f"<span style='color: white;'>|</span> <span style='color: white;'>{clear_logs_text}</span> <span style='color: white;'>|</span>"
                self.clear_logs_label._hovered_text = f"<span style='color: white;'>|</span> <span style='color: #ff9900;'>{clear_logs_text}</span> <span style='color: white;'>|</span>"
                if not self.clear_logs_label._hovered:
                    self.clear_logs_label.setText(self.clear_logs_label._original_text)
            if hasattr(self, 'color_preview'):
                self.color_preview.setToolTip(get_translation(self.current_language, 'highlight_color_label'))
            if hasattr(self, 'theme_bg_even_label'):
                self.theme_bg_even_label.setText(get_translation(self.current_language, 'theme_bg_even_label'))
            if hasattr(self, 'theme_bg_odd_label'):
                self.theme_bg_odd_label.setText(get_translation(self.current_language, 'theme_bg_odd_label'))
            if hasattr(self, 'theme_text_modified_label'):
                self.theme_text_modified_label.setText('Цвет изменённого текста' if self.current_language == 'ru' else 'Modified text color')
            if hasattr(self, 'theme_text_saved_label'):
                self.theme_text_saved_label.setText('Цвет сохранённого текста' if self.current_language == 'ru' else 'Saved text color')
            if hasattr(self, 'save_btn'):
                save_text = get_translation(self.current_language, 'save_btn')
                save_text = save_text.replace('💾 ', '').replace('💾', '').strip()
                self.save_btn.setText(save_text)
            if hasattr(self, 'cancel_btn'):
                self.cancel_btn.setText(get_translation(self.current_language, 'cancel_btn'))
            if hasattr(self, 'reset_btn'):
                # set language-specific label
                if self.current_language == 'ru':
                    new_text = 'Сбросить настройки'
                else:
                    new_text = 'Reset settings'
                self.reset_btn.setText(new_text)
                # Пересчитываем ширину под новый текст
                fm = self.reset_btn.fontMetrics()
                text_w = fm.horizontalAdvance(new_text)
                btn_w = max(120, text_w + 36)
                self.reset_btn.setMinimumWidth(btn_w)
        except:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        # place close button 15px from top-right
        try:
            x = self.width() - self.close_btn.width() - 15
            y = 15
            self.close_btn.move(x, y)
        except:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            x = self.width() - self.close_btn.width() - 15
            y = 15
            self.close_btn.move(x, y)
        except:
            pass

