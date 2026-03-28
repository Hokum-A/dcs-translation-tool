import os
import pygame
import traceback
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QProgressBar, QGridLayout, QWidget, QPlainTextEdit, QTextBrowser, QSlider, QStyle, QFileDialog, QFrame, QLineEdit, QLayout, QSizePolicy, QScrollArea, QSizeGrip, QMessageBox, QApplication, QAbstractScrollArea, QTabWidget, QSplitter, QCheckBox
from PyQt5.QtCore import Qt, QPoint, QRectF, QRect, QEvent, QUrl, QTimer, QSize, pyqtSignal, QThread, QSettings
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QPainterPath, QRegion, QDesktopServices, QFont, QFontMetrics, QMovie, QPixmap, QIcon
from localization import get_translation
from widgets import ToggleSwitch, ZoomablePreviewArea, JumpSlider, ClickableLabel, CustomSplitter, SearchCheckBox
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

def get_ui_settings():
    """Возвращает объект QSettings, привязанный к локальному INI-файлу в папке с EXE."""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(base_dir, "translation_tool_ui.ini")
    return QSettings(settings_path, QSettings.IniFormat)


class CustomDialog(QDialog):
    """Кастомный диалог без заголовка окна с поддержкой перетаскивания и закруглёнными углами"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.drag_position = QPoint()
        self.dragging = False
        self.resizing = False
        self._resizing_edge = None
        self._margin = 8  # Зона чувствительности границы для ресайза
        self.border_radius = 10
        self.border_width = 1
        self.border_color_active = QColor(255, 153, 0) # Оранжевый по умолчанию
        self.border_color_inactive = QColor("#8f8f8f") # Серый по умолчанию
        self.offset = None
        self.is_active = True # Флаг активности окна
        self.bg_color = QColor(58, 58, 58)  # #3a3a3a
        
        # Включаем отслеживание наведения для корректной смены курсора над дочерними виджетами
        self.setAttribute(Qt.WA_Hover, True)
        
        # Единый стиль для всплывающих контекстных меню (по ПКМ) внутри всех диалогов
        # Стиль полностью скопирован из original_text_all (main.py) для 100% совпадения
        self.setStyleSheet("""
            QMenu {
                background-color: #3a3a3a;
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

    def event(self, event):
        """Перехват событий наведения для управления курсором ресайза"""
        if event.type() == QEvent.HoverMove:
            self._update_cursor(event.pos())
        elif event.type() == QEvent.HoverLeave:
            self.setCursor(Qt.ArrowCursor)
        return super().event(event)

    def _update_cursor(self, pos):
        """Обновляет форму курсора в зависимости от положения"""
        if self.resizing or self.dragging:
            return

        edge = self._get_resize_edge(pos)
        
        if edge in (Qt.LeftEdge, Qt.RightEdge):
            new_cursor = Qt.SizeHorCursor
        elif edge in (Qt.TopEdge, Qt.BottomEdge):
            new_cursor = Qt.SizeVerCursor
        elif edge in (Qt.TopLeftCorner, Qt.BottomRightCorner):
            new_cursor = Qt.SizeFDiagCursor
        elif edge in (Qt.TopRightCorner, Qt.BottomLeftCorner):
            new_cursor = Qt.SizeBDiagCursor
        else:
            new_cursor = Qt.ArrowCursor
        
        if self.cursor().shape() != new_cursor:
            self.setCursor(new_cursor)

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
        # Отключаем сглаживание для самой рамки для максимальной четкости
        painter.setRenderHint(QPainter.Antialiasing, False)
        border_color = self.border_color_active if self.is_active else self.border_color_inactive
        pen = QPen(border_color, self.border_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Используем QRectF и смещение для четкой отрисовки
        # Смещение 0.5 корректно для 1px, для 2px и более нужно подбирать, но (width/2.0) - универсально
        off = self.border_width / 2.0
        rect_f = QRectF(self.rect()).adjusted(off, off, -off, -off)
        painter.drawRoundedRect(rect_f, self.border_radius, self.border_radius)

        super().paintEvent(event)

    def resizeEvent(self, event):
        """Обработка изменения размера диалога"""
        super().resizeEvent(event)
        self.update_mask()

    def showEvent(self, event):
        # Обработка показа диалога
        self.update_mask()
        self.is_active = True # Устанавливаем статус активным при показе
        # Включаем mouse tracking для корректной смены курсора при наведении на края
        self.setMouseTracking(True)
        super().showEvent(event)

    def changeEvent(self, event):
        """Отслеживает изменение состояния окна (фокус/активность)"""
        if event.type() == QEvent.ActivationChange:
            self.is_active = self.isActiveWindow()
            self.update() # Принудительно перерисовываем рамку
        super().changeEvent(event)

    def _get_resize_edge(self, pos):
        """Определяет, находится ли курсор на границе для ресайза"""
        m = self._margin  # 8px для прямых границ
        c = m * 3         # 24px для углов (увеличено для удобства при скруглении)
        w = self.width()
        h = self.height()
        x = pos.x()
        y = pos.y()

        # Сначала проверяем угловые зоны (они теперь больше для удобства)
        if x < c and y < c: return Qt.TopLeftCorner
        if x > w - c and y < c: return Qt.TopRightCorner
        if x < c and y > h - c: return Qt.BottomLeftCorner
        if x > w - c and y > h - c: return Qt.BottomRightCorner
        
        # Затем проверяем прямые границы
        if x < m: return Qt.LeftEdge
        if x > w - m: return Qt.RightEdge
        if y < m: return Qt.TopEdge
        if y > h - m: return Qt.BottomEdge
        return None

    def mousePressEvent(self, event):
        """Обработка нажатия мыши для перетаскивания или ресайза (только ЛКМ)"""
        if event.button() == Qt.LeftButton:
            # Блокируем перетаскивание при клике на интерактивные виджеты (избегаем "залипания" при вводе текста)
            child = self.childAt(event.pos())
            if child:
                # Список классов, которые должны сами обрабатывать нажатие
                interactive_classes = (QPushButton, QComboBox, QLineEdit, QPlainTextEdit, QTextBrowser, QAbstractScrollArea, QSlider)
                if isinstance(child, interactive_classes) or isinstance(child.parent(), interactive_classes):
                    super().mousePressEvent(event)
                    return

            edge = self._get_resize_edge(event.pos())
            if edge:
                self.resizing = True
                self._resizing_edge = edge
            else:
                self.dragging = True
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Обработка движения мыши для перетаскивания, ресайза или смены курсора"""
        if self.resizing and (event.buttons() & Qt.LeftButton):
            self._handle_resize(event.globalPos())
            event.accept()
        elif self.dragging and (event.buttons() & Qt.LeftButton):
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            # Курсор теперь обновляется в event() через HoverMove
            super().mouseMoveEvent(event)

    def _handle_resize(self, global_pos):
        """Логика изменения геометрии окна при ресайзе"""
        rect = self.geometry()
        edge = self._resizing_edge
        
        if edge == Qt.LeftEdge:
            new_width = rect.right() - global_pos.x()
            if new_width >= self.minimumWidth():
                rect.setLeft(global_pos.x())
        elif edge == Qt.RightEdge:
            rect.setRight(global_pos.x())
        elif edge == Qt.TopEdge:
            new_height = rect.bottom() - global_pos.y()
            if new_height >= self.minimumHeight():
                rect.setTop(global_pos.y())
        elif edge == Qt.BottomEdge:
            rect.setBottom(global_pos.y())
        elif edge == Qt.TopLeftCorner:
            new_width = rect.right() - global_pos.x()
            new_height = rect.bottom() - global_pos.y()
            if new_width >= self.minimumWidth(): rect.setLeft(global_pos.x())
            if new_height >= self.minimumHeight(): rect.setTop(global_pos.y())
        elif edge == Qt.TopRightCorner:
            new_height = rect.bottom() - global_pos.y()
            if new_height >= self.minimumHeight(): rect.setTop(global_pos.y())
            rect.setRight(global_pos.x())
        elif edge == Qt.BottomLeftCorner:
            new_width = rect.right() - global_pos.x()
            if new_width >= self.minimumWidth(): rect.setLeft(global_pos.x())
            rect.setBottom(global_pos.y())
        elif edge == Qt.BottomRightCorner:
            rect.setRight(global_pos.x())
            rect.setBottom(global_pos.y())
            
        self.setGeometry(rect)

    def mouseReleaseEvent(self, event):
        """Обработка отпускания кнопки мыши"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self._resizing_edge = None
            self.setCursor(Qt.ArrowCursor)
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
    
    def __init__(self, folders, parent=None, default_selection=None):
        super().__init__(parent)
        self.folders = self._sort_locales(list(folders))
        # Initial selection logic checks default_selection first, then "DEFAULT", then first folder
        if default_selection and default_selection in self.folders:
            self.selected_locale = default_selection
        else:
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
    def __init__(self, folders, current_language, parent=None, default_selection=None):
        super().__init__(parent)
        self.selected_folder = default_selection if default_selection and default_selection in folders else "DEFAULT"
        self.folders = folders
        self.current_language = current_language

        self.setWindowTitle(get_translation(self.current_language, 'miz_select_folder_title'))
        self.setFixedSize(450, 280) # Увеличено с 250

        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        # 1. КОНТЕНТ
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 25, 30, 15)
        content_layout.setSpacing(10)

        content_layout.addStretch() # Центрирование сверху

        title_label = QLabel(get_translation(self.current_language, 'miz_select_folder_title'))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px; background-color: transparent; border: none;")

        desc_label = QLabel(get_translation(self.current_language, 'miz_select_folder_desc'))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #bbbbbb; font-size: 12px; background-color: transparent; border: none;")

        content_layout.addWidget(title_label)
        content_layout.addWidget(desc_label)
        content_layout.addSpacing(10)

        # Селектор локалей
        try:
            self.locale_selector = LocaleSelectorWidget(folders, default_selection=default_selection)
            combo_layout = QHBoxLayout()
            combo_layout.addStretch()
            combo_layout.addWidget(self.locale_selector)
            combo_layout.addStretch()
            content_layout.addLayout(combo_layout)
            self.locale_selector.locale_activated.connect(self.handle_accept)
        except Exception:
            self.combo = QComboBox()
            self.combo.addItems(folders)
            if default_selection and default_selection in folders:
                self.combo.setCurrentText(default_selection)
            elif "DEFAULT" in folders:
                self.combo.setCurrentText("DEFAULT")
            elif folders:
                self.combo.setCurrentIndex(0)
            
            # Стиль комбобокса (упрощенный для диалога)
            self.combo.setStyleSheet("QComboBox { background-color: #606060; color: #ffffff; border: 1px solid #777; border-radius: 4px; padding: 5px; min-width: 200px; }")
            combo_layout = QHBoxLayout()
            combo_layout.addStretch()
            combo_layout.addWidget(self.combo)
            combo_layout.addStretch()
            content_layout.addLayout(combo_layout)

        content_layout.addStretch()
        main_layout.addWidget(content_widget)

        # 2. РАЗДЕЛИТЕЛЬ
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #777777; border: none;")
        main_layout.addWidget(line)

        # 3. ФУТЕР
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("QFrame { background-color: #2b2b2b; border: none; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        footer_layout.setSpacing(15)

        btn_style_open = """
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #e68a00; }
        """
        btn_style_cancel = """
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #a3a3a3; }
        """

        open_btn = QPushButton(get_translation(self.current_language, 'open_btn'))
        open_btn.setStyleSheet(btn_style_open)
        open_btn.setFixedSize(120, 32)
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(self.handle_accept)

        cancel_btn = QPushButton(get_translation(self.current_language, 'cancel_btn'))
        cancel_btn.setStyleSheet(btn_style_cancel)
        cancel_btn.setFixedSize(120, 32)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        footer_layout.addStretch()
        footer_layout.addWidget(cancel_btn)
        footer_layout.addWidget(open_btn)
        footer_layout.addStretch()
        
        main_layout.addWidget(footer)

    def handle_accept(self):
        # Берём выбранную локаль из нового селектора, либо из combo как fallback
        try:
            self.selected_folder = self.locale_selector.get_selected_locale()
        except Exception:
            self.selected_folder = self.combo.currentText() if hasattr(self, 'combo') else "DEFAULT"
        self.accept()




class MizProgressDialog(CustomDialog):
    """Кастомный диалог прогресс-бара для операций с .miz"""
    def __init__(self, parent=None, title=None, message=None):
        super().__init__(parent)
        self.setWindowTitle(title if title else "")
        self.setFixedSize(320, 110)

        lang = 'ru'
        if parent and hasattr(parent, 'current_language'):
            lang = parent.current_language
        elif self.parent() and hasattr(self.parent(), 'current_language'):
            lang = self.parent().current_language

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        display_msg = message if message else get_translation(lang, 'miz_executing')
        self.label = QLabel(display_msg)
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
                background-color: #222222;
                border: 1px solid #444;
                border-radius: 12px;
                text-align: center;
                color: #ffffff;
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
        self.setFixedSize(854, 520)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(0)

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

        self.win_close_btn = QPushButton("✕", self)
        self.win_close_btn.setFixedSize(30, 30)
        self.win_close_btn.setCursor(Qt.PointingHandCursor)
        self.win_close_btn.clicked.connect(self.accept)
        self.win_close_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #aaaaaa; border: none; font-size: 18px; font-weight: bold; }
            QPushButton:hover { color: #ff9900; }
        """)
        top_layout.addWidget(self.win_close_btn)
        self.main_layout.addWidget(top_bar)

        # Middle Grid for content and cat
        self.mid_container = QWidget()
        self.main_grid = QGridLayout(self.mid_container)
        self.main_grid.setContentsMargins(0, 0, 0, 0)
        self.main_grid.setSpacing(0)

        self.content_area = QWidget()
        self.content_area.setFixedWidth(527)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 20, 20, 20) # Left margin reduced for tighter alignment

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
 
        self.cat_label = QLabel(self) # Parent is self, so it can overlap the bottom bar
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
        self.exit_btn.setFixedSize(120, 32)
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.clicked.connect(self.accept)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #a3a3a3;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)

        self.main_layout.addWidget(self.mid_container, 1)

        # Content area stretches vertically to fill mid_container, achieving symmetric 20px margins
        self.main_grid.addWidget(self.content_area, 0, 0, Qt.AlignLeft)
        self.main_grid.setColumnStretch(1, 1) # Pushes content_area to the left

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #777777; border: none;")
        self.main_layout.addWidget(separator)

        # Bottom bar
        self.bottom_bar = QWidget()
        self.bottom_bar.setFixedHeight(60)
        self.bottom_bar.setStyleSheet("background-color: #2b2b2b; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
        self.bottom_layout = QHBoxLayout(self.bottom_bar)
        self.bottom_layout.setContentsMargins(20, 0, 20, 0)

        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.exit_btn)
        self.bottom_layout.addStretch()

        self.main_layout.addWidget(self.bottom_bar)

        # Positioning the cat manually at the bottom-right of the window
        # so it can overlap the bottom bar and separator.
        # Placing it at the exact edge (h - cat_h) ensures it gets clipped by the window's rounded corner mask.
        self.cat_label.move(self.width() - self.cat_label.width(), self.height() - self.cat_label.height())
        self.cat_label.raise_()

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
    def __init__(self, audio_path, filename, current_language, key=None, on_replace_callback=None, on_download_callback=None, parent=None, last_audio_folder=None, is_heuristic=False, miz_resource_manager=None, current_miz_path=None, shared_duration_cache=None):
        super().__init__(parent)
        self.audio_path = audio_path # Временный путь к файлу для воспроизведения
        self.filename = filename     # Оригинальное имя файла
        self.current_language = current_language
        self.key = key               # Ключ (DictKey), для которого открыт плеер
        self.on_replace_callback = on_replace_callback # Callback для сохранения замены
        self.on_download_callback = on_download_callback # Callback для загрузки (сохранения на диск)
        self.new_file_path = None    # Путь к новому файлу, если выбрали замену
        self.last_audio_folder = last_audio_folder # Последняя папка для выбора аудиофайлов
        self.is_heuristic = is_heuristic  # Аудио связано эвристически
        self.miz_resource_manager = miz_resource_manager # Менеджер ресурсов для плейлиста
        self.current_miz_path = current_miz_path # Путь к текущей миссии (для извлечения аудио)
        self.shared_duration_cache = shared_duration_cache # Кэш длительностей
        self._last_folder = miz_resource_manager.current_folder if miz_resource_manager else None
        
        self.duration_sec = 0
        self.is_playing = False
        self.is_paused = False
        self.is_slider_dragged = False
        self.play_start_offset = 0 # Смещение для корректного отображения времени при перемотке
        self.audio_loaded = False
        
        self.setWindowTitle(get_translation(current_language, 'audio_player_title'))
        self._player_base_width = 550
        self._player_base_height = 260
        self._playlist_height = 250
        self._playlist_visible = False
        # Пытаемся взять из аргумента, если передан в будущем или оставить дефолт
        self._last_expanded_height = getattr(parent, 'saved_audio_player_expanded_height', self._player_base_height + self._playlist_height)
        self.setMinimumSize(self._player_base_width, self._player_base_height)
        self.resize(self._player_base_width, self._player_base_height)
        
        # Загрузка начального трека
        if audio_path and os.path.exists(audio_path):
            self.load_audio_file(audio_path)

        self.setup_ui()
        
        # Загружаем настройки (геометрия и состояние плейлиста)
        self.load_settings()
        
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
        
        # Обновляем тултип для иконки справки
        help_text = get_translation(self.current_language, 'audio_replace_help_tooltip')
        if self.parent() and hasattr(self.parent(), 'register_custom_tooltip'):
            self.parent().register_custom_tooltip(self.help_icon, help_text)
        else:
            self.help_icon.setToolTip(help_text)
        
        # Если файл не выбран, обновляем надпись "Файл не выбран"
        if not self.audio_path:
            self.file_label.setText(get_translation(self.current_language, 'no_audio_file'))

        # Обновляем плейлист
        if hasattr(self, 'playlist_widget'):
            self.playlist_widget.retranslate_ui(self.current_language)

    def refresh_playlist(self):
        """Принудительно обновляет список аудиофайлов в таблице"""
        if hasattr(self, 'miz_resource_manager') and self.miz_resource_manager:
            # [FIX] Сброс кэша при смене локали, чтобы пересчитать длительности (т.к. файлы в EN/RU могут отличаться)
            curr_folder = self.miz_resource_manager.current_folder
            if getattr(self, '_last_folder', None) != curr_folder:
                if self.shared_duration_cache is not None:
                    self.shared_duration_cache.clear()
                self._last_folder = curr_folder

            if hasattr(self, 'playlist_widget'):
                # Получаем ключи текущей локали для фильтрации галочек «связи»
                # original_lines содержит строки ТОЛЬКО текущей локали (без DEFAULT-only ключей)
                curr_dict_keys = None
                p = self.parent()
                if p and hasattr(p, 'original_lines') and p.original_lines:
                    curr_dict_keys = {line.get('key') for line in p.original_lines if line.get('key')}
                
                all_files = self.miz_resource_manager.get_all_resource_files(current_dict_keys=curr_dict_keys)
                audio_files = [f for f in all_files if f.get('type') == 'audio']
                try:
                    self.playlist_widget.set_audio_files(audio_files)
                except Exception as e:
                    print(f"Error refreshing playlist: {e}")

    def showEvent(self, event):
        super().showEvent(event)
        # Обновляем таблицу плейлиста при каждом показе окна
        self.refresh_playlist()
        
        # [NEW] Гарантируем, что текущий активный файл (если он есть) будет выделен в списке
        if self.key and hasattr(self, 'playlist_widget'):
            resolved_key = self.miz_resource_manager.resolve_to_res_key(self.key) if self.miz_resource_manager else self.key
            self.playlist_widget.select_file_by_key(resolved_key)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignTop)

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
        self.close_btn.setFocusPolicy(Qt.NoFocus)
        self.close_btn.move(self.width() - 30 - 15, 15)
        # Фиксированный отступ сверху под крестик закрытия
        top_spacer = QWidget()
        top_spacer.setFixedHeight(15)
        top_spacer.setStyleSheet("background-color: transparent;")
        layout.addWidget(top_spacer)

        # === ОБЩАЯ рамка, объединяющая все элементы плеера ===
        self.player_outer_frame = QFrame()
        self.player_outer_frame.setObjectName("playerOuterFrame")
        self.player_outer_frame.setContentsMargins(0, 0, 0, 0)
        self.player_outer_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.player_outer_frame.setStyleSheet("""
            QFrame#playerOuterFrame {
                border: none;
                background-color: transparent;
            }
        """)
        player_frame_layout = QVBoxLayout(self.player_outer_frame)
        player_frame_layout.setContentsMargins(15, 0, 15, 5)
        player_frame_layout.setSpacing(0)

        # 1. Название файла
        self.file_label = QLabel(self.filename)
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("color: #ff9900; font-weight: bold; font-size: 14px; background-color: transparent; padding-right: 45px;")
        self.file_label.setAttribute(Qt.WA_TransparentForMouseEvents) 
        self.file_label.setContentsMargins(0, 0, 0, 0)
        player_frame_layout.addWidget(self.file_label)
        
        # Информационная строка (длительность и размер)
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #aaaaaa; font-size: 12px; margin-top: -5px; padding-right: 45px;")
        self.info_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        player_frame_layout.addWidget(self.info_label)
        
        # 2. Внутренняя рамка для управления и картинки
        self.controls_frame = QFrame()
        self.controls_frame.setObjectName("controlsFrame")
        self.controls_frame.setMinimumSize(490, 125)
        self.controls_frame.setMaximumHeight(125)
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
        self.position_slider = JumpSlider(Qt.Horizontal)
        self.position_slider.setFocusPolicy(Qt.NoFocus)
        self.position_slider.setStyleSheet("""
            QSlider { background: transparent; }
            QSlider:focus { border: none; outline: none; }
            QSlider::groove:horizontal { border: 1px solid #444; background: #222; height: 8px; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #ff9900; border: 1px solid #444; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #fff; border: 1px solid #5c5c5c; width: 14px; margin-top: -3px; margin-bottom: -3px; border-radius: 7px; }
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
        # self.play_pause_btn.setToolTip(get_translation(self.current_language, 'play_btn')) # Removed tooltip
        self.play_pause_btn.setFocusPolicy(Qt.NoFocus)
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
        # self.stop_btn.setToolTip(get_translation(self.current_language, 'stop_btn')) # Removed tooltip
        self.stop_btn.setFocusPolicy(Qt.NoFocus)
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
        
        self.volume_slider = JumpSlider(Qt.Horizontal)
        self.volume_slider.setFocusPolicy(Qt.NoFocus)
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
            QSlider { background: transparent; }
            QSlider:focus { border: none; outline: none; }
            QSlider::groove:horizontal { border: 1px solid #444; background: #222; height: 8px; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #ff9900; border: 1px solid #444; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #fff; border: 1px solid #5c5c5c; width: 14px; margin-top: -3px; margin-bottom: -3px; border-radius: 7px; }
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

        # Центрируем рамку controls_frame внутри общей рамки
        frame_centered_hbox = QHBoxLayout()
        frame_centered_hbox.setContentsMargins(0, 0, 0, 0)
        frame_centered_hbox.addStretch()
        frame_centered_hbox.addWidget(self.controls_frame)
        frame_centered_hbox.addStretch()
        player_frame_layout.addLayout(frame_centered_hbox)

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
        self.replace_btn.setFocusPolicy(Qt.NoFocus)
        self.replace_btn.clicked.connect(self.replace_audio)
        
        # 6. Иконка справки 🛈
        self.help_icon = QLabel("🛈")
        self.help_icon.setCursor(Qt.PointingHandCursor)
        self.help_icon.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 18px;
                margin-left: 8px;
                background-color: transparent;
            }
            QLabel:hover {
                color: #ff9900;
            }
        """)
        # Регистрация тултипа
        help_text = get_translation(self.current_language, 'audio_replace_help_tooltip')
        if self.parent() and hasattr(self.parent(), 'register_custom_tooltip'):
            self.parent().register_custom_tooltip(self.help_icon, help_text)
        else:
            self.help_icon.setToolTip(help_text)

        replace_layout = QHBoxLayout()
        replace_layout.setContentsMargins(0, 5, 0, 5)
        replace_layout.addStretch()
        
        # Добавляем пустой отступ слева, равный ширине значка справки + отступ (8px + ~18px),
        # чтобы сама кнопка [Заменить] осталась ровно по центру.
        replace_layout.addSpacing(26)
        
        replace_layout.addWidget(self.replace_btn)
        replace_layout.addWidget(self.help_icon)
        replace_layout.addStretch()

        # Кнопка раскрытия плейлиста (≡) — справа внизу
        self.playlist_toggle_btn = QPushButton("≡")
        self.playlist_toggle_btn.setFixedSize(28, 28)
        self.playlist_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.playlist_toggle_btn.setFocusPolicy(Qt.NoFocus)
        self.playlist_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaaaaa;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff9900;
                border-color: #ff9900;
            }
        """)
        self.playlist_toggle_btn.clicked.connect(self.toggle_playlist)
        replace_layout.addWidget(self.playlist_toggle_btn)
        replace_layout.addSpacing(5)

        player_frame_layout.addLayout(replace_layout)

        # Добавляем общую рамку в основной layout
        layout.addWidget(self.player_outer_frame)

        # === Виджет плейлиста (скрыт по умолчанию) ===
        from player import AudioPlaylistWidget
        self.playlist_widget = AudioPlaylistWidget(self.current_language, self, shared_duration_cache=self.shared_duration_cache, show_checkboxes=False)
        self.playlist_widget.setVisible(False)
        self.playlist_widget.file_clicked.connect(self._on_playlist_file_clicked)
        self.playlist_widget.file_double_clicked.connect(self._on_playlist_file_double_clicked)
        self.playlist_widget.stop_requested.connect(self.stop_audio)
        self.playlist_widget.editor_jump_requested.connect(self._on_jump_to_editor)
        self.playlist_widget.download_requested.connect(self._on_download_audio)
        self.playlist_widget.replace_requested.connect(self._on_playlist_replace_requested)
        layout.addWidget(self.playlist_widget)

        # Initial label update
        self.update_time_labels(0)
        
        # Поднимаем кнопку закрытия на самый верхний слой
        self.close_btn.raise_()

    def set_playlist_visible(self, visible):
        """Программно устанавливает видимость плейлиста без переключения."""
        if self._playlist_visible == visible:
            return
        self.toggle_playlist()

    def toggle_playlist(self):
        """Переключает видимость панели плейлиста."""
        self._playlist_visible = not self._playlist_visible
        self._is_toggling_playlist = True
        self.playlist_widget.setVisible(self._playlist_visible)
        
        # Сохраняем состояние плейлиста
        settings = get_ui_settings()
        settings.setValue("audio_player_playlist_visible", self._playlist_visible)

        if self._playlist_visible:
            # Уменьшаем нижний отступ, чтобы статусная строка была почти вплотную к краю окна
            self.layout().setContentsMargins(15, 15, 15, 2)
            
            # При открытии выделяем текущий трек
            if self.key:
                self.playlist_widget.select_file_by_key(self.key)
            # Расширяем окно вниз, разрешаем ресайз по обеим осям
            # Минимум - база + 150px для списка, чтобы он не схлопнулся совсем
            self.setMinimumSize(self._player_base_width, self._player_base_height + 150)
            self.setMaximumSize(16777215, 16777215)  # QWIDGETSIZE_MAX
            
            # Восстанавливаем последний растянутый размер (с задержкой для layout manager)
            target_height = self._last_expanded_height
            def apply_size():
                self.resize(self.width(), target_height)
                self._is_toggling_playlist = False
            QTimer.singleShot(50, apply_size)
            # Подсвечиваем кнопку
            self.playlist_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #ff9900;
                    border: 1px solid #ff9900;
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    color: #ffffff;
                    border-color: #ffffff;
                }
            """)
        else:
            # Возвращаем стандартные отступы
            self.layout().setContentsMargins(15, 15, 15, 15)
            
            # Возвращаем компактный размер
            self.setMinimumSize(self._player_base_width, self._player_base_height)
            self.setMaximumHeight(self._player_base_height)
            self.resize(self.width(), self._player_base_height)
            self._is_toggling_playlist = False
            # Возвращаем обычный стиль кнопки
            self.playlist_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #aaaaaa;
                    border: 1px solid #555;
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    color: #ff9900;
                    border-color: #ff9900;
                }
            """)

    def resizeEvent(self, event):
        """Перемещает крестик закрытия при изменении размера окна."""
        super().resizeEvent(event)
        if self._playlist_visible and not getattr(self, '_is_toggling_playlist', False):
            # Запоминаем размер развернутого списка. 
            # Только если он реально больше базового, чтобы не запомнить промежуточное состояние.
            if self.height() > self._player_base_height + 50:
                self._last_expanded_height = self.height()
                # Передаем наверх для сохранения в настройки
                if self.parent() and hasattr(self.parent(), 'saved_audio_player_expanded_height'):
                    self.parent().saved_audio_player_expanded_height = self._last_expanded_height
            
        if hasattr(self, 'close_btn'):
            self.close_btn.move(self.width() - 30 - 15, 15)

    def on_mixer_takeover(self):
        """Вызывается извне, когда другой компонент (например, Quick Play) забирает миксер."""
        # Сбрасываем позицию, так как играет чужой трек
        self.play_start_offset = 0
            
        self.is_playing = False
        self.is_paused = False # Сбрасываем и паузу тоже, будем грузить заново
        self.audio_loaded = False # Принудительный reload при следующем Play в этом окне
        
        self.play_pause_btn.setText("▶")
        self.play_pause_btn.setStyleSheet(self.btn_style_base.format(size=28, top=self.play_btn_top_offset))
        
        # Сбрасываем ползунок и время
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(0)
        self.position_slider.blockSignals(False)
        self.update_time_labels(0)

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
                
                # Обновляем инфо-лейбл (очищаем, так как эмодзи в основном плеере не нужны)
                if hasattr(self, 'info_label'):
                    self.info_label.setText("")
                
                # Используем сохраненную громкость вместо 0.5
                current_vol = 50
                if self.parent() and hasattr(self.parent(), 'audio_volume'):
                    current_vol = self.parent().audio_volume
                pygame.mixer.music.set_volume(current_vol / 100.0)
                
                # [FIX] Сбрасываем прогресс и обновляем диапазон слайдера
                # (load_audio_file может вызываться из __init__ до setup_ui, поэтому проверяем наличие)
                if hasattr(self, 'position_slider'):
                    self.position_slider.setRange(0, int(self.duration_sec * 1000))
                    self.position_slider.setValue(0)
                self.play_start_offset = 0
                self.update_time_labels(0)
        except Exception as e:
            print(f"Error loading audio file: {e}")
            self.duration_sec = 0
            self.audio_loaded = False

    def update_audio(self, audio_path, filename, key, last_audio_folder=None, is_heuristic=False, on_replace_callback=None, on_download_callback=None):
        """Обновляет плеер для нового файла без пересоздания окна"""
        # Обновляем callback при каждом использовании синглтона!
        if on_replace_callback is not None:
            self.on_replace_callback = on_replace_callback
        if on_download_callback is not None:
            self.on_download_callback = on_download_callback
        
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
        self.play_pause_btn.setEnabled(True)
        self.replace_btn.setEnabled(True)
        self.position_slider.setEnabled(True)

        if hasattr(self, 'playlist_widget') and self.playlist_widget:
            # Теперь выделяем всегда (синхронизация)
            resolved_key = self.miz_resource_manager.resolve_to_res_key(key) if self.miz_resource_manager else key
            self.playlist_widget.select_file_by_key(resolved_key)

    def _on_playlist_file_clicked(self, res_key):
        """Обработка одиночного клика в плейлисте: загружаем этот файл в плеер, но без автовоспроизведения."""
        if not self.miz_resource_manager:
            return
            
        # [FIX] Сбрасываем желтую подсветку в редакторе при переключении аудио в плейлисте
        main_win = self.parent()
        if main_win and hasattr(main_win, 'clear_audio_highlight'):
            main_win.clear_audio_highlight()

        # Если мы кликнули на уже загруженный файл (с учетом того, что это может быть DictKey), ничего не меняем
        current_res_key = self.miz_resource_manager.resolve_to_res_key(self.key) if self.key else None
        if current_res_key == res_key:
            return

        # 1. Получаем информацию об аудио для данного ресурсного ключа
        audio_info = self.miz_resource_manager.get_audio_for_res_key(res_key)
        if not audio_info:
            return
        filename, is_current_locale = audio_info
        
        # 2. Извлекаем во временную папку
        # Используем текущий путь к миссии у родителя (MainWindow)
        miz_path = getattr(self.parent(), 'current_miz_path', None)
        if not miz_path:
            return
            
        audio_path = self.miz_resource_manager.extract_resource_to_temp(miz_path, res_key)
        
        if audio_path and os.path.exists(audio_path):
            # Обновляем плеер (включая стоп старого, загрузку нового и обновление ярлыков)
            # Убеждаемся, что callback актуален
            callback = self.on_replace_callback
            if not callback and self.parent() and hasattr(self.parent(), 'handle_audio_replacement'):
                callback = self.parent().handle_audio_replacement

            self.update_audio(
                audio_path, 
                filename, 
                res_key, 
                is_heuristic=False, 
                on_replace_callback=callback
            )
            
            # Синхронизируем выделение в таблице
            self.playlist_widget.select_file_by_key(res_key)
            
            # ВНИМАНИЕ: автовоспроизведение специально убрано для одиночного клика
            
            # Сбрасываем ключ из превью, чтобы основная кнопка замены работала с тем, что в списке
            self.key = None
            
            # Флаг, чтобы предотвратить мгновенное переключение паузы при выделении новой строки
            self._just_selected_key = res_key
        
        # Высвечиваем окно если оно было скрыто
        if self.isHidden():
            self.show()
        self.raise_()
        self.activateWindow()

    def _on_playlist_file_double_clicked(self, res_key):
        """Обработка двойного клика в плейлисте: загружаем (если ещё нет) и сразу начинаем играть, либо останавливаем если уже выделен и играет/на паузе."""
        
        # Если мы дважды кликнули по УЖЕ играющему/поставленному на паузу аудио
        if self.key == res_key and (getattr(self, 'is_playing', False) or getattr(self, 'is_paused', False)):
            # При двойном клике на выделенном треке сбрасываем (останавливаем) воспроизведение
            self.stop_audio()
        else:
            # Иначе загружаем новый трек (или старый, который был остановлен) и сразу играем
            self._on_playlist_file_clicked(res_key)
            self.stop_audio()
            self.toggle_play_pause()

    def _on_jump_to_editor(self, dict_key):
        """Обработка запроса перехода к редактору из плейлиста."""
        main_window = self.parent()
        if main_window and hasattr(main_window, 'jump_to_dict_key'):
            # [FIX] Окно больше не закрываем и звук не стопаем, чтобы можно было 
            # продолжать слушать при навигации (как просил пользователь)
            QTimer.singleShot(100, lambda: main_window.jump_to_dict_key(dict_key))
            return # [FIX] Предотвращает дублирование окон (клоны)
        
        # Высвечиваем окно если оно было скрыто (только если не переходим в редактор)
        if self.isHidden():
            self.show()
        self.raise_()
        self.activateWindow()

    def _on_download_audio(self, res_key):
        """Сохранение аудиофайла из плейлиста на диск."""
        if not self.miz_resource_manager or not self.current_miz_path:
            return
            
        # Получаем информацию о файле
        res_info = self.miz_resource_manager.get_audio_for_res_key(res_key)
        if not res_info:
            return
        filename, _ = res_info
        
        # Определяем начальную папку
        settings = get_ui_settings()
        last_dir = settings.value("fm_last_export_dir", os.path.expanduser("~"))
        initial_path = os.path.join(last_dir, filename)
        
        # Открываем диалог сохранения
        path, _ = QFileDialog.getSaveFileName(
            self, 
            get_translation(self.current_language, 'fm_tooltip_download'),
            initial_path,
            get_translation(self.current_language, 'audio_file_filter')
        )
        
        if path:
            # Сохраняем папку для следующего раза
            settings.setValue("fm_last_export_dir", os.path.dirname(path))
            
            # Выполняем извлечение
            if self.miz_resource_manager.extract_resource_to_file(self.current_miz_path, res_key, path):
                # Можно добавить уведомление в статус-бар главного окна, если нужно
                main_window = self.parent()
                if main_window and hasattr(main_window, 'statusBar'):
                    msg = get_translation(self.current_language, 'fm_export_success').format(path=f" {path}")
                    # Убираем HTML теги из сообщения для статусбара
                    msg = msg.replace("<br/>", " ").replace("<span style='color: #ff9900;'>", "").replace("</span>", "").replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
                    main_window.statusBar().showMessage(msg, 5000)

    def reset_to_no_file(self):
        """Сбрасывает плеер в состояние 'Файл не выбран'."""
        self.stop_audio()
        self.audio_path = None
        self.filename = None
        self.key = None
        self.is_heuristic = False
        self.audio_loaded = False
        
        # [NEW] Обновляем список файлов в плейлисте при сбросе (смена локали/миссии)
        self.refresh_playlist()
        
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
        if not hasattr(self, 'audio_path') or not self.audio_path or not os.path.exists(self.audio_path):
            return
            
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.is_paused = True
            self.play_pause_btn.setText("▶")
            self.play_pause_btn.setStyleSheet(self.btn_style_base.format(size=28, top=self.play_btn_top_offset))
            self.play_pause_btn.setToolTip(get_translation(self.current_language, 'play_btn'))
        else:
            if self.is_paused:
                try:
                    # Если ползунок был сдвинут во время паузы, нужно играть через play(start=...)
                    if abs(self.play_start_offset - self.position_slider.value()) > 500:
                        self.play_start_offset = self.position_slider.value()
                        pygame.mixer.music.load(self.audio_path)
                        self.audio_loaded = True
                        pygame.mixer.music.play(start=self.play_start_offset / 1000.0)
                    else:
                        if not getattr(self, 'audio_loaded', False):
                             if hasattr(self, 'audio_path') and self.audio_path and os.path.exists(self.audio_path):
                                pygame.mixer.music.load(self.audio_path)
                                self.audio_loaded = True
                                pygame.mixer.music.play(start=self.play_start_offset/1000.0)
                        else:
                            pygame.mixer.music.unpause()
                except Exception:
                    try:
                        if hasattr(self, 'audio_path') and self.audio_path and os.path.exists(self.audio_path):
                            pygame.mixer.music.load(self.audio_path)
                            self.audio_loaded = True
                            pygame.mixer.music.play(start=self.position_slider.value() / 1000.0)
                    except Exception as e:
                        print(f"Audio unpause/load error: {e}")
            else:
                # Играть сначала (или с позиции ползунка, если он был сдвинут)
                self.play_start_offset = self.position_slider.value()
                try:
                    if not getattr(self, 'audio_loaded', False):
                        if hasattr(self, 'audio_path') and self.audio_path and os.path.exists(self.audio_path):
                            pygame.mixer.music.load(self.audio_path)
                            self.audio_loaded = True
                    pygame.mixer.music.play(start=self.play_start_offset / 1000.0)
                except Exception as e:
                    print(f"Audio play error: {e}")
            self.is_playing = True
            self.is_paused = False
            self.play_pause_btn.setText("\u23F8\uFE0E")
            self.play_pause_btn.setStyleSheet(self.btn_style_base.format(size=26, top=self.play_btn_top_offset))

    def stop_audio(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.play_pause_btn.setText("▶")
        self.play_pause_btn.setStyleSheet(self.btn_style_base.format(size=28, top=self.play_btn_top_offset))
        try:
            if self.audio_path:
                pygame.mixer.music.load(self.audio_path)
                self.audio_loaded = True
            self.position_slider.setValue(0)
            self.update_time_labels(0)
            self.play_start_offset = 0
        except: pass

    def set_volume(self, value):
        if self.parent() and hasattr(self.parent(), 'set_audio_volume'):
            self.parent().set_audio_volume(value, sender=self)
        else:
            vol = value / 100.0
            pygame.mixer.music.set_volume(vol)

    def on_slider_pressed(self):
        self.is_slider_dragged = True
        
    def on_slider_released(self):
        val_ms = self.position_slider.value()
        start_pos = val_ms / 1000.0
        try:
            try:
                if not getattr(self, 'audio_loaded', False):
                    if hasattr(self, 'audio_path') and self.audio_path and os.path.exists(self.audio_path):
                        pygame.mixer.music.load(self.audio_path)
                        self.audio_loaded = True
            except Exception: pass
            
            self.play_start_offset = val_ms
            self.update_time_labels(val_ms)
            
            # Продолжаем играть только если уже играло
            if self.is_playing:
                pygame.mixer.music.play(start=start_pos)
            
        except Exception as e:
            print(f"Seek error: {e}")
        self.is_slider_dragged = False

    def update_progress(self):
        if self.is_slider_dragged: return
        try:
            is_busy = pygame.mixer.music.get_busy()
            pos = pygame.mixer.music.get_pos()
            
            if self.is_playing and is_busy and pos >= 0:
                current_ms = pos + self.play_start_offset
                self.position_slider.blockSignals(True)
                self.position_slider.setValue(current_ms)
                self.position_slider.blockSignals(False)
                self.update_time_labels(current_ms)
            elif self.is_playing and not is_busy:
                # Трек реально завершился
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
        except Exception:
            pass
            try: pygame.mixer.music.load(self.audio_path)
            except: pass
            
    def update_time_labels(self, current_ms):
        def fmt(ms):
            s = int(ms // 1000) % 60
            m = int(ms // 60000)
            return f"{m:02}:{s:02}"
        dur_ms = int(self.duration_sec * 1000)
        self.time_label.setText(f"{fmt(current_ms)} / {fmt(dur_ms)}")

    def replace_audio(self):
        """Запускает выбор нового файла (основная кнопка плеера)."""
        # 1. Если есть ключ из превью (активна оранжевая рамка)
        if self.key:
            self.choose_and_replace_file(self.key)
            return
            
        # 2. Иначе проверяем выделение в плейлисте (эксклюзивность)
        if hasattr(self, 'playlist_widget') and self.playlist_widget:
            row = self.playlist_widget.table.currentRow()
            if row >= 0:
                name_item = self.playlist_widget.table.item(row, self.playlist_widget.COL_FILENAME)
                if name_item:
                    res_key = name_item.data(Qt.UserRole)
                    if res_key:
                        self.choose_and_replace_file(res_key)
            
    def choose_and_replace_file(self, key):
        """Внутренний метод выбора файла и вызова callback."""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import os
        from PyQt5.QtCore import QSettings
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseCustomDirectoryIcons
        
        settings = get_ui_settings()
        last_dir = settings.value("fm_last_import_dir", os.path.expanduser("~"))
        
        path, _ = QFileDialog.getOpenFileName(
            self,
            get_translation(self.current_language, 'select_new_audio_title'),
            self.last_audio_folder or last_dir or "",
            get_translation(self.current_language, 'audio_file_filter'),
            options=options
        )
        if path:
            settings.setValue("fm_last_import_dir", os.path.dirname(path))
            if self.on_replace_callback:
                self.on_replace_callback(key, path)
                self.update_playlist_item(key)
            else:
                error_msg = "⚠️ Cannot replace audio:\n• Audio player callback is not initialized"
                QMessageBox.warning(self, get_translation(self.current_language, 'error'), error_msg)

    def _on_playlist_replace_requested(self, res_key):
        """Замена файла из плейлиста."""
        self.choose_and_replace_file(res_key)

    def update_playlist_item(self, res_key):
        """Обновляет информацию об одном файле в плейлисте без перезагрузки всей таблицы."""
        if not self.miz_resource_manager or not hasattr(self, 'playlist_widget'):
            return
            
        # Если передан DictKey (из превью), разрешаем его до ResKey
        resolved_key = self.miz_resource_manager.resolve_to_res_key(res_key)
        
        # Получаем актуальные данные о файле
        all_files = self.miz_resource_manager.get_all_resource_files()
        file_info = next((f for f in all_files if f.get('res_key') == resolved_key), None)
        
        if file_info:
            # Обновляем точечно
            self.playlist_widget.update_item_by_key(resolved_key, file_info)

    def _on_playlist_download_requested(self, res_key):
        """Скачивание файла из плейлиста."""
        if self.on_download_callback:
            self.on_download_callback(res_key)

    def done(self, r):
        self.save_settings()  # Сохраняем ДО закрытия, пока окно ещё видимо
        self._stop_all_audio()
        super().done(r)

    def closeEvent(self, event):
        self.save_settings()  # Сохраняем ДО закрытия, пока окно ещё видимо
        self._stop_all_audio()
        super().closeEvent(event)

    def _stop_all_audio(self):
        
        try:
            if hasattr(pygame.mixer.music, 'stop'): pygame.mixer.music.stop()
            if hasattr(pygame.mixer.music, 'unload'): pygame.mixer.music.unload()
        except: pass
        self.audio_loaded = False
        if self.parent() and hasattr(self.parent(), 'set_active_audio_key'):
            self.parent().set_active_audio_key(None)

    def load_settings(self):
        """Загружает геометрию и состояние плейлиста."""
        settings = get_ui_settings()
        
        # Загружаем позицию и размер (вручную, т.к. saveGeometry не работает с FramelessWindowHint)
        saved_x = settings.value("audio_player_x", None)
        saved_y = settings.value("audio_player_y", None)
        saved_w = settings.value("audio_player_w", None)
        
        if saved_x is not None and saved_y is not None:
            self.move(int(saved_x), int(saved_y))
            if saved_w is not None:
                self.resize(int(saved_w), self.height())
        else:
            # Если позиции нет, центрируем по родителю
            if self.parent():
                p_geom = self.parent().geometry()
                self.move(p_geom.center() - self.rect().center())
        
        # Загружаем состояние плейлиста: если был открыт — открываем через toggle_playlist
        saved_visible = settings.value("audio_player_playlist_visible", "false")
        should_open = (saved_visible == "true" or saved_visible is True)
        if should_open:
            # _playlist_visible уже False из __init__, toggle_playlist инвертирует → станет True
            saved_h = settings.value("audio_player_height", self._player_base_height + self._playlist_height, type=int)
            self._last_expanded_height = saved_h
            self.toggle_playlist()

    def hideEvent(self, event):
        self.save_settings()
        super().hideEvent(event)

    def save_settings(self):
        """Сохраняет позицию, размер и состояние плейлиста."""
        settings = get_ui_settings()
        pos = self.pos()
        settings.setValue("audio_player_x", pos.x())
        settings.setValue("audio_player_y", pos.y())
        settings.setValue("audio_player_w", self.width())
        settings.setValue("audio_player_playlist_visible", self._playlist_visible)
        if self._playlist_visible:
            settings.setValue("audio_player_height", self.height())

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
        self.btn_back_width = 120
        self.btn_back_y_offset = 0 # Добавлен для гибкости

        # --- Добавляем верхнюю панель ---
        self.top_bar = QWidget(self)
        self.top_bar.setFixedHeight(36)
        self.top_bar.setStyleSheet("background-color: #3d4256; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        self.top_layout = QHBoxLayout(self.top_bar)
        self.top_layout.setContentsMargins(20, 0, 20, 0)

        self.win_close_btn = QPushButton("✕", self)
        self.win_close_btn.setFixedSize(30, 30)
        self.win_close_btn.setCursor(Qt.PointingHandCursor)
        self.win_close_btn.clicked.connect(self.close)
        self.win_close_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #aaaaaa; border: none; font-size: 18px; font-weight: bold; }
            QPushButton:hover { color: #ff9900; }
        """)
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
        self.label_1.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        
        self.edit_1 = QPlainTextEdit(self)
        self.setup_edit_style(self.edit_1)
        self.edit_1.textChanged.connect(self.on_text_1_changed)

        # Выпадающий список языков
        self.lang_label = QLabel(get_translation(self.lang, 'context_select_lang'), self)
        self.lang_label.setStyleSheet("color: #bbbbbb; font-size: 12px;")
        
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
        self.label_2.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        
        self.edit_2 = QPlainTextEdit(self)
        self.setup_edit_style(self.edit_2)
        self.edit_2.textChanged.connect(self.on_text_2_changed)

        # Заголовок окна (теперь в top_bar)
        self.title_label = QLabel(get_translation(self.lang, 'ai_context_title'), self)
        self.title_label.setStyleSheet(f"color: #ff9900; font-weight: bold; font-size: {self.title_label_font_size}px; background: transparent;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.top_layout.addWidget(self.title_label)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.win_close_btn)

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

        # Кнопка "Назад" (будет в нижней панели)
        self.btn_back = QPushButton(get_translation(self.lang, 'context_back_btn'), self)
        self.setup_white_button(self.btn_back)
        self.btn_back.clicked.connect(self.close)

        # Разделитель перед нижней панелью
        self.separator = QFrame(self)
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Plain)
        self.separator.setFixedHeight(1)
        self.separator.setStyleSheet("background-color: #777777; border: none;")

        # Нижняя панель
        self.bottom_bar = QWidget(self)
        self.bottom_bar.setFixedHeight(60)
        self.bottom_bar.setStyleSheet("background-color: #2b2b2b; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
        self.bottom_layout = QHBoxLayout(self.bottom_bar)
        self.bottom_layout.setContentsMargins(20, 0, 20, 0)
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.btn_back)
        self.bottom_layout.addStretch()

        self.update_positions()

    def setup_edit_style(self, edit):
        edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #2b2b2b;
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
                background-color: #3a3a3a;
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
                background-color: #3a3a3a;
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
        
        # Разделитель и Нижняя панель (с отступом 2px для рамки, как в других окнах с QVBoxLayout)
        self.top_bar.setGeometry(2, 2, w - 4, 36)
        self.separator.setGeometry(2, h - 63, w - 4, 1)
        self.bottom_bar.setGeometry(2, h - 62, w - 4, 60)

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
                elif event.type() in [QEvent.MouseButtonPress, QEvent.MouseButtonDblClick]:
                    return True # Поглощаем нажатие и двойной клик, чтобы не срабатывал dragging в CustomDialog
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
        self.setMinimumSize(750, 900)
        self.resize(750, 900)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        # Top bar (if needed, but InstructionsWindow didn't have one, adding consistency)
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

        self.win_close_btn = QPushButton("✕", self)
        self.win_close_btn.setFixedSize(30, 30)
        self.win_close_btn.setCursor(Qt.PointingHandCursor)
        self.win_close_btn.clicked.connect(self.accept)
        self.win_close_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #aaaaaa; border: none; font-size: 18px; font-weight: bold; }
            QPushButton:hover { color: #ff9900; }
        """)
        top_layout.addWidget(self.win_close_btn)
        layout.addWidget(top_bar)

        # Content area
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(25, 15, 25, 15)
        content_layout.setSpacing(15)
        
        # Текст заголовка (внутри контента)
        # title_label = QLabel(get_translation(lang, 'instructions_btn'))
        # title_label.setAlignment(Qt.AlignCenter)
        # title_label.setStyleSheet("color: #ff9900; font-weight: bold; font-size: 18px; background-color: transparent;")
        # content_layout.addWidget(title_label)
        
        # Область вкладок
        from PyQt5.QtWidgets import QTextBrowser, QTabWidget
        
        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setExpanding(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { 
                border: none; 
                background: transparent;
            }
            QTabBar::tab {
                background: #3d4256;
                color: #aaaaaa;
                height: 34px;
                min-width: 330px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #555555;
                color: #ff9900;
            }
            QTabBar::tab:hover:!selected {
                background: #4d5266;
                color: #ffffff;
            }
        """)
        
        browser_style = """
            QTextBrowser {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #777;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
                border-top-right-radius: 6px;
                margin: 0px;
            }
        """

        # Вкладка 1: Инструкция
        self.instruction_browser = QTextBrowser()
        self.instruction_browser.setReadOnly(True)
        self.instruction_browser.setStyleSheet(browser_style)
        
        # Вкладка 2: Руководство пользователя
        self.manual_browser = QTextBrowser()
        self.manual_browser.setReadOnly(True)
        self.manual_browser.setStyleSheet(browser_style)
        
        # Устанавливаем кастомные скроллбары
        try:
            from widgets import CustomScrollBar
            self.instruction_browser.setVerticalScrollBar(CustomScrollBar())
            self.manual_browser.setVerticalScrollBar(CustomScrollBar())
        except Exception:
            pass
            
        # Загружаем контент
        self.instruction_browser.setHtml(get_translation(lang, 'instruction_content'))
        self.manual_browser.setHtml(get_translation(lang, 'user_manual_content'))
        
        # Добавляем вкладки
        self.tab_widget.addTab(self.instruction_browser, get_translation(lang, 'tab_instruction'))
        self.tab_widget.addTab(self.manual_browser, get_translation(lang, 'tab_user_manual'))
        
        content_layout.addWidget(self.tab_widget)
        layout.addWidget(content_container)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #777777; border: none;")
        layout.addWidget(separator)

        # Нижняя панель
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(60)
        bottom_bar.setStyleSheet("background-color: #2b2b2b; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 0, 20, 0)
        
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
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #a3a3a3;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.close_btn)
        bottom_layout.addStretch()
        layout.addWidget(bottom_bar)

    def update_language(self, lang):
        """Обновляет текст в окне при смене языка интерфейса"""
        from localization import get_translation
        self.setWindowTitle(get_translation(lang, 'instructions_btn'))
        
        # Обновляем контент во вкладках
        self.instruction_browser.setHtml(get_translation(lang, 'instruction_content'))
        self.manual_browser.setHtml(get_translation(lang, 'user_manual_content'))
        
        # Обновляем названия вкладок
        self.tab_widget.setTabText(0, get_translation(lang, 'tab_instruction'))
        self.tab_widget.setTabText(1, get_translation(lang, 'tab_user_manual'))
        
        # Обновляем кнопку
        self.close_btn.setText(get_translation(lang, 'exit_btn'))


class DeleteConfirmDialog(CustomDialog):
    """Диалог подтверждения удаления локали с красной кнопкой ДА"""
    def __init__(self, locale_name, current_language, parent=None):
        super().__init__(parent)
        self.current_language = current_language
        self.locale_name = locale_name

        self.setWindowTitle(get_translation(self.current_language, 'delete_confirm_title'))
        self.setFixedSize(400, 200) # Немного увеличили высоту для футера

        # Основной layout с отступами для рамки
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        # 1. КОНТЕНТНАЯ ОБЛАСТЬ
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 25, 30, 15)
        content_layout.setSpacing(15)

        # Формируем сообщение
        full_msg = get_translation(self.current_language, 'delete_confirm_msg')
        parts = full_msg.split('{locale}')
        
        msg_container = QWidget()
        msg_container.setStyleSheet("background: transparent; border: none;")
        msg_h_layout = QHBoxLayout(msg_container)
        msg_h_layout.setContentsMargins(0, 0, 0, 0)
        msg_h_layout.setSpacing(0)
        msg_h_layout.addStretch()

        # Текст ДО названия
        if parts[0]:
            label_before = QLabel(parts[0])
            label_before.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px; background: transparent; border: none;")
            msg_h_layout.addWidget(label_before)
            
        # Само НАЗВАНИЕ (Оранжевое)
        label_name = QLabel(self.locale_name)
        label_name.setStyleSheet("color: #ff9900; font-weight: bold; font-size: 13px; background: transparent; border: none;")
        msg_h_layout.addWidget(label_name)
        
        # Текст ПОСЛЕ названия
        if len(parts) > 1 and parts[1]:
            label_after = QLabel(parts[1])
            label_after.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px; background: transparent; border: none;")
            msg_h_layout.addWidget(label_after)
            
        msg_h_layout.addStretch()
        content_layout.addStretch() # Центрируем по вертикали
        content_layout.addWidget(msg_container)
        content_layout.addStretch() # Центрируем по вертикали
        
        main_layout.addWidget(content_widget)

        # 2. РАЗДЕЛИТЕЛЬ
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #777777; border: none;")
        main_layout.addWidget(line)

        # 3. ФУТЕР (Темная панель)
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("QFrame { background-color: #2b2b2b; border: none; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(15, 0, 15, 0)
        footer_layout.setSpacing(15)

        # Красная кнопка ДА
        self.yes_btn = QPushButton(get_translation(self.current_language, 'yes_btn'))
        self.yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #e53935;
                color: #ffffff;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #c62828; }
            QPushButton:pressed { background-color: #b71c1c; }
        """)
        self.yes_btn.setFixedSize(120, 32)
        self.yes_btn.setCursor(Qt.PointingHandCursor)
        self.yes_btn.clicked.connect(self.accept)

        # Белая кнопка Отмена
        self.no_btn = QPushButton(get_translation(self.current_language, 'cancel_btn'))
        self.no_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:pressed { background-color: #d0d0d0; }
        """)
        self.no_btn.setFixedSize(120, 32)
        self.no_btn.setCursor(Qt.PointingHandCursor)
        self.no_btn.clicked.connect(self.reject)

        # Добавляем кнопки в футер (в ряд по центру)
        footer_layout.addStretch()
        footer_layout.addWidget(self.no_btn)
        footer_layout.addWidget(self.yes_btn)
        footer_layout.addStretch()
        
        main_layout.addWidget(footer)


class FilesWindow(CustomDialog):
    """Окно менеджера файлов"""
    def __init__(self, current_language, parent=None, shared_duration_cache=None):
        super().__init__(parent)
        self.current_language = current_language
        self.shared_duration_cache = shared_duration_cache
        self.setWindowTitle(get_translation(current_language, 'files_window_title'))
        
        # Адаптивный размер: пытаемся поставить 1400x900, но не более 90% от экрана
        from PyQt5.QtWidgets import QApplication
        screen_geo = QApplication.primaryScreen().availableGeometry()
        default_w = min(1400, int(screen_geo.width() * 0.9))
        default_h = min(900, int(screen_geo.height() * 0.9))
        
        self.setMinimumSize(min(1400, default_w), min(900, default_h))
        self.resize(default_w, default_h)
        
        # Установка иконки окна
        icon_path = resource_path("DSCTT.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Основной layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        # Верхняя панель (Заголовок + Кнопка закрытия)
        top_bar = QWidget()
        top_bar.setFixedHeight(36)
        top_bar.setStyleSheet("background-color: #3d4256; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        # Заголовок
        self.title_label = QLabel(self.windowTitle())
        self.title_label.setStyleSheet("color: #ff9900; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        top_layout.addWidget(self.title_label)
        
        top_layout.addStretch()
        
        # Кнопка закрытия
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.reject)
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
        top_layout.addWidget(self.close_btn)
        
        layout.addWidget(top_bar)
        
        # Основная область контента с FileManagerWidget
        content_area = QWidget()
        content_area.setStyleSheet("background-color: transparent; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(12, 12, 12, 3)
        
        from manager import FileManagerWidget
        self.file_manager_widget = FileManagerWidget(current_language, self, shared_duration_cache=self.shared_duration_cache)
        content_layout.addWidget(self.file_manager_widget)
        
        layout.addWidget(content_area)

    def set_data(self, miz_resource_manager, miz_path):
        """Передаёт данные ресурсов в FileManagerWidget."""
        self.file_manager_widget.set_data(miz_resource_manager, miz_path)

    def keyPressEvent(self, event):
        """Обработка нажатия Enter для открытия предпросмотра и предотвращения закрытия окна"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Всегда поглощаем Enter для этого окна, чтобы оно не закрылось через QDialog.keyPressEvent
            if hasattr(self, 'file_manager_widget'):
                table = self.file_manager_widget.table
                search = self.file_manager_widget.search_input
                # Если фокус на таблице или поиске - пытаемся открыть файл
                if table.hasFocus() or search.hasFocus():
                    current_idx = table.currentIndex()
                    if current_idx.isValid():
                        self.file_manager_widget._on_table_double_clicked(current_idx)
            event.accept()
            return

        super().keyPressEvent(event)

    def retranslate_ui(self, current_language):
        """Обновляет переводы интерфейса"""
        self.current_language = current_language
        self.setWindowTitle(get_translation(self.current_language, 'files_window_title'))
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.windowTitle())
        if hasattr(self, 'file_manager_widget'):
            self.file_manager_widget.retranslate_ui(current_language)

    def done(self, r):
        self._stop_all_audio()
        super().done(r)

    def closeEvent(self, event):
        self._stop_all_audio()
        super().closeEvent(event)

    def _stop_all_audio(self):
        """Остановка аудио в менеджере"""
        if hasattr(self, 'file_manager_widget'):
            try:
                # reset_ui=False, так как виджеты уже могут быть невалидны при закрытии
                self.file_manager_widget._stop_preview_audio(reset_ui=False)
            except:
                pass


class BriefingEdit(QPlainTextEdit):
    """Специальное поле ввода, которое прокручивается только если в фокусе.
    Если не в фокусе или достигнут предел прокрутки - пробрасывает событие родителю.
    """
    def wheelEvent(self, event):
        if not self.hasFocus():
            event.ignore()
            return
        
        # Проверяем, достигнут ли предел прокрутки
        vbar = self.verticalScrollBar()
        if (event.angleDelta().y() > 0 and vbar.value() == vbar.minimum()) or \
           (event.angleDelta().y() < 0 and vbar.value() == vbar.maximum()):
            event.ignore()
            return
            
        super().wheelEvent(event)


class BriefingWindow(CustomDialog):
    """Модальное окно Брифинга с 5 полями ввода и кнопками Сохранить / Отмена"""
    
    # Сигнал для перехода к ключу в основном окне
    jump_requested = pyqtSignal(str)
    
    # Минимальная и максимальная высота полей ввода (в строках)
    MIN_LINES = 3
    MAX_LINES = 20
    
    def __init__(self, current_language, parent=None):
        super().__init__(parent)
        self.current_language = current_language
        self.setWindowTitle(get_translation(current_language, 'briefing_window_title'))
        self.setMinimumSize(500, 400)
        self.resize(750, 850)
        
        # Ключи для 4 полей брифинга
        self._tab_keys = [
            'DictKey_descriptionText_', 
            'DictKey_descriptionRedTask_', 
            'DictKey_descriptionBlueTask_',
            'DictKey_descriptionNeutralsTask_'
        ]
        
        font_family = getattr(parent, 'preview_font_family', 'Segoe UI')
        font_size = getattr(parent, 'preview_font_size', 13)
        
        # Основной layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        # Верхняя панель (Заголовок + Кнопка закрытия)
        top_bar = QWidget()
        top_bar.setFixedHeight(36)
        top_bar.setStyleSheet("background-color: #3d4256; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        # Заголовок
        self.title_label = QLabel(self.windowTitle())
        self.title_label.setStyleSheet("color: #ff9900; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        self.title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        top_layout.addWidget(self.title_label)
        
        top_layout.addStretch()
        
        # Кнопка закрытия → Отмена
        self.close_btn = QPushButton("✕", top_bar)
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.reject)
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
        top_layout.addWidget(self.close_btn)
        
        layout.addWidget(top_bar)
        
        # === Область контента с прокруткой ===
        from widgets import CustomScrollBar
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBar(CustomScrollBar())
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 10)
        scroll_layout.setSpacing(10)
        scroll_layout.setAlignment(Qt.AlignTop)
        
        # Общий стиль для редакторов
        editor_style = f"""
            QPlainTextEdit {{
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 4px 6px;
                font-family: '{font_family}';
                font-size: {font_size}pt;
            }}
            QPlainTextEdit:focus {{
                border-color: #ff9900;
            }}
            QMenu {{
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #777;
            }}
            QMenu::item {{
                padding: 4px 20px;
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: #ff9900;
                color: #000000;
            }}
            QMenu::item:disabled {{
                color: #808080;
            }}
        """
        
        # 1. Поле "Название миссии" (как ссылка)
        self.mission_name_label = ClickableLabel(get_translation(current_language, 'briefing_mission_name_label'))
        self.mission_name_label.setStyleSheet("""
            ClickableLabel {
                color: #ff9900; 
                font-weight: bold; 
                font-size: 13px; 
                background: transparent;
                text-decoration: none;
            }
            ClickableLabel:hover {
                text-decoration: underline;
            }
        """)
        self.mission_name_label.clicked.connect(lambda: self.jump_requested.emit('DictKey_sortie_'))
        scroll_layout.addWidget(self.mission_name_label)

        self.mission_name_edit = BriefingEdit()
        self.mission_name_edit.setFixedHeight(32)
        self.mission_name_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.mission_name_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.mission_name_edit.setLineWrapMode(QPlainTextEdit.NoWrap)
        
        # Блокируем Enter для названия миссии
        original_mne_keyPressEvent = self.mission_name_edit.keyPressEvent
        def mission_name_key_press(event):
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                event.ignore()
                return
            original_mne_keyPressEvent(event)
        self.mission_name_edit.keyPressEvent = mission_name_key_press

        self.mission_name_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 2px 4px;
                font-family: '{font_family}';
                font-size: {font_size}pt;
            }}
            QPlainTextEdit:focus {{
                border-color: #ff9900;
            }}
            QMenu {{
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #777;
            }}
            QMenu::item {{
                padding: 4px 20px;
                background-color: transparent;
            }}
            QMenu::item:selected {{
                background-color: #ff9900;
                color: #000000;
            }}
            QMenu::item:disabled {{
                color: #808080;
            }}
        """)
        scroll_layout.addWidget(self.mission_name_edit)

        # 2. Четыре поля брифинга с подписями
        briefing_label_keys = [
            'briefing_tab_description',
            'briefing_tab_red_task',
            'briefing_tab_blue_task',
            'briefing_tab_neutrals_task',
        ]
        
        self.briefing_labels = []
        self.briefing_edits = []
        
        for i, label_key in enumerate(briefing_label_keys):
            # Подпись (как ссылка)
            label = ClickableLabel(get_translation(current_language, label_key))
            
            # Специфические цвета для задач сторон
            if 'red_task' in label_key:
                color = "#ff3333"
            elif 'blue_task' in label_key:
                color = "#3366ff"
            elif 'neutrals_task' in label_key:
                color = "#bdbdbd"
            elif 'tab_description' in label_key:
                color = "#ffffff"
            else:
                color = "#ff9900"
                
            label.setStyleSheet(f"""
                ClickableLabel {{
                    color: {color}; 
                    font-weight: bold; 
                    font-size: 13px; 
                    background: transparent;
                    text-decoration: none;
                }}
                ClickableLabel:hover {{
                    text-decoration: underline;
                }}
            """)
            
            # При нажатии посылаем соответствующий префикс
            prefix = self._tab_keys[i]
            label.clicked.connect(lambda p=prefix: self.jump_requested.emit(p))
            
            scroll_layout.addWidget(label)
            self.briefing_labels.append(label)
            
            # Поле ввода
            edit = BriefingEdit()
            edit.setVerticalScrollBar(CustomScrollBar(edit))
            edit.setStyleSheet(editor_style)
            edit.setContextMenuPolicy(Qt.DefaultContextMenu)
            # Динамическая высота: подключаем textChanged
            edit.textChanged.connect(lambda ed=edit: self._adjust_editor_height(ed))
            scroll_layout.addWidget(edit)
            self.briefing_edits.append(edit)

        
        scroll_layout.addStretch()
        
        self.scroll_area.setWidget(scroll_content)
        layout.addWidget(self.scroll_area, 1)
        
        # 3. Кнопки Сохранить / Отмена (под scroll_area, внизу окна)
        # Разделительная полоса перед нижней панелью
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #777777; border: none;")
        layout.addWidget(separator)

        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(60)
        bottom_bar.setStyleSheet("background-color: #2b2b2b; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 0, 20, 0)
        bottom_layout.setSpacing(15)
        
        bottom_layout.addStretch()
        
        cancel_btn = QPushButton(get_translation(current_language, 'cancel_btn'))
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedSize(120, 32)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #a3a3a3;
            }
        """)
        bottom_layout.addWidget(cancel_btn)
        
        save_btn_text = get_translation(current_language, 'save_btn').replace('💾', '').strip()
        save_btn = QPushButton(save_btn_text)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedSize(120, 32)
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
        """)
        bottom_layout.addWidget(save_btn)
        
        bottom_layout.addStretch()
        
        # Ручка для изменения размера
        self.size_grip = QSizeGrip(self)
        self.size_grip.setFixedSize(16, 16)
        bottom_layout.addWidget(self.size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        layout.addWidget(bottom_bar)

    def showEvent(self, event):
        """Пересчитываем высоты при показе окна (шрифт уже финальный)"""
        super().showEvent(event)
        self._adjust_all_heights()

    def _adjust_editor_height(self, editor):
        """Подстраивает высоту поля: мин 3 строки, макс 20 строк (учитывает перенос строк)"""
        fm = editor.fontMetrics()
        line_h = fm.lineSpacing()
        
        # Считаем визуальные строки (с учётом переноса), а не логические блоки
        doc = editor.document()
        visual_lines = 0
        block = doc.begin()
        while block.isValid():
            layout = block.layout()
            if layout:
                visual_lines += max(1, layout.lineCount())
            else:
                visual_lines += 1
            block = block.next()
        
        line_count = max(self.MIN_LINES, min(self.MAX_LINES, visual_lines))
        # document margin * 2 + CSS padding + border + запас
        extra = int(doc.documentMargin()) * 2 + 12
        editor.setFixedHeight(line_count * line_h + extra)

    def _adjust_all_heights(self):
        """Подстраивает высоту всех 4 полей"""
        for edit in self.briefing_edits:
            self._adjust_editor_height(edit)

    def load_data(self, mission_name, tab_texts):
        """Загружает данные при открытии диалога.
        mission_name: str — название миссии
        tab_texts: dict {0: str, 1: str, 2: str, 3: str} — тексты полей
        """
        self.mission_name_edit.blockSignals(True)
        self.mission_name_edit.setPlainText(mission_name)
        self.mission_name_edit.blockSignals(False)
        
        for i, edit in enumerate(self.briefing_edits):
            edit.blockSignals(True)
            edit.setPlainText(tab_texts.get(i, ''))
            edit.blockSignals(False)
        
        # Сохраняем начальные значения для проверки изменений при закрытии
        self._original_mission_name = mission_name
        self._original_tab_texts = dict(tab_texts)
        
        # Подстраиваем высоту после загрузки данных
        self._adjust_all_heights()

    def reject(self):
        """Переопределяем закрытие окна для проверки несохраненных изменений"""
        # Проверяем были ли изменения
        if hasattr(self, '_original_mission_name') and hasattr(self, '_original_tab_texts'):
            current_name, current_tabs = self.get_result()
            
            # Сравниваем
            changed = False
            if current_name != self._original_mission_name:
                changed = True
            else:
                for i in range(len(self.briefing_edits)):
                    if current_tabs.get(i, '') != self._original_tab_texts.get(i, ''):
                        changed = True
                        break
            
            if changed:
                dialog = CustomDialog(self)
                dialog.bg_color = QColor("#333333")
                dialog.setWindowTitle(get_translation(self.current_language, 'confirm_exit_title'))
                dialog.setFixedSize(440, 220)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
                
                content_style = """
                    QWidget#ConfirmContent {
                        background-color: #333333;
                        border: none;
                        border-radius: 9px;
                    }
                    QLabel {
                        color: #ffffff;
                        font-weight: bold;
                        font-size: 14px;
                        background-color: transparent;
                        border: none;
                    }
                    QPushButton#yesBtn {
                        background-color: #ff3333;
                        color: #ffffff;
                        border: none;
                        padding: 10px 25px;
                        border-radius: 18px;
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
                        background-color: #ffffff;
                        color: #000000;
                        border: none;
                        padding: 10px 25px;
                        border-radius: 18px;
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
                layout.setContentsMargins(1, 1, 1, 1)
                
                container = QWidget()
                container.setObjectName("ConfirmContent")
                container.setStyleSheet(content_style)
                container_layout = QVBoxLayout(container)
                container_layout.setContentsMargins(30, 30, 30, 30)
                container_layout.setSpacing(20)
                
                msg_label = QLabel(get_translation(self.current_language, 'briefing_exit_msg'))
                msg_label.setAlignment(Qt.AlignCenter)
                msg_label.setWordWrap(True)
                
                yes_btn = QPushButton(get_translation(self.current_language, 'briefing_exit_yes'))
                yes_btn.setObjectName("yesBtn")
                yes_btn.setCursor(Qt.PointingHandCursor)
                
                no_btn = QPushButton(get_translation(self.current_language, 'briefing_exit_no'))
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
                
                if dialog.exec_() != QDialog.Accepted:
                    return # Отменяем закрытие
        
        super().reject()

    def get_result(self):
        """Возвращает результат редактирования.
        Returns: (mission_name: str, tab_texts: dict {0: str, 1: str, 2: str, 3: str})
        """
        mission_name = self.mission_name_edit.toPlainText()
        tab_texts = {}
        for i, edit in enumerate(self.briefing_edits):
            tab_texts[i] = edit.toPlainText()
        return mission_name, tab_texts

    def keyPressEvent(self, event):
        """Предотвращаем закрытие диалога по Enter в полях ввода"""
        from PyQt5.QtCore import Qt
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if hasattr(self, 'mission_name_edit') and self.mission_name_edit.hasFocus():
                event.accept()
                return
            # Проверяем все 4 поля брифинга
            for edit in self.briefing_edits:
                if edit.hasFocus():
                    event.accept()
                    return
        super().keyPressEvent(event)

    def retranslate_ui(self, current_language):
        """Обновляет переводы интерфейса"""
        self.current_language = current_language
        self.setWindowTitle(get_translation(self.current_language, 'briefing_window_title'))
        if hasattr(self, 'title_label'):
            self.title_label.setText(self.windowTitle())
        if hasattr(self, 'mission_name_label'):
            self.mission_name_label.setText(get_translation(self.current_language, 'briefing_mission_name_label'))
        label_keys = [
            'briefing_tab_description', 
            'briefing_tab_red_task', 
            'briefing_tab_blue_task',
            'briefing_tab_neutrals_task'
        ]
        for i, key in enumerate(label_keys):
            if i < len(self.briefing_labels):
                label = self.briefing_labels[i]
                label.setText(get_translation(self.current_language, key))
                
                # Сохраняем цветовое разделение при смене языка
                if 'red_task' in key:
                    color = "#ff3333"
                elif 'blue_task' in key:
                    color = "#3366ff"
                elif 'neutrals_task' in key:
                    color = "#bdbdbd"
                elif 'tab_description' in key:
                    color = "#ffffff"
                else:
                    color = "#ff9900"
                label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px; background: transparent;")


class SettingsWindow(CustomDialog):
    """Окно Настроек (минималистичный вариант)"""
    def __init__(self, current_language, parent=None):
        super().__init__(parent)
        self.current_language = current_language
        self.parent_window = parent
        self.setWindowTitle(get_translation(self.current_language, 'settings_window_title'))
        # Увеличиваем высоту в 2 раза, делаем окно растягиваемым, но с минимальным размером
        self.setMinimumSize(600, 720)
        self.resize(600, 720)

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

        # === Ряд 0: Цвета закладок ===
        row_bookmarks = QWidget()
        row_bookmarks_layout = QHBoxLayout(row_bookmarks)
        row_bookmarks_layout.setContentsMargins(5, 0, 5, 0)
        row_bookmarks_layout.setSpacing(10)
        
        self.bookmark_colors_label = QLabel(get_translation(self.current_language, 'bookmark_colors_label'))
        self.bookmark_colors_label.setStyleSheet('color: #ddd; background: transparent;')
        row_bookmarks_layout.addWidget(self.bookmark_colors_label)
        row_bookmarks_layout.addStretch()
        
        icon_style = "color: #fff; font-size: 14px; font-weight: bold; background: transparent;"
        
        # Star
        lbl_star = QLabel("★")
        lbl_star.setStyleSheet(icon_style)
        self.bookmark_star_preview = QLabel()
        self.bookmark_star_preview.setFixedSize(22, 22)
        self.bookmark_star_preview.setCursor(Qt.PointingHandCursor)
        self.bookmark_star_preview.mousePressEvent = lambda e: self.open_color_dialog('bookmark_star')
        row_bookmarks_layout.addWidget(lbl_star)
        row_bookmarks_layout.addWidget(self.bookmark_star_preview)
        
        # Alert
        lbl_alert = QLabel("!")
        lbl_alert.setStyleSheet(icon_style)
        self.bookmark_alert_preview = QLabel()
        self.bookmark_alert_preview.setFixedSize(22, 22)
        self.bookmark_alert_preview.setCursor(Qt.PointingHandCursor)
        self.bookmark_alert_preview.mousePressEvent = lambda e: self.open_color_dialog('bookmark_alert')
        row_bookmarks_layout.addWidget(lbl_alert)
        row_bookmarks_layout.addWidget(self.bookmark_alert_preview)

        # Question
        lbl_question = QLabel("?")
        lbl_question.setStyleSheet(icon_style)
        self.bookmark_question_preview = QLabel()
        self.bookmark_question_preview.setFixedSize(22, 22)
        self.bookmark_question_preview.setCursor(Qt.PointingHandCursor)
        self.bookmark_question_preview.mousePressEvent = lambda e: self.open_color_dialog('bookmark_question')
        row_bookmarks_layout.addWidget(lbl_question)
        row_bookmarks_layout.addWidget(self.bookmark_question_preview)
        
        # Opacity slider
        self.bookmark_opacity_label = QLabel(get_translation(self.current_language, 'bookmark_opacity_label'))
        self.bookmark_opacity_label.setStyleSheet('color: #ddd; background: transparent;')
        row_bookmarks_layout.addWidget(self.bookmark_opacity_label)
        
        from PyQt5.QtWidgets import QSlider
        self.bookmark_opacity_slider = QSlider(Qt.Horizontal)
        self.bookmark_opacity_slider.setRange(0, 100)
        self.bookmark_opacity_slider.setFixedWidth(80)
        self.bookmark_opacity_slider.setCursor(Qt.PointingHandCursor)
        self.bookmark_opacity_slider.setStyleSheet('''
            QSlider { background: transparent; border: none; }
            QSlider:focus { border: none; outline: none; }
            QSlider::groove:horizontal { border: 1px solid #444; background: #222; height: 8px; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #ff9900; border: 1px solid #444; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #fff; border: 1px solid #5c5c5c; width: 14px; margin-top: -3px; margin-bottom: -3px; border-radius: 7px; }
        ''')
        row_bookmarks_layout.addWidget(self.bookmark_opacity_slider)
        
        self.bookmark_opacity_val_label = QLabel("70%")
        self.bookmark_opacity_val_label.setFixedWidth(35)
        self.bookmark_opacity_val_label.setStyleSheet('color: #ff9900; background: transparent; font-weight: bold;')
        row_bookmarks_layout.addWidget(self.bookmark_opacity_val_label)
        
        self.bookmark_opacity_slider.valueChanged.connect(lambda v: self.bookmark_opacity_val_label.setText(f"{v}%"))
        
        row_bookmarks.setFixedHeight(28)
        content_layout.addWidget(row_bookmarks, 0, Qt.AlignTop)

        # --- Разделитель между закладками и фоном ---
        line_bookmarks = QFrame()
        line_bookmarks.setFrameShape(QFrame.HLine)
        line_bookmarks.setFrameShadow(QFrame.Plain)
        line_bookmarks.setFixedHeight(1)
        line_bookmarks.setStyleSheet("background-color: #777777; border: none;")
        content_layout.addWidget(line_bookmarks)

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
        line_fonts.setStyleSheet("background-color: #777777; border: none;")
        content_layout.addWidget(line_fonts)

        # === Ряд: Цвет изменённого шрифта ===
        row_text_mod = QWidget()
        row_text_mod_layout = QHBoxLayout(row_text_mod)
        row_text_mod_layout.setContentsMargins(5, 0, 5, 0)
        row_text_mod_layout.setSpacing(10)
        
        mod_font_label = get_translation(self.current_language, 'theme_text_modified_label')
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
        
        saved_font_label = get_translation(self.current_language, 'theme_text_saved_label')
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

        # === Ряд: Цвет сессионного (изменённого и сохранённого) шрифта ===
        row_text_session = QWidget()
        row_text_session_layout = QHBoxLayout(row_text_session)
        row_text_session_layout.setContentsMargins(5, 0, 5, 0)
        row_text_session_layout.setSpacing(10)
        
        session_font_label = get_translation(self.current_language, 'theme_text_session_label')
        self.theme_text_session_label = QLabel(session_font_label)
        self.theme_text_session_label.setStyleSheet('color: #ddd; background: transparent;')
        row_text_session_layout.addWidget(self.theme_text_session_label)
        row_text_session_layout.addStretch()
        
        self.theme_text_session_preview = QLabel()
        self.theme_text_session_preview.setFixedSize(22, 22)
        self.theme_text_session_preview.setCursor(Qt.PointingHandCursor)
        self.theme_text_session_preview.mousePressEvent = lambda e: self.open_color_dialog('text_session')
        row_text_session_layout.addWidget(self.theme_text_session_preview)
        
        row_text_session.setFixedHeight(28)
        content_layout.addWidget(row_text_session, 0, Qt.AlignTop)

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
        line0.setStyleSheet("background-color: #777777; border: none;")
        content_layout.addWidget(line0)

        # Compact row: Toggle + label + color preview (clickable)
        row = QWidget()
        row_layout = QHBoxLayout(row)
        # Боковой отступ 5px слева, 5px справа
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
        line1.setStyleSheet("background-color: #777777; border: none;")
        content_layout.addWidget(line1)

        # === Второй ряд: Включить логи ===
        row2 = QWidget()
        row2_layout = QHBoxLayout(row2)
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
                font-size: 12px;
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

        # --- Смещение и Многооконный режим ---
        row2_layout.addSpacing(20)
        
        self.multi_window_toggle = ToggleSwitch()
        row2_layout.addWidget(self.multi_window_toggle)
        
        self.multi_window_label = QLabel(get_translation(self.current_language, 'settings_multi_window_mode'))
        self.multi_window_label.setStyleSheet('color: #ddd; background: transparent;')
        row2_layout.addWidget(self.multi_window_label)
        
        if self.parent_window and hasattr(self.parent_window, 'register_custom_tooltip'):
            self.parent_window.register_custom_tooltip(self.multi_window_label, get_translation(self.current_language, 'tooltip_multi_window_mode'))
        else:
            self.multi_window_label.setToolTip(get_translation(self.current_language, 'tooltip_multi_window_mode'))

        row2.setFixedHeight(28)
        row2_layout.addStretch()
        content_layout.addWidget(row2, 0, Qt.AlignTop)

        # --- Разделитель после второй строки ---
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Plain)
        line2.setFixedHeight(1)
        line2.setStyleSheet("background-color: #777777; border: none;")
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
        standard_locales = ['DEFAULT', 'EN', 'RU', 'FR', 'DE', 'CN', 'CS', 'ES', 'JP', 'KO']
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
        line3.setStyleSheet("background-color: #777777; border: none;")
        content_layout.addWidget(line3)

        # === Ряд 4: Пропускать окно выбора локали ===
        row4 = QWidget()
        row4_layout = QHBoxLayout(row4)
        row4_layout.setContentsMargins(5, 0, 5, 0)
        row4_layout.setSpacing(10)

        self.skip_locale_toggle = ToggleSwitch()
        row4_layout.addWidget(self.skip_locale_toggle)

        self.skip_locale_label = QLabel(get_translation(self.current_language, 'settings_skip_locale_dialog'))
        self.skip_locale_label.setStyleSheet('color: #ddd; background: transparent;')
        row4_layout.addWidget(self.skip_locale_label)
        
        row4.setFixedHeight(28)
        row4_layout.addStretch()
        content_layout.addWidget(row4, 0, Qt.AlignTop)

        # === Ряд 5: Вспомогательное поле установки локали по умолчанию ===
        row5 = QWidget()
        row5_layout = QHBoxLayout(row5)
        row5_layout.setContentsMargins(5, 0, 5, 0)
        row5_layout.setSpacing(10)

        self.default_open_locale_label = QLabel(get_translation(self.current_language, 'settings_default_open_locale'))
        self.default_open_locale_label.setStyleSheet('color: #ddd; background: transparent;')
        row5_layout.addWidget(self.default_open_locale_label)

        row5_layout.addStretch()

        self.default_open_locale_combo = QComboBox()
        self.default_open_locale_combo.addItems(standard_locales)
        self.default_open_locale_combo.setFixedWidth(120)
        self.default_open_locale_combo.setStyleSheet(combo_style)
        row5_layout.addWidget(self.default_open_locale_combo)

        row5.setFixedHeight(28)
        content_layout.addWidget(row5, 0, Qt.AlignTop)

        # --- Разделитель перед областью поиска ---
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Plain)
        line3.setFixedHeight(1)
        line3.setStyleSheet("background-color: #777777; border: none;")
        content_layout.addWidget(line3)

        # === Ряд 4: Область поиска ===
        search_scope_label_text = get_translation(self.current_language, 'search_scope_label')
        self.search_scope_title = QLabel(search_scope_label_text)
        self.search_scope_title.setStyleSheet('color: #ddd; background: transparent; font-weight: bold; margin-top: 5px;')
        content_layout.addWidget(self.search_scope_title)

        # Контейнер для чекбоксов (горизонтальный ряд)
        scope_container = QWidget()
        scope_layout = QHBoxLayout(scope_container)
        scope_layout.setContentsMargins(5, 0, 5, 0)
        scope_layout.setSpacing(10)

        self.scope_orig_cb = SearchCheckBox(get_translation(self.current_language, 'scope_original'))
        self.scope_ref_cb = SearchCheckBox(get_translation(self.current_language, 'scope_reference'))
        self.scope_edit_cb = SearchCheckBox(get_translation(self.current_language, 'scope_editor'))
        self.scope_audio_cb = SearchCheckBox(get_translation(self.current_language, 'scope_audio'))

        scope_layout.addWidget(self.scope_orig_cb)
        scope_layout.addWidget(self.scope_ref_cb)
        scope_layout.addWidget(self.scope_edit_cb)
        scope_layout.addWidget(self.scope_audio_cb)
        scope_layout.addStretch() # Прижимаем чекбоксы влево

        content_layout.addWidget(scope_container)

        # === Ряд 6: Регистр поиска ===
        row_case = QWidget()
        row_case_layout = QHBoxLayout(row_case)
        row_case_layout.setContentsMargins(5, 0, 5, 0)
        row_case_layout.setSpacing(10)
        
        self.search_case_sensitive_toggle = ToggleSwitch()
        row_case_layout.addWidget(self.search_case_sensitive_toggle)
        
        self.search_case_sensitive_label = QLabel(get_translation(self.current_language, 'case_sensitive_search'))
        self.search_case_sensitive_label.setStyleSheet('color: #ddd; background: transparent;')
        row_case_layout.addWidget(self.search_case_sensitive_label)
        
        row_case.setFixedHeight(28)
        row_case_layout.addStretch()
        content_layout.addWidget(row_case, 0, Qt.AlignTop)

        # --- Разделитель после области поиска ---
        line4 = QFrame()
        line4.setFrameShape(QFrame.HLine)
        line4.setFrameShadow(QFrame.Plain)
        line4.setFixedHeight(1)
        line4.setStyleSheet("background-color: #777777; border: none;")
        content_layout.addWidget(line4)

        # === Ряд: Умная вставка с маркерами ===
        row_smart_paste = QWidget()
        row_smart_paste_layout = QHBoxLayout(row_smart_paste)
        row_smart_paste_layout.setContentsMargins(5, 0, 5, 0)
        row_smart_paste_layout.setSpacing(10)

        self.smart_paste_toggle = ToggleSwitch()
        row_smart_paste_layout.addWidget(self.smart_paste_toggle)

        self.smart_paste_label = QLabel(get_translation(self.current_language, 'settings_smart_paste_enabled'))
        self.smart_paste_label.setStyleSheet('color: #ddd; background: transparent;')
        row_smart_paste_layout.addWidget(self.smart_paste_label)
        
        if self.parent_window and hasattr(self.parent_window, 'register_custom_tooltip'):
            self.parent_window.register_custom_tooltip(self.smart_paste_label, get_translation(self.current_language, 'tooltip_smart_paste'))
        else:
            self.smart_paste_label.setToolTip(get_translation(self.current_language, 'tooltip_smart_paste'))

        row_smart_paste.setFixedHeight(28)
        row_smart_paste_layout.addStretch()
        content_layout.addWidget(row_smart_paste, 0, Qt.AlignTop)

        # Заполняем пустое пространство в скролле, чтобы настройки были сверху
        content_layout.addStretch()
        
        self.scroll_area.setWidget(scroll_content)
        layout.addWidget(self.scroll_area)

        # Разделительная полоса перед нижней панелью
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #777777; border: none;")
        layout.addWidget(separator)

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
                font-size: 12px;
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
                font-size: 12px;
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
                font-size: 12px;
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
            col = getattr(self.parent_window, 'highlight_empty_color', '#434343')
            logs = getattr(self.parent_window, 'debug_logs_enabled', False)
            self.highlight_toggle.setChecked(val)
            self.enable_logs_toggle.setChecked(logs)
            self.multi_window_toggle.setChecked(getattr(self.parent_window, 'multi_window_enabled', False))
            self.color_preview.setStyleSheet(f'background-color: {col}; border: 1px solid #777;')
            
            # Загружаем цвета темы (fallback — встроенные значения)
            c_even = getattr(self.parent_window, 'theme_bg_even', '#393939')
            c_odd = getattr(self.parent_window, 'theme_bg_odd', '#2f2f2f')
            self.theme_bg_even_preview.setStyleSheet(f'background-color: {c_even}; border: 1px solid #777;')
            self.theme_bg_odd_preview.setStyleSheet(f'background-color: {c_odd}; border: 1px solid #777;')

            # Загружаем настройки закладок
            c_bm_star = getattr(self.parent_window, 'bookmark_bg_star', '#423400')
            c_bm_question = getattr(self.parent_window, 'bookmark_bg_question', '#0d4200')
            c_bm_alert = getattr(self.parent_window, 'bookmark_bg_alert', '#420000')
            op_bm = getattr(self.parent_window, 'bookmark_bg_opacity', 0.60)
            
            self.bookmark_star_preview.setStyleSheet(f'background-color: {c_bm_star}; border: 1px solid #777;')
            self.bookmark_question_preview.setStyleSheet(f'background-color: {c_bm_question}; border: 1px solid #777;')
            self.bookmark_alert_preview.setStyleSheet(f'background-color: {c_bm_alert}; border: 1px solid #777;')
            self.bookmark_opacity_slider.setValue(int((1.0 - op_bm) * 100))
            self.bookmark_opacity_val_label.setText(f"{int((1.0 - op_bm) * 100)}%")

            # Загружаем шрифт (fallback — встроенные значения)
            c_mod = getattr(self.parent_window, 'theme_text_modified', '#ff6666')
            c_saved = getattr(self.parent_window, 'theme_text_saved', '#2ecc71')
            self.theme_text_modified_preview.setStyleSheet(f'background-color: {c_mod}; border: 1px solid #777;')
            self.theme_text_saved_preview.setStyleSheet(f'background-color: {c_saved}; border: 1px solid #777;')
            c_session = getattr(self.parent_window, 'theme_text_session', '#bbf324')
            self.theme_text_session_preview.setStyleSheet(f'background-color: {c_session}; border: 1px solid #777;')

            # Загружаем reference locale
            ref_locale = getattr(self.parent_window, 'settings_reference_locale', 'DEFAULT')
            idx = self.reference_locale_combo.findText(ref_locale)
            if idx >= 0:
                self.reference_locale_combo.setCurrentIndex(idx)
            else:
                self.reference_locale_combo.setCurrentText(ref_locale)

            # Загружаем настройку регистра
            self.search_case_sensitive_toggle.setChecked(getattr(self.parent_window, 'search_case_sensitive', False))

            # Загружаем шрифт предпросмотра
            f_family = getattr(self.parent_window, 'preview_font_family', 'Arial')
            f_size = str(getattr(self.parent_window, 'preview_font_size', 11))
            
            idx_f = self.preview_font_family_combo.findText(f_family)
            if idx_f >= 0: self.preview_font_family_combo.setCurrentIndex(idx_f)
            
            idx_s = self.preview_font_size_combo.findText(f_size)
            if idx_s >= 0: self.preview_font_size_combo.setCurrentIndex(idx_s)

            # Загружаем область поиска
            self.scope_orig_cb.setChecked(getattr(self.parent_window, 'search_scope_original', True))
            self.scope_ref_cb.setChecked(getattr(self.parent_window, 'search_scope_reference', True))
            self.scope_edit_cb.setChecked(getattr(self.parent_window, 'search_scope_editor', True))
            self.scope_audio_cb.setChecked(getattr(self.parent_window, 'search_scope_audio', True))
            
            # Загружаем опции локали
            self.skip_locale_toggle.setChecked(getattr(self.parent_window, 'skip_locale_dialog', False))
            
            # Загружаем настройку Smart Paste
            self.smart_paste_toggle.setChecked(getattr(self.parent_window, 'smart_paste_enabled', True))
            
            def_open_locale = getattr(self.parent_window, 'default_open_locale', 'DEFAULT')
            idx_def = self.default_open_locale_combo.findText(def_open_locale)
            if idx_def >= 0:
                self.default_open_locale_combo.setCurrentIndex(idx_def)
            else:
                self.default_open_locale_combo.setCurrentText(def_open_locale)

            # save snapshot of parent's current values so Cancel can restore them
            try:
                self._orig_parent_values = {
                    'highlight_empty_fields': bool(getattr(self.parent_window, 'highlight_empty_fields', True)),
                    'highlight_empty_color': str(getattr(self.parent_window, 'highlight_empty_color', '#434343')),
                    'debug_logs_enabled': bool(getattr(self.parent_window, 'debug_logs_enabled', False)),
                    'theme_bg_even': str(getattr(self.parent_window, 'theme_bg_even', '#393939')),
                    'theme_bg_odd': str(getattr(self.parent_window, 'theme_bg_odd', '#2f2f2f')),
                    'theme_text_modified': str(getattr(self.parent_window, 'theme_text_modified', '#ff6666')),
                    'theme_text_saved': str(getattr(self.parent_window, 'theme_text_saved', '#2ecc71')),
                    'theme_text_session': str(getattr(self.parent_window, 'theme_text_session', '#bbf324')),
                    'reference_locale': str(getattr(self.parent_window, 'settings_reference_locale', 'DEFAULT')),
                    'skip_locale_dialog': bool(getattr(self.parent_window, 'skip_locale_dialog', False)),
                    'default_open_locale': str(getattr(self.parent_window, 'default_open_locale', 'DEFAULT')),
                    'preview_font_family': str(getattr(self.parent_window, 'preview_font_family', 'Consolas')),
                    'preview_font_size': int(getattr(self.parent_window, 'preview_font_size', 10)),
                    'multi_window_enabled': bool(getattr(self.parent_window, 'multi_window_enabled', False)),
                    'search_scope_original': bool(getattr(self.parent_window, 'search_scope_original', True)),
                    'search_scope_reference': bool(getattr(self.parent_window, 'search_scope_reference', True)),
                    'search_scope_editor': bool(getattr(self.parent_window, 'search_scope_editor', True)),
                    'search_scope_audio': bool(getattr(self.parent_window, 'search_scope_audio', True)),
                    'smart_paste_enabled': bool(getattr(self.parent_window, 'smart_paste_enabled', True))
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
            # Defaults: highlight enabled, color #434343, logs disabled
            # Block signals to avoid emitting toggled and triggering any external handlers
            try:
                self.highlight_toggle.blockSignals(True)
                self.enable_logs_toggle.blockSignals(True)
            except Exception:
                pass
            try:
                self.highlight_toggle.setChecked(True)
                self.enable_logs_toggle.setChecked(False)
            finally:
                try:
                    self.highlight_toggle.blockSignals(False)
                    self.enable_logs_toggle.blockSignals(False)
                    self.multi_window_toggle.blockSignals(False)
                except Exception:
                    pass
            # Update color preview (no signals expected)
            self.color_preview.setStyleSheet('background-color: #434343; border: 1px solid #777;')
            self.theme_bg_even_preview.setStyleSheet('background-color: #393939; border: 1px solid #777;')
            self.theme_bg_odd_preview.setStyleSheet('background-color: #2f2f2f; border: 1px solid #777;')
            self.theme_text_modified_preview.setStyleSheet('background-color: #ff6666; border: 1px solid #777;')
            self.theme_text_saved_preview.setStyleSheet('background-color: #2ecc71; border: 1px solid #777;')
            self.theme_text_session_preview.setStyleSheet('background-color: #bbf324; border: 1px solid #777;')
            
            # Reset bookmarks
            self.bookmark_star_preview.setStyleSheet('background-color: #423400; border: 1px solid #777;')
            self.bookmark_question_preview.setStyleSheet('background-color: #0d4200; border: 1px solid #777;')
            self.bookmark_alert_preview.setStyleSheet('background-color: #420000; border: 1px solid #777;')
            self.bookmark_opacity_slider.setValue(40)
            self.bookmark_opacity_val_label.setText("40%")

            # Reset reference locale to DEFAULT
            idx = self.reference_locale_combo.findText('DEFAULT')
            if idx >= 0:
                self.reference_locale_combo.setCurrentIndex(idx)
            
            # Reset preview font to Arial 11
            idx_f = self.preview_font_family_combo.findText('Arial')
            if idx_f >= 0: self.preview_font_family_combo.setCurrentIndex(idx_f)
            idx_s = self.preview_font_size_combo.findText('11')
            if idx_s >= 0: self.preview_font_size_combo.setCurrentIndex(idx_s)
            
            # Reset locale behavior
            self.skip_locale_toggle.setChecked(False)
            self.multi_window_toggle.setChecked(False)
            idx_def = self.default_open_locale_combo.findText('DEFAULT')
            if idx_def >= 0: self.default_open_locale_combo.setCurrentIndex(idx_def)
            
            # Reset search scope
            self.search_case_sensitive_toggle.setChecked(False)
            self.smart_paste_toggle.setChecked(True)
            self.scope_orig_cb.setChecked(True)
            self.scope_orig_cb.setChecked(True)
            self.scope_ref_cb.setChecked(True)
            self.scope_edit_cb.setChecked(True)
            self.scope_audio_cb.setChecked(True)
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
                'translation_tool_debug.log',
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
            from localization import get_translation
            if cleared_count > 0:
                msg = get_translation(self.current_language, 'logs_cleared').format(count=cleared_count)
            else:
                msg = get_translation(self.current_language, 'logs_no_files')
            
            QMessageBox.information(self, get_translation(self.current_language, 'success_title'), msg)
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
        elif target == 'text_session':
            initial = self.theme_text_session_preview.styleSheet()
        elif target == 'bookmark_star':
            initial = self.bookmark_star_preview.styleSheet()
        elif target == 'bookmark_alert':
            initial = self.bookmark_alert_preview.styleSheet()
        elif target == 'bookmark_question':
            initial = self.bookmark_question_preview.styleSheet()
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
            elif target == 'text_session':
                self.theme_text_session_preview.setStyleSheet(f'background-color: {c}; border: 1px solid #777;')
            elif target == 'bookmark_star':
                self.bookmark_star_preview.setStyleSheet(f'background-color: {c}; border: 1px solid #777;')
            elif target == 'bookmark_alert':
                self.bookmark_alert_preview.setStyleSheet(f'background-color: {c}; border: 1px solid #777;')
            elif target == 'bookmark_question':
                self.bookmark_question_preview.setStyleSheet(f'background-color: {c}; border: 1px solid #777;')
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
            # Переключаем глобальный флаг логов сразу и обновляем хендлеры
            from error_logger import ErrorLogger
            ErrorLogger.ENABLED = self.parent_window.debug_logs_enabled
            ErrorLogger.setup()
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

            m_session = re.search(r'background-color:\s*([^;]+);', self.theme_text_session_preview.styleSheet())
            self.parent_window.theme_text_session = m_session.group(1).strip() if m_session else '#bbf324'

            # extract bookmark colors and opacity
            m_bm_star = re.search(r'background-color:\s*([^;]+);', self.bookmark_star_preview.styleSheet())
            self.parent_window.bookmark_bg_star = m_bm_star.group(1).strip() if m_bm_star else '#423400'
            
            m_bm_question = re.search(r'background-color:\s*([^;]+);', self.bookmark_question_preview.styleSheet())
            self.parent_window.bookmark_bg_question = m_bm_question.group(1).strip() if m_bm_question else '#0d4200'
            
            m_bm_alert = re.search(r'background-color:\s*([^;]+);', self.bookmark_alert_preview.styleSheet())
            self.parent_window.bookmark_bg_alert = m_bm_alert.group(1).strip() if m_bm_alert else '#420000'
            
            self.parent_window.bookmark_bg_opacity = 1.0 - (self.bookmark_opacity_slider.value() / 100.0)

            # Save font settings
            self.parent_window.preview_font_family = self.preview_font_family_combo.currentText()
            try:
                self.parent_window.preview_font_size = int(self.preview_font_size_combo.currentText())
            except:
                self.parent_window.preview_font_size = 10
            
            # Apply font changes
            if hasattr(self.parent_window, 'apply_preview_font_settings'):
                self.parent_window.apply_preview_font_settings()

            # Save search scope settings
            self.parent_window.search_scope_original = self.scope_orig_cb.isChecked()
            self.parent_window.search_scope_reference = self.scope_ref_cb.isChecked()
            self.parent_window.search_scope_editor = self.scope_edit_cb.isChecked()
            self.parent_window.search_scope_audio = self.scope_audio_cb.isChecked()
            self.parent_window.search_case_sensitive = self.search_case_sensitive_toggle.isChecked()
            
            # Save locale behavior settings
            self.parent_window.skip_locale_dialog = self.skip_locale_toggle.isChecked()
            self.parent_window.multi_window_enabled = self.multi_window_toggle.isChecked()
            self.parent_window.smart_paste_enabled = self.smart_paste_toggle.isChecked()
            self.parent_window.default_open_locale = self.default_open_locale_combo.currentText()

            # Save reference locale setting (do not reload active file's reference data)
            new_ref_locale = self.reference_locale_combo.currentText()
            self.parent_window.settings_reference_locale = new_ref_locale

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
            # Обновляем цвета закладок в превью без перерисовки
            if hasattr(self.parent_window, 'refresh_bookmark_visuals'):
                self.parent_window.refresh_bookmark_visuals()
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
                    self.parent_window.theme_text_modified = vals.get('theme_text_modified', '#ff6666')
                    self.parent_window.theme_text_saved = vals.get('theme_text_saved', '#2ecc71')
                    self.parent_window.theme_text_session = vals.get('theme_text_session', '#bbf324')
                    self._log_debug(f"  - theme colors restored")
                except Exception as e:
                    self._log_debug(f"  - ERROR restoring theme colors: {e}")
                
                try:
                    self.parent_window.settings_reference_locale = vals.get('reference_locale', 'DEFAULT')
                    self.parent_window.reference_locale = vals.get('reference_locale', 'DEFAULT')
                    self.parent_window.skip_locale_dialog = vals.get('skip_locale_dialog', False)
                    self.parent_window.default_open_locale = vals.get('default_open_locale', 'DEFAULT')
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
            if self.parent_window:
                if hasattr(self.parent_window, '_suppress_settings_save'):
                    self.parent_window._suppress_settings_save = False
                self.parent_window.saved_settings_window_geom = [self.x(), self.y(), self.width(), self.height()]
        except Exception:
            pass
        super().closeEvent(event)

    def _log_debug(self, message: str):
        from error_logger import ErrorLogger
        if not ErrorLogger.ENABLED:
            return
            
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
            if hasattr(self, 'multi_window_label'):
                self.multi_window_label.setText(get_translation(self.current_language, 'settings_multi_window_mode'))
                if self.parent_window and hasattr(self.parent_window, 'register_custom_tooltip'):
                    self.parent_window.register_custom_tooltip(self.multi_window_label, get_translation(self.current_language, 'tooltip_multi_window_mode'))
                else:
                    self.multi_window_label.setToolTip(get_translation(self.current_language, 'tooltip_multi_window_mode'))
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
            if hasattr(self, 'preview_font_label'):
                self.preview_font_label.setText(get_translation(self.current_language, 'preview_font_family_label'))
            if hasattr(self, 'reference_locale_label'):
                self.reference_locale_label.setText(get_translation(self.current_language, 'reference_locale_label'))
            if hasattr(self, 'skip_locale_label'):
                self.skip_locale_label.setText(get_translation(self.current_language, 'settings_skip_locale_dialog'))
            if hasattr(self, 'default_open_locale_label'):
                self.default_open_locale_label.setText(get_translation(self.current_language, 'settings_default_open_locale'))
            if hasattr(self, 'theme_text_modified_label'):
                self.theme_text_modified_label.setText(get_translation(self.current_language, 'theme_text_modified_label'))
            if hasattr(self, 'theme_text_saved_label'):
                self.theme_text_saved_label.setText(get_translation(self.current_language, 'theme_text_saved_label'))
            if hasattr(self, 'theme_text_session_label'):
                self.theme_text_session_label.setText(get_translation(self.current_language, 'theme_text_session_label'))
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
                
            # Перевод области поиска
            if hasattr(self, 'search_scope_title'):
                self.search_scope_title.setText(get_translation(self.current_language, 'search_scope_label'))
            if hasattr(self, 'scope_orig_cb'):
                self.scope_orig_cb.setText(get_translation(self.current_language, 'scope_original'))
            if hasattr(self, 'scope_ref_cb'):
                self.scope_ref_cb.setText(get_translation(self.current_language, 'scope_reference'))
            if hasattr(self, 'scope_edit_cb'):
                self.scope_edit_cb.setText(get_translation(self.current_language, 'scope_editor'))
            if hasattr(self, 'scope_audio_cb'):
                self.scope_audio_cb.setText(get_translation(self.current_language, 'scope_audio'))
            if hasattr(self, 'bookmark_colors_label'):
                self.bookmark_colors_label.setText(get_translation(self.current_language, 'bookmark_colors_label'))
            if hasattr(self, 'bookmark_opacity_label'):
                self.bookmark_opacity_label.setText(get_translation(self.current_language, 'bookmark_opacity_label'))
            if hasattr(self, 'search_case_sensitive_label'):
                self.search_case_sensitive_label.setText(get_translation(self.current_language, 'case_sensitive_search'))
            if hasattr(self, 'smart_paste_label'):
                self.smart_paste_label.setText(get_translation(self.current_language, 'settings_smart_paste_enabled'))
                if self.parent_window and hasattr(self.parent_window, 'register_custom_tooltip'):
                    self.parent_window.register_custom_tooltip(self.smart_paste_label, get_translation(self.current_language, 'tooltip_smart_paste'))
                else:
                    self.smart_paste_label.setToolTip(get_translation(self.current_language, 'tooltip_smart_paste'))
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


class NavZone(QWidget):
    """Специальный виджет для зоны навигации с мгновенным ховером."""
    clicked = pyqtSignal()

    def __init__(self, arrow_text, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.label = QLabel(arrow_text, self)
        self.label.setStyleSheet("color: #ff9900; font-size: 80px; background: transparent; border: none;")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.hide()
        self.setCursor(Qt.PointingHandCursor)

    def enterEvent(self, event):
        self.label.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.label.hide()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.label.setFixedSize(100, 100)
        # Центрируем стрелку в зоне
        self.label.move((self.width() - 100) // 2, (self.height() - 100) // 2)

class ImagePreviewDialog(CustomDialog):
    """Продвинутое окно предпросмотра изображений с зумом и навигацией."""
    
    replaceRequested = pyqtSignal(str) # res_key
    exportRequested = pyqtSignal(str)  # res_key

    def __init__(self, current_index, image_list, current_language, parent=None):
        super().__init__(parent)
        # Настройка флагов окна для поддержки и модальности, и отсутствия рамок
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.image_list = image_list
        self.current_idx = current_index
        self.current_language = current_language
        self.zoom_factor = 1.0
        self.dragging = False
        self.drag_position = QPoint()
        self.border_radius = 10
        self.border_width = 1
        self.border_color_active = QColor("#666666")
        
        # Ищем главное окно через иерархию родителей
        self.main_window = None
        curr = self.parent()
        while curr:
            if hasattr(curr, 'image_viewer_maximized'):
                self.main_window = curr
                break
            # Если дошли до конца, но у родителя есть ссылка на main_app (случай с FilesWindow)
            if hasattr(curr, 'main_app') and curr.main_app:
                self.main_window = curr.main_app
                break
            curr = curr.parent()

        # Настраиваем геометрию
        screen_geo = QApplication.primaryScreen().availableGeometry()
        
        saved_geom = None
        if self.main_window and hasattr(self.main_window, 'saved_image_viewer_geom'):
            saved_geom = self.main_window.saved_image_viewer_geom

        if saved_geom and len(saved_geom) == 4:
            x, y, w, h = saved_geom
            # Clamping: проверяем, что окно не ушло за границы экрана
            if w > screen_geo.width(): w = int(screen_geo.width() * 0.9)
            if h > screen_geo.height(): h = int(screen_geo.height() * 0.9)
            
            # Центрируем, если сохраненные координаты некорректны или уводят окно за экран
            if x + w > screen_geo.right() or y + h > screen_geo.bottom() or x < screen_geo.left() or y < screen_geo.top():
                x = screen_geo.left() + (screen_geo.width() - w) // 2
                y = screen_geo.top() + (screen_geo.height() - h) // 2
            
            self.setGeometry(x, y, w, h)
        else:
            # Default: 70% от экрана и центрирование
            w = int(screen_geo.width() * 0.70)
            h = int(screen_geo.height() * 0.70)
            x = screen_geo.left() + (screen_geo.width() - w) // 2
            y = screen_geo.top() + (screen_geo.height() - h) // 2
            self.setGeometry(x, y, w, h)
            
        # Сохраняем "нормальную" геометрию для переключения из полноэкранного режима
        self.normal_geometry = self.geometry()

        self.init_ui()
        
        # Восстанавливаем состояние "развернуто", если оно было сохранено в настройках
        if self.main_window and getattr(self.main_window, 'image_viewer_maximized', False):
            self.showMaximized()
            # Нужно дождаться инициализации UI, чтобы кнопка существовала
            # Но init_ui вызывается чуть выше.
            if hasattr(self, 'maximize_btn'):
                self.maximize_btn.setText("🗗")
            # После showMaximized на FramelessWindowHint нормальная геометрия может исказиться, 
            # поэтому мы её уже сохранили выше.

        self.load_image()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        margin = 0 if self.isMaximized() else self.border_width
        self.main_layout.setContentsMargins(margin, margin, margin, margin)
        self.main_layout.setSpacing(0)
        
        # Основной контейнер
        self.container = QWidget()
        self.container.setObjectName("ImageContainer")
        self._update_border_style()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(1, 1, 1, 1) # Чтобы рамка контейнера была видна поверх дочерних виджетов
        self.container_layout.setSpacing(0)
        
        # Область просмотра (с поддержкой зума и панорамирования)
        self.view_area = ZoomablePreviewArea(self.container)
        self.view_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Индикаторы навигации (дочерние к self для корректного hover/geometry)
        self.left_nav = NavZone("◀", self)
        self.left_nav.clicked.connect(lambda: self.navigate(-1))
        self.left_nav.setStyleSheet("background: transparent;")
        
        self.right_nav = NavZone("▶", self)
        self.right_nav.clicked.connect(lambda: self.navigate(1))
        self.right_nav.setStyleSheet("background: transparent;")
        
        # Крестик закрытия (Без кружка, оранжевый ховер)
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(45, 45)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                border: none;
                font-size: 32px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff9900;
            }
        """)
        self.close_btn.setFocusPolicy(Qt.NoFocus)
        self.close_btn.clicked.connect(self.accept)
        
        # Нижняя панель действий
        self.toolbar = QWidget()
        self.toolbar.setFixedHeight(70)
        # Убрали бордеры чтобы не конфликтовали с основной рамкой окна
        self.toolbar.setStyleSheet("""
            background-color: rgba(25, 25, 25, 240); 
            border-top: 1px solid #444; 
            border-bottom-left-radius: 9px; 
            border-bottom-right-radius: 9px;
        """)
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(30, 0, 30, 0)
        toolbar_layout.setSpacing(15)
        
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #aaa; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        toolbar_layout.addWidget(self.info_label)
        
        toolbar_layout.addStretch()
        
        # Стили кнопок полностью как у "Сохранить перевод" (высота 34, радиус 17, динамическая ширина)
        btn_pill_style = """
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                padding: 0px 16px;
                border-radius: 17px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        """
        
        export_text = get_translation(self.current_language, 'fm_tooltip_download')
        self.export_btn = QPushButton(export_text)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setStyleSheet(btn_pill_style)
        self.export_btn.setFixedHeight(34)
        self.export_btn.setFocusPolicy(Qt.NoFocus)
        self.export_btn.clicked.connect(self._on_export)
        
        replace_text = get_translation(self.current_language, 'fm_tooltip_replace')
        self.replace_btn = QPushButton(replace_text)
        self.replace_btn.setCursor(Qt.PointingHandCursor)
        self.replace_btn.setStyleSheet(btn_pill_style)
        self.replace_btn.setFixedHeight(34)
        self.replace_btn.setFocusPolicy(Qt.NoFocus)
        self.replace_btn.clicked.connect(self._on_replace)
        
        toolbar_layout.addWidget(self.export_btn)
        toolbar_layout.addWidget(self.replace_btn)
        
        # Кнопка разворота (🗖 / 🗗)
        self.maximize_btn = QPushButton("🗖", self)
        self.maximize_btn.setFixedSize(45, 45)
        self.maximize_btn.setCursor(Qt.PointingHandCursor)
        self.maximize_btn.setFocusPolicy(Qt.NoFocus)
        self.maximize_btn.setStyleSheet(self.close_btn.styleSheet())
        self.maximize_btn.clicked.connect(self.toggle_maximize)

        self.container_layout.addWidget(self.view_area, 1)
        self.container_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.container)
        
        self.setMouseTracking(True)
        self.view_area.setMouseTracking(True)
        self.container.setMouseTracking(True)
        
        # Предотвращаем потерю фокуса основным окном при клике по картинке
        self.view_area.setFocusPolicy(Qt.NoFocus)
        if hasattr(self.view_area, 'image_label'):
            self.view_area.image_label.setFocusPolicy(Qt.NoFocus)
        
        # Устанавливаем фильтр событий для перехвата двойного клика на картинке
        self.view_area.installEventFilter(self)
        if hasattr(self.view_area, 'image_label'):
            self.view_area.image_label.installEventFilter(self)

    def load_image(self):
        if not self.image_list: return
        res_key, display_name, path = self.image_list[self.current_idx]
        if path and not os.path.isabs(path) and hasattr(self.parent(), '_extract_resource_to_temp'):
            path = self.parent()._extract_resource_to_temp(res_key, path)
        
        self.pixmap = QPixmap(path)
        if self.pixmap.isNull():
            self.view_area.image_label.setText("Error loading image")
            self.info_label.setText(f"{display_name}  ({self.current_idx + 1} / {len(self.image_list)})")
        else:
            self.view_area.setPixmap(self.pixmap)
            
            # Получаем разрешение и размер файла
            width = self.pixmap.width()
            height = self.pixmap.height()
            
            file_size_kb = 0
            try:
                if os.path.exists(path):
                    file_size_kb = os.path.getsize(path) / 1024
            except:
                pass
            
            # Формируем расширенную строку информации
            info_text = f"{display_name}  ({self.current_idx + 1} / {len(self.image_list)})"
            info_text += f"   •   📐 {width}x{height}"
            info_text += f"   •   💾 {file_size_kb:.1f} KB"
            
            self.info_label.setText(info_text)

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()
        # Дадим окну показаться и выставим картинку (для правильного первичного скейлинга внутри ZoomablePreviewArea)
        QTimer.singleShot(100, lambda: self.view_area.setPixmap(self.pixmap) if hasattr(self, 'pixmap') and not self.pixmap.isNull() else None)

    def navigate(self, delta):
        self.current_idx = (self.current_idx + delta) % len(self.image_list)
        self.load_image()
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.accept()
        elif event.key() in (Qt.Key_Left, Qt.Key_A):
            self.navigate(-1)
        elif event.key() in (Qt.Key_Right, Qt.Key_D):
            self.navigate(1)
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            new_zoom = self.view_area._zoom_factor * 1.2
            if new_zoom <= 10.0:
                self.view_area._zoom_factor = new_zoom
                self.view_area._update_image_scale()
        elif event.key() == Qt.Key_Minus:
            new_zoom = self.view_area._zoom_factor / 1.2
            if new_zoom >= 0.1:
                self.view_area._zoom_factor = new_zoom
                self.view_area._update_image_scale()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        pos = event.pos()
        
        # 1. Если кликнули в области тулбара - не закрываем
        if self.toolbar.geometry().translated(self.container.pos()).contains(pos):
             return super().mousePressEvent(event)
            
        # 2. Если попали в зону навигации - сработает navigate
        if self.left_nav.geometry().contains(pos) or self.right_nav.geometry().contains(pos):
            return super().mousePressEvent(event)

        # 3. Перетаскивание окна (только ЛКМ)
        if event.button() == Qt.LeftButton:
            # Запрещаем перетаскивание, если окно развернуто
            if self.isMaximized():
                return super().mousePressEvent(event)
                
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # Проверяем флаги перед вызовом super(), так как он их сбросит
        was_resizing = getattr(self, 'resizing', False)
        was_dragging = getattr(self, 'dragging', False)
        
        super().mouseReleaseEvent(event)
        
        if (was_resizing or was_dragging) and not self.isMaximized():
            # Запоминаем новую позицию как "нормальную"
            self.normal_geometry = self.geometry()
            # Сохраняем в главное приложение
            if self.main_window:
                geom = self.normal_geometry
                self.main_window.saved_image_viewer_geom = [geom.x(), geom.y(), geom.width(), geom.height()]
                if hasattr(self.main_window, 'save_settings'):
                    self.main_window.save_settings()
            event.accept()

    def closeEvent(self, event):
        """Сохраняем геометрию перед закрытием."""
        if self.main_window:
            if self.isMaximized():
                self.main_window.image_viewer_maximized = True
            else:
                self.main_window.image_viewer_maximized = False
                # Сохраняем геометрию только если не развернуто
                geom = self.geometry()
                self.main_window.saved_image_viewer_geom = [geom.x(), geom.y(), geom.width(), geom.height()]
            
            # Инициируем сохранение настроек в main.py
            if hasattr(self.main_window, 'save_settings'):
                self.main_window.save_settings()
        
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Округляем углы через маску
        self._update_mask()
        
        # NavZone дочерние к self — позиционируются абсолютно, не конфликтуя с layout
        self.left_nav.setGeometry(0, 80, 250, self.height() - 160)
        self.right_nav.setGeometry(self.width() - 250, 80, 250, self.height() - 160)
        
        self.close_btn.move(self.width() - 70, 15)
        self.maximize_btn.move(self.width() - 120, 10)
        
        # Z-order: NavZone поверх container, close_btn поверх всех
        self.left_nav.raise_()
        self.right_nav.raise_()
        self.close_btn.raise_()
        self.maximize_btn.raise_()

    def toggle_maximize(self):
        """Переключает окно между стандартным масштабом и полным экраном."""
        if self.isMaximized():
            self.showNormal()
            if self.normal_geometry:
                self.setGeometry(self.normal_geometry)
            self.maximize_btn.setText("🗖")
        else:
            # Запоминаем текущую геометрию перед развертыванием
            self.normal_geometry = self.geometry()
            self.showMaximized()
            self.maximize_btn.setText("🗗")
        self._update_border_style()
        self._update_mask()
        
        # Обновляем отступы макета в зависимости от режима
        margin = 0 if self.isMaximized() else getattr(self, 'border_width', 1)
        if hasattr(self, 'main_layout'):
            self.main_layout.setContentsMargins(margin, margin, margin, margin)
        
        # Сохраняем состояние в общие настройки приложения
        if self.main_window:
            self.main_window.image_viewer_maximized = self.isMaximized()
            if self.isMaximized():
                 # Если развернули - сохраняем текущую нормальную геометрию
                 geom = getattr(self, 'normal_geometry', None)
                 if geom:
                     self.main_window.saved_image_viewer_geom = [geom.x(), geom.y(), geom.width(), geom.height()]
            
            if hasattr(self.main_window, 'save_settings'):
                self.main_window.save_settings()
        # Принудительно возвращаем фокус диалогу для клавиатурной навигации
        self.setFocus()

    def mouseDoubleClickEvent(self, event):
        """Двойной клик по свободному месту в окне также переключает масштаб."""
        if event.button() == Qt.LeftButton:
            # Если не в области тулбара
            if not self.toolbar.geometry().translated(self.container.pos()).contains(event.pos()):
                self.toggle_maximize()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def eventFilter(self, obj, event):
        """Перехват событий для управления фокусом и полноэкранным режимом."""
        if event.type() == QEvent.MouseButtonPress:
            # При любом клике по картинке или области возвращаем фокус диалогу
            if obj in (self.view_area, getattr(self.view_area, 'image_label', None)):
                self.setFocus()
                # Не возвращаем True, чтобы событие прошло дальше (например для панорамирования)
        
        if event.type() == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton:
            if obj in (self.view_area, getattr(self.view_area, 'image_label', None)):
                self.toggle_maximize()
                return True
        return super().eventFilter(obj, event)

    def changeEvent(self, event):
        """Отслеживание фокуса для изменения цвета рамки"""
        if event.type() == QEvent.ActivationChange:
            self.is_active = self.isActiveWindow()
            self._update_border_style()
        super().changeEvent(event)

    def _update_border_style(self):
        """Обновление стиля контейнера (фон)"""
        radius = 0 if self.isMaximized() else self.border_radius
        self.container.setStyleSheet(f"""
            #ImageContainer {{ 
                background-color: rgba(0, 0, 0, 230); 
                border: none;
                border-radius: {radius}px;
            }}
            QPushButton:hover {{ background-color: #a3a3a3; }}
        """)

    def _update_mask(self):
        """Создает маску для закругленных углов"""
        if self.isMaximized():
            self.clearMask()
            return

        path = QPainterPath()
        rect = QRectF(self.rect())
        path.addRoundedRect(rect, self.border_radius, self.border_radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def mouseMoveEvent(self, event):
        if hasattr(self, 'dragging') and self.dragging and (event.buttons() & Qt.LeftButton):
            # На всякий случай проверяем и здесь
            if self.isMaximized():
                self.dragging = False
                return super().mouseMoveEvent(event)
                
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            return
            
        # Tracking now handled by NavZone widgets for arrows
        super().mouseMoveEvent(event)

    def _hide_nav_labels(self):
        # Deprecated: NavZone handles its own visibility via enter/leaveEvent
        pass

    def _on_export(self):
        res_key = self.image_list[self.current_idx][0]
        self.exportRequested.emit(res_key)

    def _on_replace(self):
        res_key = self.image_list[self.current_idx][0]
        
        # Эмитим сигнал для родительского окна (FileManager)
        #FileManager обработает замену, обновит свой кэш файлов _all_files 
        # и перерисует список файлов через resourcesChanged.
        self.replaceRequested.emit(res_key)
        
        # Даем небольшую задержку, чтобы MainForm успела обновить self._all_files
        # прежде чем мы запросим новые данные (иначе мы получим старое имя расширения).
        QTimer.singleShot(150, lambda: self._reload_image_info(res_key))
        
    def _reload_image_info(self, res_key):
        """Вспомогательный метод для обновления информации о картинке после замены."""
        if self.parent() and hasattr(self.parent(), 'get_resource_info_by_key'):
            new_info = self.parent().get_resource_info_by_key(res_key)
            if new_info:
                self.image_list[self.current_idx] = new_info
        
        # Перезагружаем изображение после замены
        self.load_image()


class TypeMismatchDialog(CustomDialog):
    """Диалог предупреждения о несовпадении типов файлов при Drag & Drop замене"""
    def __init__(self, current_language, original_ext, new_ext, parent=None):
        super().__init__(parent)
        self.current_language = current_language
        self.original_ext = original_ext.lower()
        self.new_ext = new_ext.lower()
        
        def get_category(ext):
            if ext in ['.png', '.jpg', '.jpeg']: return get_translation(self.current_language, 'fm_filter_images')
            if ext in ['.wav', '.ogg']: return get_translation(self.current_language, 'fm_filter_audio')
            return "File"
            
        orig_cat = get_category(self.original_ext)
        new_cat = get_category(self.new_ext)

        self.setWindowTitle(get_translation(self.current_language, 'type_mismatch_title'))
        self.setFixedSize(450, 310) # Увеличено с 280

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        # 1. КОНТЕНТ
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 25, 30, 15)
        content_layout.setSpacing(15)

        title_label = QLabel(get_translation(self.current_language, 'type_mismatch_title'))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #ff3333; font-weight: bold; font-size: 16px; background-color: transparent; border: none;")
        content_layout.addWidget(title_label)
        content_layout.addStretch()

        warning_text = get_translation(self.current_language, 'type_mismatch_desc').format(
            orig_cat=orig_cat, orig_ext=self.original_ext,
            new_cat=new_cat, new_ext=self.new_ext
        )
        
        desc_label = QLabel(warning_text)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #dddddd; font-size: 13px; background-color: transparent; border: none;")
        content_layout.addWidget(desc_label)
        content_layout.addStretch()

        main_layout.addWidget(content_widget)

        # 2. РАЗДЕЛИТЕЛЬ
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #777777; border: none;")
        main_layout.addWidget(line)

        # 3. ФУТЕР
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("QFrame { background-color: #2b2b2b; border: none; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        footer_layout.setSpacing(15)

        btn_style_continue = """
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #e68a00; }
        """
        btn_style_cancel = """
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #a3a3a3; }
        """

        continue_btn = QPushButton(get_translation(self.current_language, 'continue_btn'))
        continue_btn.setStyleSheet(btn_style_continue)
        continue_btn.setFixedSize(120, 32)
        continue_btn.setCursor(Qt.PointingHandCursor)
        continue_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton(get_translation(self.current_language, 'cancel_btn'))
        cancel_btn.setStyleSheet(btn_style_cancel)
        cancel_btn.setFixedSize(120, 32)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        footer_layout.addStretch()
        footer_layout.addWidget(cancel_btn)
        footer_layout.addWidget(continue_btn)
        footer_layout.addStretch()
        
        main_layout.addWidget(footer)

class StandardQuestionDialog(CustomDialog):
    """Универсальный стилизованный диалог вопроса (Да/Нет)"""
    def __init__(self, title, message, current_language, parent=None, yes_text=None, no_text=None):
        super().__init__(parent)
        self.current_language = current_language
        self.setWindowTitle(title)
        self.setFixedSize(450, 200) # Увеличено для футера

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        # 1. КОНТЕНТ
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 25, 30, 15)
        content_layout.setSpacing(10)

        content_layout.addStretch()
        self.msg_label = QLabel(message)
        self.msg_label.setStyleSheet("color: #ffffff; font-size: 14px; background: transparent; border: none;")
        self.msg_label.setWordWrap(True)
        self.msg_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.msg_label)
        content_layout.addStretch()

        main_layout.addWidget(content_widget)

        # 2. РАЗДЕЛИТЕЛЬ
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #777777; border: none;")
        main_layout.addWidget(line)

        # 3. ФУТЕР
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("QFrame { background-color: #2b2b2b; border: none; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        footer_layout.setSpacing(15)

        yes_label = yes_text if yes_text else get_translation(self.current_language, 'yes_btn')
        self.yes_btn = QPushButton(yes_label)
        self.yes_btn.setCursor(Qt.PointingHandCursor)
        self.yes_btn.setFixedSize(120, 32)
        self.yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9900;
                color: #1a1a1a;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #ffb347; }
            QPushButton:pressed { background-color: #e68a00; }
        """)
        self.yes_btn.clicked.connect(self.accept)

        no_label = no_text if no_text else get_translation(self.current_language, 'no_btn')
        self.no_btn = QPushButton(no_label)
        self.no_btn.setCursor(Qt.PointingHandCursor)
        self.no_btn.setFixedSize(120, 32)
        self.no_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #a3a3a3; }
        """)
        self.no_btn.clicked.connect(self.reject)

        footer_layout.addStretch()
        footer_layout.addWidget(self.no_btn)
        footer_layout.addWidget(self.yes_btn)
        footer_layout.addStretch()
        
        main_layout.addWidget(footer)


class StandardInfoDialog(CustomDialog):
    """Универсальный стилизованный информационный диалог (ОК)"""
    def __init__(self, title, message, current_language, parent=None, is_error=False):
        super().__init__(parent)
        self.current_language = current_language
        self.setWindowTitle(title)
        self.setFixedSize(400, 200) # Увеличено для футера

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        # 1. КОНТЕНТ
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 25, 30, 15)
        content_layout.setSpacing(10)

        content_layout.addStretch()
        self.msg_label = QLabel(message)
        text_color = "#ff6666" if is_error else "#ffffff"
        self.msg_label.setStyleSheet(f"color: {text_color}; font-size: 14px; background: transparent; border: none;")
        self.msg_label.setWordWrap(True)
        self.msg_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.msg_label)
        content_layout.addStretch()

        main_layout.addWidget(content_widget)

        # 2. РАЗДЕЛИТЕЛЬ
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #777777; border: none;")
        main_layout.addWidget(line)

        # 3. ФУТЕР
        footer = QFrame()
        footer.setFixedHeight(60)
        footer.setStyleSheet("QFrame { background-color: #2b2b2b; border: none; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        footer_layout.setSpacing(15)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.setCursor(Qt.PointingHandCursor)
        self.ok_btn.setFixedSize(120, 32)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9900;
                color: #1a1a1a;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #ffb347; }
        """)
        self.ok_btn.clicked.connect(self.accept)

        footer_layout.addStretch()
        footer_layout.addWidget(self.ok_btn)
        footer_layout.addStretch()
        
        main_layout.addWidget(footer)

class VoiceDownloadWorker(QThread):
    """Поток для скачивания языковой модели Piper."""
    progress = pyqtSignal(int, int, int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, engine, voice_id):
        super().__init__()
        self.engine = engine
        self.voice_id = voice_id

    def run(self):
        try:
            success = self.engine.download_voice(self.voice_id, self.progress.emit)
            self.finished.emit(success, self.voice_id)
        except Exception:
            self.finished.emit(False, self.voice_id)

class XTTSDownloadWorker(QThread):
    """Поток для скачивания модели XTTS v2 (~1.5GB)."""
    progress = pyqtSignal(int, int, int)
    progress_text = pyqtSignal(str)
    finished = pyqtSignal(bool)
    
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def run(self):
        try:
            success = self.engine.download_xtts_model(self.progress.emit, self.progress_text.emit)
            self.finished.emit(success)
        except Exception:
            self.finished.emit(False)

class LibraryInstallWorker(QThread):
    """Поток для установки библиотек coqui-tts и torch."""
    progress = pyqtSignal(int, int, int)
    progress_text = pyqtSignal(str)
    finished = pyqtSignal(bool)
    
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def run(self):
        try:
            success = self.engine.install_tts_libraries(self.progress.emit, self.progress_text.emit)
            self.finished.emit(success)
        except Exception:
            self.finished.emit(False)

class PiperEngineWorker(QThread):
    """Поток для скачивания самого движка Piper (piper.exe)."""
    progress = pyqtSignal(int, int, int)
    progress_text = pyqtSignal(str)
    finished = pyqtSignal(bool)
    
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def run(self):
        try:
            success = self.engine.download_piper_components(self.progress.emit, self.progress_text.emit)
            self.finished.emit(success)
        except Exception:
            self.finished.emit(False)

class TTSLoadingDialog(CustomDialog):
    """Маленькое информационное окно загрузки для TTS."""
    def __init__(self, current_language="ru", parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 100)
        from localization import get_translation
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        msg = get_translation(current_language, 'tts_loading_msg')
        self.label = QLabel(msg)
        self.label.setStyleSheet("color: #ffffff; font-size: 14px; background: transparent;")
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)
        
        self.progress = QProgressBar()
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0) # Анимация "бегающая полоска"
        self.progress.setStyleSheet("""
            QProgressBar { border: none; background: #222; border-radius: 2px; }
            QProgressBar::chunk { background: #ff9900; border-radius: 2px; }
        """)
        main_layout.addWidget(self.progress)

class TTSManualInstallDialog(CustomDialog):
    """Окно с подробной инструкцией по ручной установке TTS."""
    def __init__(self, current_language="ru", parent=None):
        super().__init__(parent)
        self.current_language = current_language
        from localization import get_translation
        self.setWindowTitle(get_translation(self.current_language, 'tts_manual_install_title'))
        self.setFixedSize(650, 900)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        # Контент (инструкция)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(False)
        self.text_browser.setHtml(get_translation(self.current_language, 'tts_manual_install_text'))
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #222;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', 'Segoe UI', 'Arial';
                font-size: 13px;
            }
            QScrollBar:vertical {
                background: #2a2a2a; width: 14px; margin: 16px 2px 16px 2px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #ff9900; min-height: 20px; border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover { background: #e68a00; }
            QScrollBar::sub-line:vertical {
                background: none; border: none; height: 16px;
                subcontrol-position: top; subcontrol-origin: margin;
            }
            QScrollBar::add-line:vertical {
                background: none; border: none; height: 16px;
                subcontrol-position: bottom; subcontrol-origin: margin;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                width: 10px; height: 10px; background: #ff9900; border-radius: 5px; margin: 2px;
            }
        """)
        
        content_layout.addWidget(self.text_browser)
        main_layout.addWidget(content_widget)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #777777; border: none;")
        main_layout.addWidget(line)

        # Футер
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet("QFrame { background-color: #2b2b2b; border: none; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)

        self.ok_btn = QPushButton(get_translation(self.current_language, 'ok_btn'))
        self.ok_btn.setCursor(Qt.PointingHandCursor)
        self.ok_btn.setFixedSize(120, 32)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9900;
                color: #1a1a1a;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #ffb347; }
        """)
        self.ok_btn.clicked.connect(self.accept)

        footer_layout.addStretch()
        footer_layout.addWidget(self.ok_btn)
        footer_layout.addStretch()

        main_layout.addWidget(footer)

class TTSPreviewDialog(CustomDialog):
    """Диалог для настройки параметров TTS, предпрослушивания и выбора голоса/языка."""

    def __init__(self, text, engine, parent=None, shared_tts_duration_cache=None):
        super().__init__(parent)
        self.shared_tts_duration_cache = shared_tts_duration_cache
        self.setMinimumWidth(1315)
        self.setMinimumHeight(800)
        
        parent_lang = getattr(self.parent(), 'current_language', None)
        if not parent_lang:
            settings = get_ui_settings()
            parent_lang = settings.value("language", "ru")
        self.current_language = parent_lang
        from localization import get_translation
        self.setWindowTitle(get_translation(self.current_language, 'tts_window_title'))
        
        # Загрузка размеров окна из настроек
        self.settings = get_ui_settings()
        geom = self.settings.value("tts_window_geometry")
        if geom:
            self.restoreGeometry(geom)
        else:
            self.resize(1300, 800) # По умолчанию минимальный размер (800+500)
        self.text = text
        self.engine = engine
        self.preview_path = None
        self._current_audio_path = None
        self._playing_res_key = None    # Какой res_key загружен в плеер
        self.is_playing = False
        self.is_paused = False
        
        # Кэш сгенерированных TTS файлов
        from tts_engine import TTSAudioCache
        self.tts_cache = TTSAudioCache()
        
        # Состояние пакетной генерации
        self._batch_mode = False
        self._batch_queue = []       # [(res_key, text, output_path), ...]
        self._batch_index = 0
        self._batch_total = 0
        self._batch_stop_requested = False
        self._batch_times = []       # времена генерации каждого файла (секунды)
        self._batch_start_time = None
        
        # Кэш отредактированных текстов в текущем окне (для пакетной генерации)
        self._edited_texts = {} # {res_key: "edited text"}
        
        # Состояние плеера
        self.duration_sec = 0
        self.is_slider_dragged = False
        self.play_start_offset = 0
        self.audio_loaded = False
        
        from tts_engine import VOICE_REGISTRY
        self.registry = VOICE_REGISTRY
        # self.settings уже инициализирован выше
        
        # Инциализация кастомного тултипа
        from widgets import CustomToolTip
        self.custom_tooltip = CustomToolTip()
        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self._show_pending_tooltip)
        self._pending_tooltip_data = None
        self._custom_tooltip_map = {}
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)
        
        # === ГОРИЗОНТАЛЬНЫЙ СПЛИТТЕР: Левая часть (контролы TTS) + Правая часть (плейлист) ===
        from widgets import CustomSplitter
        self.tts_splitter = CustomSplitter(Qt.Horizontal)
        self.tts_splitter.setHandleWidth(3)
        self.tts_splitter.setStyleSheet("background-color: transparent; border: none;")
        
        # --- ЛЕВАЯ ПАНЕЛЬ (все существующие контролы TTS) ---
        left_panel = QWidget()
        left_panel.setMinimumWidth(800)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Заголовок (в контейнере для отступов)
        title_container = QWidget()
        title_vbox = QVBoxLayout(title_container)
        title_vbox.setContentsMargins(20, 20, 20, 10)
        from localization import get_translation
        self.title_label = QLabel(get_translation(self.current_language, 'tts_title'))
        self.title_label.setStyleSheet("color: #ff9900; font-size: 18px; font-weight: bold; background: transparent;")
        self.title_label.setAlignment(Qt.AlignCenter)
        title_vbox.addWidget(self.title_label)
        left_layout.addWidget(title_container)
        
        # --- Табы выбора движка ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; background: #2b2b2b; border-top-left-radius: 0px; border-top-right-radius: 8px; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; top: -1px; }
            QTabBar::tab { 
                background: #333; color: #cccccc; 
                padding: 10px 25px; 
                min-width: 150px;
                border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; 
            }
            QTabBar::tab:selected { background: #2b2b2b; color: #ff9900; border: 1px solid #444; border-bottom: none; }
            QTabBar::tab:hover:!selected { background: #3d3d3d; color: #ffffff; }
        """)

        # 1. Вкладка Piper
        self.tab_piper = QWidget()
        self._setup_tab_piper()
        self.tabs.addTab(self.tab_piper, get_translation(self.current_language, 'tts_tab_piper'))
        
        # 2. Вкладка XTTS
        self.tab_xtts = QWidget()
        self._setup_tab_xtts()
        self.tabs.addTab(self.tab_xtts, get_translation(self.current_language, 'tts_tab_xtts'))
        
        # Вкладки с отступом 15px
        tabs_container = QWidget()
        tabs_hbox = QHBoxLayout(tabs_container)
        tabs_hbox.setContentsMargins(15, 0, 15, 0)
        self.tabs.setFixedHeight(220) # Фиксируем высоту, чтобы окно не прыгало и обе вкладки были идентичны по размеру
        tabs_hbox.addWidget(self.tabs)
        
        self.btn_manual_install = QPushButton(" " + get_translation(self.current_language, 'tts_manual_install_btn') + " ")
        self.btn_manual_install.setCursor(Qt.PointingHandCursor)
        self.btn_manual_install.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #aaaaaa;
                text-decoration: underline;
                border: none;
                font-size: 13px;
                margin-bottom: 5px;
                padding-right: 10px;
            }
            QPushButton:hover { color: #ff9900; }
        """)
        self.btn_manual_install.clicked.connect(self._show_manual_install_dialog)
        self.tabs.setCornerWidget(self.btn_manual_install, Qt.TopRightCorner)
        
        left_layout.addWidget(tabs_container)
        
        # --- Фильтр символов (замена на пробел перед генерацией) ---
        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(15, 0, 15, 0)
        filter_row.setSpacing(8)
        
        self.cb_filter_symbols = QCheckBox(get_translation(self.current_language, 'tts_filter_symbols'))
        self.cb_filter_symbols.setChecked(False)
        # Генерируем иконку галочки для чекбокса
        import tempfile
        checkmark_pixmap = QPixmap(14, 14)
        checkmark_pixmap.fill(QColor(0, 0, 0, 0))
        _p = QPainter(checkmark_pixmap)
        _p.setRenderHint(QPainter.Antialiasing)
        _pen = QPen(QColor("#ff9900"), 2.5)
        _pen.setCapStyle(Qt.RoundCap)
        _p.setPen(_pen)
        _p.drawLine(2, 7, 5, 11)
        _p.drawLine(5, 11, 12, 3)
        _p.end()
        self._checkmark_path = os.path.join(tempfile.gettempdir(), "tts_checkmark.png")
        checkmark_pixmap.save(self._checkmark_path)
        _css_path = self._checkmark_path.replace("\\", "/")
        self.cb_filter_symbols.setStyleSheet(f"""
            QCheckBox {{ color: #ccc; font-size: 12px; background: transparent; spacing: 5px; }}
            QCheckBox::indicator {{ width: 14px; height: 14px; border: 1px solid #555; border-radius: 3px; background: #1a1a1a; }}
            QCheckBox::indicator:checked {{ background: #1a1a1a; border-color: #555; image: url({_css_path}); }}
        """)
        self.cb_filter_symbols.toggled.connect(lambda v: self.settings.setValue("tts_filter_symbols_enabled", v))
        filter_row.addWidget(self.cb_filter_symbols)
        
        self.edit_filter_symbols = QLineEdit()
        self.edit_filter_symbols.setText('/ \\ " \' « »')
        self.edit_filter_symbols.setFixedWidth(140)
        self.edit_filter_symbols.setStyleSheet("background: #1a1a1a; color: #fff; border: 1px solid #333; border-radius: 4px; padding: 2px 5px; font-size: 12px;")
        self.edit_filter_symbols.textChanged.connect(lambda t: self.settings.setValue("tts_filter_symbols_list", t))
        filter_row.addWidget(self.edit_filter_symbols)
        
        filter_row.addSpacing(20)
        
        self.cb_replace_symbols = QCheckBox(get_translation(self.current_language, 'tts_replace_symbol_from'))
        self.cb_replace_symbols.setChecked(True)  # Теперь ВКЛ по умолчанию
        self.cb_replace_symbols.setStyleSheet(self.cb_filter_symbols.styleSheet())
        self.cb_replace_symbols.toggled.connect(lambda v: self.settings.setValue("tts_replace_symbols_enabled", v))
        self.register_custom_tooltip(self.cb_replace_symbols, get_translation(self.current_language, 'tts_replace_symbol_tooltip'))
        filter_row.addWidget(self.cb_replace_symbols)
        
        self.edit_replace_from = QLineEdit(".")
        self.edit_replace_from.setFixedWidth(60)
        self.edit_replace_from.setStyleSheet(self.edit_filter_symbols.styleSheet())
        self.edit_replace_from.textChanged.connect(lambda t: self.settings.setValue("tts_replace_from_list", t))
        filter_row.addWidget(self.edit_replace_from)
        
        self.lbl_replace_to_label = QLabel(get_translation(self.current_language, 'tts_replace_symbol_to'))
        self.lbl_replace_to_label.setStyleSheet("color: #ccc; font-size: 12px; background: transparent;")
        filter_row.addWidget(self.lbl_replace_to_label)
        
        self.edit_replace_to = QLineEdit("!")
        self.edit_replace_to.setFixedWidth(60)
        self.edit_replace_to.setStyleSheet(self.edit_filter_symbols.styleSheet())
        self.edit_replace_to.textChanged.connect(lambda t: self.settings.setValue("tts_replace_to_list", t))
        filter_row.addWidget(self.edit_replace_to)
        
        filter_row.addStretch()
        
        left_layout.addLayout(filter_row)
        
        # Текст (для подстройки интонаций)
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlainText(text)
        self.text_edit.setReadOnly(False) # Разрешаем редактирование для ТТС
        self.text_edit.setMinimumHeight(120)
        self.text_edit.setMaximumHeight(200)
        
        # Шрифт из настроек
        # Пытаемся взять из TranslationApp через FilesWindow -> main_app
        f_family = "Consolas"
        f_size = 11
        
        main_win = None
        if hasattr(self.parent(), "parent_window") and hasattr(self.parent().parent_window, "main_app"):
            main_win = self.parent().parent_window.main_app
        
        if main_win:
            f_family = getattr(main_win, "preview_font_family", "Consolas")
            f_size = getattr(main_win, "preview_font_size", 11)
        else:
            f_family = self.settings.value("preview_font_family", "Consolas")
            f_size = self.settings.value("preview_font_size", "11")
        
        # Единая стилизация (фон, рамка, шрифт и скроллбары)
        self.text_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #222; 
                color: #ffffff;
                border: 1px solid #444; 
                border-radius: 4px; 
                padding: 10px;
                font-family: '{f_family}', 'Consolas', 'Segoe UI', 'Arial'; 
                font-size: {f_size}pt;
            }}
        """ + self._get_scrollbar_style())
        
        # Горизонтальный слой с такими же отступами как у табов (15px)
        text_h_layout = QHBoxLayout()
        text_h_layout.setContentsMargins(15, 0, 15, 0)
        text_h_layout.addWidget(self.text_edit)
        left_layout.addLayout(text_h_layout)
        left_layout.addSpacing(15)
        
        # Кнопки действия (Интегрированный Плеер как в Менеджере)
        self._ap_controls_frame = QFrame()
        self._ap_controls_frame.setObjectName("apControlsFrame")
        self._ap_controls_frame.setFixedSize(490, 125)
        self._ap_controls_frame.setStyleSheet("""
            QFrame#apControlsFrame {
                border: 1px solid #777777;
                border-radius: 5px;
                background-color: transparent;
            }
        """)
        frame_hbox = QHBoxLayout(self._ap_controls_frame)
        frame_hbox.setContentsMargins(15, 5, 15, 5)
        frame_hbox.setSpacing(10)

        controls_vbox = QVBoxLayout()
        controls_vbox.setSpacing(5)

        # Время
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #aaaaaa; font-size: 12px; background: transparent;")
        controls_vbox.addWidget(self.time_label)

        # Слайдер позиции
        self.position_slider = JumpSlider(Qt.Horizontal)
        self.position_slider.setFocusPolicy(Qt.NoFocus)
        self.position_slider.setStyleSheet("""
            QSlider { background: transparent; border: none; }
            QSlider:focus { border: none; outline: none; }
            QSlider::groove:horizontal { border: 1px solid #444; background: #222; height: 8px; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #ff9900; border: 1px solid #444; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #fff; border: 1px solid #5c5c5c; width: 14px; margin-top: -3px; margin-bottom: -3px; border-radius: 7px; }
        """)
        self.position_slider.setRange(0, 0)
        self.position_slider.setEnabled(True)
        self.position_slider.sliderPressed.connect(self.on_slider_pressed)
        self.position_slider.sliderReleased.connect(self.on_slider_released)
        controls_vbox.addWidget(self.position_slider)

        # Кнопки
        controls_row = QHBoxLayout()
        controls_row.setAlignment(Qt.AlignCenter)
        controls_row.setSpacing(15)

        ap_btn_style = """
            QPushButton {{
                background-color: transparent;
                color: #ffffff;
                border: none;
                font-family: 'Segoe UI Symbol', Consolas, 'Segoe UI', sans-serif;
                font-weight: bold;
                font-size: {size}px;
                min-width: 40px; min-height: 40px; max-width: 40px; max-height: 40px;
                padding-top: {top}px;
                text-align: center;
            }}
            QPushButton:hover {{ color: #ff9900; }}
            QPushButton:disabled {{ color: #555; }}
        """

        self.btn_play_preview = QPushButton("▶")
        self.btn_play_preview.setFocusPolicy(Qt.NoFocus)
        self.btn_play_preview.setStyleSheet(ap_btn_style.format(size=28, top=-4))
        self.btn_play_preview.setFixedSize(40, 40)
        self.btn_play_preview.setCursor(Qt.PointingHandCursor)
        self.btn_play_preview.clicked.connect(self.toggle_play_pause)
        self.btn_play_preview.setEnabled(True)
        controls_row.addWidget(self.btn_play_preview)

        self.btn_stop_preview = QPushButton("■")
        self.btn_stop_preview.setFocusPolicy(Qt.NoFocus)
        self.btn_stop_preview.setStyleSheet(ap_btn_style.format(size=24, top=0))
        self.btn_stop_preview.setFixedSize(40, 40)
        self.btn_stop_preview.setCursor(Qt.PointingHandCursor)
        self.btn_stop_preview.clicked.connect(self.stop_audio)
        self.btn_stop_preview.setEnabled(True)
        controls_row.addWidget(self.btn_stop_preview)

        controls_row.addStretch()

        vol_ico = QLabel("🔊")
        vol_ico.setStyleSheet("color: #aaa; background: transparent; font-size: 18px; padding-top: -2px;")
        controls_row.addWidget(vol_ico)

        self.volume_slider = JumpSlider(Qt.Horizontal)
        self.volume_slider.setFocusPolicy(Qt.NoFocus)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setRange(0, 100)
        
        main_app = self._get_main_app()
        initial_vol = 50
        if main_app:
            initial_vol = getattr(main_app, 'audio_volume', 50)
        elif self.settings.contains("audio_volume"):
            initial_vol = int(self.settings.value("audio_volume", 50))
            
        self.volume_slider.setStyleSheet("""
            QSlider { background: transparent; border: none; }
            QSlider:focus { border: none; outline: none; }
            QSlider::groove:horizontal { border: 1px solid #444; background: #222; height: 8px; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #ff9900; border: 1px solid #444; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #fff; border: 1px solid #5c5c5c; width: 14px; margin-top: -3px; margin-bottom: -3px; border-radius: 7px; }
        """)
        self.volume_slider.valueChanged.connect(self.set_volume)
        # [FIX] Устанавливаем значение ПОСЛЕ подключения сигнала, чтобы вызвался set_volume
        self.volume_slider.setValue(initial_vol)
        # На случай, если значение не изменилось (уже было 50), вызываем явно для инициализации mixer
        self.set_volume(initial_vol)
        
        controls_row.addWidget(self.volume_slider)

        controls_vbox.addLayout(controls_row)
        frame_hbox.addLayout(controls_vbox)
        frame_hbox.addSpacing(130)

        # Картинка radiocat.png
        self.img_cat_label = QLabel(self._ap_controls_frame)
        self.img_cat_label.setFixedSize(121, 110)
        img_path = os.path.join(os.path.dirname(__file__), "radiocat.png")
        if os.path.exists(img_path):
            pix = QPixmap(img_path)
            self.img_cat_label.setPixmap(pix.scaled(121, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.img_cat_label.setStyleSheet("border: 1px dashed #777; color: #777; font-size: 10px;")
            self.img_cat_label.setText("radiocat.png")
            self.img_cat_label.setAlignment(Qt.AlignCenter)
        self.img_cat_label.move(354 + 14, 7 + 7)  # Смещение как в AudioPlayerDialog
        self.img_cat_label.show()
        
        # Центрированный контейнер для рамки плеера
        player_h_layout = QHBoxLayout()
        player_h_layout.addStretch()
        player_h_layout.addWidget(self._ap_controls_frame)
        player_h_layout.addStretch()
        left_layout.addLayout(player_h_layout)
        left_layout.addSpacing(15)
        
        # Кнопка генерации (центрованная, стиль как у Reset)
        btn_h_layout = QHBoxLayout()
        btn_h_layout.addStretch()
        self.btn_main_action = QPushButton(get_translation(self.current_language, 'tts_btn_generate'))
        self.btn_main_action.setFixedSize(280, 32)
        self.btn_main_action.setCursor(Qt.PointingHandCursor)
        self.register_custom_tooltip(self.btn_main_action, get_translation(self.current_language, 'tts_btn_generate_tooltip'))
        self.btn_main_action.setStyleSheet(self._get_main_btn_style())
        self.btn_main_action.clicked.connect(self._on_main_action_clicked)
        self.text_edit.textChanged.connect(self._on_text_edited)
        btn_h_layout.addWidget(self.btn_main_action)
        
        # [NEW] Чекбокс авто-проигрывания
        self.cb_auto_play = QCheckBox(get_translation(self.current_language, 'tts_auto_play'))
        self.cb_auto_play.setCursor(Qt.PointingHandCursor)
        self.register_custom_tooltip(self.cb_auto_play, get_translation(self.current_language, 'tts_auto_play_tooltip'))
        
        main_app = self._get_main_app()
        initial_auto_play = getattr(main_app, 'tts_auto_play', False) if main_app else False
        self.cb_auto_play.setChecked(initial_auto_play)
        
        # Стилизация (используем существующий стиль чекбоксов)
        self.cb_auto_play.setStyleSheet(self.cb_filter_symbols.styleSheet())
        self.cb_auto_play.toggled.connect(self._on_auto_play_toggled)
        
        btn_h_layout.addSpacing(15)
        btn_h_layout.addWidget(self.cb_auto_play)
        btn_h_layout.addStretch()
        left_layout.addLayout(btn_h_layout)
        
        left_layout.addSpacing(3) # Зазор 3px между кнопкой и статусом
        
        # Статус
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #ffffff; font-size: 12px; background: transparent;")
        left_layout.addWidget(self.lbl_status)
        
        left_layout.addStretch()

        # Полоса прогресса внизу
        self.download_progress = QProgressBar()
        self.download_progress.setFixedHeight(4)
        self.download_progress.setTextVisible(False)
        self.download_progress.setStyleSheet("""
            QProgressBar { border: none; background: #222; border-radius: 2px; }
            QProgressBar::chunk { background: #ff9900; border-radius: 2px; }
        """)
        self.download_progress.hide()
        # Добавим в контейнер с отступами 15px
        progress_container = QWidget()
        progress_hbox = QHBoxLayout(progress_container)
        progress_hbox.setContentsMargins(15, 0, 15, 5)
        progress_hbox.addWidget(self.download_progress)
        left_layout.addWidget(progress_container)
        
        # --- ПРАВАЯ ПАНЕЛЬ (плейлист аудиофайлов) ---
        right_panel = QWidget()
        right_panel.setMinimumWidth(500)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 5, 15, 5) # Зазор 15px справа и 5px сверху/снизу
        right_layout.setSpacing(0)
        
        # Заголовок плейлиста
        self.playlist_title_label = QLabel(get_translation(self.current_language, 'tts_playlist_title'))
        self.playlist_title_label.setAlignment(Qt.AlignCenter)
        self.playlist_title_label.setStyleSheet("color: #ff9900; font-size: 13px; font-weight: bold; background: transparent; padding: 8px;")
        right_layout.addWidget(self.playlist_title_label)
        
        # Виджет плейлиста (копия из AudioPlayerDialog)
        from player import AudioPlaylistWidget
        if self.shared_tts_duration_cache is not None:
            self._tts_duration_cache = self.shared_tts_duration_cache
        else:
            self._tts_duration_cache = {}  # Локальный кэш
        self.tts_playlist_widget = AudioPlaylistWidget(self.current_language, self, shared_duration_cache=self._tts_duration_cache, show_checkboxes=True, show_link_column=False)
        right_layout.addWidget(self.tts_playlist_widget)
        
        # Собираем сплиттер
        self.tts_splitter.addWidget(left_panel)
        self.tts_splitter.addWidget(right_panel)
        
        # Пропорции по умолчанию: 800px левая, 500px правая
        self.tts_splitter.setSizes([800, 500])
        self.tts_splitter.setStretchFactor(0, 1)
        self.tts_splitter.setStretchFactor(1, 0) # Плейлист не растягивается по умолчанию сильнее левой части
        
        main_layout.addWidget(self.tts_splitter, 1)  # stretch=1, чтобы занимал всё пространство
        
        # --- ТЕМНЫЙ ФУТЕР ---
        self.footer_panel = QFrame()
        self.footer_panel.setFixedHeight(60)
        self.footer_panel.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
            }
        """)
        footer_layout = QHBoxLayout(self.footer_panel)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        
        self.btn_cancel = QPushButton(get_translation(self.current_language, 'close_btn'))
        self.btn_cancel.setFixedSize(120, 32)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border-radius: 16px;
                padding: 0px 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:pressed { background-color: #d0d0d0; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_apply = QPushButton(get_translation(self.current_language, 'tts_btn_apply'))
        self.btn_apply.setFixedSize(310, 32)
        self.btn_apply.setCursor(Qt.PointingHandCursor)
        self.btn_apply.setEnabled(False)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #ff9900;
                color: #000000;
                border-radius: 16px;
                padding: 0px 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #e68a00; }
            QPushButton:pressed { background-color: #cc7a00; }
            QPushButton:disabled { background-color: #555; color: #888; }
        """)
        self.btn_apply.clicked.connect(self._on_apply_checked_clicked)
        
        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_apply)
        
        # РАЗДЕЛИТЕЛЬ (максимально тонкий 1px)
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #777777; border: none;")
        main_layout.addWidget(line)
        
        main_layout.addWidget(self.footer_panel)
        
        # Уменьшаем отступы до минимума для футера, но оставляем зазор для рамки (2px как в других окнах)
        # Устанавливаем spacing(0) чтобы разделитель был вплотную к футеру
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)
        # Но для верхнего контента добавим отступы через горизонтальные слои или добавим внутренний лайаут
        # Но проще добавить отступы в компоненты или в табы
        
        # Таймер и воркеры
        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self._check_playback)
        self.play_timer.start(100)
        
        self.download_worker = None
        self.xtts_worker = None
        self.lib_worker = None
        
        # Загрузка настроек
        self._load_settings()
        
        # Обработка смены вкладок
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._on_tab_changed()
        
        # Заполнение плейлиста аудиофайлами из миссии
        self._populate_tts_playlist()

    def update_ui_texts(self):
        """Обновление текстов при смене языка в главном окне."""
        main_app = self._get_main_app()
        if main_app:
            self.current_language = getattr(main_app, 'current_language', self.current_language)
            
        from localization import get_translation
        
        # Заголовок окна
        self.setWindowTitle(get_translation(self.current_language, 'tts_window_title'))
        
        # Вкладки
        self.tabs.setTabText(0, get_translation(self.current_language, 'tts_tab_piper'))
        self.tabs.setTabText(1, get_translation(self.current_language, 'tts_tab_xtts'))
        
        # Общие элементы
        self.cb_filter_symbols.setText(get_translation(self.current_language, 'tts_filter_symbols'))
        self.cb_replace_symbols.setText(get_translation(self.current_language, 'tts_replace_symbol_from'))
        self.lbl_replace_to_label.setText(get_translation(self.current_language, 'tts_replace_symbol_to'))
        self.register_custom_tooltip(self.cb_replace_symbols, get_translation(self.current_language, 'tts_replace_symbol_tooltip'))
        
        if not self._batch_mode:
            self.btn_main_action.setText(get_translation(self.current_language, 'tts_btn_generate'))
        self.register_custom_tooltip(self.btn_main_action, get_translation(self.current_language, 'tts_btn_generate_tooltip'))
        self.cb_auto_play.setText(get_translation(self.current_language, 'tts_auto_play'))
        self.register_custom_tooltip(self.cb_auto_play, get_translation(self.current_language, 'tts_auto_play_tooltip'))
        
        self.playlist_title_label.setText(get_translation(self.current_language, 'tts_playlist_title'))
        self.btn_cancel.setText(get_translation(self.current_language, 'close_btn'))
        self.btn_apply.setText(get_translation(self.current_language, 'tts_btn_apply'))
        
        # Вкладка Piper
        if hasattr(self, 'lbl_piper_info'):
            self.lbl_piper_info.setText(get_translation(self.current_language, 'tts_piper_info'))
            if self.engine and not self.engine._check_piper_available():
                self.btn_install_piper.setText(get_translation(self.current_language, 'tts_btn_engine'))
            else:
                self.btn_install_piper.setText(get_translation(self.current_language, 'tts_status_piper_ok'))
            self.register_custom_tooltip(self.btn_install_piper, get_translation(self.current_language, 'tts_btn_engine_tooltip'))
            self.lbl_piper_lang.setText(get_translation(self.current_language, 'tts_lbl_lang'))
            self.lbl_piper_voice.setText(get_translation(self.current_language, 'tts_lbl_voice'))
            self.lbl_piper_speed.setText(get_translation(self.current_language, 'tts_lbl_speed'))
            self.register_custom_tooltip(self.lbl_piper_speed, get_translation(self.current_language, 'tts_lbl_speed_tooltip'))
            self.lbl_piper_pause.setText(get_translation(self.current_language, 'tts_lbl_pause'))
            self.register_custom_tooltip(self.lbl_piper_pause, get_translation(self.current_language, 'tts_lbl_pause_tooltip'))
            self.lbl_piper_noise.setText(get_translation(self.current_language, 'tts_lbl_noise'))
            self.register_custom_tooltip(self.lbl_piper_noise, get_translation(self.current_language, 'tts_lbl_noise_tooltip'))
            self.btn_reset_piper.setText(get_translation(self.current_language, 'tts_btn_reset'))
            self.register_custom_tooltip(self.btn_reset_piper, get_translation(self.current_language, 'tts_btn_reset_tooltip'))
            
        # Вкладка XTTS
        if hasattr(self, 'lbl_xtts_info'):
            self.lbl_xtts_info.setText(get_translation(self.current_language, 'tts_xtts_info'))
            self.register_custom_tooltip(self.btn_install_xtts_libs, get_translation(self.current_language, 'tts_btn_libs_tooltip'))
            self.register_custom_tooltip(self.btn_install_xtts_model, get_translation(self.current_language, 'tts_btn_model_tooltip'))
            self.lbl_xtts_lang_label.setText(get_translation(self.current_language, 'tts_lbl_lang'))
            self.lbl_xtts_voice_label.setText(get_translation(self.current_language, 'tts_lbl_voice'))
            self.lbl_speaker_wav.setText(get_translation(self.current_language, 'tts_lbl_wav'))
            self.edit_speaker_wav.setPlaceholderText(get_translation(self.current_language, 'tts_wav_placeholder'))
            self.lbl_xtts_speed_label.setText(get_translation(self.current_language, 'tts_lbl_xtts_speed'))
            self.register_custom_tooltip(self.lbl_xtts_speed_label, get_translation(self.current_language, 'tts_lbl_xtts_speed_tooltip'))
            self.lbl_xtts_temp_label.setText(get_translation(self.current_language, 'tts_lbl_xtts_temp'))
            self.register_custom_tooltip(self.lbl_xtts_temp_label, get_translation(self.current_language, 'tts_lbl_xtts_temp_tooltip'))
            self.lbl_xtts_rep_label.setText(get_translation(self.current_language, 'tts_lbl_xtts_rep'))
            self.register_custom_tooltip(self.lbl_xtts_rep_label, get_translation(self.current_language, 'tts_lbl_xtts_rep_tooltip'))
            self.lbl_xtts_k_label.setText(get_translation(self.current_language, 'tts_lbl_xtts_k'))
            self.register_custom_tooltip(self.lbl_xtts_k_label, get_translation(self.current_language, 'tts_lbl_xtts_k_tooltip'))
            self.lbl_xtts_p_label.setText(get_translation(self.current_language, 'tts_lbl_xtts_p'))
            self.register_custom_tooltip(self.lbl_xtts_p_label, get_translation(self.current_language, 'tts_lbl_xtts_p_tooltip'))
            self.lbl_xtts_len_label.setText(get_translation(self.current_language, 'tts_lbl_xtts_len'))
            self.register_custom_tooltip(self.lbl_xtts_len_label, get_translation(self.current_language, 'tts_lbl_xtts_len_tooltip'))
            self.btn_reset_xtts.setText(get_translation(self.current_language, 'tts_btn_reset'))
            self.register_custom_tooltip(self.btn_reset_xtts, get_translation(self.current_language, 'tts_btn_reset_xtts_tooltip'))
            
            # Обновляем 'Clone' в combo_xtts_voice
            clone_text = get_translation(self.current_language, 'tts_xtts_clone')
            self.combo_xtts_voice.setItemText(0, clone_text)

        if hasattr(self, 'tts_playlist_widget'):
            self.tts_playlist_widget.retranslate_ui(self.current_language)

        self._update_ui_state()

    def _setup_tab_piper(self):
        layout = QVBoxLayout(self.tab_piper)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Верхний ряд: Инфо + Кнопка установки
        top_row = QHBoxLayout()
        from localization import get_translation
        self.lbl_piper_info = QLabel(get_translation(self.current_language, 'tts_piper_info'))
        self.lbl_piper_info.setStyleSheet("color: #aaa; font-size: 10px; background: transparent;")
        top_row.addWidget(self.lbl_piper_info, 1)

        self.btn_install_piper = QPushButton(get_translation(self.current_language, 'tts_btn_engine'))
        self.register_custom_tooltip(self.btn_install_piper, get_translation(self.current_language, 'tts_btn_engine_tooltip'))
        self.btn_install_piper.setCursor(Qt.ArrowCursor)
        self.btn_install_piper.setStyleSheet("QPushButton { background-color: #333; color: #fff; border: 1px solid #444; border-radius: 4px; padding: 2px 8px; font-size: 10px; }")
        self.btn_install_piper.clicked.connect(self._start_piper_engine_install)
        top_row.addWidget(self.btn_install_piper)
        layout.addLayout(top_row)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnMinimumWidth(0, 80)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1) # Phantom stretch column

        premium_combo_style = self._get_premium_combo_style()

        self.lbl_piper_lang = QLabel(get_translation(self.current_language, 'tts_lbl_lang'))
        self.lbl_piper_lang.setStyleSheet("color: #ffffff; background: transparent;")
        grid.addWidget(self.lbl_piper_lang, 0, 0)
        
        lang_hbox = QHBoxLayout()
        lang_hbox.setContentsMargins(0, 0, 0, 0)
        self.combo_lang = QComboBox()
        self.combo_lang.setCursor(Qt.PointingHandCursor)
        self.combo_lang.setStyleSheet(premium_combo_style)
        lang_hbox.addWidget(self.combo_lang)
        lang_hbox.addStretch()
        grid.addLayout(lang_hbox, 0, 1, Qt.AlignLeft)

        self.lbl_piper_voice = QLabel(get_translation(self.current_language, 'tts_lbl_voice'))
        self.lbl_piper_voice.setStyleSheet("color: #ffffff; background: transparent;")
        grid.addWidget(self.lbl_piper_voice, 1, 0)
        
        voice_hbox = QHBoxLayout()
        voice_hbox.setContentsMargins(0, 0, 0, 0)
        voice_hbox.setSpacing(5)
        self.combo_voice = QComboBox()
        self.combo_voice.setCursor(Qt.PointingHandCursor)
        self.combo_voice.setStyleSheet(premium_combo_style)
        voice_hbox.addWidget(self.combo_voice)
        
        self.lbl_voice_status = QLabel("")
        self.lbl_voice_status.setFixedWidth(20)
        self.lbl_voice_status.setAlignment(Qt.AlignCenter)
        voice_hbox.addWidget(self.lbl_voice_status)
        voice_hbox.addStretch()
        grid.addLayout(voice_hbox, 1, 1, Qt.AlignLeft)

        layout.addLayout(grid)

        # Слайдеры Piper (3 штуки)
        sliders_grid = QGridLayout()
        sliders_grid.setSpacing(8)

        self.lbl_piper_speed = QLabel(get_translation(self.current_language, 'tts_lbl_speed'))
        self.lbl_piper_speed.setStyleSheet("color: #ffffff; background: transparent; font-size: 12px;")
        self.register_custom_tooltip(self.lbl_piper_speed, get_translation(self.current_language, 'tts_lbl_speed_tooltip'))
        self.slider_speed = JumpSlider(Qt.Horizontal)
        self.slider_speed.setRange(50, 200); self.slider_speed.setValue(100)
        self.lbl_speed_val = QLabel("1.0x")
        self.lbl_speed_val.setStyleSheet("color: #ff9900; background: transparent; min-width: 35px; font-size: 12px;")
        self.slider_speed.valueChanged.connect(self._on_piper_params_changed)
        self.slider_speed.valueChanged.connect(lambda v: self.lbl_speed_val.setText(f"{v/100:.1f}x"))

        self.lbl_piper_pause = QLabel(get_translation(self.current_language, 'tts_lbl_pause'))
        self.lbl_piper_pause.setStyleSheet("color: #ffffff; background: transparent; font-size: 12px;")
        self.register_custom_tooltip(self.lbl_piper_pause, get_translation(self.current_language, 'tts_lbl_pause_tooltip'))
        self.slider_silence = JumpSlider(Qt.Horizontal)
        self.slider_silence.setRange(0, 100); self.slider_silence.setValue(20)
        self.lbl_silence_val = QLabel("0.2s")
        self.lbl_silence_val.setStyleSheet("color: #ff9900; background: transparent; min-width: 35px; font-size: 12px;")
        self.slider_silence.valueChanged.connect(self._on_piper_params_changed)
        self.slider_silence.valueChanged.connect(lambda v: self.lbl_silence_val.setText(f"{v/100:.1f}s"))

        self.lbl_piper_noise = QLabel(get_translation(self.current_language, 'tts_lbl_noise'))
        self.lbl_piper_noise.setStyleSheet("color: #ffffff; background: transparent; font-size: 12px;")
        self.register_custom_tooltip(self.lbl_piper_noise, get_translation(self.current_language, 'tts_lbl_noise_tooltip'))
        self.slider_noise = JumpSlider(Qt.Horizontal)
        self.slider_noise.setRange(0, 100); self.slider_noise.setValue(66) # Default noise_scale 0.667
        self.lbl_noise_val = QLabel("0.66")
        self.lbl_noise_val.setStyleSheet("color: #ff9900; background: transparent; min-width: 35px; font-size: 12px;")
        self.slider_noise.valueChanged.connect(self._on_piper_params_changed)
        self.slider_noise.valueChanged.connect(lambda v: self.lbl_noise_val.setText(f"{v/100:.2f}"))

        slider_style = self._get_slider_style()
        self.slider_speed.setStyleSheet(slider_style)
        self.slider_silence.setStyleSheet(slider_style)
        self.slider_noise.setStyleSheet(slider_style)

        sliders_grid.addWidget(self.lbl_piper_speed, 0, 0)
        sliders_grid.addWidget(self.slider_speed, 0, 1)
        sliders_grid.addWidget(self.lbl_speed_val, 0, 2)
        
        sliders_grid.addWidget(self.lbl_piper_pause, 1, 0)
        sliders_grid.addWidget(self.slider_silence, 1, 1)
        sliders_grid.addWidget(self.lbl_silence_val, 1, 2)

        sliders_grid.addWidget(self.lbl_piper_noise, 2, 0)
        sliders_grid.addWidget(self.slider_noise, 2, 1)
        sliders_grid.addWidget(self.lbl_noise_val, 2, 2)

        layout.addLayout(sliders_grid)
        
        # Кнопка сброса
        reset_h_box = QHBoxLayout()
        reset_h_box.addStretch()
        self.btn_reset_piper = QPushButton(get_translation(self.current_language, 'tts_btn_reset'))
        self.btn_reset_piper.setCursor(Qt.PointingHandCursor)
        self.btn_reset_piper.setStyleSheet(self._get_reset_btn_style())
        self.btn_reset_piper.clicked.connect(self._reset_piper_sliders)
        self.register_custom_tooltip(self.btn_reset_piper, get_translation(self.current_language, 'tts_btn_reset_tooltip'))
        reset_h_box.addWidget(self.btn_reset_piper)
        layout.addLayout(reset_h_box)

        layout.addStretch()
        
        # События
        # Приводим к формату "КОД Название" по просьбе пользователя
        lang_names = {
            'ru': 'RU Русский', 'en': 'EN English', 'de': 'DE Deutsch', 
            'fr': 'FR Français', 'es': 'ES Español', 'it': 'IT Italiano',
            'zh': 'ZH 中文 (Chinese)', 'uk': 'UK Українська', 'pl': 'PL Polski',
            'pt': 'PT Português', 'tr': 'TR Türkçe', 'nl': 'NL Nederlands',
            'fi': 'FI Suomi', 'sv': 'SV Svenska', 'da': 'DA Dansk',
            'no': 'NO Norsk', 'el': 'EL Ελληνικά', 'ar': 'AR العربية (Arabic)',
            'hi': 'HI हिन्दी (Hindi)', 'vi': 'VI Tiếng Việt', 'kk': 'KK Қазақша',
            'bg': 'BG Български', 'cs': 'CS Čeština', 'hu': 'HU Magyar',
            'sk': 'SK Slovenčina', 'sl': 'SL Slovenščina', 'ro': 'RO Română',
            'cy': 'CY Welsh', 'fa': 'FA Persian', 'id': 'ID Indonesian',
            'is': 'IS Icelandic', 'ka': 'KA Georgian', 'lb': 'LB Luxembourgish',
            'lv': 'LV Latvian', 'ml': 'ML Malayalam', 'ne': 'NE Nepali',
            'sr': 'SR Serbian', 'sw': 'SW Swahili', 'te': 'TE Telugu',
            'ca': 'CA Català'
        }
        
        # Сортируем ключи по отображаемому имени
        def get_display_name(code):
            return lang_names.get(code, f"{code.upper()} ({code})")

        sorted_langs = sorted(self.registry.keys(), key=get_display_name)
        
        for lang_code in sorted_langs:
            self.combo_lang.addItem(get_display_name(lang_code), lang_code)
            
        self.combo_lang.currentIndexChanged.connect(self._on_piper_lang_changed)
        self.combo_voice.currentIndexChanged.connect(self._on_piper_voice_changed)

    def _setup_tab_xtts(self):
        layout = QVBoxLayout(self.tab_xtts)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Верхний ряд: Инфо слева + Кнопки установки справа
        top_row = QHBoxLayout()
        from localization import get_translation
        self.lbl_xtts_info = QLabel(get_translation(self.current_language, 'tts_xtts_info'))
        self.lbl_xtts_info.setWordWrap(True)
        self.lbl_xtts_info.setStyleSheet("color: #aaa; font-size: 10px; background: transparent;")
        top_row.addWidget(self.lbl_xtts_info, 1)
        
        # Кнопки в правом верхнем углу
        install_btns_layout = QHBoxLayout()
        install_btns_layout.setSpacing(5)
        
        btn_style = "QPushButton { background-color: #333; color: #fff; border: 1px solid #444; border-radius: 4px; padding: 2px 8px; font-size: 10px; }"
        
        self.btn_install_xtts_libs = QPushButton(get_translation(self.current_language, 'tts_btn_libs'))
        self.btn_install_xtts_libs.setStyleSheet(btn_style)
        self.btn_install_xtts_libs.setCursor(Qt.ArrowCursor)
        self.register_custom_tooltip(self.btn_install_xtts_libs, get_translation(self.current_language, 'tts_btn_libs_tooltip'))
        self.btn_install_xtts_libs.clicked.connect(self._start_library_install)
        
        self.btn_install_xtts_model = QPushButton(get_translation(self.current_language, 'tts_btn_model'))
        self.btn_install_xtts_model.setStyleSheet(btn_style)
        self.btn_install_xtts_model.setCursor(Qt.ArrowCursor)
        self.register_custom_tooltip(self.btn_install_xtts_model, get_translation(self.current_language, 'tts_btn_model_tooltip'))
        self.btn_install_xtts_model.clicked.connect(self._start_xtts_download)
        
        self.lbl_xtts_status = QLabel(get_translation(self.current_language, 'tts_lbl_xtts_status'))
        self.lbl_xtts_status.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.lbl_xtts_status.setStyleSheet("color: #888; font-size: 10px; background: transparent; margin-right: 5px;")
        
        install_btns_layout.addWidget(self.lbl_xtts_status)
        install_btns_layout.addWidget(self.btn_install_xtts_libs)
        install_btns_layout.addWidget(self.btn_install_xtts_model)
        
        # Контейнер для кнопок и статуса справа вверху
        right_top_vbox = QVBoxLayout()
        right_top_vbox.setSpacing(4)
        right_top_vbox.addLayout(install_btns_layout)
        
        # (self.lbl_xtts_status уже добавлен выше)
        
        top_row.addLayout(right_top_vbox)
        layout.addLayout(top_row)
        
        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnMinimumWidth(0, 80) # Фиксированная ширина для меток
        grid.setColumnStretch(1, 0)       # Меню не растягиваются
        grid.setColumnStretch(2, 1)       # WAV теперь растягивается
        grid.setColumnStretch(3, 0)       # Больше не растягиваем пустую колонку
        
        # Переносим стили в общий метод
        premium_combo_style = self._get_premium_combo_style()

        # Язык XTTS (строка 0)
        self.lbl_xtts_lang_label = QLabel(get_translation(self.current_language, 'tts_lbl_lang'))
        self.lbl_xtts_lang_label.setStyleSheet("color: #ffffff; background: transparent;")
        grid.addWidget(self.lbl_xtts_lang_label, 0, 0)
        
        xtts_lang_hbox = QHBoxLayout()
        self.combo_xtts_lang = QComboBox()
        self.combo_xtts_lang.setCursor(Qt.PointingHandCursor)
        xtts_langs = [
            ("Русский", "ru"), ("English", "en"), ("Français", "fr"), ("Deutsch", "de"),
            ("Español", "es"), ("Italiano", "it"), ("Português", "pt"), ("Polski", "pl"),
            ("Türkçe", "tr"), ("Nederlands", "nl"), ("Čeština", "cs"), ("العربية", "ar"),
            ("中文", "zh-cn"), ("日本語", "ja"), ("Magyar", "hu"), ("한국어", "ko"), ("हिन्दी", "hi")
        ]
        for name, code in xtts_langs:
            self.combo_xtts_lang.addItem(name, code)
        self.combo_xtts_lang.setStyleSheet(premium_combo_style)
        self.combo_xtts_lang.currentIndexChanged.connect(self._on_xtts_lang_changed)
        xtts_lang_hbox.addWidget(self.combo_xtts_lang)
        xtts_lang_hbox.addStretch()
        grid.addLayout(xtts_lang_hbox, 0, 1, 1, 1, Qt.AlignLeft)
        
        # Голос (строка 1)
        self.lbl_xtts_voice_label = QLabel(get_translation(self.current_language, 'tts_lbl_voice'))
        self.lbl_xtts_voice_label.setStyleSheet("color: #ffffff; background: transparent;")
        grid.addWidget(self.lbl_xtts_voice_label, 1, 0)
        
        # Col 1: Комбо выбора голоса
        voice_dropdown_hbox = QHBoxLayout()
        voice_dropdown_hbox.setContentsMargins(0, 0, 0, 0)
        self.combo_xtts_voice = QComboBox()
        self.combo_xtts_voice.setCursor(Qt.PointingHandCursor)
        self.combo_xtts_voice.addItem(get_translation(self.current_language, 'tts_xtts_clone'), "clone")
        from tts_engine import XTTS_STANDARD_VOICES
        for voice in XTTS_STANDARD_VOICES:
            self.combo_xtts_voice.addItem(f"🎙 {voice}", voice)
        self.combo_xtts_voice.setStyleSheet(premium_combo_style)
        self.combo_xtts_voice.currentIndexChanged.connect(self._on_xtts_voice_type_changed)
        voice_dropdown_hbox.addWidget(self.combo_xtts_voice)
        voice_dropdown_hbox.addStretch()
        grid.addLayout(voice_dropdown_hbox, 1, 1, Qt.AlignLeft)
        
        # Col 2: Выбор образца (WAV)
        voice_wav_hbox = QHBoxLayout()
        voice_wav_hbox.setContentsMargins(0, 0, 0, 0)
        voice_wav_hbox.setSpacing(8)
        
        self.lbl_speaker_wav = QLabel(get_translation(self.current_language, 'tts_lbl_wav'))
        self.lbl_speaker_wav.setStyleSheet("color: #ffffff; background: transparent; margin-left: 5px;")
        voice_wav_hbox.addWidget(self.lbl_speaker_wav)
        
        self.edit_speaker_wav = QLineEdit()
        self.edit_speaker_wav.setPlaceholderText(get_translation(self.current_language, 'tts_wav_placeholder'))
        self.edit_speaker_wav.setReadOnly(True)
        self.edit_speaker_wav.setStyleSheet("background: #1a1a1a; color: #fff; border: 1px solid #333; border-radius: 4px; padding: 2px 5px; font-size: 10px;")
        voice_wav_hbox.addWidget(self.edit_speaker_wav)
        
        self.btn_browse_wav = QPushButton("📁")
        self.btn_browse_wav.setCursor(Qt.PointingHandCursor)
        self.btn_browse_wav.setFixedWidth(30)
        self.btn_browse_wav.setStyleSheet("""
            QPushButton { background-color: #444; color: white; border-radius: 4px; padding: 2px; }
            QPushButton:hover { background-color: #555; }
        """)
        self.btn_browse_wav.clicked.connect(self._on_browse_speaker_wav)
        voice_wav_hbox.addWidget(self.btn_browse_wav)
        
        grid.addLayout(voice_wav_hbox, 1, 2)
        layout.addLayout(grid)

        # Слайдеры XTTS
        sliders_grid = QGridLayout()
        sliders_grid.setSpacing(8)

        self.lbl_xtts_speed_label = QLabel(get_translation(self.current_language, 'tts_lbl_xtts_speed'))
        self.lbl_xtts_speed_label.setStyleSheet("color: #ffffff; background: transparent; font-size: 12px;")
        self.register_custom_tooltip(self.lbl_xtts_speed_label, get_translation(self.current_language, 'tts_lbl_xtts_speed_tooltip'))
        self.slider_xtts_speed = JumpSlider(Qt.Horizontal)
        self.slider_xtts_speed.setRange(50, 200); self.slider_xtts_speed.setValue(100)
        self.lbl_xtts_speed_val = QLabel("1.0x")
        self.lbl_xtts_speed_val.setStyleSheet("color: #ff9900; background: transparent; min-width: 35px; font-size: 12px;")
        self.slider_xtts_speed.valueChanged.connect(self._on_xtts_params_changed)
        self.slider_xtts_speed.valueChanged.connect(lambda v: self.lbl_xtts_speed_val.setText(f"{v/100:.1f}x"))
        
        self.lbl_xtts_temp_label = QLabel(get_translation(self.current_language, 'tts_lbl_xtts_temp'))
        self.lbl_xtts_temp_label.setStyleSheet("color: #ffffff; background: transparent; font-size: 12px;")
        self.register_custom_tooltip(self.lbl_xtts_temp_label, get_translation(self.current_language, 'tts_lbl_xtts_temp_tooltip'))
        self.slider_xtts_temp = JumpSlider(Qt.Horizontal)
        self.slider_xtts_temp.setRange(10, 100); self.slider_xtts_temp.setValue(75)
        self.lbl_xtts_temp_val = QLabel("0.75")
        self.lbl_xtts_temp_val.setStyleSheet("color: #ff9900; background: transparent; min-width: 35px; font-size: 12px;")
        self.slider_xtts_temp.valueChanged.connect(self._on_xtts_params_changed)
        self.slider_xtts_temp.valueChanged.connect(lambda v: self.lbl_xtts_temp_val.setText(f"{v/100:.2f}"))

        # 3. Штраф за повторы (Repetition Penalty)
        self.lbl_xtts_rep_label = QLabel(get_translation(self.current_language, 'tts_lbl_xtts_rep'))
        self.lbl_xtts_rep_label.setStyleSheet("color: #ffffff; background: transparent; font-size: 12px;")
        self.register_custom_tooltip(self.lbl_xtts_rep_label, get_translation(self.current_language, 'tts_lbl_xtts_rep_tooltip'))
        self.slider_xtts_rep = JumpSlider(Qt.Horizontal)
        self.slider_xtts_rep.setRange(10, 100); self.slider_xtts_rep.setValue(20) # Default 2.0 (mapped as 10-100 for 1.0-10.0)
        
        self.lbl_xtts_rep_val = QLabel("2.0")
        self.lbl_xtts_rep_val.setStyleSheet("color: #ff9900; background: transparent; min-width: 35px; font-size: 12px;")
        self.slider_xtts_rep.valueChanged.connect(self._on_xtts_params_changed)
        self.slider_xtts_rep.valueChanged.connect(lambda v: self.lbl_xtts_rep_val.setText(f"{v/10:.1f}"))

        slider_style = """
            QSlider::groove:horizontal { background: #1a1a1a; height: 4px; border-radius: 2px; }
            QSlider::handle:horizontal { background: #ff9900; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
        """
        self.slider_xtts_speed.setStyleSheet(slider_style)
        self.slider_xtts_temp.setStyleSheet(slider_style)
        self.slider_xtts_rep.setStyleSheet(slider_style)

        sliders_grid.addWidget(self.lbl_xtts_speed_label, 0, 0)
        sliders_grid.addWidget(self.slider_xtts_speed, 0, 1)
        sliders_grid.addWidget(self.lbl_xtts_speed_val, 0, 2)
        
        sliders_grid.addWidget(self.lbl_xtts_temp_label, 1, 0)
        sliders_grid.addWidget(self.slider_xtts_temp, 1, 1)
        sliders_grid.addWidget(self.lbl_xtts_temp_val, 1, 2)

        sliders_grid.addWidget(self.lbl_xtts_rep_label, 2, 0)
        sliders_grid.addWidget(self.slider_xtts_rep, 2, 1)
        sliders_grid.addWidget(self.lbl_xtts_rep_val, 2, 2)

        # 4. Top-K
        self.lbl_xtts_k_label = QLabel(get_translation(self.current_language, 'tts_lbl_xtts_k'))
        self.lbl_xtts_k_label.setStyleSheet("color: #ffffff; background: transparent; font-size: 12px;")
        self.register_custom_tooltip(self.lbl_xtts_k_label, get_translation(self.current_language, 'tts_lbl_xtts_k_tooltip'))
        self.slider_xtts_k = JumpSlider(Qt.Horizontal)
        self.slider_xtts_k.setRange(1, 100); self.slider_xtts_k.setValue(50)
        self.lbl_xtts_k_val = QLabel("50")
        self.lbl_xtts_k_val.setStyleSheet("color: #ff9900; background: transparent; min-width: 35px; font-size: 12px;")
        self.slider_xtts_k.valueChanged.connect(self._on_xtts_params_changed)
        self.slider_xtts_k.valueChanged.connect(lambda v: self.lbl_xtts_k_val.setText(str(v)))
        self.slider_xtts_k.setStyleSheet(slider_style)
        
        sliders_grid.addWidget(self.lbl_xtts_k_label, 0, 3)
        sliders_grid.addWidget(self.slider_xtts_k, 0, 4)
        sliders_grid.addWidget(self.lbl_xtts_k_val, 0, 5)

        # 5. Top-P
        self.lbl_xtts_p_label = QLabel(get_translation(self.current_language, 'tts_lbl_xtts_p'))
        self.lbl_xtts_p_label.setStyleSheet("color: #ffffff; background: transparent; font-size: 12px;")
        self.register_custom_tooltip(self.lbl_xtts_p_label, get_translation(self.current_language, 'tts_lbl_xtts_p_tooltip'))
        self.slider_xtts_p = JumpSlider(Qt.Horizontal)
        self.slider_xtts_p.setRange(0, 100); self.slider_xtts_p.setValue(80)
        self.lbl_xtts_p_val = QLabel("0.80")
        self.lbl_xtts_p_val.setStyleSheet("color: #ff9900; background: transparent; min-width: 35px; font-size: 12px;")
        self.slider_xtts_p.valueChanged.connect(self._on_xtts_params_changed)
        self.slider_xtts_p.valueChanged.connect(lambda v: self.lbl_xtts_p_val.setText(f"{v/100:.2f}"))
        self.slider_xtts_p.setStyleSheet(slider_style)
        
        sliders_grid.addWidget(self.lbl_xtts_p_label, 1, 3)
        sliders_grid.addWidget(self.slider_xtts_p, 1, 4)
        sliders_grid.addWidget(self.lbl_xtts_p_val, 1, 5)

        # 6. Length Penalty
        self.lbl_xtts_len_label = QLabel(get_translation(self.current_language, 'tts_lbl_xtts_len'))
        self.lbl_xtts_len_label.setStyleSheet("color: #ffffff; background: transparent; font-size: 12px;")
        self.register_custom_tooltip(self.lbl_xtts_len_label, get_translation(self.current_language, 'tts_lbl_xtts_len_tooltip'))
        self.slider_xtts_len = JumpSlider(Qt.Horizontal)
        self.slider_xtts_len.setRange(0, 500); self.slider_xtts_len.setValue(100) # 0.0 to 5.0
        self.lbl_xtts_len_val = QLabel("1.0")
        self.lbl_xtts_len_val.setStyleSheet("color: #ff9900; background: transparent; min-width: 35px; font-size: 12px;")
        self.slider_xtts_len.valueChanged.connect(self._on_xtts_params_changed)
        self.slider_xtts_len.valueChanged.connect(lambda v: self.lbl_xtts_len_val.setText(f"{v/100:.1f}"))
        self.slider_xtts_len.setStyleSheet(slider_style)
        
        sliders_grid.addWidget(self.lbl_xtts_len_label, 2, 3)
        sliders_grid.addWidget(self.slider_xtts_len, 2, 4)
        sliders_grid.addWidget(self.lbl_xtts_len_val, 2, 5)

        layout.addLayout(sliders_grid)
        
        # Кнопка сброса
        reset_h_box = QHBoxLayout()
        reset_h_box.addStretch()
        self.btn_reset_xtts = QPushButton(get_translation(self.current_language, 'tts_btn_reset'))
        self.btn_reset_xtts.setCursor(Qt.PointingHandCursor)
        self.btn_reset_xtts.setStyleSheet(self._get_reset_btn_style())
        self.btn_reset_xtts.clicked.connect(self._reset_xtts_sliders)
        self.register_custom_tooltip(self.btn_reset_xtts, get_translation(self.current_language, 'tts_btn_reset_xtts_tooltip'))
        reset_h_box.addWidget(self.btn_reset_xtts)
        layout.addLayout(reset_h_box)
        
        layout.addStretch()

    def _on_xtts_voice_type_changed(self):
        is_clone = self.combo_xtts_voice.currentData() == "clone"
        self.lbl_speaker_wav.setVisible(is_clone)
        self.edit_speaker_wav.setVisible(is_clone)
        self.btn_browse_wav.setVisible(is_clone)
        
        if not is_clone:
            self.settings.setValue("tts_xtts_default_voice", self.combo_xtts_voice.currentData())
        
        self._update_ui_state()

    def _get_premium_combo_style(self):
        return """
            QComboBox {
                background-color: #222;
                color: #ff9900;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 2px 15px 2px 8px;
                min-height: 22px;
                max-width: 250px;
                font-weight: bold;
                combobox-popup: 0;
            }
            QComboBox::item { text-align: left; }
            QComboBox::drop-down {
                subcontrol-origin: margin;
                subcontrol-position: top right;
                width: 18px;
                border-left: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ff9900;
            }
            QComboBox QAbstractItemView {
                background-color: #222;
                color: #fff;
                selection-background-color: #ff9900;
                selection-color: #000;
                border: 1px solid #444;
                outline: none;
            }
        """ + self._get_scrollbar_style()

    def _get_slider_style(self):
        return """
            QSlider::groove:horizontal { background: #1a1a1a; height: 4px; border-radius: 2px; }
            QSlider::handle:horizontal { background: #ff9900; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
        """

    def _show_manual_install_dialog(self):
        """Открывает окно с ручными инструкциями по установке."""
        dlg = TTSManualInstallDialog(self.current_language, self)
        dlg.exec_()

    def _get_main_btn_style(self, type="normal"):
        return """
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                border: 1px solid #ffffff;
                border-radius: 16px;
                padding: 0px 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { border-color: #ff9900; color: #ff9900; }
            QPushButton:pressed { background-color: rgba(255,255,255,0.04); }
            QPushButton:disabled { border-color: #555; color: #555; }
        """

    def _get_reset_btn_style(self):
        return """
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                border: none;
                font-size: 10px;
                text-decoration: none;
            }
            QPushButton:hover {
                color: #ff9900;
                text-decoration: underline;
            }
        """

    def _get_scrollbar_style(self):
        return """
            QScrollBar:vertical {
                background: #2a2a2a; width: 14px; margin: 16px 2px 16px 2px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #ff9900; min-height: 20px; border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover { background: #e68a00; }
            QScrollBar::sub-line:vertical {
                background: none; border: none; height: 16px;
                subcontrol-position: top; subcontrol-origin: margin;
            }
            QScrollBar::add-line:vertical {
                background: none; border: none; height: 16px;
                subcontrol-position: bottom; subcontrol-origin: margin;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                width: 10px; height: 10px; background: #ff9900; border-radius: 5px; margin: 2px;
            }
            
            QScrollBar:horizontal {
                background: #2a2a2a; height: 14px; margin: 2px 16px 2px 16px; border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #ff9900; min-width: 20px; border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover { background: #e68a00; }
            QScrollBar::sub-line:horizontal {
                background: none; border: none; width: 16px;
                subcontrol-position: left; subcontrol-origin: margin;
            }
            QScrollBar::add-line:horizontal {
                background: none; border: none; width: 16px;
                subcontrol-position: right; subcontrol-origin: margin;
            }
            QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
                width: 10px; height: 10px; background: #ff9900; border-radius: 5px; margin: 2px;
            }
        """

    def _load_settings(self):
        # Восстановление состояния сплиттера
        splitter_state = self.settings.value("tts_splitter_state")
        if splitter_state:
            self.tts_splitter.restoreState(splitter_state)

        # Восстановление таба
        last_engine = self.settings.value("tts_last_engine", "piper")
        if last_engine == "xtts": self.tabs.setCurrentIndex(1)
        else: self.tabs.setCurrentIndex(0)
        
        # Восстановление Piper
        saved_lang = self.settings.value("tts_last_lang", "ru")
        idx = self.combo_lang.findData(saved_lang)
        if idx >= 0: 
            self.combo_lang.setCurrentIndex(idx)
        
        # ВАЖНО: Всегда вызываем при загрузке, так как setCurrentIndex не кинет сигнал
        # если индекс совпадает с дефолтным (0), а список голосов еще пуст.
        self._on_piper_lang_changed()
        
        # Восстановление XTTS
        self.edit_speaker_wav.setText(self.settings.value("tts_xtts_speaker_wav", ""))
        idx = self.combo_xtts_lang.findData(self.settings.value("tts_xtts_lang", "ru"))
        if idx >= 0: self.combo_xtts_lang.setCurrentIndex(idx)
        
        saved_xtts_voice = self.settings.value("tts_xtts_last_voice", "clone")
        idx = self.combo_xtts_voice.findData(saved_xtts_voice)
        if idx >= 0: 
            self.combo_xtts_voice.setCurrentIndex(idx)
        self._on_xtts_voice_type_changed()

        # Параметры XTTS
        speed = int(self.settings.value("tts_xtts_speed", 100))
        temp = int(self.settings.value("tts_xtts_temp", 75))
        rep = int(self.settings.value("tts_xtts_rep", 20))
        top_k = int(self.settings.value("tts_xtts_top_k", 50))
        top_p = int(self.settings.value("tts_xtts_top_p", 80))
        len_pen = int(self.settings.value("tts_xtts_len_pen", 100))
        
        self.slider_xtts_speed.setValue(speed)
        self.slider_xtts_temp.setValue(temp)
        self.slider_xtts_rep.setValue(rep)
        self.slider_xtts_k.setValue(top_k)
        self.slider_xtts_p.setValue(top_p)
        self.slider_xtts_len.setValue(len_pen)

        # Параметры Piper
        p_speed = int(self.settings.value("tts_piper_speed", 100))
        p_silence = int(self.settings.value("tts_piper_silence", 20))
        p_noise = int(self.settings.value("tts_piper_noise", 66))
        self.slider_speed.setValue(p_speed)
        self.slider_silence.setValue(p_silence)
        self.slider_noise.setValue(p_noise)

        # Фильтр символов
        filter_enabled = self.settings.value("tts_filter_symbols_enabled", False)
        if isinstance(filter_enabled, str): filter_enabled = filter_enabled.lower() == 'true'
        self.cb_filter_symbols.setChecked(bool(filter_enabled))
        saved_symbols = self.settings.value("tts_filter_symbols_list", None)
        if saved_symbols is not None:
            self.edit_filter_symbols.setText(saved_symbols)
            
        # Замена символов
        rep_enabled = self.settings.value("tts_replace_symbols_enabled", True)
        if isinstance(rep_enabled, str): rep_enabled = rep_enabled.lower() == 'true'
        self.cb_replace_symbols.setChecked(bool(rep_enabled))
        
        saved_from = self.settings.value("tts_replace_from_list", ".")
        self.edit_replace_from.setText(saved_from)
        
        saved_to = self.settings.value("tts_replace_to_list", "!")
        self.edit_replace_to.setText(saved_to)

    def _populate_tts_playlist(self):
        """Заполняет плейлист аудиофайлами из миссии (через miz_resource_manager родителя)."""
        try:
            miz_manager = None
            miz_path = None
            
            # Ищем miz_resource_manager через цепочку родителей
            parent = self.parent()
            if parent:
                # 1) Родитель — главное окно (standalone TTS кнопка)
                miz_manager = getattr(parent, 'miz_resource_manager', None)
                miz_path = getattr(parent, 'miz_path', None) or getattr(parent, 'current_miz_path', None)
                
                # 2) Родитель — FilesWindow (через parent_window -> main_app)
                if not miz_manager and hasattr(parent, 'parent_window'):
                    main_app = getattr(parent.parent_window, 'main_app', None) if parent.parent_window else None
                    if main_app:
                        miz_manager = getattr(main_app, 'miz_resource_manager', None)
                        miz_path = getattr(main_app, 'current_miz_path', None)
                
                # 3) Родитель — FilesWindow напрямую
                if not miz_manager:
                    main_app = getattr(parent, 'main_app', None)
                    if main_app:
                        miz_manager = getattr(main_app, 'miz_resource_manager', None)
                        miz_path = getattr(main_app, 'current_miz_path', None)
            
            # Сохраняем ссылки для использования плейлистом
            self.miz_resource_manager = miz_manager
            self.current_miz_path = miz_path
            
            if miz_manager:
                all_files = miz_manager.get_all_resource_files()
                audio_files = [f for f in all_files if f.get('type') == 'audio']
                
                # Фильтруем: оставляем только файлы с привязкой к субтитрам И наличием текста
                final_audio_files = []
                for f in audio_files:
                    rk = f.get('res_key')
                    if not rk: continue
                    # Проверяем, есть ли для этого файла текст в текущей локали
                    text = self._get_text_for_res_key(rk)
                    if text and text.strip():
                        final_audio_files.append(f)
                
                audio_files = final_audio_files
                
                self.tts_playlist_widget.set_audio_files(audio_files)
                # Подключаем клик: загрузка текста для выбранного файла
                self.tts_playlist_widget.file_clicked.connect(self._on_playlist_file_clicked)
                # Двойной клик: воспроизведение оригинального аудио
                self.tts_playlist_widget.file_double_clicked.connect(self._on_tts_playlist_double_click)
                # Контекстное меню: скачать файл
                self.tts_playlist_widget.download_requested.connect(self._on_tts_download_requested)
        except Exception as e:
            print(f"DEBUG: Error populating TTS playlist: {e}")

    def _on_text_edited(self):
        """Сохраняет измененный текст в локальный кэш окна."""
        res_key = getattr(self, '_current_playlist_res_key', None)
        if res_key:
            self._edited_texts[res_key] = self.text_edit.toPlainText()

    def _on_playlist_file_clicked(self, res_key):
        """Загружает текст из миссии (или кэша правок) для выбранного файла."""
        try:
            if not getattr(self, 'miz_resource_manager', None): return
            
            # Блокируем сигнал, чтобы при загрузке текста не сработал _on_text_edited
            self.text_edit.blockSignals(True)
            try:
                # Останавливаем предыдущее аудио при выборе другого файла
                if getattr(self, '_playing_res_key', None) != res_key:
                    self.stop_audio()
                    
                    # Обновляем UI длительности без загрузки pygame
                    duration = 0
                    if hasattr(self, 'tts_playlist_widget') and hasattr(self.tts_playlist_widget, '_duration_cache'):
                        if res_key in self.tts_playlist_widget._duration_cache:
                            duration = self.tts_playlist_widget._duration_cache[res_key][0]
                    
                    self.duration_sec = duration
                    if duration > 0:
                        self.position_slider.setRange(0, int(duration * 1000))
                        self.position_slider.setValue(0)
                        self.update_time_labels(0)
                    else:
                        self.position_slider.setRange(0, 0)
                        self.position_slider.setValue(0)
                        self.update_time_labels(0)
                
                # Сохраняем текущий res_key
                self._current_playlist_res_key = res_key
                
                # 1. Проверяем, есть ли уже отредактированный текст
                if res_key in self._edited_texts:
                    self.text_edit.setPlainText(self._edited_texts[res_key])
                    from localization import get_translation
                    self.lbl_status.setText(get_translation(self.current_language, 'tts_status_loaded_edited').format(key=res_key))
                    return

                # 2. Иначе грузим оригинал из миссии
                dict_key = None
                for dk, rk in self.miz_resource_manager.subtitle_to_reskey.items():
                    if rk == res_key:
                        dict_key = dk
                        break
                
                if not dict_key: return
                
                main_window = self._get_main_app()
                if main_window:
                    lines_data = getattr(main_window, 'all_lines_data', None) or getattr(main_window, 'original_lines', [])
                    text_lines = []
                    for line in lines_data:
                        if line.get('key') == dict_key:
                            t = line.get('translated_text') or line.get('text', '')
                            if t: text_lines.append(t)
                    
                    new_text = "\n".join(text_lines)
                    if new_text:
                        self.text_edit.setPlainText(new_text)
                        # Сохраняем в кэш, чтобы при смене вкладок или пакетной генерации он был доступен
                        self._edited_texts[res_key] = new_text
                        from localization import get_translation
                        self.lbl_status.setText(get_translation(self.current_language, 'tts_status_loaded_orig').format(key=res_key))
            finally:
                self.text_edit.blockSignals(False)
        except Exception as e:
            print(f"DEBUG: Error loading text from playlist: {e}")

    def _on_tts_playlist_double_click(self, res_key):
        """Двойной клик: воспроизводим выбранный аудиофайл через единый плеер."""
        # Повторный дабл-клик по тому же файлу — остановка
        if self.is_playing and getattr(self, '_playing_res_key', None) == res_key:
            self.stop_audio()
            return
            
        self._play_selected_audio(res_key)

    def _play_selected_audio(self, res_key=None):
        """Единая функция воспроизведения: играет сгенерированное аудио, если есть, иначе оригинал."""
        if not res_key:
            res_key = getattr(self, '_current_playlist_res_key', None)
        if not res_key or not getattr(self, 'miz_resource_manager', None) or not getattr(self, 'current_miz_path', None):
            return
            
        # Находим удобочитаемое имя файла
        filename = res_key
        if hasattr(self, 'tts_playlist_widget'):
            for f_info in self.tts_playlist_widget._all_audio_files:
                if f_info.get('res_key') == res_key:
                    filename = f_info.get('filename', res_key)
                    break
                    
        cached_path = self.tts_cache.get(res_key)
        is_generated = False
        
        if cached_path and os.path.exists(cached_path):
            audio_path = cached_path
            is_generated = True
        else:
            audio_path = self.miz_resource_manager.extract_resource_to_temp(self.current_miz_path, res_key)
            
        if audio_path and os.path.exists(audio_path):
            # Избегаем гонки при загрузке НО обязательно перезагружаем, если файл был принудительно выгружен
            if getattr(self, '_current_audio_path', None) != audio_path or not getattr(self, 'audio_loaded', False):
                self.stop_audio()
                self.load_audio_file(audio_path)
            
            if not getattr(self, 'audio_loaded', False):
                from localization import get_translation
                if not is_generated and filename.lower().endswith(".ogg"):
                    self.lbl_status.setText(get_translation(self.current_language, 'tts_status_err_ogg'))
                else:
                    self.lbl_status.setText(get_translation(self.current_language, 'tts_status_err_load'))
                return
                
            import pygame
            pygame.mixer.music.play()
            
            self.is_playing = True
            self.is_paused = False
            self.btn_play_preview.setText("⏸")
            self._playing_res_key = res_key
            
            from localization import get_translation
            prefix = get_translation(self.current_language, 'tts_status_gen_prefix') if is_generated else get_translation(self.current_language, 'tts_status_orig_prefix')
            self.lbl_status.setText(f"▶️ {prefix}: {filename}")

    def _on_xtts_params_changed(self):
        self.settings.setValue("tts_xtts_speed", self.slider_xtts_speed.value())
        self.settings.setValue("tts_xtts_temp", self.slider_xtts_temp.value())
        self.settings.setValue("tts_xtts_rep", self.slider_xtts_rep.value())
        self.settings.setValue("tts_xtts_top_k", self.slider_xtts_k.value())
        self.settings.setValue("tts_xtts_top_p", self.slider_xtts_p.value())
        self.settings.setValue("tts_xtts_len_pen", self.slider_xtts_len.value())

    def _on_piper_params_changed(self):
        self.settings.setValue("tts_piper_speed", self.slider_speed.value())
        self.settings.setValue("tts_piper_silence", self.slider_silence.value())
        self.settings.setValue("tts_piper_noise", self.slider_noise.value())

    def _reset_piper_sliders(self):
        self.slider_speed.setValue(100)
        self.slider_silence.setValue(20)
        self.slider_noise.setValue(66)
        self._on_piper_params_changed()

    def _reset_xtts_sliders(self):
        self.slider_xtts_speed.setValue(100)
        self.slider_xtts_temp.setValue(75)
        self.slider_xtts_rep.setValue(20)
        self.slider_xtts_k.setValue(50)
        self.slider_xtts_p.setValue(80)
        self.slider_xtts_len.setValue(100)
        self._on_xtts_params_changed()

    def _clean_text_for_generation(self, text):
        """Заменяет указанные символы на пробел или на другие символы (если фильтры включены)."""
        # 1. Замена на пробел
        if self.cb_filter_symbols.isChecked():
            symbols = self.edit_filter_symbols.text()
            for ch in symbols:
                if ch == ' ':  # Пробелы в строке фильтра — разделители, пропускаем
                    continue
                text = text.replace(ch, ' ')
        
        # 2. Посимвольная замена
        if self.cb_replace_symbols.isChecked():
            from_chars = self.edit_replace_from.text()
            to_chars = self.edit_replace_to.text()
            for i in range(len(from_chars)):
                if i < len(to_chars):
                    text = text.replace(from_chars[i], to_chars[i])
                else:
                    # Если во второй строке нет символа для этой позиции, заменяем на последний доступный или на пробел?
                    # Пользователь сказал "из первого поля на символы во втором". 
                    # Обычно это 1-в-1. Если не хватило — просто заменим на пробел для безопасности.
                    text = text.replace(from_chars[i], ' ')
                    
        return text

    def _on_tab_changed(self):
        engine_name = "piper" if self.tabs.currentIndex() == 0 else "xtts"
        self.settings.setValue("tts_last_engine", engine_name)
        self._update_ui_state()
        self.stop_audio() # Останавливаем звук при смене движка

    def _update_ui_state(self):
        """Обновляет состояние кнопок и статусов в зависимости от выбранного движка."""
        # Общий стиль для кнопок OK (рамка становится оранжевой при наведении)
        status_ok_style = """
            QPushButton { 
                background-color: transparent; 
                color: #0c6; 
                border: 1px solid #444; 
                border-radius: 4px; 
                padding: 2px 8px; 
                font-size: 10px; 
            }
            QPushButton:hover {
                border: 1px solid #ff9900;
            }
        """
        
        if self.tabs.currentIndex() == 0: # Piper
            voice_id = self.combo_voice.currentData()
            installed_voices = self.engine.get_installed_voices()
            piper_engine_ready = self.engine._check_piper_available()
            
            from localization import get_translation
            
            if not piper_engine_ready:
                self.lbl_status.setText(get_translation(self.current_language, 'tts_status_piper_not_found'))
                self.lbl_status.setStyleSheet("color: #ff9900; background: transparent;")
                self.btn_install_piper.setText(get_translation(self.current_language, 'tts_btn_engine'))
                self.btn_install_piper.setStyleSheet("QPushButton { background-color: #433; color: #ffaa00; border: 1px solid #ffaa00; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold; }")
                self.btn_install_piper.setCursor(Qt.ArrowCursor)
            else:
                self.lbl_status.setStyleSheet("color: #ffffff; background: transparent;")
                self.btn_install_piper.setText(get_translation(self.current_language, 'tts_status_piper_ok'))
                self.btn_install_piper.setStyleSheet(status_ok_style)
                self.btn_install_piper.setCursor(Qt.ArrowCursor)

            if voice_id in installed_voices:
                self.lbl_voice_status.setText("✅"); self.lbl_voice_status.setStyleSheet("color: #00cc66;")
                self.btn_main_action.setEnabled(True)
                voice_name = self.combo_voice.currentText()
                self.btn_main_action.setText(get_translation(self.current_language, 'tts_btn_gen_voice').format(name=voice_name))
            else:
                self.lbl_voice_status.setText("📥"); self.lbl_voice_status.setStyleSheet("color: #ffaa00;")
                self.btn_main_action.setText(get_translation(self.current_language, 'tts_btn_download_voice').format(name=self.combo_voice.currentText()))
                self.btn_main_action.setEnabled(True)

        else: # XTTS
            libs_ok = self.engine.is_tts_libraries_installed()
            model_ok = self.engine.is_xtts_available()
            from localization import get_translation
            
            self.btn_install_xtts_libs.setEnabled(True)
            self.btn_install_xtts_model.setEnabled(True)
            
            if libs_ok:
                self.btn_install_xtts_libs.setText(get_translation(self.current_language, 'tts_status_libs_ok'))
                self.btn_install_xtts_libs.setStyleSheet(status_ok_style)
                self.btn_install_xtts_libs.setCursor(Qt.ArrowCursor)
            else:
                self.btn_install_xtts_libs.setText(get_translation(self.current_language, 'tts_btn_libs'))
                self.btn_install_xtts_libs.setStyleSheet("QPushButton { background-color: #433; color: #fff; border: 1px solid #ff9900; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold; }")
                self.btn_install_xtts_libs.setCursor(Qt.ArrowCursor)
                
            if model_ok:
                self.btn_install_xtts_model.setText(get_translation(self.current_language, 'tts_status_model_ok'))
                self.btn_install_xtts_model.setStyleSheet(status_ok_style)
                self.btn_install_xtts_model.setCursor(Qt.ArrowCursor)
            else:
                self.btn_install_xtts_model.setText(get_translation(self.current_language, 'tts_btn_model'))
                self.btn_install_xtts_model.setStyleSheet("QPushButton { background-color: #433; color: #fff; border: 1px solid #ff9900; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold; }")
                self.btn_install_xtts_model.setCursor(Qt.ArrowCursor)

            if libs_ok and model_ok:
                self.lbl_xtts_status.setText(get_translation(self.current_language, 'tts_status_xtts_ready'))
                self.lbl_xtts_status.setStyleSheet("color: #0c6; font-size: 12px; background: transparent;")
                v_type = self.combo_xtts_voice.currentData()
                self.btn_main_action.setEnabled(True)
                if v_type == "clone": 
                    self.btn_main_action.setText(get_translation(self.current_language, 'tts_btn_gen_clone'))
                else: 
                    self.btn_main_action.setText(get_translation(self.current_language, 'tts_btn_gen_voice').format(name=v_type))
            else:
                self.lbl_xtts_status.setText(get_translation(self.current_language, 'tts_status_xtts_req'))
                self.lbl_xtts_status.setStyleSheet("color: #ffaa00; font-size: 12px; background: transparent;")
                self.btn_main_action.setEnabled(False)
                self.btn_XTTS_status = get_translation(self.current_language, 'tts_status_xtts_waiting')
                self.btn_main_action.setText(self.btn_XTTS_status)

    def register_custom_tooltip(self, widget, text, side='bottom'):
        """Регистрирует виджет для показа кастомного тултипа."""
        self._custom_tooltip_map[widget] = {'text': text, 'side': side}
        try:
            widget.setToolTip('')
            widget.installEventFilter(self)
        except Exception: pass

    def unregister_custom_tooltip(self, widget):
        """Удаляет регистрацию кастомного тултипа."""
        if widget in self._custom_tooltip_map:
            del self._custom_tooltip_map[widget]

    def _show_pending_tooltip(self):
        """Отображает отложенный тултип."""
        if self._pending_tooltip_data:
            text, obj, info = self._pending_tooltip_data
            if isinstance(info, QPoint):
                self.custom_tooltip.show_tooltip_at_pos(text, info)
            else:
                self.custom_tooltip.show_tooltip(text, obj, info)

    def eventFilter(self, obj, event):
        """Фильтр событий для перехвата наведения мыши."""
        if obj in self._custom_tooltip_map:
            if event.type() == QEvent.Enter:
                data = self._custom_tooltip_map[obj]
                self._pending_tooltip_data = (data['text'], obj, data['side'])
                self.tooltip_timer.start(400)
                return True
            elif event.type() in [QEvent.Leave, QEvent.MouseButtonPress]:
                self.tooltip_timer.stop()
                self._pending_tooltip_data = None
                self.custom_tooltip.hide()
        return super().eventFilter(obj, event)

    def _on_piper_lang_changed(self):
        lang_code = self.combo_lang.currentData()
        if not lang_code: return
        self.settings.setValue("tts_last_lang", lang_code)
        self.combo_voice.blockSignals(True); self.combo_voice.clear()
        voices = self.registry.get(lang_code, [])
        for v in voices: self.combo_voice.addItem(v['name'], v['id'])
        self.combo_voice.blockSignals(False)
        
        saved_voice = self.settings.value(f"tts_last_voice_{lang_code}")
        idx = self.combo_voice.findData(saved_voice) if saved_voice else -1
        if idx >= 0: self.combo_voice.setCurrentIndex(idx)
        self._on_piper_voice_changed()

    def _on_xtts_lang_changed(self):
        lang_code = self.combo_xtts_lang.currentData()
        if lang_code:
            self.settings.setValue("tts_xtts_lang", lang_code)
        self._update_ui_state()

    def _on_piper_voice_changed(self):
        v_id = self.combo_voice.currentData()
        l_code = self.combo_lang.currentData()
        if v_id: self.settings.setValue(f"tts_last_voice_{l_code}", v_id)
        self._update_ui_state()

    def _on_browse_speaker_wav(self):
        from localization import get_translation
        path, _ = QFileDialog.getOpenFileName(self, get_translation(self.current_language, 'tts_select_wav'), "", "Audio Files (*.wav *.mp3)")
        if path:
            self.edit_speaker_wav.setText(path)
            self.settings.setValue("tts_xtts_speaker_wav", path)

    def _on_main_action_clicked(self):
        # --- Если сейчас идёт пакетная генерация — остановить ---
        if self._batch_mode:
            self._batch_stop_requested = True
            from localization import get_translation
            self.lbl_status.setText(get_translation(self.current_language, 'tts_status_stop_batch'))
            return
        
        # --- Пакетный режим: если есть отмеченные файлы ---
        checked = self.tts_playlist_widget.checked_keys
        if checked:
            self._start_batch_generation(checked)
            return
        
        # --- Одиночный режим (текущий текст из поля) ---
        if self.tabs.currentIndex() == 0: # Piper
            voice_id = self.combo_voice.currentData()
            if voice_id not in self.engine.get_installed_voices():
                self._start_piper_download(voice_id)
            else:
                self._generate_preview_engine("piper")
        else: # XTTS
            if not self.engine.is_tts_libraries_installed():
                self._start_library_install()
                return

            if not self.engine.is_xtts_available():
                self._start_xtts_download()
            else:
                v_type = self.combo_xtts_voice.currentData()
                if v_type == "clone" and not self.edit_speaker_wav.text():
                    from localization import get_translation
                    self.lbl_status.setText(get_translation(self.current_language, 'tts_err_clone_wav'))
                    return
                
                # Сохраняем последний выбор
                self.settings.setValue("tts_xtts_last_voice", v_type)
                self._generate_preview_engine("xtts")

    # ==================== ПАКЕТНАЯ ГЕНЕРАЦИЯ ====================
    
    def _get_text_for_res_key(self, res_key):
        """Находит текст субтитров для данного res_key (сначала из кэша правок)."""
        # 1. Проверяем кэш локальных правок
        if res_key in getattr(self, '_edited_texts', {}):
            return self._edited_texts[res_key]
            
        if not self.miz_resource_manager: return None
        
        dict_key = None
        for dk, rk in self.miz_resource_manager.subtitle_to_reskey.items():
            if rk == res_key:
                dict_key = dk
                break
        if not dict_key: return None
        
        main_window = self._get_main_app()
        if not main_window: return None
        
        lines_data = getattr(main_window, 'all_lines_data', None) or getattr(main_window, 'original_lines', [])
        text_lines = []
        for line in lines_data:
            if line.get('key') == dict_key:
                t = line.get('translated_text') or line.get('text', '')
                if t: text_lines.append(t)
        
        return "\n".join(text_lines) if text_lines else None
    
    def _get_tts_params(self):
        """Собирает текущие параметры TTS (движок, голос, настройки)."""
        params = {}
        if self.tabs.currentIndex() == 0:  # Piper
            engine_type = "piper"
            lang = self.combo_lang.currentData()
            voice_id = self.combo_voice.currentData()
            params['length_scale'] = 1.0 / (self.slider_speed.value() / 100.0)
            params['sentence_silence'] = self.slider_silence.value() / 100.0
            params['noise_scale'] = self.slider_noise.value() / 100.0
        else:  # XTTS
            engine_type = "xtts"
            lang = self.combo_xtts_lang.currentData()
            voice = self.combo_xtts_voice.currentData()
            voice_id = voice if voice != "clone" else self.edit_speaker_wav.text()
            if voice == "clone":
                params['speaker_wav'] = voice_id
            params['speed'] = self.slider_xtts_speed.value() / 100.0
            params['temperature'] = self.slider_xtts_temp.value() / 100.0
            params['repetition_penalty'] = self.slider_xtts_rep.value() / 10.0
            params['top_k'] = self.slider_xtts_k.value()
            params['top_p'] = self.slider_xtts_p.value() / 100.0
            params['length_penalty'] = self.slider_xtts_len.value() / 100.0
        return engine_type, lang, voice_id, params
    
    def _start_batch_generation(self, checked_keys):
        """Запуск пакетной генерации для отмеченных файлов."""
        import time, tempfile
        
        from localization import get_translation
        # Проверка доступности движка
        if self.tabs.currentIndex() == 0:  # Piper
            voice_id = self.combo_voice.currentData()
            if voice_id not in self.engine.get_installed_voices():
                self.lbl_status.setText(get_translation(self.current_language, 'tts_err_dl_voice'))
                return
        else:  # XTTS
            if not self.engine.is_tts_libraries_installed():
                self.lbl_status.setText(get_translation(self.current_language, 'tts_err_install_libs'))
                return
            if not self.engine.is_xtts_available():
                self.lbl_status.setText(get_translation(self.current_language, 'tts_err_dl_model'))
                return
        
        # Собираем очередь: (res_key, text, output_path)
        self._batch_queue = []
        tts_data_dir = os.path.join(str(self.engine.base_dir), "batch")
        os.makedirs(tts_data_dir, exist_ok=True)
        
        skipped = 0
        for res_key in checked_keys:
            text = self._get_text_for_res_key(res_key)
            if not text:
                skipped += 1
                continue
            # Используем уникальное имя для кэша, чтобы не перезаписывать файлы с одинаковыми именами (но разными текстами)
            safe_key = "".join([c if c.isalnum() else "_" for c in res_key])
            engine_type = "piper" if self.tabs.currentIndex() == 0 else "xtts"
            output_filename = f"batch_{engine_type}_{safe_key}.wav"
            output_path = os.path.join(tts_data_dir, output_filename)
            self._batch_queue.append((res_key, text, output_path))
        
        if not self._batch_queue:
            from localization import get_translation
            self.lbl_status.setText(get_translation(self.current_language, 'tts_err_no_files').format(count=skipped))
            return
        
        # Инициализируем состояние пакета
        self._batch_mode = True
        self._batch_index = 0
        self._batch_total = len(self._batch_queue)
        self._batch_stop_requested = False
        self._batch_times = []
        self._batch_start_time = time.time()
        
        # Меняем кнопку
        from localization import get_translation
        self.btn_main_action.setText(get_translation(self.current_language, 'tts_btn_stop_gen'))
        
        # Прогресс
        self.download_progress.setRange(0, self._batch_total)
        self.download_progress.setValue(0)
        self.download_progress.show()
        
        # Останавливаем аудио
        self.stop_audio()
        
        if skipped:
            print(f"DEBUG: Batch: skipped {skipped} files without text")
        
        # Запускаем первый
        self._process_next_batch_item()
    
    def _process_next_batch_item(self):
        """Запускает генерацию следующего элемента из очереди."""
        import time
        
        if self._batch_stop_requested or self._batch_index >= self._batch_total:
            self._finish_batch()
            return
        
        res_key, raw_text, output_path = self._batch_queue[self._batch_index]
        text = self._clean_text_for_generation(raw_text)
        # Ищем читаемое имя файла
        filename = res_key
        for f_info in self.tts_playlist_widget._all_audio_files:
            if f_info.get('res_key') == res_key:
                filename = f_info.get('filename', res_key)
                break
        
        from localization import get_translation
        remaining_str = ""
        if self._batch_times:
            avg_time = sum(self._batch_times) / len(self._batch_times)
            remaining = avg_time * (self._batch_total - self._batch_index)
            mins, secs = divmod(int(remaining), 60)
            remaining_str = get_translation(self.current_language, 'tts_status_gen_rem').format(mins=mins, secs=f"{secs:02d}", avg=f"{avg_time:.0f}")
        
        self.lbl_status.setText(
            get_translation(self.current_language, 'tts_status_gen_progress').format(index=self._batch_index + 1, total=self._batch_total, filename=filename) + remaining_str
        )
        self.download_progress.setValue(self._batch_index)
        
        # Запускаем воркер
        engine_type, lang, voice_id, params = self._get_tts_params()
        self._batch_item_start = time.time()
        
        from tts_engine import TTSWorker
        self.worker = TTSWorker(
            self.engine, text, output_path,
            lang=lang, engine_type=engine_type, voice_id=voice_id,
            **params
        )
        self.worker.finished.connect(self._on_batch_item_finished)
        self.worker.error.connect(self._on_batch_item_error)
        self.worker.start()
    
    def _on_batch_item_finished(self, path):
        """Один файл из пакета успешно сгенерирован."""
        import time
        
        res_key = self._batch_queue[self._batch_index][0]
        elapsed = time.time() - self._batch_item_start
        self._batch_times.append(elapsed)
        
        # Сохраняем в кэш
        self.tts_cache.put(res_key, path)
        
        # Обновляем 🧠 в плейлисте
        if hasattr(self, 'tts_playlist_widget'):
            # Узнаем длительность и обновляем UI плейлиста
            try:
                import pygame
                sound = pygame.mixer.Sound(path)
                duration = sound.get_length()
                del sound
                # Показываем длительность сгенерированного аудио в колонке 🧠, а не ⏳
                self.tts_playlist_widget.update_generated_indicator(res_key, True, duration_sec=duration)
                
                # Если это сейчас выбранный файл и мы не играем, обновим плеер
                if getattr(self, '_current_playlist_res_key', None) == res_key:
                    self.duration_sec = duration
                    if not self.is_playing and not self.is_paused:
                        self.position_slider.setRange(0, int(duration * 1000))
                        self.update_time_labels(0)
            except Exception:
                self.tts_playlist_widget.update_generated_indicator(res_key, True)
        
        # Следующий
        self._batch_index += 1
        self._process_next_batch_item()
    
    def _on_batch_item_error(self, err_msg):
        """Ошибка генерации одного файла — пропускаем, продолжаем."""
        res_key = self._batch_queue[self._batch_index][0]
        print(f"DEBUG: Batch error for {res_key}: {err_msg}")
        
        self._batch_index += 1
        self._process_next_batch_item()
    
    def _finish_batch(self):
        """Завершает пакетную генерацию."""
        import time
        
        generated_count = len([t for t in self._batch_times])  # кол-во успешных
        total_time = time.time() - self._batch_start_time if self._batch_start_time else 0
        mins, secs = divmod(int(total_time), 60)
        
        self._batch_mode = False
        self.download_progress.setValue(self._batch_total)
        self.download_progress.hide()
        
        # Возвращаем кнопку
        self._update_ui_state()
        
        from localization import get_translation
        if self._batch_stop_requested:
            self.lbl_status.setText(
                get_translation(self.current_language, 'tts_status_batch_stopped').format(count=generated_count, total=self._batch_total, mins=mins, secs=f"{secs:02d}")
            )
        else:
            self.lbl_status.setText(
                get_translation(self.current_language, 'tts_status_batch_done').format(count=generated_count, total=self._batch_total, mins=mins, secs=f"{secs:02d}")
            )
        
        # Включаем кнопку "Заменить" если есть сгенерированные
        if generated_count > 0:
            self.btn_apply.setEnabled(True)


    def _generate_preview_engine(self, engine_type):
        # ВАЖНО: Останавливаем и ВЫГРУЖАЕМ аудио перед генерацией, чтобы не было PermissionError
        self.stop_audio()
        
        from localization import get_translation
        self.lbl_status.setText(get_translation(self.current_language, 'tts_status_generating'))
        self.btn_main_action.setEnabled(False)
        self.download_progress.setRange(0, 0)
        self.download_progress.show()
        current_res_key = getattr(self, '_current_playlist_res_key', None)
        safe_key = "".join([c if c.isalnum() else "_" for c in (current_res_key or "unknown")])
        output_name = f"preview_{engine_type}_{safe_key}.wav"
        output_path = os.path.join(str(self.engine.base_dir), output_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        current_text = self._clean_text_for_generation(self.text_edit.toPlainText())
        
        params = {}
        if engine_type == "piper":
            lang = self.combo_lang.currentData()
            voice_id = self.combo_voice.currentData()
            params['length_scale'] = 1.0 / (self.slider_speed.value() / 100.0)
            params['sentence_silence'] = self.slider_silence.value() / 100.0
            params['noise_scale'] = self.slider_noise.value() / 100.0
        else: # XTTS
            lang = self.combo_xtts_lang.currentData()
            voice = self.combo_xtts_voice.currentData()
            voice_id = voice if voice != "clone" else self.edit_speaker_wav.text()
            if voice == "clone":
                params['speaker_wav'] = voice_id
            params['speed'] = self.slider_xtts_speed.value() / 100.0
            params['temperature'] = self.slider_xtts_temp.value() / 100.0
            params['repetition_penalty'] = self.slider_xtts_rep.value() / 10.0
            params['top_k'] = self.slider_xtts_k.value()
            params['top_p'] = self.slider_xtts_p.value() / 100.0
            params['length_penalty'] = self.slider_xtts_len.value() / 100.0

        from tts_engine import TTSWorker
        self.worker = TTSWorker(
            self.engine, 
            current_text, 
            output_path, 
            lang=lang,
            engine_type=engine_type,
            voice_id=voice_id,
            **params
        )
        
        self.worker.finished.connect(self._on_generation_finished)
        self.worker.error.connect(self._on_generation_error)
        self.worker.start()

    def _on_generation_finished(self, path):
        self.preview_path = path
        self.btn_main_action.setEnabled(True)
        self.download_progress.hide()
        from localization import get_translation
        self.lbl_status.setText(get_translation(self.current_language, 'tts_status_done'))
        
        # Загружаем файл в плеер
        self.load_audio_file(path)
        
        # Включаем управление плеером
        self.btn_play_preview.setEnabled(True)
        self.btn_stop_preview.setEnabled(True)
        self.position_slider.setEnabled(True)
        self.btn_apply.setEnabled(True)
        
        # 🧠 Обновляем индикатор в плейлисте и сохраняем в кэш
        current_res_key = getattr(self, '_current_playlist_res_key', None)
        if current_res_key:
            self.tts_cache.put(current_res_key, path)
            if hasattr(self, 'tts_playlist_widget'):
                # Узнаем длительность и обновляем UI плейлиста
                try:
                    import pygame
                    sound = pygame.mixer.Sound(path)
                    duration = sound.get_length()
                    del sound
                    # Показываем длительность сгенерированного аудио в колонке 🧠, а не ⏳
                    self.tts_playlist_widget.update_generated_indicator(current_res_key, True, duration_sec=duration)
                    self.duration_sec = duration
                    self._playing_res_key = current_res_key
                    if not self.is_playing and not self.is_paused:
                        self.position_slider.setRange(0, int(duration * 1000))
                        self.update_time_labels(0)
                except Exception: 
                    self.tts_playlist_widget.update_generated_indicator(current_res_key, True)

        
        # Автоматическое воспроизведение, если включен чекбокс
        if self.cb_auto_play.isChecked():
            # Если уже играет — не перезапускаем (хотя после генерации мы загружаем новый файл)
            self.toggle_play_pause()

    def _on_generation_error(self, err_msg):
        self.btn_main_action.setEnabled(True)
        self.download_progress.hide()
        from localization import get_translation
        self.lbl_status.setText(get_translation(self.current_language, 'tts_err_gen_failed').format(error=err_msg))
        QMessageBox.critical(self, get_translation(self.current_language, 'tts_msgbox_gen_err_title'), get_translation(self.current_language, 'tts_msgbox_gen_err_msg').format(error=err_msg))

    def _on_auto_play_toggled(self, checked):
        """Сохраняем состояние авто-проигрывания в глобальные настройки."""
        main_app = self._get_main_app()
        if main_app:
            main_app.tts_auto_play = checked
            # [FIX] Выключаем перерисовку UI основного окна, так как здесь она не нужна
            main_app.save_settings(update_ui=False)

    def _on_tts_download_requested(self, res_key):
        """Обработка запроса на сохранение аудиофайла на диск."""
        import shutil
        from localization import get_translation
        
        # 1. Определяем источник (генерация или оригинал)
        source_path = self.tts_cache.get(res_key)
        is_generated = source_path is not None
        
        if not is_generated:
            # Если не сгенерировано — извлекаем оригинал из миссии во временную папку
            if not self.miz_resource_manager or not self.current_miz_path:
                self.lbl_status.setText(get_translation(self.current_language, 'tts_err_no_mission'))
                return
            
            self.lbl_status.setText(get_translation(self.current_language, 'tts_status_extract_orig'))
            source_path = self.miz_resource_manager.extract_resource_to_temp(self.current_miz_path, res_key)
            
        if not source_path or not os.path.exists(source_path):
            self.lbl_status.setText(get_translation(self.current_language, 'tts_err_file_not_found'))
            return

        # 2. Предлагаем имя для сохранения
        # Пытаемся найти реальное имя файла из плейлиста
        suggested_filename = res_key
        for f_info in self.tts_playlist_widget._all_audio_files:
            if f_info.get('res_key') == res_key:
                suggested_filename = f_info.get('filename', res_key)
                break
        
        # Если это сгенерированный файл, добавим пометку (по желанию, но лучше сохранить оригинал расширения)
        file_ext = os.path.splitext(source_path)[1]
        if not suggested_filename.lower().endswith(file_ext.lower()):
            suggested_filename = os.path.splitext(suggested_filename)[0] + file_ext

        # Запоминание последнего пути сохранения
        ui_settings = get_ui_settings()
        last_dir = ui_settings.value("last_tts_download_dir", "")
        if last_dir and os.path.exists(last_dir):
            initial_path = os.path.join(last_dir, suggested_filename)
        else:
            initial_path = suggested_filename

        # 3. Диалог сохранения
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            get_translation(self.current_language, 'fm_tooltip_download'),
            initial_path,
            f"Audio Files (*{file_ext});;All Files (*)"
        )
        
        if save_path:
            try:
                shutil.copy2(source_path, save_path)
                self.lbl_status.setText(get_translation(self.current_language, 'tts_status_saved').format(name=os.path.basename(save_path)))
                
                # Сохраняем путь для следующего раза
                ui_settings.setValue("last_tts_download_dir", os.path.dirname(save_path))
                
                # Тултип об успехе убран по просьбе пользователя
            except Exception as e:
                QMessageBox.critical(self, get_translation(self.current_language, 'tts_msgbox_save_err'), get_translation(self.current_language, 'tts_msgbox_save_err_msg').format(error=str(e)))
        else:
            self.lbl_status.setText("")

    # --- ЛОГИКА ПЛЕЕРА ---
    def load_audio_file(self, audio_path):
        try:
            if audio_path and os.path.exists(audio_path):
                import pygame
                sound = pygame.mixer.Sound(audio_path)
                self.duration_sec = sound.get_length()
                del sound
                
                pygame.mixer.music.load(audio_path)
                self.audio_loaded = True
                self._current_audio_path = audio_path  # Запоминаем текущий загруженный файл
                
                self.position_slider.setRange(0, int(self.duration_sec * 1000))
                self.position_slider.setValue(0)
                self.play_start_offset = 0
                self.update_time_labels(0)
        except Exception as e:
            print(f"Error loading audio file: {e}")
            self.duration_sec = 0
            self.audio_loaded = False

    def toggle_play_pause(self):
        res_key = getattr(self, '_current_playlist_res_key', None)
        
        # Если выбран другой файл в отличие от того, который загружен сейчас
        if res_key and getattr(self, '_playing_res_key', None) != res_key:
            self._play_selected_audio(res_key)
            return
            
        import pygame
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.is_paused = True
            self.btn_play_preview.setText("▶")
        elif self.is_paused:
            # Если ползунок был сдвинут во время паузы
            if abs(self.play_start_offset - self.position_slider.value()) > 500:
                self.play_start_offset = self.position_slider.value()
                pygame.mixer.music.load(self._current_audio_path)
                pygame.mixer.music.play(start=self.play_start_offset / 1000.0)
            else:
                pygame.mixer.music.unpause()
            self.is_playing = True
            self.is_paused = False
            self.btn_play_preview.setText("⏸")
        else:
            # Stopped state
            if self.audio_loaded:
                self.play_start_offset = self.position_slider.value()
                pygame.mixer.music.play(start=self.play_start_offset / 1000.0)
                self.is_playing = True
                self.is_paused = False
                self.btn_play_preview.setText("⏸")
            else:
                self._play_selected_audio(res_key)
            
    def stop_audio(self):
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()  # Освобождаем файл
        except Exception:
            pass
        self.is_playing = False
        self.is_paused = False
        self.btn_play_preview.setText("▶")
        self.position_slider.setValue(0)
        self.update_time_labels(0)
        self.play_start_offset = 0
        self.audio_loaded = False
        self._playing_res_key = None

    def _get_main_app(self):
        """Находит главное окно (main_app) через цепочку родителей."""
        parent = self.parent()
        if not parent:
            return None
        # 1) Родитель — главное окно напрямую (standalone TTS)
        if hasattr(parent, 'audio_volume') and hasattr(parent, 'set_audio_volume'):
            return parent
        # 2) Родитель — FilesWindow (через parent_window -> main_app)
        if hasattr(parent, 'parent_window') and parent.parent_window:
            return getattr(parent.parent_window, 'main_app', None)
        # 3) Родитель — FilesWindow с main_app напрямую
        return getattr(parent, 'main_app', None)

    def set_volume(self, value):
        import pygame
        pygame.mixer.music.set_volume(value / 100.0)
        
        # Синхронизируем с остальными плеерами через главное окно
        main_app = self._get_main_app()
        if main_app:
            main_app.set_audio_volume(value, sender=self)

    def on_slider_pressed(self):
        self.is_slider_dragged = True
        
    def on_slider_released(self):
        import pygame
        val_ms = self.position_slider.value()
        self.play_start_offset = val_ms
        if self.is_playing:
            pygame.mixer.music.play(start=val_ms / 1000.0)
        self.update_time_labels(val_ms)
        self.is_slider_dragged = False

    def _check_playback(self):
        """Обновление прогресса плеера"""
        if getattr(self, 'is_slider_dragged', False): return
        
        try:
            import pygame
            is_busy = pygame.mixer.music.get_busy()
            pos = pygame.mixer.music.get_pos()
            
            if self.is_playing and is_busy and pos >= 0:
                current_ms = pos + self.play_start_offset
                self.position_slider.blockSignals(True)
                self.position_slider.setValue(current_ms)
                self.position_slider.blockSignals(False)
                self.update_time_labels(current_ms)
            elif self.is_playing and not is_busy:
                # Трек завершился
                self.stop_audio()
        except Exception:
            pass

    def update_time_labels(self, current_ms):
        def fmt(ms):
            s = int(ms // 1000) % 60
            m = int(ms // 60000)
            return f"{m:02}:{s:02}"
        dur_ms = int(self.duration_sec * 1000)
        self.time_label.setText(f"{fmt(current_ms)} / {fmt(dur_ms)}")

    def _start_piper_download(self, voice_id):
        self.btn_main_action.setEnabled(False); self.download_progress.show()
        self.download_worker = VoiceDownloadWorker(self.engine, voice_id)
        self.download_worker.progress.connect(self.download_progress.setValue)
        self.download_worker.finished.connect(lambda s, v: self._on_download_finished(s))
        self.download_worker.start()

    def _start_xtts_download(self):
        self.btn_install_xtts_model.setEnabled(False); self.download_progress.show()
        self.xtts_worker = XTTSDownloadWorker(self.engine)
        self.xtts_worker.progress.connect(self.download_progress.setValue)
        self.xtts_worker.progress_text.connect(self.lbl_status.setText)
        self.xtts_worker.finished.connect(self._on_download_finished)
        self.xtts_worker.start()

    def _start_piper_engine_install(self):
        self.btn_install_piper.setEnabled(False); self.download_progress.show()
        from localization import get_translation
        self.lbl_status.setText(get_translation(self.current_language, 'tts_status_dl_piper'))
        self.piper_engine_worker = PiperEngineWorker(self.engine)
        self.piper_engine_worker.progress.connect(self.download_progress.setValue)
        self.piper_engine_worker.progress_text.connect(self.lbl_status.setText)
        self.piper_engine_worker.finished.connect(self._on_piper_engine_finished)
        self.piper_engine_worker.start()

    def _on_piper_engine_finished(self, success):
        self.download_progress.hide(); self.btn_install_piper.setEnabled(True)
        from localization import get_translation
        if success: self.lbl_status.setText(get_translation(self.current_language, 'tts_status_piper_installed'))
        else: self.lbl_status.setText(get_translation(self.current_language, 'tts_err_dl_piper'))
        self._update_ui_state()

    def _start_library_install(self):
        self.btn_install_xtts_libs.setEnabled(False); self.download_progress.show()
        from localization import get_translation
        self.lbl_status.setText(get_translation(self.current_language, 'tts_status_install_libs'))
        self.lib_worker = LibraryInstallWorker(self.engine)
        self.lib_worker.progress.connect(lambda p, c, t: self.download_progress.setValue((self.download_progress.value() + 5) % 100))
        self.lib_worker.progress_text.connect(self.lbl_status.setText)
        self.lib_worker.finished.connect(self._on_library_install_finished)
        self.lib_worker.start()

    def _on_library_install_finished(self, success):
        self.download_progress.hide(); self.btn_main_action.setEnabled(True)
        from localization import get_translation
        if success:
            if self.engine.is_tts_libraries_installed():
                self.lbl_status.setText(get_translation(self.current_language, 'tts_status_libs_installed'))
                self._update_ui_state()
            else:
                self.lbl_status.setText(get_translation(self.current_language, 'tts_err_libs_dll'))
                self._update_ui_state()
        else:
            self.lbl_status.setText(get_translation(self.current_language, 'tts_err_install_libs_log'))
            
            # Показываем подробное окно с рекомендациями
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle(get_translation(self.current_language, 'tts_msgbox_xtts_err_title'))
            msg.setText(get_translation(self.current_language, 'tts_msgbox_xtts_err_text'))
            msg.setInformativeText(get_translation(self.current_language, 'tts_msgbox_xtts_err_info'))
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            self._update_ui_state()

    def _on_download_finished(self, success):
        self.download_progress.hide(); self.btn_main_action.setEnabled(True)
        from localization import get_translation
        if success:
            self.lbl_status.setText(get_translation(self.current_language, 'tts_status_dl_done'))
            self._update_ui_state()
        else:
            self.lbl_status.setText(get_translation(self.current_language, 'tts_err_dl_net'))

    def get_generated_path(self): return self.preview_path
    
    def _on_apply_checked_clicked(self):
        """Заменяет в миссии только отмеченные и сгенерированные файлы."""
        if not self.miz_resource_manager:
            from localization import get_translation
            self.lbl_status.setText(get_translation(self.current_language, 'tts_err_no_mission'))
            return
        
        # Останавливаем аудио перед заменой (чтобы не было PermissionError)
        self.stop_audio()
        
        checked = self.tts_playlist_widget.checked_keys
        replaced = 0
        replaced_keys = []
        
        for res_key in list(checked):
            cached_path = self.tts_cache.get(res_key)
            if cached_path:
                try:
                    # Получаем оригинальное имя файла из mapResource
                    audio_info = self.miz_resource_manager.get_audio_for_res_key(res_key)
                    if audio_info:
                        original_filename = audio_info[0]
                    else:
                        original_filename = os.path.basename(cached_path)
                    
                    # ВАЖНО: сохраняем расширение сгенерированного файла (.wav), 
                    # но используем базовое имя оригинала (чтобы не сломать формат файла)
                    base_name, _ = os.path.splitext(original_filename)
                    _, gen_ext = os.path.splitext(cached_path)
                    
                    # [МЕГА-ФИКС] Делаем финальное имя уникальным для каждого res_key,
                    # чтобы одинаковые имена файлов с разными текстами не перезаписывали 
                    # друг друга внутри архива миссии при сохранении.
                    safe_key = "".join([c if c.isalnum() else "_" for c in res_key])
                    final_filename = f"{base_name}_{safe_key}{gen_ext}"
                    
                    # Копируем во временную папку с правильным именем
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    renamed_path = os.path.join(temp_dir, final_filename)
                    import shutil
                    shutil.copy2(cached_path, renamed_path)
                    
                    self.miz_resource_manager.replace_audio(res_key, renamed_path)
                    self.tts_cache.remove(res_key)
                    self.tts_playlist_widget.update_generated_indicator(res_key, False)
                    replaced_keys.append(res_key)
                    replaced += 1
                except Exception as e:
                    print(f"DEBUG: Error replacing {res_key}: {e}")
        
        from localization import get_translation
        if replaced > 0:
            self.lbl_status.setText(get_translation(self.current_language, 'tts_status_replaced').format(count=replaced))
            # [FIX] Уведомляем основное окно о том, что миссия была изменена
            if self.parent() and hasattr(self.parent(), 'set_modified'):
                self.parent().set_modified(True)
            
            # [FIX] Обновляем метаданные в превью основного окна (название, цвет, иконка ⚠)
            main_win = self.parent()
            if main_win and hasattr(main_win, 'update_preview_for_key'):
                for rk in replaced_keys:
                    # Сбрасываем кэш длительности
                    if hasattr(main_win, 'shared_duration_cache'):
                        main_win.shared_duration_cache.pop(rk, None)
                    
                    # Обновляем превью для ResKey
                    main_win.update_preview_for_key(rk)
                    
                    # Обновляем превью для всех связанных DictKey
                    if hasattr(self.miz_resource_manager, 'subtitle_to_reskey'):
                        for dk, linked_rk in self.miz_resource_manager.subtitle_to_reskey.items():
                            if linked_rk == rk:
                                if hasattr(main_win, 'shared_duration_cache'):
                                    main_win.shared_duration_cache.pop(dk, None)
                                main_win.update_preview_for_key(dk)
                
            # Обновляем только заменённые строки в TTS плейлисте
            all_files = self.miz_resource_manager.get_all_resource_files()
            for rk in replaced_keys:
                for f_info in all_files:
                    if f_info.get('res_key') == rk:
                        self.tts_playlist_widget.update_item_by_key(rk, f_info)
                        break
            
            # [FIX] Обновляем плейлист в аудиоплеере главного окна (если он открыт)
            if main_win and hasattr(main_win, 'audio_player') and main_win.audio_player is not None:
                player = main_win.audio_player
                if hasattr(player, 'playlist_widget'):
                    for rk in replaced_keys:
                        for f_info in all_files:
                            if f_info.get('res_key') == rk:
                                player.playlist_widget.update_item_by_key(rk, f_info)
                                break
        else:
            self.lbl_status.setText(get_translation(self.current_language, 'tts_err_no_gen_files'))
        
        # Если кэш пуст, выключаем кнопку
        if not self.tts_cache._cache:
            self.btn_apply.setEnabled(False)

    def _has_unsaved_generated(self):
        """Проверяет, есть ли неприменённые сгенерированные файлы."""
        if not hasattr(self, 'tts_cache'):
            return False
        # Проверяем все файлы в кэше (не только отмеченные)
        return bool(self.tts_cache._cache)
    
    def _show_close_warning(self):
        """Показывает предупреждение о неприменённых файлах. Возвращает True если можно закрывать."""
        from localization import get_translation
        
        dialog = StandardQuestionDialog(
            title=get_translation(self.current_language, 'tts_close_warning_title'),
            message=get_translation(self.current_language, 'tts_close_warning_msg'),
            current_language=self.current_language,
            parent=self,
            yes_text=None,
            no_text=None
        )
        return dialog.exec_() == 1  # Accepted
    
    def done(self, r):
        if self._has_unsaved_generated():
            if not self._show_close_warning():
                return  # Отмена закрытия
            self.tts_cache.clear()
        if hasattr(self, 'settings'):
            self.settings.setValue("tts_window_geometry", self.saveGeometry())
            self.settings.setValue("tts_splitter_state", self.tts_splitter.saveState())
        self._stop_playback_safely()
        # Останавливаем фоновый сервер XTTS для освобождения VRAM
        if hasattr(self, 'engine') and hasattr(self.engine, 'shutdown_xtts_server'):
            self.engine.shutdown_xtts_server()
        super().done(r)

    def closeEvent(self, event):
        if self._has_unsaved_generated():
            if not self._show_close_warning():
                event.ignore()
                return
            self.tts_cache.clear()
        if hasattr(self, 'settings'):
            self.settings.setValue("tts_window_geometry", self.saveGeometry())
            self.settings.setValue("tts_splitter_state", self.tts_splitter.saveState())
        self._stop_playback_safely()
        # Останавливаем фоновый сервер XTTS для освобождения VRAM
        if hasattr(self, 'engine') and hasattr(self.engine, 'shutdown_xtts_server'):
            self.engine.shutdown_xtts_server()
        super().closeEvent(event)
    def _stop_playback_safely(self):
        try:
            import pygame
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except: pass
        self.is_playing = False

