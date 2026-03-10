# -*- coding: utf-8 -*-
"""
=== МОДУЛЬ МЕНЕДЖЕРА ФАЙЛОВ ===
UI-виджет для управления ресурсами миссии (аудио + изображения).
Показывает таблицу файлов с фильтрами, поиском, превью изображений
и встроенным аудиоплеером.
"""

import os
import logging
import zipfile
import shutil
import tempfile
import random
import string
import pygame

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QLineEdit, QPushButton, QSplitter, QSlider,
    QAbstractItemView, QFileDialog, QStyledItemDelegate, QStyle,
    QProxyStyle, QStyleOptionHeader, QStyleOptionSlider, QInputDialog, QMessageBox,
    QRadioButton, QDialog, QFrame, QStackedWidget, QApplication, QMenu, QShortcut
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject, QEvent, QPoint, QSize, QRect, QSettings, pyqtProperty, QEasingCurve, QPropertyAnimation, QMimeData, QUrl, QThread
from PyQt5.QtGui import QPixmap, QColor, QIcon, QFont, QCursor, QPainter, QPen, QBrush, QPainterPath, QPolygon, QFontMetrics, QDrag, QKeySequence

from localization import get_translation
from widgets import ToggleSwitch, CustomToolTip, ClickableLabel, ZoomablePreviewArea
from tts_engine import TTSEngine
from dialogs import (StandardQuestionDialog, StandardInfoDialog, MizProgressDialog, TTSPreviewDialog)

logger = logging.getLogger(__name__)


# Маппинг context -> ключ локализации
CONTEXT_TO_LOC_KEY = {
    'briefing_blue': 'fm_desc_briefing_blue',
    'briefing_red': 'fm_desc_briefing_red',
    'briefing_neutral': 'fm_desc_briefing_neutral',
    'trigger': 'fm_desc_trigger',
    'audio_linked': 'fm_desc_audio_linked',
    'audio_trigger': 'fm_desc_audio_trigger',
    'kneeboard': 'fm_desc_kneeboard',
}

# ═══ Настройки иконок режимов отображения ═══
# Эти значки используются над слайдером в правой части окна.
ICON_VIEW_TABLE = "≡"            # Режим легкого списка
ICON_VIEW_TABLE_SIZE = 20        # Размер значка списка (px)
ICON_VIEW_CONTENT = "⊞"          # Режим миниатюр
ICON_VIEW_CONTENT_SIZE = 23      # Размер значка миниатюр (px)


class TTSWorker(QThread):
    """Поток для генерации озвучки, чтобы не фризить UI."""
    finished = pyqtSignal(bool, str) # успех, сообщение

    def __init__(self, tts_engine, text, output_path, lang='ru', **kwargs):
        super().__init__()
        self.tts = tts_engine
        self.text = text
        self.output_path = output_path
        self.lang = lang
        self.kwargs = kwargs

    def run(self):
        try:
            success = self.tts.generate_speech(self.text, self.output_path, self.lang, **self.kwargs)
            self.finished.emit(success, self.output_path)
        except Exception as e:
            logger.error(f"TTSWorker error: {e}")
            self.finished.emit(False, str(e))
# ══════════════════════════════════════════



class ColorKeepingDelegate(QStyledItemDelegate):
    """Делегат, который сохраняет ForegroundRole на выделенных ячейках.
    Qt по умолчанию перекрашивает текст selected-ячеек через stylesheet.
    Этот делегат берет цвет из ForegroundRole и применяет его вместо стандартного."""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Берем цвет из модели (ForegroundRole)
        fg = index.data(Qt.ForegroundRole)
        if fg:
            if isinstance(fg, QBrush):
                option.palette.setColor(option.palette.Text, fg.color())
                option.palette.setColor(option.palette.HighlightedText, fg.color())
            elif isinstance(fg, QColor):
                option.palette.setColor(option.palette.Text, fg)
                option.palette.setColor(option.palette.HighlightedText, fg)


class SortableTableWidgetItem(QTableWidgetItem):
    """Ячейка таблицы с кастомной логикой сортировки."""
    def __init__(self, text, sort_value):
        super().__init__(text)
        self.sort_value = sort_value

    def __lt__(self, other):
        if isinstance(other, SortableTableWidgetItem):
            return self.sort_value < other.sort_value
        return super().__lt__(other)


class NaturalSortTableWidgetItem(QTableWidgetItem):
    """Кастомный элемент таблицы для естественной сортировки строк с числами (например, 'Item 2' перед 'Item 10')"""
    def __lt__(self, other):
        if isinstance(other, QTableWidgetItem):
            import re
            def convert(text):
                return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', text)]
            return convert(self.text()) < convert(other.text())
        return super().__lt__(other)


class JumpSlider(QSlider):
    """Слайдер, который сразу перемещается к месту клика."""
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            # Вычисляем новое значение на основе позиции клика
            val = self.style().sliderValueFromPosition(
                self.minimum(), self.maximum(), event.x(), self.width()
            )
            self.setValue(val)
        super().mousePressEvent(event)


class FileManagerStyle(QProxyStyle):
    """Proxy-стиль для отрисовки элементов интерфейса менеджера в едином стиле."""

    def drawPrimitive(self, element, option, painter, widget=None):
        # 1. Отрисовка стрелок сортировки цветом #999999
        if element == QStyle.PE_IndicatorHeaderArrow:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor('#999999'))
            rect = option.rect
            cx = rect.center().x()
            cy = rect.center().y()
            size = 3 # В 1.6 раза меньше (было 5)
            # В QStyleOptionHeader направление хранится в sortIndicator
            # Также проверяем биты состояния UpArrow/DownArrow
            is_up = False
            if hasattr(option, 'sortIndicator'):
                is_up = (option.sortIndicator == QStyleOptionHeader.SortUp)
            else:
                is_up = bool(option.state & QStyle.State_UpArrow)

            if is_up:
                # Стрелка ВВЕРХ (острием вверх)
                poly = QPolygon([QPoint(cx - size, cy + size // 2),
                                 QPoint(cx + size, cy + size // 2),
                                 QPoint(cx, cy - size)])
            else:
                # Стрелка ВНИЗ (острием вниз)
                poly = QPolygon([QPoint(cx - size, cy - size // 2),
                                 QPoint(cx + size, cy - size // 2),
                                 QPoint(cx, cy + size)])
            painter.drawPolygon(poly)
            painter.restore()
            return

        # 2. Отрисовка чекбоксов с оранжевой галочкой #ff9900
        if element == QStyle.PE_IndicatorCheckBox:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Рамка чекбокса
            rect = option.rect.adjusted(1, 1, -1, -1)
            painter.setPen(QPen(QColor('#666666'), 1))
            painter.setBrush(QBrush(QColor('#333333')))
            painter.drawRoundedRect(rect, 2, 2)
            
            # Галочка (при включенном состоянии)
            if option.state & (QStyle.State_On | QStyle.State_NoChange):
                painter.setPen(QPen(QColor('#ff9900'), 2))
                if option.state & QStyle.State_NoChange:
                    # Частичное выделение (минус в центре)
                    painter.drawLine(rect.left() + 3, rect.center().y(), rect.right() - 3, rect.center().y())
                else:
                    # Полное выделение (галочка) - пропорциональные отступы
                    p1 = QPoint(rect.left() + rect.width()//5 + 1, rect.center().y() + 1)
                    p2 = QPoint(rect.center().x() - 1, rect.bottom() - rect.height()//5 - 1)
                    p3 = QPoint(rect.right() - rect.width()//5, rect.top() + rect.height()//5 + 1)
                    painter.drawLine(p1, p2)
                    painter.drawLine(p2, p3)
            painter.restore()
            return

        super().drawPrimitive(element, option, painter, widget)

    def pixelMetric(self, metric, option=None, widget=None):
        """Переопределяем размеры чекбоксов (увеличение на ~20%)."""
        if metric == QStyle.PM_IndicatorWidth:
            return 19
        if metric == QStyle.PM_IndicatorHeight:
            return 19
        return super().pixelMetric(metric, option, widget)


class CheckboxHeader(QHeaderView):
    """Кастомный заголовок с чекбоксом в первой колонке."""
    checkboxToggled = pyqtSignal(int)
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.check_state = Qt.Unchecked
        
    def set_check_state(self, state):
        if self.check_state != state:
            self.check_state = state
            self.updateSection(0) # COL_CHECK всегда 0

    def _get_checkbox_rect(self, section_rect):
        """Возвращает прямоугольник чекбокса для хит-теста и отрисовки."""
        cb_size = 20
        return QRect(
            section_rect.left() + (section_rect.width() - cb_size) // 2 - 7,
            section_rect.top() + (section_rect.height() - cb_size) // 2,
            cb_size, cb_size
        )

    def mousePressEvent(self, event):
        """Обработка клика: если попали в чекбокс - переключаем, иначе - отдаем на сортировку."""
        logical_index = self.logicalIndexAt(event.pos())
        if logical_index == 0:
            section_rect = QRect(self.sectionViewportPosition(0), 0, self.sectionSize(0), self.height())
            cb_rect = self._get_checkbox_rect(section_rect)
            
            # Расширяем область клика для удобства (хитбокс)
            hitbox = cb_rect.adjusted(-5, -5, 5, 5)
            if hitbox.contains(event.pos()):
                # Инвертируем состояние
                new_state = Qt.Checked if self.check_state == Qt.Unchecked else Qt.Unchecked
                self.set_check_state(new_state)
                self.checkboxToggled.emit(new_state)
                event.accept()
                return

        super().mousePressEvent(event)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        # Вызываем стандартную отрисовку фона (через стиль/stylesheet)
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()

        # Если это колонка чекбоксов, рисуем сам чекбокс поверх
        if logicalIndex == 0:
            cb_rect = self._get_checkbox_rect(rect)
            
            # Используем FileManagerStyle для отрисовки через PE_IndicatorCheckBox
            style_option = QStyleOptionHeader()
            style_option.rect = cb_rect
            if self.check_state == Qt.Checked:
                style_option.state |= QStyle.State_On
            elif self.check_state == Qt.PartiallyChecked:
                style_option.state |= QStyle.State_NoChange
            else:
                style_option.state |= QStyle.State_Off
            
            style_option.state |= QStyle.State_Enabled
            self.style().drawPrimitive(QStyle.PE_IndicatorCheckBox, style_option, painter, self)


class ToolTipFilter(QObject):
    """
    Перехватывает стандартные системные события ToolTip (черный квадрат) 
    и заменяет их на плавное отображение CustomToolTip.
    """
    def __init__(self, table, parent=None):
        super().__init__(parent)
        self.table = table
        self.table.viewport().installEventFilter(self)
        self.tooltip_timer = QTimer(self)
        self.tooltip_timer.setSingleShot(True)
        self.tooltip_timer.timeout.connect(self._show_tooltip)
        self.custom_tooltip = CustomToolTip()
        self._last_item = None
        self._pending_text = ""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ToolTip:
            return True  # Подавляем системный тултип
            
        if obj == self.table.viewport() and event.type() in (QEvent.MouseMove, QEvent.HoverMove):
            item = self.table.itemAt(event.pos())
            if item != self._last_item:
                self._last_item = item
                self.tooltip_timer.stop()
                self.custom_tooltip.hide()
                
                if item:
                    text = item.data(Qt.ToolTipRole)
                    if text:
                        self._pending_text = text
                        self.tooltip_timer.start(500)
            return False
            
        elif obj == self.table.viewport() and event.type() == QEvent.Leave:
            self.tooltip_timer.stop()
            self.custom_tooltip.hide()
            self._last_item = None
            return False
            
        return super().eventFilter(obj, event)

    def _show_tooltip(self):
        if self._pending_text:
            pos = QCursor.pos()
            # Используем fallback метод CustomToolTip для отображения по координатам мыши
            try:
                self.custom_tooltip._fallback_show(self._pending_text, pos)
            except AttributeError:
                pass


class ButtonToolTipFilter(QObject):
    """Перехватывает системные тултипы на QPushButton и показывает CustomToolTip."""
    def __init__(self, custom_tooltip, parent=None):
        super().__init__(parent)
        self.custom_tooltip = custom_tooltip
        self._buttons = []

    def add_button(self, btn):
        btn.installEventFilter(self)
        self._buttons.append(btn)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ToolTip:
            return True  # Подавляем системный
        if event.type() == QEvent.Enter:
            text = obj.toolTip()
            if text:
                pos = QCursor.pos()
                self.custom_tooltip._fallback_show(text, QPoint(pos.x(), pos.y() + 20))
            return False
        if event.type() == QEvent.Leave:
            self.custom_tooltip.hide()
            return False
        return super().eventFilter(obj, event)



class ModeToggleSwitch(QWidget):
    """Кастомный toggle-переключатель для выбора режима (Suffix/Single) с цветами Blue/Red."""
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(34, 16)
        self.setCursor(Qt.PointingHandCursor)
        self._checked = False
        self._circle_position = 2
        self.animation = QPropertyAnimation(self, b"circle_position")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.bg_color_off = QColor(51, 102, 255) # Blue
        self.bg_color_on = QColor(255, 51, 51)  # Red
        self.circle_color = QColor(240, 240, 240)

    def get_circle_position(self): return self._circle_position
    def set_circle_position(self, pos):
        self._circle_position = pos
        self.update()
    circle_position = pyqtProperty(int, get_circle_position, set_circle_position)

    def isChecked(self): return self._checked
    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self.start_animation()
            self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
            event.accept()

    def start_animation(self):
        self.animation.setStartValue(self._circle_position)
        self.animation.setEndValue(20 if self._checked else 2)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.contentsRect()
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.bg_color_on if self._checked else self.bg_color_off)
        painter.drawRoundedRect(rect, 8, 8)
        painter.setBrush(self.circle_color)
        painter.drawEllipse(self._circle_position - 1, 1, 14, 14)


class BatchReplaceDialog(QDialog):
    """Кастомный диалог пакетной замены ресурсов."""
    def __init__(self, current_language, file_filter="All Files (*)", parent=None):
        super().__init__(parent)
        self.current_language = current_language
        self.file_filter = file_filter
        self.mode = "suffix" # "suffix" or "single"
        self.selected_file = None
        
        # Настройка кастомного окна
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(580, 400)
        
        if parent:
            # Центрируем относительно родителя
            parent_geo = parent.window().geometry()
            self.move(
                parent_geo.center().x() - 580 // 2,
                parent_geo.center().y() - 400 // 2 - 50
            )
            
        self.drag_pos = QPoint()
        self._is_dragging = False
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        
        container = QFrame()
        container.setObjectName("BatchReplaceContent")
        container.setStyleSheet("""
            QFrame#BatchReplaceContent {
                background-color: #333333;
                border: 1px solid #ff9900;
                border-radius: 9px;
            }
            QLabel { 
                color: #ffffff; 
                background-color: transparent;
                font-size: 13px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #2b2d30;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 10px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #ff9900; }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(20)
        
        # Настройки окна
        self.setWindowTitle(get_translation(self.current_language, 'fm_br_title_window'))
        self.setFixedSize(580, 400)
        
        # Заголовок
        title_label = QLabel(get_translation(self.current_language, 'fm_br_title'))
        title_label.setStyleSheet("font-size: 16px; color: #ff9900; font-weight: bold; margin-bottom: 5px;")
        title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title_label)
        
        # Ряд с тогглом (По суффиксу -- ТОГГЛ -- Один файл для всех)
        toggle_row = QWidget()
        toggle_row.setStyleSheet("background: transparent;")
        toggle_layout = QHBoxLayout(toggle_row)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(12)
        toggle_layout.addStretch()
        
        from widgets import ClickableLabel
        self.lbl_mode_suffix = ClickableLabel(get_translation(self.current_language, 'fm_br_mode_suffix'))
        self.lbl_mode_single = ClickableLabel(get_translation(self.current_language, 'fm_br_mode_single'))
        self.lbl_mode_suffix.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        self.lbl_mode_single.setStyleSheet("color: #888888; font-size: 12px; font-weight: normal;")
        
        self.mode_toggle = ModeToggleSwitch()
        self.mode_toggle.setChecked(False) # Слева (Suffix)
        
        toggle_layout.addWidget(self.lbl_mode_suffix)
        toggle_layout.addWidget(self.mode_toggle)
        toggle_layout.addWidget(self.lbl_mode_single)
        toggle_layout.addStretch()
        container_layout.addWidget(toggle_row)
        
        # Область описания
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #cccccc; font-size: 12px; font-weight: normal; line-height: 1.4;")
        container_layout.addWidget(self.desc_label)
        
        # Контейнер для ввода префикса и суффикса
        self.suffix_container = QWidget()
        self.suffix_container.setStyleSheet("background: transparent;")
        suffix_layout = QGridLayout(self.suffix_container)
        suffix_layout.setContentsMargins(0, 0, 0, 0)
        suffix_layout.setSpacing(10)
        
        # Префикс
        prefix_label = QLabel(get_translation(self.current_language, 'fm_br_prefix_label'))
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("new_")
        settings = QSettings("MissionTranslator", "DCSTranslatorTool")
        self.prefix_input.setText(settings.value("fm_last_batch_prefix", ""))
        
        suffix_layout.addWidget(prefix_label, 0, 0)
        suffix_layout.addWidget(self.prefix_input, 0, 1)
        
        # Суффикс
        suffix_label = QLabel(get_translation(self.current_language, 'fm_replace_suffix_label'))
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("_old")
        self.suffix_input.setText(settings.value("fm_last_batch_suffix", ""))
        
        suffix_layout.addWidget(suffix_label, 1, 0)
        suffix_layout.addWidget(self.suffix_input, 1, 1)
        
        container_layout.addWidget(self.suffix_container)
        
        # Контейнер для выбора одного файла
        self.single_container = QWidget()
        self.single_container.setStyleSheet("background: transparent;")
        single_layout = QHBoxLayout(self.single_container)
        single_layout.setContentsMargins(0, 0, 0, 0)
        self.file_path_label = QLineEdit()
        self.file_path_label.setReadOnly(True)
        self.file_path_label.setPlaceholderText(get_translation(self.current_language, 'fm_br_select_file'))
        self.btn_browse = QPushButton("...")
        self.btn_browse.setFixedWidth(40)
        self.btn_browse.setCursor(Qt.PointingHandCursor)
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #2b2d30;
                border: 1px solid #555;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton:hover { border-color: #ff9900; background-color: #3d3f43; }
        """)
        self.btn_browse.clicked.connect(self._on_browse_clicked)
        single_layout.addWidget(self.file_path_label)
        single_layout.addWidget(self.btn_browse)
        self.single_container.hide()
        container_layout.addWidget(self.single_container)
        
        container_layout.addSpacing(10)
        
        # Кнопки внизу (ПИЛЮЛЯ)
        btns_layout = QHBoxLayout()
        self.btn_cancel = QPushButton(get_translation(self.current_language, 'fm_br_btn_cancel'))
        self.btn_apply = QPushButton(get_translation(self.current_language, 'fm_br_btn_apply'))
        
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_apply.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setFixedSize(90, 34)
        self.btn_apply.setFixedSize(90, 34)
        
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 17px;
                padding: 0;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #dddddd; }
            QPushButton:pressed { background-color: #aaaaaa; }
        """)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #ff9900;
                color: #1a1c26;
                border: none;
                border-radius: 17px;
                padding: 0;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #ffaa33; }
        """)
        
        btns_layout.addStretch()
        btns_layout.addWidget(self.btn_apply)
        btns_layout.addSpacing(15)
        btns_layout.addWidget(self.btn_cancel)
        btns_layout.addStretch()
        container_layout.addLayout(btns_layout)
        
        main_layout.addWidget(container)
        
        # Подключения
        self.mode_toggle.toggled.connect(self._update_visibility)
        self.lbl_mode_suffix.clicked.connect(lambda: self.mode_toggle.setChecked(False))
        self.lbl_mode_single.clicked.connect(lambda: self.mode_toggle.setChecked(True))
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self.accept)
        
        self._update_visibility()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Предотвращаем перетаскивание, если кликнули на интерактивный элемент
            # Используем рекурсивную проверку имен классов для надежности
            child = self.childAt(event.pos())
            is_interactive = False
            temp = child
            while temp:
                if temp.__class__.__name__ in ["QPushButton", "QLineEdit", "ModeToggleSwitch", "ClickableLabel", "QRadioButton"]:
                    is_interactive = True
                    break
                temp = temp.parentWidget()
                
            if is_interactive:
                self._is_dragging = False
                return
            
            self._is_dragging = True
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._is_dragging:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False

    def _update_visibility(self):
        is_single = self.mode_toggle.isChecked()
        self.mode = "single" if is_single else "suffix"
        
        self.suffix_container.setVisible(not is_single)
        self.single_container.setVisible(is_single)
        
        # Обновляем стили меток
        if is_single:
            self.lbl_mode_single.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
            self.lbl_mode_suffix.setStyleSheet("color: #888888; font-size: 12px; font-weight: normal;")
            self.desc_label.setText(get_translation(self.current_language, 'fm_br_desc_single'))
        else:
            self.lbl_mode_suffix.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
            self.lbl_mode_single.setStyleSheet("color: #888888; font-size: 12px; font-weight: normal;")
            self.desc_label.setText(get_translation(self.current_language, 'fm_br_desc_suffix'))

    def _on_browse_clicked(self):
        settings = QSettings("MissionTranslator", "DCSTranslatorTool")
        last_dir = settings.value("fm_last_import_dir", os.path.expanduser("~"))
        
        path, _ = QFileDialog.getOpenFileName(
            self, get_translation(self.current_language, 'fm_br_select_file'),
            last_dir,
            self.file_filter
        )
        if path:
            self.selected_file = path
            self.file_path_label.setText(os.path.basename(path))
            settings.setValue("fm_last_import_dir", os.path.dirname(path))

    def get_result(self):
        return {
            "mode": "single" if self.mode_toggle.isChecked() else "suffix",
            "prefix": self.prefix_input.text().strip(),
            "suffix": self.suffix_input.text().strip(),
            "file_path": self.selected_file
        }



    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._is_dragging:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False


class FileManagerWidget(QWidget):
    """Виджет менеджера файлов для управления ресурсами миссии."""
    resourcesChanged = pyqtSignal()

    # Индексы колонок (колонка Номер удалена, теперь используется Action/VerticalHeader)
    COL_CHECK = 0
    COL_TYPE = 1
    COL_FILENAME = 2
    COL_DESCRIPTION = 3
    COL_STATUS = 4
    COL_ACTIONS = 5

    def __init__(self, current_language, parent=None):
        super().__init__(parent)
        self.current_language = current_language
        self.parent_window = parent
        
        # Настройки окна (Увеличенная ширина для вмещения тулбара)
        self.setWindowTitle(get_translation(current_language, 'fm_title'))
        # Гарантируем, что само окно достаточно широкое, чтобы вместить таблицу (минимум 750) и превью
        self.setMinimumSize(1250, 700)
        self.miz_resource_manager = None
        self.miz_path = None
        self._all_files = []  # Полный список ресурсов от MizResourceManager
        self._last_checked_row = None # Для Shift+Click

        # Аудио состояние
        self._preview_audio_key = None   # res_key аудио в превью-плеере
        self._preview_audio_path = None  # темп-путь к файлу превью
        self._preview_playing = False
        self._preview_paused = False
        self._preview_duration_sec = 0
        self._preview_play_offset = 0
        self._preview_audio_loaded = False
        self._preview_slider_dragged = False
        self._action_playing_key = None  # res_key аудио, играющего через кнопку действий
        self._action_playing_btn = None  # QPushButton для смены иконки
        self._action_paused = False

        # TTS движок
        self.tts = TTSEngine()
        self._tts_worker = None

        # Кэш миниатюр для режима "Содержимое"
        self._thumbnail_cache = {}
        self._default_row_height = 28
        self._default_type_col_width = 55

        self._init_ui()

        # Таймер обновления аудио состояния
        self._audio_timer = QTimer(self)
        self._audio_timer.timeout.connect(self._check_audio_state)
        self._audio_timer.start(200)

        # Загрузка сохраненного положения слайдера
        settings = QSettings("MissionTranslator", "DCSTranslatorTool")
        saved_view = settings.value("fm_view_slider_value", 0, type=int)
        self.view_slider.setValue(saved_view)

    def _init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ═══ Панель управления (поиск + фильтры) ═══
        controls_widget = QWidget()
        controls_widget.setFixedHeight(36)
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(10, 5, 10, 5)
        controls_layout.setSpacing(10)

        # Строка поиска (уменьшенная ширина)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            get_translation(self.current_language, 'fm_search_placeholder'))
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMaximumWidth(200)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2d30;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #ff9900;
            }
        """)
        self.search_input.textChanged.connect(self._apply_filters)
        controls_layout.addWidget(self.search_input)

        # Горячая клавиша Ctrl+F для фокуса на поиске
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.search_input.setFocus)

        # Фильтр: Аудио (ToggleSwitch + Label)
        self.filter_audio = ToggleSwitch()
        self.filter_audio.setChecked(True)
        self.filter_audio.toggled.connect(self._apply_filters)
        container_audio, self.label_filter_audio = self._create_toggle_container(
            self.filter_audio, get_translation(self.current_language, 'fm_filter_audio'))
        controls_layout.addWidget(container_audio)

        # Фильтр: Изображения (ToggleSwitch + Label)
        self.filter_images = ToggleSwitch()
        self.filter_images.setChecked(True)
        self.filter_images.toggled.connect(self._apply_filters)
        container_images, self.label_filter_images = self._create_toggle_container(
            self.filter_images, get_translation(self.current_language, 'fm_filter_images'))
        controls_layout.addWidget(container_images)

        # Фильтр: Планшет (ToggleSwitch + Label)
        self.filter_kneeboard = ToggleSwitch()
        self.filter_kneeboard.setChecked(True)
        self.filter_kneeboard.toggled.connect(self._apply_filters)
        container_kneeboard, self.label_filter_kneeboard = self._create_toggle_container(
            self.filter_kneeboard, get_translation(self.current_language, 'fm_filter_kneeboard'))
        controls_layout.addWidget(container_kneeboard)
        
        controls_layout.addSpacing(10)
        
        # Кнопки массовых действий
        self.btn_batch_replace = QPushButton(get_translation(self.current_language, 'fm_btn_batch_replace'))
        self.btn_batch_replace.setEnabled(False)
        self.btn_batch_replace.setCursor(Qt.PointingHandCursor)
        self.btn_batch_replace.setFixedHeight(30)
        self.btn_batch_replace.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                border: 1px solid #ffffff;
                border-radius: 15px;
                padding: 0 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: transparent;
                color: #ff9900;
                border-color: #ff9900;
            }
            QPushButton:disabled { color: #555; border-color: #555; }
        """)
        self.btn_batch_replace.clicked.connect(self._on_batch_replace_clicked)
        controls_layout.addWidget(self.btn_batch_replace)

        self.btn_batch_export = QPushButton(get_translation(self.current_language, 'fm_btn_batch_export'))
        self.btn_batch_export.setEnabled(False)
        self.btn_batch_export.setCursor(Qt.PointingHandCursor)
        self.btn_batch_export.setFixedHeight(30)
        self.btn_batch_export.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                border: 1px solid #ffffff;
                border-radius: 15px;
                padding: 0 15px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: transparent; 
                color: #ff9900;
                border-color: #ff9900;
            }
            QPushButton:disabled { color: #555; border-color: #555; }
        """)
        self.btn_batch_export.clicked.connect(self._on_batch_export_clicked)
        controls_layout.addWidget(self.btn_batch_export)

        controls_layout.addStretch()
        
        # --- Правая часть: Инфо о миссии и локали ---
        self.info_container = QWidget()
        self.info_container.setStyleSheet("background: transparent;")
        info_layout = QHBoxLayout(self.info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        
        # Стили (белый текст для заголовков, оранжевый для значений)
        lbl_style = "color: #ffffff; font-size: 12px; font-weight: bold; background: transparent; border: none;"
        val_style = "color: #ff9900; font-size: 12px; font-weight: bold; background: transparent; border: none;"
        
        # Миссия
        self.label_mission_prefix = QLabel(get_translation(self.current_language, 'mission_label'))
        self.label_mission_prefix.setStyleSheet(lbl_style)
        info_layout.addWidget(self.label_mission_prefix)
        
        self.label_mission_name = QLabel("-")
        self.label_mission_name.setStyleSheet(val_style)
        info_layout.addWidget(self.label_mission_name)
        
        # Разделитель
        sep = QLabel("|")
        sep.setStyleSheet("color: #555; font-size: 12px; background: transparent; border: none;")
        info_layout.addWidget(sep)
        
        # Локаль
        self.label_locale_prefix = QLabel(get_translation(self.current_language, 'localization_label'))
        self.label_locale_prefix.setStyleSheet(lbl_style)
        info_layout.addWidget(self.label_locale_prefix)
        
        self.label_locale_name = QLabel("-")
        self.label_locale_name.setStyleSheet(val_style)
        info_layout.addWidget(self.label_locale_name)
        
        controls_layout.addWidget(self.info_container)

        layout.addWidget(controls_widget)

        # ═══ Сплиттер: Таблица + Превью (Горизонтальный) ═══
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(0) # Убираем разделитель
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;
            }
        """)

        # ─── Таблица файлов ───
        self.table = QTableWidget()
        self.table.setColumnCount(6) # Убрали колонку с номером, теперь их 6
        
        # Включаем и настраиваем вертикальный заголовок для отображения настоящих номеров строк
        v_header = self.table.verticalHeader()
        v_header.setVisible(True)
        v_header.setDefaultSectionSize(28) # Высота строки
        v_header.setMinimumWidth(35)
        v_header.setHighlightSections(False)
        v_header.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        v_header.setSectionResizeMode(QHeaderView.Fixed)

        self._update_table_headers()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        self.table.setMouseTracking(True)
        self.table.viewport().setMouseTracking(True)
        
        # Делегат, сохраняющий цвета ForegroundRole на выделенных ячейках
        self.table.setItemDelegate(ColorKeepingDelegate(self.table))
        
        self.fm_style = FileManagerStyle(self.table.style())
        self.table.setStyle(self.fm_style)
        
        # Коллекция выделенных ключей для сохранения выбора при фильтрации
        self.checked_keys = set()
        self._first_load = True  # Флаг для первоначальной сортировки (картинки выше)
        
        # Кастомный заголовок с чекбоксом в первой колонке
        self.table.setHorizontalHeader(CheckboxHeader(Qt.Horizontal, self.table))
        self._update_table_headers()
        
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.table.itemChanged.connect(self._on_item_changed)

        # Настройка колонок
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_CHECK, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_TYPE, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_FILENAME, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_DESCRIPTION, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.Fixed)
        header.setSectionResizeMode(self.COL_ACTIONS, QHeaderView.Fixed)
        self.table.setColumnWidth(self.COL_CHECK, 50)
        self.table.setColumnWidth(self.COL_TYPE, 55)
        self.table.setColumnWidth(self.COL_DESCRIPTION, 150)
        self.table.setColumnWidth(self.COL_STATUS, 65)
        self.table.setColumnWidth(self.COL_ACTIONS, 100) 

        # Устанавливаем кастомный тултип для таблицы
        self._tooltip_filter = ToolTipFilter(self.table, self)
        # Кастомный тултип для кнопок действий
        self._btn_tooltip_filter = ButtonToolTipFilter(self._tooltip_filter.custom_tooltip, self)

        # Стиль таблицы + скроллбар в стиле основного окна (CustomScrollBar)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                gridline-color: transparent;
                font-size: 13px;
                outline: 0;
            }
            QTableWidget QLineEdit {
                background-color: #2b2b2b;
                color: #ff9900;
                border: 1px solid #ff9900;
                border-radius: 2px;
                padding: 0px 3px;
                margin: 0px;
                height: 20px;
                selection-background-color: #ff9900;
                selection-color: #1a1a1a;
            }
            QTableWidget::item {
                padding: 4px 6px;
                border-bottom: 1px solid #2d2d30;
            }
            QTableWidget::item:selected {
                background-color: #3d4256;
            }
            QHeaderView::section:horizontal {
                background-color: #2b2d30;
                color: #ff9900;
                padding: 6px 20px 6px 8px; /* Резервируем место справа под стрелку сортировки */
                border: none;
                border-bottom: 1px solid #ff9900;
                font-weight: bold;
                font-size: 12px;
            }
            QHeaderView::section:vertical {
                background-color: transparent;
                color: #ffffff;
                border: none;
                border-right: 1px solid #3d4256;
                padding-right: 5px;
                font-size: 12px;
            }
            QHeaderView::option {
                background-color: transparent;
            }
            QTableCornerButton::section {
                background-color: #2b2d30;
                border: none;
                border-bottom: 1px solid #ff9900;
                border-right: 1px solid #3d4256;
            }

            /* Скроллбар — стиль из основного окна (CustomScrollBar) */
            QScrollBar:vertical {
                background: #333333;
                width: 16px;
                margin: 18px 0px 18px 0px;
                border-radius: 8px;
            }
            QScrollBar::handle:vertical {
                background: #ff9900;
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #e68a00;
            }
            QScrollBar::sub-line:vertical {
                background: none;
                height: 16px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::add-line:vertical {
                background: none;
                height: 16px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                width: 14px;
                height: 14px;
                background: #ff9900;
                border-radius: 7px;
                margin: 1px;
            }
            QScrollBar::up-arrow:vertical:hover, QScrollBar::down-arrow:vertical:hover {
                background: #e68a00;
            }

            QScrollBar:horizontal {
                background: #333333;
                height: 16px;
                margin: 0px 18px 0px 18px;
                border-radius: 8px;
            }
            QScrollBar::handle:horizontal {
                background: #ff9900;
                min-width: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #e68a00;
            }
            QScrollBar::sub-line:horizontal {
                background: none;
                width: 16px;
                subcontrol-position: left;
                subcontrol-origin: margin;
            }
            QScrollBar::add-line:horizontal {
                background: none;
                width: 16px;
                subcontrol-position: right;
                subcontrol-origin: margin;
            }
            QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
                width: 14px;
                height: 14px;
                background: #ff9900;
                border-radius: 7px;
                margin: 1px;
            }
            QScrollBar::left-arrow:horizontal:hover, QScrollBar::right-arrow:horizontal:hover {
                background: #e68a00;
            }
        """)

        self.table.currentCellChanged.connect(self._on_row_selected)
        self.table.doubleClicked.connect(self._on_table_double_clicked)
        self.table.viewport().installEventFilter(self) # Для Shift-Click на чекбоксах и Drag-Out
        self.table.setMouseTracking(True)
        self.table.viewport().setMouseTracking(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        self._drag_start_pos = None
        self._drag_start_row = None

        # Устанавливаем минимальную ширину таблицы, чтобы все верхние элементы помещались
        self.table.setMinimumWidth(750)
        self.splitter.addWidget(self.table)

        # Здесь можно вручную задать стартовые размеры [ШиринаТаблицы, ШиринаПревьюПлеер]
        # Например, 750 для таблицы и 300 для правой панели:
        self.splitter.setSizes([900, 300])

        # ─── Область превью ───
        self.preview_container = QWidget()
        self.preview_container.setMinimumWidth(514 + 20)
        self.preview_container.setMaximumWidth(514 + 20)
        self.preview_container.setStyleSheet(
            "QWidget#previewContainer { background-color: #3a3a3a; border: 1px solid #555555; border-radius: 4px; }")
        self.preview_container.setObjectName("previewContainer")
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(10, 10, 10, 10)

        self.preview_stack = QStackedWidget(self.preview_container)
        self.preview_stack.setStyleSheet("""
            QStackedWidget {
                border: 1px solid #555555;
                border-radius: 0px;
                background-color: transparent;
            }
        """)
        self.preview_stack.setFixedSize(514, 514)
        preview_layout.addWidget(self.preview_stack, 0, Qt.AlignCenter)
        
        # Информационная строка изображения (разрешение и размер)
        self.image_info_label = QLabel("")
        self.image_info_label.setStyleSheet("color: #aaaaaa; font-size: 11px; margin: 4px 0 2px 0; background: transparent; border: none;")
        self.image_info_label.setAlignment(Qt.AlignLeft)
        self.image_info_label.hide() # По умолчанию скрыта
        preview_layout.addWidget(self.image_info_label)
        
        # [FIX] Распорка, чтобы вытолкнуть ползунок и подсказку в самый низ
        preview_layout.addStretch()

        # 1. Страница: Плейсхолдер (надпись)
        self.placeholder_label = QLabel()
        self.placeholder_label.setFixedSize(512, 512)
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setWordWrap(True)
        self.placeholder_label.setText(get_translation(self.current_language, 'fm_preview_placeholder'))
        self.placeholder_label.setStyleSheet(
            "color: #777; font-size: 14px; border: none; border-radius: 4px; background: transparent;")
        self.preview_stack.addWidget(self.placeholder_label)

        # 2. Страница: Просмотр картинок
        self.preview_area = ZoomablePreviewArea()
        self.preview_area.setFixedSize(512, 512)
        self.preview_stack.addWidget(self.preview_area)

        # 3. Страница: Аудиоплеер
        self._audio_player_widget = QWidget()
        self._audio_player_widget.setStyleSheet("background: transparent; border: none;")
        self.preview_stack.addWidget(self._audio_player_widget)
        
        ap_layout = QVBoxLayout(self._audio_player_widget)
        ap_layout.setContentsMargins(0, 0, 0, 0)
        ap_layout.setSpacing(2)
        
        # [FIX] Распорка сверху для центрирования плеера
        ap_layout.addStretch()

        # Название файла
        self._ap_file_label = QLabel(get_translation(self.current_language, 'fm_audio_no_file'))
        self._ap_file_label.setAlignment(Qt.AlignCenter)
        self._ap_file_label.setWordWrap(True)
        self._ap_file_label.setStyleSheet("color: #ff9900; font-weight: bold; font-size: 14px; background: transparent;")
        ap_layout.addWidget(self._ap_file_label)

        # Рамка управления
        self._ap_controls_frame = QFrame()
        self._ap_controls_frame.setObjectName("apControlsFrame")
        self._ap_controls_frame.setFixedSize(490, 125)
        self._ap_controls_frame.setStyleSheet("""
            QFrame#apControlsFrame {
                border: 1px solid #555555;
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
        self._ap_time_label = QLabel("00:00 / 00:00")
        self._ap_time_label.setAlignment(Qt.AlignCenter)
        self._ap_time_label.setStyleSheet("color: #aaaaaa; font-size: 12px; background: transparent;")
        controls_vbox.addWidget(self._ap_time_label)

        # Слайдер позиции
        self._ap_position_slider = QSlider(Qt.Horizontal)
        self._ap_position_slider.setStyleSheet("""
            QSlider { background: transparent; border: none; }
            QSlider:focus { border: none; outline: none; }
            QSlider::groove:horizontal { border: 1px solid #444; background: #222; height: 8px; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #ff9900; border: 1px solid #444; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #fff; border: 1px solid #5c5c5c; width: 14px; margin-top: -3px; margin-bottom: -3px; border-radius: 7px; }
        """)
        self._ap_position_slider.setRange(0, 0)
        self._ap_position_slider.sliderPressed.connect(self._on_preview_slider_pressed)
        self._ap_position_slider.sliderReleased.connect(self._on_preview_slider_released)
        controls_vbox.addWidget(self._ap_position_slider)

        # Кнопки
        controls_row = QHBoxLayout()
        controls_row.setAlignment(Qt.AlignCenter)
        controls_row.setSpacing(15)

        self._ap_btn_style = """
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
        """

        self._ap_play_btn = QPushButton("▶")
        self._ap_play_btn.setFocusPolicy(Qt.NoFocus)
        self._ap_play_btn.setStyleSheet(self._ap_btn_style.format(size=28, top=-4))
        self._ap_play_btn.setFixedSize(40, 40)
        self._ap_play_btn.setCursor(Qt.PointingHandCursor)
        self._ap_play_btn.clicked.connect(self._toggle_preview_play_pause)
        controls_row.addWidget(self._ap_play_btn)

        self._ap_stop_btn = QPushButton("■")
        self._ap_stop_btn.setFocusPolicy(Qt.NoFocus)
        self._ap_stop_btn.setStyleSheet(self._ap_btn_style.format(size=24, top=0))
        self._ap_stop_btn.setFixedSize(40, 40)
        self._ap_stop_btn.setCursor(Qt.PointingHandCursor)
        self._ap_stop_btn.clicked.connect(lambda: self._stop_preview_audio()) # Use lambda to ensure reset_ui=True
        controls_row.addWidget(self._ap_stop_btn)

        controls_row.addStretch()

        vol_label = QLabel("🔊")
        vol_label.setStyleSheet("color: #aaa; background: transparent; font-size: 18px;")
        controls_row.addWidget(vol_label)

        self._ap_volume_slider = QSlider(Qt.Horizontal)
        self._ap_volume_slider.setFixedWidth(100)
        self._ap_volume_slider.setRange(0, 100)
        main_win = self._get_main_window()
        initial_vol = main_win.audio_volume if main_win and hasattr(main_win, 'audio_volume') else 50
        self._ap_volume_slider.setValue(initial_vol)
        self._ap_volume_slider.setStyleSheet("""
            QSlider { background: transparent; border: none; }
            QSlider:focus { border: none; outline: none; }
            QSlider::groove:horizontal { border: 1px solid #444; background: #222; height: 8px; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #ff9900; border: 1px solid #444; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #fff; border: 1px solid #5c5c5c; width: 14px; margin-top: -3px; margin-bottom: -3px; border-radius: 7px; }
        """)
        self._ap_volume_slider.valueChanged.connect(self._set_preview_volume)
        controls_row.addWidget(self._ap_volume_slider)

        controls_vbox.addLayout(controls_row)
        frame_hbox.addLayout(controls_vbox)
        frame_hbox.addSpacing(130)

        # Картинка radiocat.png (как в основном плеере)
        self._ap_img_label = QLabel(self._ap_controls_frame)
        self._ap_img_label.setFixedSize(121, 110)
        img_path = os.path.join(os.path.dirname(__file__), "radiocat.png")
        if os.path.exists(img_path):
            pix = QPixmap(img_path)
            self._ap_img_label.setPixmap(pix.scaled(121, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self._ap_img_label.setStyleSheet("border: 1px dashed #777; color: #777; font-size: 10px;")
            self._ap_img_label.setText("radiocat.png")
            self._ap_img_label.setAlignment(Qt.AlignCenter)
        self._ap_img_label.move(354 + 14, 7 + 7)  # Смещение как в AudioPlayerDialog
        self._ap_img_label.show()

        # Центрирование рамки
        frame_centered = QHBoxLayout()
        frame_centered.setContentsMargins(0, 0, 0, 0)
        frame_centered.addStretch()
        frame_centered.addWidget(self._ap_controls_frame)
        frame_centered.addStretch()
        ap_layout.addLayout(frame_centered)

        # Кнопка замены
        self._ap_replace_btn = QPushButton(get_translation(self.current_language, 'replace_audio_btn'))
        self._ap_replace_btn.setCursor(Qt.PointingHandCursor)
        self._ap_replace_btn.setFocusPolicy(Qt.NoFocus)
        self._ap_replace_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9900; color: #000000; border: none;
                padding: 8px 20px; border-radius: 15px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #e68a00; }
        """)
        self._ap_replace_btn.clicked.connect(self._on_preview_replace_audio)
        replace_layout = QHBoxLayout()
        replace_layout.setContentsMargins(0, 10, 0, 15)
        replace_layout.addStretch()
        replace_layout.addWidget(self._ap_replace_btn)
        replace_layout.addStretch()
        ap_layout.addLayout(replace_layout)
        
        # [FIX] Распорка снизу для центрирования плеера
        ap_layout.addStretch()

        # ═══ Ползунок переключения Таблица / Содержимое ═══
        slider_row = QHBoxLayout()
        slider_row.setContentsMargins(4, 0, 4, 0)
        slider_row.setSpacing(6)

        # Иконка "Таблица" (слева)
        self.table_icon = ClickableLabel(ICON_VIEW_TABLE)
        self.table_icon.setStyleSheet(f"""
            ClickableLabel {{
                color: #aaaaaa; 
                font-size: {ICON_VIEW_TABLE_SIZE}px; 
                background: transparent; 
                border: none;
            }}
            ClickableLabel:hover {{
                color: #ff9900;
            }}
        """)
        self.table_icon.setFixedWidth(24)
        self.table_icon.setAlignment(Qt.AlignCenter)
        self.table_icon.setCursor(Qt.PointingHandCursor)
        self.table_icon.clicked.connect(lambda: self.view_slider.setValue(0))
        slider_row.addWidget(self.table_icon)

        # Слайдер
        self.view_slider = JumpSlider(Qt.Horizontal)
        self.view_slider.setRange(0, 15)  # 0 = таблица, 1..15 = 32..256 px
        self.view_slider.setValue(0)
        self.view_slider.setFixedHeight(20)
        self.view_slider.setStyleSheet("""
            QSlider { background: transparent; border: none; }
            QSlider:focus { border: none; outline: none; }
            QSlider::groove:horizontal { border: 1px solid #444; background: #222; height: 8px; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #ff9900; border: 1px solid #444; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #fff; border: 1px solid #5c5c5c; width: 14px; margin-top: -3px; margin-bottom: -3px; border-radius: 7px; }
        """)
        self.view_slider.valueChanged.connect(self._on_view_slider_changed)
        slider_row.addWidget(self.view_slider)

        # Иконка "Содержимое" (справа)
        self.content_icon = ClickableLabel(ICON_VIEW_CONTENT)
        self.content_icon.setStyleSheet(f"""
            ClickableLabel {{
                color: #aaaaaa; 
                font-size: {ICON_VIEW_CONTENT_SIZE}px; 
                background: transparent; 
                border: none;
            }}
            ClickableLabel:hover {{
                color: #ff9900;
            }}
        """)
        self.content_icon.setFixedWidth(32)
        self.content_icon.setAlignment(Qt.AlignCenter)
        self.content_icon.setCursor(Qt.PointingHandCursor)
        self.content_icon.clicked.connect(lambda: self.view_slider.setValue(15))
        slider_row.addWidget(self.content_icon)

        preview_layout.addLayout(slider_row)

        # Информационная надпись по Shift+Click (внизу слева)
        self.shift_hint_label = QLabel(get_translation(self.current_language, 'fm_shift_selection_hint'))
        self.shift_hint_label.setStyleSheet("color: #999999; font-size: 12px; background: transparent; border: none;")
        self.shift_hint_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        preview_layout.addWidget(self.shift_hint_label)

        self.splitter.addWidget(self.preview_container)
        self.splitter.setSizes([800, 532])

        layout.addWidget(self.splitter, 1)

        # Drag & Drop на таблицю
        self.table.setAcceptDrops(True)
        self.table.setDragDropMode(QAbstractItemView.DropOnly)
        self.table.viewport().setAcceptDrops(True)


    def _restore_table_focus_by_key(self, res_key):
        """Вспомогательный метод для возврата фокуса на нужную строку по ключу ресурса"""
        if not hasattr(self, 'table'): return
        for r in range(self.table.rowCount()):
            it = self.table.item(r, self.COL_FILENAME)
            if it and it.data(Qt.UserRole) == res_key:
                self.table.selectRow(r)
                self.table.setFocus()
                break

    @staticmethod
    def _create_toggle_container(toggle, text):
        """Создаёт контейнер с ToggleSwitch + Label (как в основном окне)."""
        container = QWidget()
        container.setStyleSheet('background-color: transparent; border: none;')
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(toggle)
        label = QLabel(text)
        label.setStyleSheet('''
            color: #ffffff;
            background-color: transparent;
            border: none;
            padding: 0;
        ''')
        layout.addWidget(label)
        return container, label

    def _update_table_headers(self):
        """Обновляет заголовки таблицы из локализации."""
        lang = self.current_language
        headers = [
            "", # Колонка чекбоксов
            get_translation(lang, 'fm_col_type'),
            get_translation(lang, 'fm_col_filename'),
            get_translation(lang, 'fm_col_description'),
            get_translation(lang, 'fm_col_status'),
            get_translation(lang, 'fm_col_actions'),
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Подключаем клик по заголовку для "Выбрать все"
        header = self.table.horizontalHeader()
        if isinstance(header, CheckboxHeader):
            try:
                header.checkboxToggled.disconnect()
            except Exception: pass
            header.checkboxToggled.connect(self._on_header_checkbox_toggled)
            
        # Остальные колонки - обычная сортировка
        header.sectionClicked.connect(self._on_header_clicked)

    def _on_header_checkbox_toggled(self, new_state):
        """Прямая обработка переключения чекбокса в заголовке."""
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            it = self.table.item(r, self.COL_CHECK)
            if it:
                it.setCheckState(new_state)
                # Обновляем вес для сортировки
                if isinstance(it, SortableTableWidgetItem):
                    it.sort_value = 1 if new_state == Qt.Checked else 0
                
                # Синхронизируем checked_keys
                key = it.data(Qt.UserRole)
                if key:
                    if new_state == Qt.Checked:
                        self.checked_keys.add(key)
                    else:
                        self.checked_keys.discard(key)
        self.table.blockSignals(False)
        self._update_header_checkbox()
        self._update_batch_buttons_state()

    def _on_header_clicked(self, index):
        """Обработка клика по заголовку (для сортировки в любой колонке)."""
        # Теперь здесь только логика, реагирующая на системный клик для сортировки
        # (выделение перенесено в _on_header_checkbox_toggled)
        pass

    def eventFilter(self, obj, event):
        """Перехват событий для реализации Shift+Click и Drag & Drop."""
        if obj == self.table.viewport():
            # 1. Обработка кликов (Shift+Click)
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    pos = event.pos()
                    row = self.table.rowAt(pos.y())
                    col = self.table.columnAt(pos.x())
                    
                    if col == self.COL_CHECK and row >= 0:
                        item = self.table.item(row, col)
                        if item:
                            # Если зажат Shift и есть предыдущий клик
                            if (event.modifiers() & Qt.ShiftModifier) and self._last_checked_row is not None:
                                start = min(self._last_checked_row, row)
                                end = max(self._last_checked_row, row)
                                
                                # Целевое состояние - противоположное текущему состоянию кликнутого элемента
                                target_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
                                
                                self.table.blockSignals(True)
                                for r in range(start, end + 1):
                                    it = self.table.item(r, self.COL_CHECK)
                                    if it:
                                        it.setCheckState(target_state)
                                        key = it.data(Qt.UserRole)
                                        if key:
                                            if target_state == Qt.Checked:
                                                self.checked_keys.add(key)
                                                it.sort_value = 1
                                            else:
                                                self.checked_keys.discard(key)
                                                it.sort_value = 0
                                self.table.blockSignals(False)
                                
                                self._last_checked_row = row
                                self._update_header_checkbox()
                                self._update_batch_buttons_state()
                                event.accept()
                                return True # Поглощаем событие, чтобы Qt не переключил чекбокс еще раз
                            else:
                                # Обычный клик - просто запоминаем строку
                                self._last_checked_row = row
                                # Даем Qt обработать клик штатно (через _on_item_changed)
                                
                    # Логика для Drag-Out (захват за иконку в COL_TYPE)
                    if col == self.COL_TYPE and row >= 0:
                        self._drag_start_pos = event.pos()
                        self._drag_start_row = row

            elif event.type() == QEvent.MouseMove:
                pos = event.pos()
                row = self.table.rowAt(pos.y())
                col = self.table.columnAt(pos.x())
                
                # 1. Меняем курсор на ладонь при наведении на иконку типа
                if col == self.COL_TYPE and row >= 0:
                    self.table.viewport().setCursor(Qt.OpenHandCursor)
                else:
                    self.table.viewport().setCursor(Qt.ArrowCursor)

                # 2. Проверяем начало перетаскивания
                if (event.buttons() & Qt.LeftButton) and self._drag_start_pos:
                    if (event.pos() - self._drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                        self._execute_drag(self._drag_start_row)
                        self._drag_start_pos = None

            elif event.type() == QEvent.MouseButtonRelease:
                self._drag_start_pos = None

            # 2. Обработка Drag & Drop
            elif event.type() == QEvent.DragEnter:
                # [FIX] Блокируем перетаскивание внутри программы (если источник - мы сами)
                if event.source() == self:
                    event.ignore()
                    return True
                if event.mimeData().hasUrls():
                    event.accept()
                    return True
            elif event.type() == QEvent.DragMove:
                if event.source() == self:
                    event.ignore()
                    return True
                if event.mimeData().hasUrls():
                    event.accept()
                    return True
            elif event.type() == QEvent.Drop:
                if event.source() == self:
                    event.ignore()
                    return True
                if event.mimeData().hasUrls():
                    urls = event.mimeData().urls()
                    if urls:
                        file_path = urls[0].toLocalFile()
                        if file_path and os.path.isfile(file_path):
                            # Определяем строку из координат
                            pos = event.pos()
                            row = self.table.rowAt(pos.y())
                            
                            if row >= 0:
                                # Получаем ключ ресурса и оригинальное имя файла
                                item = self.table.item(row, self.COL_FILENAME)
                                if item:
                                    res_key = item.data(Qt.UserRole)
                                    orig_filename = item.text()
                                    
                                    _, orig_ext = os.path.splitext(orig_filename)
                                    _, new_ext = os.path.splitext(file_path)
                                    
                                    # Проверяем расширения (типы файлов)
                                    def get_category_by_ext(ext):
                                        ext = ext.lower()
                                        if ext in ['.png', '.jpg', '.jpeg']: return 'image'
                                        if ext in ['.wav', '.ogg']: return 'audio'
                                        return 'other'
                                        
                                    orig_cat = get_category_by_ext(orig_ext)
                                    new_cat = get_category_by_ext(new_ext)
                                    
                                    # Если категории разные (например аудио меняют на картинку) - предупреждаем
                                    if orig_cat != new_cat:
                                        from dialogs import TypeMismatchDialog
                                        dialog = TypeMismatchDialog(self.current_language, orig_ext, new_ext, parent=self)
                                        if not dialog.exec_():
                                            return True # Пользователь отменил замену
                                            
                                    # Если все ок или пользователь подтвердил - заменяем
                                    new_filename = self.miz_resource_manager.replace_audio(res_key, file_path)
                                    if new_filename:
                                        # Если это KNEEBOARD, ключ мог измениться вместе с именем файла
                                        selected_res_key = res_key
                                        if res_key.startswith("KneeboardKey_"):
                                            selected_res_key = f"KneeboardKey_{new_filename}"

                                        # Очищаем кэш миниатюр
                                        for rk in [res_key, selected_res_key]:
                                            if rk in self._thumbnail_cache:
                                                del self._thumbnail_cache[rk]
                                            
                                        self._all_files = self.miz_resource_manager.get_all_resource_files()
                                        self.resourcesChanged.emit()
                                        self._apply_filters()
                                        
                                        # Оставляем выделение на текущей строке (используем потенциально новый ключ)
                                        self._restore_table_focus_by_key(selected_res_key)
                                    
                            event.accept()
                            return True
        
        return super().eventFilter(obj, event)

    def _on_item_changed(self, item):
        """Инвалидация состояния заголовка при ручном клике по чекбоксу в ячейке
        или обработка переименования файла.
        """
        if item.column() == self.COL_CHECK:
            key = item.data(Qt.UserRole)
            if key:
                if item.checkState() == Qt.Checked:
                    self.checked_keys.add(key)
                    item.sort_value = 1
                else:
                    self.checked_keys.discard(key)
                    item.sort_value = 0
            self._update_header_checkbox()
        elif item.column() == self.COL_FILENAME:
            res_key = item.data(Qt.UserRole)
            old_name = item.data(Qt.UserRole + 2)
            new_name = item.text().strip()
            
            if res_key and new_name and new_name != old_name:
                # [BUG-3 FIX] Валидация имени файла
                invalid_chars = set('<>:"/\\|?*')
                if any(c in new_name for c in invalid_chars):
                    item.setText(old_name)  # Откат: недопустимые символы
                    self._update_batch_buttons_state()
                    return
                # Сохраняем оригинальное расширение, если пользователь его убрал
                _, old_ext = os.path.splitext(old_name)
                _, new_ext = os.path.splitext(new_name)
                if not new_ext:
                    new_name = new_name + old_ext
                
                new_res_key = self.miz_resource_manager.rename_resource(res_key, new_name, self.miz_path)
                if new_res_key:
                    # [FIX] Блокируем сигналы, чтобы перестроение таблицы не вызвало рекурсию
                    self.table.blockSignals(True)
                    # Обновляем внутренние данные
                    self._all_files = self.miz_resource_manager.get_all_resource_files()
                    self.resourcesChanged.emit()
                    # Перерисовываем таблицу (чтобы статус стал красным)
                    self._apply_filters()
                    # Восстанавливаем фокус на эту строку (используем новый ключ!)
                    self._restore_table_focus_by_key(new_res_key)
                    self.table.blockSignals(False)
                else:
                    # Если ошибка - возвращаем старое имя
                    item.setText(old_name)

        self._update_batch_buttons_state()

    def _on_context_menu(self, pos):
        """Отображает контекстное меню для таблицы."""
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
            
        if index.column() == self.COL_FILENAME:
            menu = QMenu(self)
            # Применяем оранжевое выделение (как в главном окне)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #ff9900;
                    border-radius: 4px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 5px 25px 5px 20px;
                    border-radius: 3px;
                }
                QMenu::item:selected {
                    background-color: #ff9900;
                    color: #1a1a1a;
                }
                QMenu::separator {
                    height: 1px;
                    background: #444;
                    margin: 5px 0;
                }
            """)
            
            rename_action = menu.addAction(get_translation(self.current_language, 'fm_menu_rename'))
            
            # Добавляем действия только для аудио
            tts_action = None
            show_in_editor_action = None
            row = index.row()
            fname_item = self.table.item(row, self.COL_FILENAME)
            if fname_item and fname_item.data(Qt.UserRole + 1) == 'audio':
                res_key = fname_item.data(Qt.UserRole)
                # Ищем связанный DictKey (есть ли этот аудио в превью)
                linked_dict_key = None
                for dk, rk in self.miz_resource_manager.subtitle_to_reskey.items():
                    if rk == res_key:
                        linked_dict_key = dk
                        break
                
                if linked_dict_key:
                    show_in_editor_action = menu.addAction(
                        get_translation(self.current_language, 'fm_menu_show_in_editor'))
                
                menu.addSeparator()
                tts_text = "🎙 Озвучить (Премиум TTS)"
                if not self.tts.use_piper:
                    tts_text = "🎙 Удалить/Скачать Премиум TTS"
                
                tts_action = menu.addAction(tts_text)

            action = menu.exec_(self.table.viewport().mapToGlobal(pos))
            if action == rename_action:
                self.table.editItem(self.table.item(index.row(), index.column()))
            elif show_in_editor_action and action == show_in_editor_action:
                main_window = self._get_main_window()
                if main_window:
                    self._stop_preview_audio()
                    # Восстанавливаем главное окно
                    main_window.show()
                    # Закрываем менеджер
                    self.window().close()
                    # Получаем имя аудиофайла для передачи в поиск
                    audio_info = self.miz_resource_manager.get_audio_for_res_key(res_key)
                    audio_filename = audio_info[0] if audio_info else fname_item.text()
                    # Отложенно выделяем элемент
                    QTimer.singleShot(200, lambda f=audio_filename: main_window.show_audio_in_editor(f))
            elif tts_action and action == tts_action:
                self._on_tts_clicked(index.row())

    def _on_tts_clicked(self, row):
        """Обработка клика по пункту 'Озвучить'."""
        if not self.tts.use_piper:
            dialog = StandardQuestionDialog(
                "Piper TTS",
                "Качественная озвучка (Piper) не обнаружена.\n"
                "Хотите скачать компоненты сейчас (~85 МБ)?\n"
                "Это обеспечит чистое нейросетевое звучание офлайн.",
                self.current_language,
                self
            )
            if dialog.exec_():
                self._start_tts_download()
            return

        fname_item = self.table.item(row, self.COL_FILENAME)
        if not fname_item: return
        res_key = fname_item.data(Qt.UserRole)  # ResKey_advancedFile_* (ключ ресурса)
        
        main_window = self._get_main_window()
        if not main_window: return
        
        # Поиск текста для этого файла
        text_to_speak = ""
        dict_key = None
        miz = self.miz_resource_manager
        
        # res_key из таблицы — это уже ResKey (например ResKey_advancedFile_12).
        # subtitle_to_reskey хранит {DictKey → ResKey}, ищем DictKey по нашему ResKey.
        for d_key, r_key in miz.subtitle_to_reskey.items():
            if r_key == res_key:
                dict_key = d_key
                break
        
        # Берём ВСЕ строки перевода из основного окна для этого ключа
        text_lines = []
        if dict_key:
            for line in getattr(main_window, 'original_lines', []):
                if line.get('key') == dict_key:
                    t = line.get('translated_text') or line.get('text', '')
                    if t:
                        text_lines.append(t)
        
        text_to_speak = "\n".join(text_lines)
        if not text_to_speak.strip():
            msg = StandardInfoDialog("TTS", "Для этого файла не найден текст перевода в миссии.", self.current_language, self)
            msg.exec_()
            return

        # Открываем диалог предпрослушивания и настроек
        dialog = TTSPreviewDialog(text_to_speak, self.tts, self)
        if dialog.exec_() == QDialog.Accepted:
            generated_path = dialog.get_generated_path()
            if generated_path and os.path.exists(generated_path):
                # Заменяем аудио в менеджере ресурсов
                self.miz_resource_manager.replace_audio(res_key, generated_path)
                self.resourcesChanged.emit()
                self._populate_table()
                
                # Восстанавливаем фокус по res_key
                self._restore_table_focus_by_key(res_key)
                
                # Показываем превью нового файла
                filename = self.miz_resource_manager.map_resource_current.get(res_key)
                if filename:
                    self._show_audio_preview(res_key, filename, auto_play=True)
                
                # Пытаемся удалить временный файл после копирования (shutil.copy2 внутри replace_audio)
                try:
                    os.remove(generated_path)
                except Exception:
                    pass

    def _start_tts_download(self):
        """Скачивание Piper в отдельном потоке (упрощенно)."""
        progress = MizProgressDialog(
            self, 
            get_translation(self.current_language, 'fm_title'), 
            "Загрузка Piper TTS и голосов (~85 МБ)..."
        )
        progress.show()
        QApplication.processEvents()
        
        def progress_hook(percent, _block_size, _total_size):
            """percent передаётся напрямую из tts_engine (0-100)."""
            progress.set_value(min(percent, 99))
            QApplication.processEvents()

        success = self.tts.download_piper_components(progress_callback=progress_hook)
        
        progress.set_value(100)
        QApplication.processEvents()
        progress.close()
        
        if success:
            msg = StandardInfoDialog("TTS", "Piper успешно установлен! Теперь вы можете генерировать озвучку.", self.current_language, self)
            msg.exec_()
        else:
            msg = StandardInfoDialog("TTS", "Ошибка при загрузке компонентов.\nПроверьте подключение к интернету и попробуйте снова.", self.current_language, self, is_error=True)
            msg.exec_()
        
    def _update_batch_buttons_state(self):
        """Обновляет доступность кнопок массовых действий."""
        has_selection = len(self.checked_keys) > 0
        self.btn_batch_export.setEnabled(has_selection)
        self.btn_batch_replace.setEnabled(has_selection)

    def _update_header_checkbox(self):
        """Пересчитывает и устанавливает состояние чекбокса в заголовке."""
        header = self.table.horizontalHeader()
        if not isinstance(header, CheckboxHeader):
            return
            
        checked_count = 0
        total_count = self.table.rowCount()
        
        for r in range(total_count):
            it = self.table.item(r, self.COL_CHECK)
            if it and it.checkState() == Qt.Checked:
                checked_count += 1
                
        if checked_count == 0:
            header.set_check_state(Qt.Unchecked)
        elif checked_count == total_count:
            header.set_check_state(Qt.Checked)
        else:
            header.set_check_state(Qt.PartiallyChecked)

    def _on_view_slider_changed(self, value):
        """Обработчик ползунка Таблица/Содержимое."""
        # Сохраняем настройку сразу при изменении
        settings = QSettings("MissionTranslator", "DCSTranslatorTool")
        settings.setValue("fm_view_slider_value", value)

        if value == 0:
            thumb_size = 0
        else:
            # Сетка: 32, 48, 64, ..., 256 (шаг 16px)
            thumb_size = 16 + value * 16

        v_header = self.table.verticalHeader()

        self.table.setUpdatesEnabled(False)

        if thumb_size == 0:
            # Режим «Таблица» — возвращаем эмодзи
            self.table.setIconSize(QSize(16, 16))
            v_header.setDefaultSectionSize(self._default_row_height)
            self.table.setColumnWidth(self.COL_TYPE, self._default_type_col_width)

            for r in range(self.table.rowCount()):
                type_item = self.table.item(r, self.COL_TYPE)
                if type_item is None:
                    continue
                fname_item = self.table.item(r, self.COL_FILENAME)
                file_type = fname_item.data(Qt.UserRole + 1) if fname_item else ''
                if file_type == 'image':
                    type_item.setIcon(QIcon())
                    type_item.setText("🖼️")
                # Сбрасываем высоту строки к дефолту
                self.table.setRowHeight(r, self._default_row_height)
        else:
            # Режим «Содержимое» — заменяем эмодзи картинки на миниатюры
            self.table.setIconSize(QSize(thumb_size, thumb_size))
            row_h = thumb_size + 6
            v_header.setDefaultSectionSize(row_h)
            col_w = max(self._default_type_col_width, thumb_size + 20)
            self.table.setColumnWidth(self.COL_TYPE, col_w)

            for r in range(self.table.rowCount()):
                type_item = self.table.item(r, self.COL_TYPE)
                if type_item is None:
                    continue
                fname_item = self.table.item(r, self.COL_FILENAME)
                file_type = fname_item.data(Qt.UserRole + 1) if fname_item else ''

                if file_type == 'image':
                    res_key = fname_item.data(Qt.UserRole)
                    filename = fname_item.data(Qt.UserRole + 2)
                    if res_key in self._thumbnail_cache:
                        type_item.setIcon(self._thumbnail_cache[res_key])
                    else:
                        type_item.setIcon(QIcon())
                        self._thumbnail_queue.append((type_item, res_key, filename))
                    type_item.setText("")
                    self.table.setRowHeight(r, row_h)
                else:
                    # Аудио — оставляем высоту дефолтную
                    self.table.setRowHeight(r, self._default_row_height)

        self.table.setUpdatesEnabled(True)
        self.table.viewport().update()

        # Запускаем асинхронную загрузку оставшихся превьюшек
        if getattr(self, '_thumbnail_queue', []):
            self._process_thumbnail_queue()

    def _process_thumbnail_queue(self):
        """Обрабатывает по одной миниатюре изочереди без зависания UI."""
        try:
            if not self or not hasattr(self, '_thumbnail_queue') or not self._thumbnail_queue:
                return
                
            # Берем первый элемент из очереди
            item_type, res_key, filename = self._thumbnail_queue.pop(0)
            
            # Обновляем только если элемент еще существует (пользователь не закрыл окно/не сменил миссию)
            try:
                # Генерируем с помощью существующей логики
                icon = self._get_thumbnail(res_key, filename)
                
                # Присваиваем иконку
                if icon and not icon.isNull():
                    item_type.setIcon(icon)
            except RuntimeError:
                pass # Элемент таблицы был удален
                
            # Запускаем таймер для следующей итерации (10мс для плавности UI)
            if self._thumbnail_queue:
                if not hasattr(self, '_thumbnail_timer'):
                    self._thumbnail_timer = QTimer(self)
                    self._thumbnail_timer.setSingleShot(True)
                    self._thumbnail_timer.timeout.connect(self._process_thumbnail_queue)
                self._thumbnail_timer.start(10)
        except RuntimeError:
            return # Сам виджет FileManagerWidget был удален

    def _get_thumbnail(self, res_key, filename):
        """Генерирует и кэширует миниатюру для файла изображения."""
        if res_key in self._thumbnail_cache:
            return self._thumbnail_cache[res_key]

        temp_path = self._extract_resource_to_temp(res_key, filename)
        if not temp_path:
            return QIcon()

        pixmap = QPixmap(temp_path)
        if pixmap.isNull():
            return QIcon()

        # Генерируем миниатюру максимального размера (256x256), Qt будет уменьшать через setIconSize
        thumb = pixmap.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon = QIcon(thumb)
        self._thumbnail_cache[res_key] = icon
        return icon


    def set_data(self, miz_resource_manager, miz_path):
        """Устанавливает данные и заполняет таблицу.
        
        Args:
            miz_resource_manager: экземпляр MizResourceManager
            miz_path: путь к .miz файлу
        """
        # [FIX] Очищаем выделенные файлы при смене миссии
        self.checked_keys.clear()
        # Останавливаем аудио и сбрасываем превью
        self._stop_preview_audio()
        self._preview_audio_key = None
        self._preview_audio_path = None
        self._action_playing_key = None
        self._action_playing_btn = None
        self._action_paused = False
        
        # [FIX] Очищаем кэш миниатюр ВСЕГДА при установке данных.
        # Это предотвращает сохранение старых превью при восстановлении бекапа по тому же пути.
        self._thumbnail_cache.clear()
            
        # Очередь для асинхронной генерации
        self._thumbnail_queue = []
        if hasattr(self, '_thumbnail_timer'):
            self._thumbnail_timer.stop()
        
        self.miz_resource_manager = miz_resource_manager
        self.miz_path = miz_path
        
        # Обновляем инфо в заголовке
        if hasattr(self, 'label_mission_name'):
             filename = os.path.basename(miz_path) if miz_path else "-"
             self.label_mission_name.setText(filename)
        if hasattr(self, 'label_locale_name'):
             # Текущая локаль из менеджера ресурсов
             locale = miz_resource_manager.current_folder if miz_resource_manager else "-"
             self.label_locale_name.setText(locale)

        self._all_files = miz_resource_manager.get_all_resource_files()
        self._populate_table()
        
        # Синхронизируем громкость с главным окном при загрузке данных
        main_win = self._get_main_window()
        if main_win and hasattr(main_win, 'audio_volume'):
            self._ap_volume_slider.blockSignals(True)
            self._ap_volume_slider.setValue(main_win.audio_volume)
            self._ap_volume_slider.blockSignals(False)

        # При первом открытии окна в текущей сессии сортируем по описанию
        if self._first_load:
            self.table.sortByColumn(self.COL_DESCRIPTION, Qt.AscendingOrder)
            self._first_load = False

    def _populate_table(self):
        """Заполняет таблицу данными с учётом фильтров."""
        filtered = self._get_filtered_files()
        self._last_checked_row = None  # Сбрасываем при обновлении списка

        # [FIX] Приостанавливаем обновление UI на время заполнения, чтобы кнопки не прыгали
        self.table.blockSignals(True)
        self.table.setUpdatesEnabled(False)
        self.table.viewport().setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        
        # [FIX] Очищаем за собой, чтобы старые виджеты точно удалились
        self.table.setRowCount(0)
        self.table.setRowCount(len(filtered))

        slider_val = self.view_slider.value()
        thumb_size = 0 if slider_val == 0 else (16 + slider_val * 16)
        row_h = self._default_row_height if thumb_size == 0 else (thumb_size + 6)
        
        if thumb_size > 0:
            self.table.setIconSize(QSize(thumb_size, thumb_size))
            col_w = max(self._default_type_col_width, thumb_size + 20)
            self.table.setColumnWidth(self.COL_TYPE, col_w)
            self.table.verticalHeader().setDefaultSectionSize(row_h)
        else:
            self.table.setIconSize(QSize(16, 16))
            self.table.setColumnWidth(self.COL_TYPE, self._default_type_col_width)
            self.table.verticalHeader().setDefaultSectionSize(self._default_row_height)

        for row, item in enumerate(filtered):
            # Чекбокс для выбора
            res_key = item['res_key']
            is_checked = res_key in self.checked_keys
            
            # Используем SortableTableWidgetItem для возможности сортировки по галочкам
            check_item = SortableTableWidgetItem("", 1 if is_checked else 0)
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            
            # Восстанавливаем состояние из checked_keys
            check_item.setData(Qt.UserRole, res_key)
            if is_checked:
                check_item.setCheckState(Qt.Checked)
            else:
                check_item.setCheckState(Qt.Unchecked)
                
            check_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, self.COL_CHECK, check_item)

            # Тип (иконка или миниатюра)
            type_sort_value = 0 if item['type'] == 'image' else 1
            
            if item['type'] == 'image' and thumb_size > 0:
                type_item = SortableTableWidgetItem("", type_sort_value)
                if item['res_key'] in self._thumbnail_cache:
                    type_item.setIcon(self._thumbnail_cache[item['res_key']])
                else:
                    type_item.setIcon(QIcon())
                    self._thumbnail_queue.append((type_item, item['res_key'], item['filename']))
            else:
                type_icon = "🖼️" if item['type'] == 'image' else "♫"
                type_item = SortableTableWidgetItem(type_icon, type_sort_value)
                
            type_item.setTextAlignment(Qt.AlignCenter)
            if item['type'] == 'audio':
                font = type_item.font()
                font.setPointSize(14)
                type_item.setFont(font)
                type_item.setForeground(QColor('#999966'))
                type_item.setData(Qt.UserRole + 3, '#999966')
            
            self.table.setItem(row, self.COL_TYPE, type_item)
            self.table.setRowHeight(row, row_h if item['type'] == 'image' else self._default_row_height)

            # Имя файла
            fname_item = QTableWidgetItem(item['filename'])
            fname_item.setFlags(fname_item.flags() | Qt.ItemIsEditable)
            fname_item.setData(Qt.UserRole, item['res_key'])  # Сохраняем res_key
            fname_item.setData(Qt.UserRole + 1, item['type'])  # Сохраняем тип
            fname_item.setData(Qt.UserRole + 2, item['filename'])  # Сохраняем filename
            fname_item.setData(Qt.UserRole + 3, '#ffffff')
            fname_item.setForeground(QColor('#ffffff'))
            self.table.setItem(row, self.COL_FILENAME, fname_item)

            # Описание
            loc_key = CONTEXT_TO_LOC_KEY.get(item['context'], 'fm_desc_trigger')
            desc_text = get_translation(self.current_language, loc_key)
            
            # Добавляем номер по порядку для картинок брифинга
            if item.get('index') is not None:
                desc_text = f"{desc_text} [{item['index']}]"
                
            desc_item = NaturalSortTableWidgetItem(desc_text)
            # Цвет описания по контексту
            if item['context'] == 'briefing_blue':
                color = '#3366ff'
            elif item['context'] == 'briefing_red':
                color = '#ff3333'
            elif item['context'] == 'briefing_neutral':
                color = '#bdbdbd'
            else:
                color = '#888888'
            desc_item.setForeground(QColor(color))
            desc_item.setData(Qt.UserRole + 3, color)
            self.table.setItem(row, self.COL_DESCRIPTION, desc_item)

        # Статус (цветная точка)
            # зеленый - в локали текущей, серый - только в DEFAULT, красный - заменен (не сохранено)
            is_replaced = False
            if self.miz_path and self.miz_resource_manager:
                is_replaced = self.miz_resource_manager.is_resource_replaced(item['res_key'])

            status_text = "●"
            
            # Определяем вес для сортировки
            if is_replaced:
                sort_weight = 2
                color = '#ff3333'
                tooltip_key = 'fm_status_replaced'
            elif item['in_current_locale']:
                sort_weight = 0
                color = '#33cc33'
                tooltip_key = 'fm_status_in_locale'
            else:
                sort_weight = 1
                color = '#999999'
                tooltip_key = 'fm_status_default_only'

            # Используем кастомный класс для правильной сортировки без отображения цифр
            status_item = SortableTableWidgetItem(status_text, sort_weight)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setData(Qt.UserRole + 3, color)
            status_item.setForeground(QColor(color))
            status_item.setData(Qt.ToolTipRole, get_translation(self.current_language, tooltip_key))
            
            font = status_item.font()
            font.setPointSize(14)
            status_item.setFont(font)
            
            self.table.setItem(row, self.COL_STATUS, status_item)

            # Действия
            # [FIX] Сразу привязываем к таблице (родителю), чтобы не появлялось в (0,0)
            actions_widget = QWidget(self.table)
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 9, 2)
            actions_layout.setSpacing(8)
            actions_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            btn_style = """
                QPushButton {
                background: transparent;
                color: #ffffff;
                border: none;
                font-size: 20px;
            }
            QPushButton:hover {
                color: #ff9900;
            }
            """
            
            action_buttons = []  # Собираем все кнопки для установки фильтра тултипов
            
            if item['type'] == 'audio':
                btn_play = QPushButton("▶")
                btn_play.setCursor(Qt.PointingHandCursor)
                btn_play.setFocusPolicy(Qt.NoFocus)
                btn_play.setToolTip(get_translation(self.current_language, 'fm_tooltip_play'))
                btn_play.setStyleSheet(btn_style)
                
                btn_stop = QPushButton("■")
                btn_stop.setCursor(Qt.PointingHandCursor)
                btn_stop.setFocusPolicy(Qt.NoFocus)
                btn_stop.setToolTip(get_translation(self.current_language, 'fm_tooltip_stop'))
                btn_stop_style = btn_style + "\nQPushButton { padding-bottom: 2px; }"
                btn_stop.setStyleSheet(btn_stop_style)
                
                # Подключаем кнопки действий к аудио
                btn_play.clicked.connect(lambda _, rk=item['res_key'], b=btn_play: self._on_action_play_toggle(rk, b))
                btn_stop.clicked.connect(lambda _, rk=item['res_key'], b=btn_play: self._on_action_stop(rk, b))
                
                actions_layout.addWidget(btn_play)
                actions_layout.addWidget(btn_stop)
                action_buttons.extend([btn_play, btn_stop])
            elif item['type'] == 'image':
                # Удален эмодзи глаза (btn_view) по просьбе пользователя
                pass
                
            # Стиль для кнопок замены и скачивания (на 20% меньше основных кнопок)
            btn_small_style = btn_style.replace("font-size: 20px;", "font-size: 16px;")
            
            btn_replace = QPushButton("⟲")
            btn_replace.setCursor(Qt.PointingHandCursor)
            btn_replace.setFocusPolicy(Qt.NoFocus)
            btn_replace.setToolTip(get_translation(self.current_language, 'fm_tooltip_replace'))
            btn_replace.setStyleSheet(btn_small_style)
            
            btn_download = QPushButton("🡇")
            btn_download.setCursor(Qt.PointingHandCursor)
            btn_download.setFocusPolicy(Qt.NoFocus)
            btn_download.setToolTip(get_translation(self.current_language, 'fm_tooltip_download'))
            btn_download.setStyleSheet(btn_small_style)
            
            btn_replace.clicked.connect(lambda _, rk=item['res_key']: self._on_replace_clicked(rk))
            btn_download.clicked.connect(lambda _, rk=item['res_key']: self._on_download_clicked(rk))
            
            actions_layout.addWidget(btn_replace)
            actions_layout.addWidget(btn_download)
            action_buttons.extend([btn_replace, btn_download])
            
            # Устанавливаем кастомные тултипы на все кнопки
            for btn in action_buttons:
                self._btn_tooltip_filter.add_button(btn)
            
            self.table.setCellWidget(row, self.COL_ACTIONS, actions_widget)

        # Восстанавливаем сортировку
        self.table.setSortingEnabled(True)
        
        # [FIX] Возвращаем отрисовку и принудительно обновляем
        self.table.viewport().setUpdatesEnabled(True)
        self.table.setUpdatesEnabled(True)
        self.table.blockSignals(False)
        self.table.viewport().update()
        
        # Запускаем фоновую загрузку миниатюр
        if getattr(self, '_thumbnail_queue', []):
            self._process_thumbnail_queue()

    def _get_filtered_files(self):
        """Возвращает отфильтрованный список файлов."""
        show_audio = self.filter_audio.isChecked()
        show_images = self.filter_images.isChecked()
        show_kneeboard = self.filter_kneeboard.isChecked()
        search_text = self.search_input.text().strip().lower()

        result = []
        for item in self._all_files:
            # Разделяем обычные изображения и планшет
            is_kneeboard = item.get('context') == 'kneeboard'

            # Фильтр по типу
            if item['type'] == 'audio' and not show_audio:
                continue
            
            if item['type'] == 'image':
                if is_kneeboard:
                    if not show_kneeboard:
                        continue
                else:
                    if not show_images:
                        continue

            # Фильтр по поиску
            if search_text and search_text not in item['filename'].lower():
                continue
            result.append(item)

        return result

    def _apply_filters(self):
        """Применяет фильтры и перестраивает таблицу."""
        self._populate_table()

    def _on_table_selection_changed(self):
        """Обновляет цвета статусов при смене выделения, чтобы серый цвет не пропадал."""
        for row in range(self.table.rowCount()):
            fname_item = self.table.item(row, self.COL_FILENAME)
            if not fname_item:
                continue
            is_selected = fname_item.isSelected()
            
            # Переопределяем цвета для текста (исключаем чекбокс, статус и тип)
            cols_to_update = [self.COL_FILENAME, self.COL_DESCRIPTION]
            for col in cols_to_update:
                item = self.table.item(row, col)
                if item:
                    base_color = item.data(Qt.UserRole + 3)
                    if not base_color:
                        base_color = '#ffffff'
                    
                    if is_selected:
                        item.setForeground(QColor('#ff9900'))
                    else:
                        item.setForeground(QColor(base_color))

    def _recalculate_row_numbers(self):
        """Перенумеровывает строки по визуальному порядку (1..N) после сортировки."""
        self.table.blockSignals(True)
        # Отменяем возможность сортировать таблицу по колонке с номерами
        # Для этого просто перебираем все видимые строки по порядку их отображения
        
        # Получаем вертикальный заголовок, который хранит визуальный порядок
        v_header = self.table.verticalHeader()
        logical_count = self.table.rowCount()
        
        # Индекс отображаемой строки -> логический индекс строки
        # logical_index(visual_index) возвращает логический номер строки для данной визуальной позиции
        for visual_row in range(logical_count):
            logical_row = v_header.logicalIndex(visual_row)
            num_item = self.table.item(logical_row, self.COL_NUMBER)
            if num_item:
                num_item.setText(str(visual_row + 1))
                
        self.table.blockSignals(False)

    def _on_row_selected(self, current_row, current_col, prev_row, prev_col):
        """Обработчик выбора строки — показывает превью."""
        if current_row < 0:
            self._show_preview_placeholder()
            return

        fname_item = self.table.item(current_row, self.COL_FILENAME)
        if not fname_item:
            self._show_preview_placeholder()
            return

        file_type = fname_item.data(Qt.UserRole + 1)
        res_key = fname_item.data(Qt.UserRole)
        filename = fname_item.data(Qt.UserRole + 2)

        if file_type == 'image':
            # Останавливаем превью-аудио при переходе на картинку
            self._stop_preview_audio()
            self._show_image_preview(res_key, filename)
        elif file_type == 'audio':
            self._show_audio_preview(res_key, filename)
        else:
            self._stop_preview_audio()
            self._show_preview_placeholder()

    # ─── Аудио: превью-плеер ──────────────────────────────────────────

    def _show_audio_preview(self, res_key, filename, auto_play=False):
        """Показывает мини-плеер для аудиофайла в области превью."""
        if hasattr(self, 'image_info_label'):
            self.image_info_label.hide()
        # Если выбрали другой файл — останавливаем текущий
        if self._preview_audio_key != res_key:
            self._stop_preview_audio(reset_ui=False)
        
        self._preview_audio_key = res_key
        
        # Извлекаем файл во временную папку
        temp_path = self._extract_resource_to_temp(res_key, filename)
        self._preview_audio_path = temp_path
        
        # Переключаем на страницу аудиоплеера
        self.preview_stack.setCurrentWidget(self._audio_player_widget)
        
        # Обновляем название
        self._ap_file_label.setText(filename)
        
        # Загружаем длительность
        self._preview_duration_sec = 0
        self._preview_audio_loaded = False
        self._preview_play_offset = 0
        
        if temp_path and os.path.exists(temp_path):
            try:
                sound = pygame.mixer.Sound(temp_path)
                self._preview_duration_sec = sound.get_length()
                del sound
            except Exception as e:
                logger.error(f"Error loading audio duration: {e}")
        
        # Обновляем инфо (длительность и размер)
        file_size_kb = 0
        try:
            if temp_path and os.path.exists(temp_path):
                file_size_kb = os.path.getsize(temp_path) / 1024
        except: pass

        def fmt_time(sec):
            m = int(sec // 60)
            s = int(sec % 60)
            return f"{m:02}:{s:02}"
            
        info_text = f"⏳ {fmt_time(self._preview_duration_sec)}   •   💾 {file_size_kb:.1f} KB"
        self.image_info_label.setText(info_text)
        self.image_info_label.show()

        # Обновляем слайдер
        self._ap_position_slider.setRange(0, int(self._preview_duration_sec * 1000))
        self._ap_position_slider.setValue(0)
        self._update_preview_time_labels(0)
        
        # Сбрасываем кнопку play
        self._ap_play_btn.setText("▶")
        self._ap_play_btn.setStyleSheet(self._ap_btn_style.format(size=28, top=-4))
        
        # Синхронизация громкости с основным окном
        main_win = self._get_main_window()
        if main_win and hasattr(main_win, 'audio_volume'):
            self._ap_volume_slider.blockSignals(True)
            self._ap_volume_slider.setValue(main_win.audio_volume)
            self._ap_volume_slider.blockSignals(False)
        
        if auto_play:
            self._toggle_preview_play_pause()

    def _toggle_preview_play_pause(self):
        """Переключение play/pause для превью-плеера."""
        if not self._preview_audio_path or not os.path.exists(self._preview_audio_path):
            return
        
        # Перехватываем миксер у кнопок действий
        if self._action_playing_key:
            self._reset_action_button()
            self._action_playing_key = None
            self._action_paused = False
        
        if self._preview_playing:
            # Пауза
            try:
                pygame.mixer.music.pause()
            except Exception:
                pass
            self._preview_playing = False
            self._preview_paused = True
            self._ap_play_btn.setText("▶")
            self._ap_play_btn.setStyleSheet(self._ap_btn_style.format(size=28, top=-4))
        else:
            if self._preview_paused:
                # Продолжить
                try:
                    if not self._preview_audio_loaded:
                        pygame.mixer.music.load(self._preview_audio_path)
                        self._preview_audio_loaded = True
                        pygame.mixer.music.play(start=self._preview_play_offset / 1000.0)
                    else:
                        pygame.mixer.music.unpause()
                except Exception:
                    try:
                        pygame.mixer.music.load(self._preview_audio_path)
                        self._preview_audio_loaded = True
                        pygame.mixer.music.play()
                    except Exception:
                        pass
            else:
                # Играть сначала
                self._preview_play_offset = 0
                try:
                    pygame.mixer.music.load(self._preview_audio_path)
                    self._preview_audio_loaded = True
                    vol = self._ap_volume_slider.value() / 100.0
                    pygame.mixer.music.set_volume(vol)
                    pygame.mixer.music.play()
                except Exception as e:
                    logger.error(f"Audio play error: {e}")
                    return
            
            self._preview_playing = True
            self._preview_paused = False
            self._ap_play_btn.setText("\u23F8\uFE0E")
            self._ap_play_btn.setStyleSheet(self._ap_btn_style.format(size=26, top=-4))

    def _stop_preview_audio(self, reset_ui=True):
        """Останавливает превью-плеер."""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        
        self._preview_playing = False
        self._preview_paused = False
        self._preview_play_offset = 0
        self._preview_audio_loaded = False
        
        if reset_ui:
            self._ap_play_btn.setText("▶")
            self._ap_play_btn.setStyleSheet(self._ap_btn_style.format(size=28, top=-4))
            self._ap_position_slider.setValue(0)
            self._update_preview_time_labels(0)
            # Перезагружаем для чистого старта
            if self._preview_audio_path and os.path.exists(self._preview_audio_path):
                try:
                    pygame.mixer.music.load(self._preview_audio_path)
                    self._preview_audio_loaded = True
                except Exception:
                    pass

    def _on_preview_slider_pressed(self):
        self._preview_slider_dragged = True

    def _on_preview_slider_released(self):
        val_ms = self._ap_position_slider.value()
        start_pos = val_ms / 1000.0
        
        # Перехватываем миксер
        if self._action_playing_key:
            self._reset_action_button()
            self._action_playing_key = None
            self._action_paused = False
        
        try:
            if not self._preview_audio_loaded:
                if self._preview_audio_path and os.path.exists(self._preview_audio_path):
                    pygame.mixer.music.load(self._preview_audio_path)
                    self._preview_audio_loaded = True
            pygame.mixer.music.play(start=start_pos)
            self._preview_play_offset = val_ms
            self._preview_playing = True
            self._preview_paused = False
            self._ap_play_btn.setText("\u23F8\uFE0E")
            self._ap_play_btn.setStyleSheet(self._ap_btn_style.format(size=26, top=-4))
        except Exception as e:
            logger.error(f"Seek error: {e}")
        
        self._preview_slider_dragged = False

    def _set_preview_volume(self, value):
        # Используем централизованный метод в главном окне
        main_win = self._get_main_window()
        if main_win and hasattr(main_win, 'set_audio_volume'):
            main_win.set_audio_volume(value, sender=self)
        else:
            # Fallback
            vol = value / 100.0
            try:
                pygame.mixer.music.set_volume(vol)
            except Exception: pass

    def _update_preview_time_labels(self, current_ms):
        def fmt(ms):
            s = int(ms // 1000) % 60
            m = int(ms // 60000)
            return f"{m:02}:{s:02}"
        dur_ms = int(self._preview_duration_sec * 1000)
        self._ap_time_label.setText(f"{fmt(current_ms)} / {fmt(dur_ms)}")

    def _on_preview_replace_audio(self):
        """Замена аудио из превью-плеера."""
        if not self._preview_audio_key:
            return
        self._on_replace_clicked(self._preview_audio_key)
        # После замены обновляем превью
        res_info = self.miz_resource_manager.get_audio_for_res_key(self._preview_audio_key)
        if res_info:
            self._show_audio_preview(self._preview_audio_key, res_info[0])

    def _get_main_window(self):
        """Возвращает главное окно приложения."""
        widget = self.parent()
        while widget:
            if hasattr(widget, 'audio_volume'):
                return widget
            # У FilesWindow нет родителя (None), но есть ссылка main_app
            if hasattr(widget, 'main_app') and widget.main_app:
                return widget.main_app
            widget = widget.parent() if hasattr(widget, 'parent') else None
        return None

    # ─── Аудио: кнопки действий (▶/■ в строке) ───────────────────────

    def _on_action_play_toggle(self, res_key, btn):
        """Play/Pause через кнопку действий в строке (независимо от превью)."""
        # Перехватываем миксер у превью-плеера
        if self._preview_playing or self._preview_paused:
            # Сохраняем позицию
            if self._preview_playing:
                try:
                    current_ms = pygame.mixer.music.get_pos() + self._preview_play_offset
                    self._preview_play_offset = current_ms
                except Exception:
                    pass
            self._preview_playing = False
            self._preview_paused = True
            self._preview_audio_loaded = False
            self._ap_play_btn.setText("▶")
            self._ap_play_btn.setStyleSheet(self._ap_btn_style.format(size=28, top=-4))
        
        btn_style_normal = """
            QPushButton { background: transparent; color: #ffffff; border: none; font-size: 20px; }
            QPushButton:hover { color: #ff9900; }
        """
        btn_style_pause = """
            QPushButton { background: transparent; color: #ff9900; border: none;
                font-family: 'Segoe UI Symbol', Consolas, sans-serif; font-size: 16px; }
            QPushButton:hover { color: #ffffff; }
        """
        
        if self._action_playing_key == res_key:
            # Тот же ключ — toggle
            try:
                if pygame.mixer.music.get_busy() and not self._action_paused:
                    # Пауза
                    pygame.mixer.music.pause()
                    self._action_paused = True
                    btn.setText("▶")
                    btn.setStyleSheet(btn_style_normal)
                elif self._action_paused:
                    # Продолжить
                    pygame.mixer.music.unpause()
                    self._action_paused = False
                    btn.setText("\u23F8\uFE0E")
                    btn.setStyleSheet(btn_style_pause)
                else:
                    # Трек завершился, играем заново
                    self._play_action_audio(res_key, btn, btn_style_pause)
            except Exception:
                self._play_action_audio(res_key, btn, btn_style_pause)
        else:
            # Другой ключ — останавливаем предыдущий
            self._reset_action_button()
            self._play_action_audio(res_key, btn, btn_style_pause)
        
        # [FIX] Возвращаем фокус и выделение на таблицу для управления стрелками
        self._restore_table_focus_by_key(res_key)

    def _play_action_audio(self, res_key, btn, pause_style):
        """Запускает воспроизведение через кнопку действий."""
        res_info = self.miz_resource_manager.get_audio_for_res_key(res_key)
        if not res_info:
            return
        filename, _ = res_info
        temp_path = self._extract_resource_to_temp(res_key, filename)
        if temp_path and os.path.exists(temp_path):
            try:
                pygame.mixer.music.load(temp_path)
                vol = self._ap_volume_slider.value() / 100.0
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play()
                self._action_playing_key = res_key
                self._action_playing_btn = btn
                self._action_paused = False
                btn.setText("\u23F8\uFE0E")
                btn.setStyleSheet(pause_style)
            except Exception as e:
                logger.error(f"Action play error: {e}")

    def _on_action_stop(self, res_key, play_btn):
        """Стоп через кнопку действий."""
        if self._action_playing_key == res_key:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self._action_playing_key = None
            self._action_paused = False
            self._action_playing_btn = None
            btn_style_normal = """
                QPushButton { background: transparent; color: #ffffff; border: none; font-size: 20px; }
                QPushButton:hover { color: #ff9900; }
            """
            play_btn.setText("▶")
            play_btn.setStyleSheet(btn_style_normal)
        
        # [FIX] Возвращаем фокус на таблицу
        self._restore_table_focus_by_key(res_key)

    def _reset_action_button(self):
        """Сбрасывает иконку предыдущей кнопки действий."""
        if self._action_playing_btn:
            btn_style_normal = """
                QPushButton { background: transparent; color: #ffffff; border: none; font-size: 20px; }
                QPushButton:hover { color: #ff9900; }
            """
            self._action_playing_btn.setText("▶")
            self._action_playing_btn.setStyleSheet(btn_style_normal)
            self._action_playing_btn = None

    # ─── Аудио: таймер ────────────────────────────────────────────────

    def _check_audio_state(self):
        """Периодическая проверка состояния аудио (200мс)."""
        try:
            # --- Обновление превью-плеера ---
            if self._preview_playing:
                if not self._preview_slider_dragged:
                    try:
                        if pygame.mixer.music.get_busy():
                            current_ms = pygame.mixer.music.get_pos() + self._preview_play_offset
                            self._ap_position_slider.blockSignals(True)
                            self._ap_position_slider.setValue(int(current_ms))
                            self._ap_position_slider.blockSignals(False)
                            self._update_preview_time_labels(current_ms)
                        else:
                            # Трек завершился
                            self._preview_playing = False
                            self._preview_paused = False
                            self._preview_play_offset = 0
                            self._ap_play_btn.setText("▶")
                            self._ap_play_btn.setStyleSheet(self._ap_btn_style.format(size=28, top=-4))
                            self._ap_position_slider.blockSignals(True)
                            self._ap_position_slider.setValue(0)
                            self._ap_position_slider.blockSignals(False)
                            self._update_preview_time_labels(0)
                            if self._preview_audio_path and os.path.exists(self._preview_audio_path):
                                try:
                                    pygame.mixer.music.load(self._preview_audio_path)
                                    self._preview_audio_loaded = True
                                except Exception:
                                    pass
                    except Exception:
                        pass
            
            # --- Проверка кнопок действий ---
            if self._action_playing_key and not self._action_paused:
                try:
                    if not pygame.mixer.music.get_busy():
                        self._reset_action_button()
                        self._action_playing_key = None
                        self._action_paused = False
                except Exception:
                    pass
        except Exception:
            pass

    # ─── Двойной клик для автопроигрывания ────────────────────────────

    def _on_table_double_clicked(self, index):
        """Обработчик двойного клика по строке таблицы."""
        row = index.row()
        fname_item = self.table.item(row, self.COL_FILENAME)
        if not fname_item:
            return
        file_type = fname_item.data(Qt.UserRole + 1)
        res_key = fname_item.data(Qt.UserRole)
        
        if file_type == 'audio':
            filename = fname_item.data(Qt.UserRole + 2)
            self._show_audio_preview(res_key, filename, auto_play=True)
        elif file_type == 'image':
            # Собираем список всех изображений в текущем отфильтрованном виде
            image_list = []
            current_idx = 0
            
            for r in range(self.table.rowCount()):
                it = self.table.item(r, self.COL_FILENAME)
                if it and it.data(Qt.UserRole + 1) == 'image':
                    rk = it.data(Qt.UserRole)
                    disp = it.text()
                    path = it.data(Qt.UserRole + 2)
                    
                    if rk == res_key:
                        current_idx = len(image_list)
                    image_list.append((rk, disp, path))
            
            if image_list:
                from dialogs import ImagePreviewDialog
                dlg = ImagePreviewDialog(current_idx, image_list, self.current_language, self)
                dlg.exportRequested.connect(self._on_download_clicked)
                dlg.replaceRequested.connect(self._on_replace_clicked)
                dlg.exec_()

    def _on_download_clicked(self, res_key):
        """Сохранение одного файла."""
        settings = QSettings("MissionTranslator", "DCSTranslatorTool")
        last_dir = settings.value("fm_last_export_dir", os.path.expanduser("~"))
        
        # Получаем имя файла для предложения
        res_info = self.miz_resource_manager.get_audio_for_res_key(res_key)
        if not res_info: return
        filename, _ = res_info
        
        path, _ = QFileDialog.getSaveFileName(
            self, get_translation(self.current_language, 'fm_tooltip_download'),
            os.path.join(last_dir, filename),
            "All Files (*)"
        )
        if path:
            settings.setValue("fm_last_export_dir", os.path.dirname(path))
            if self.miz_resource_manager.extract_resource_to_file(self.miz_path, res_key, path):
                pass
        
        # [FIX] Возвращаем фокус
        self._restore_table_focus_by_key(res_key)

    def _on_replace_clicked(self, res_key):
        """Замена одного файла."""
        settings = QSettings("MissionTranslator", "DCSTranslatorTool")
        last_dir = settings.value("fm_last_import_dir", os.path.expanduser("~"))
        
        # Определяем тип файла по расширению оригинального файла
        res_info = self.miz_resource_manager.get_audio_for_res_key(res_key)
        is_audio = False
        if res_info:
            filename, _ = res_info
            _, ext = os.path.splitext(filename.lower())
            if ext in ['.ogg', '.wav']:
                is_audio = True

        filter_str = get_translation(self.current_language, 'audio_file_filter') if is_audio else "Images (*.png *.jpg);;All Files (*)"

        path, _ = QFileDialog.getOpenFileName(
            self, get_translation(self.current_language, 'fm_tooltip_replace'),
            last_dir,
            filter_str
        )
        if path:
            settings.setValue("fm_last_import_dir", os.path.dirname(path))
            
            new_filename = self.miz_resource_manager.replace_audio(res_key, path)
            if new_filename: # Метод универсален для ресурсов
                # Если это KNEEBOARD, ключ мог измениться вместе с именем файла
                if res_key.startswith("KneeboardKey_"):
                    selected_res_key = f"KneeboardKey_{new_filename}"
                else:
                    selected_res_key = res_key

                # Очищаем кэш миниатюр для этого файла (чтобы подгрузилась новая)
                # Очищаем по обоим ключам на всякий случай
                for rk in [res_key, selected_res_key]:
                    if rk in self._thumbnail_cache:
                        del self._thumbnail_cache[rk]
                    
                self._all_files = self.miz_resource_manager.get_all_resource_files()
                self.resourcesChanged.emit()
                self._apply_filters() # Обновляем таблицу (статус станет красным)
                
                # Восстанавливаем выделение, чтобы обновилось превью и имя
                for r in range(self.table.rowCount()):
                    it = self.table.item(r, self.COL_FILENAME)
                    if it and it.data(Qt.UserRole) == selected_res_key:
                        self.table.selectRow(r)
                        self.table.setFocus()
                        break
        else:
            # Если отменили выбор файла, тоже возвращаем фокус
            self._restore_table_focus_by_key(res_key)

    def get_resource_info_by_key(self, res_key):
        """Возвращает актуальную информацию о ресурсе (res_key, display_name, filename)."""
        for item in self._all_files:
            if item['res_key'] == res_key:
                return (res_key, item['filename'], item['filename'])
        return None

    def _on_batch_export_clicked(self):
        """Массовый экспорт выбранных файлов."""
        if not self.checked_keys: return
        
        settings = QSettings("MissionTranslator", "DCSTranslatorTool")
        last_dir = settings.value("fm_last_export_dir", os.path.expanduser("~"))
        
        dir_path = QFileDialog.getExistingDirectory(
            self, get_translation(self.current_language, 'fm_btn_batch_export'),
            last_dir
        )
        if dir_path:
            settings.setValue("fm_last_export_dir", dir_path)
            success_count = 0
            for res_key in self.checked_keys:
                res_info = self.miz_resource_manager.get_audio_for_res_key(res_key)
                if not res_info: continue
                filename, _ = res_info
                
                out_path = os.path.join(dir_path, filename)
                if self.miz_resource_manager.extract_resource_to_file(self.miz_path, res_key, out_path):
                    success_count += 1
            
            if success_count > 0:
                formatted_path = f"<br/><span style='color: #ff9900;'>📂 {dir_path}</span>"
                msg = get_translation(self.current_language, 'fm_export_success').format(path=formatted_path)
            else:
                msg = get_translation(self.current_language, 'fm_export_zero')
                
            dialog = StandardInfoDialog(get_translation(self.current_language, 'fm_title'), msg, self.current_language, self)
            dialog.exec_()

    def _on_batch_replace_clicked(self):
        """Массовая замена ресурсов через кастомный диалог."""
        if not self.checked_keys: return
        
        # Определяем фильтр на основе типов выбранных файлов
        is_audio = False
        is_image = False
        for r_key in self.checked_keys:
            r_info = self.miz_resource_manager.get_audio_for_res_key(r_key)
            if r_info:
                f_name, _ = r_info
                _, ext = os.path.splitext(f_name.lower())
                if ext in ['.wav', '.ogg']:
                    is_audio = True
                elif ext in ['.png', '.jpg', '.jpeg']:
                    is_image = True
        
        if is_audio:
            filter_str = get_translation(self.current_language, 'audio_file_filter')
        elif is_image:
            filter_str = "Images (*.png *.jpg);;All Files (*)"
        else:
            filter_str = "All Files (*)"

        dialog = BatchReplaceDialog(self.current_language, filter_str, self)
        if dialog.exec_() != QDialog.Accepted:
            return
            
        result = dialog.get_result()
        mode = result["mode"]
        
        success_count = 0
        total_selected = len(self.checked_keys)
        
        if mode == "suffix":
            prefix = result["prefix"]
            suffix = result["suffix"]
            # Сохраняем префикс и суффикс
            settings = QSettings("MissionTranslator", "DCSTranslatorTool")
            settings.setValue("fm_last_batch_prefix", prefix)
            settings.setValue("fm_last_batch_suffix", suffix)
            
            # Выбор папки
            last_dir = settings.value("fm_last_import_dir", os.path.expanduser("~"))
            dir_path = QFileDialog.getExistingDirectory(
                self, get_translation(self.current_language, 'fm_btn_batch_replace'),
                last_dir
            )
            if not dir_path: return
            settings.setValue("fm_last_import_dir", dir_path)
            
            for res_key in list(self.checked_keys):
                res_info = self.miz_resource_manager.get_audio_for_res_key(res_key)
                if not res_info: continue
                filename, _ = res_info
                pure_name = os.path.basename(filename)
                base, ext = os.path.splitext(pure_name)
                local_name = f"{prefix}{base}{suffix}{ext}"
                local_path = os.path.join(dir_path, local_name)
                
                if os.path.exists(local_path):
                    if self.miz_resource_manager.replace_audio(res_key, local_path):
                        success_count += 1
        else:
            # Режим "Один файл для всех"
            file_path = result["file_path"]
            if not file_path or not os.path.exists(file_path):
                return
                
            for res_key in list(self.checked_keys):
                if self.miz_resource_manager.replace_audio(res_key, file_path):
                    success_count += 1
                    
        # Показываем результат (даже если 0)
        path_info = ""
        if mode == "suffix" and 'dir_path' in locals():
            path_info = f"<br/><span style='color: #ff9900;'>📂 {dir_path}</span>"
        
        if success_count > 0:
            # [BUG-5 FIX] Очищаем кэш миниатюр для заменённых файлов
            for res_key in list(self.checked_keys):
                if res_key in self._thumbnail_cache:
                    del self._thumbnail_cache[res_key]
            self._all_files = self.miz_resource_manager.get_all_resource_files()
            self.resourcesChanged.emit()
            self._apply_filters()
            
            msg = get_translation(self.current_language, 'fm_batch_replace_success').format(
                count=success_count, 
                total=total_selected,
                path=path_info
            )
        else:
            msg = get_translation(self.current_language, 'fm_batch_replace_zero').format(
                total=total_selected,
                path=path_info
            )
            
        dialog = StandardInfoDialog(get_translation(self.current_language, 'fm_title'), msg, self.current_language, self)
        dialog.exec_()

    def _show_preview_placeholder(self):
        """Показывает placeholder в области превью."""
        self.preview_stack.setCurrentWidget(self.placeholder_label)
        if hasattr(self, 'image_info_label'):
            self.image_info_label.hide()
        self.placeholder_label.setText(
            get_translation(self.current_language, 'fm_preview_placeholder'))
        self.placeholder_label.setStyleSheet(
            "color: #777; font-size: 14px; border: 1px dashed #555; border-radius: 4px; background: transparent;")

    def _show_image_preview(self, res_key, filename):
        """Извлекает и показывает изображение в области превью."""
        self.preview_stack.setCurrentWidget(self.preview_area)
        
        if not self.miz_path or not self.miz_resource_manager:
            self._show_preview_placeholder()
            return

        temp_path = self._extract_resource_to_temp(res_key, filename)
        if not temp_path:
            self.preview_stack.setCurrentWidget(self.placeholder_label)
            self.placeholder_label.setText(f"❌ {filename}")
            self.placeholder_label.setStyleSheet(
                "color: #ff3333; font-size: 14px; border: 1px solid #ff3333; border-radius: 4px;")
            return

        pixmap = QPixmap(temp_path)
        if pixmap.isNull():
            self.preview_stack.setCurrentWidget(self.placeholder_label)
            self.placeholder_label.setText(f"❌ {filename}")
            self.placeholder_label.setStyleSheet(
                "color: #ff3333; font-size: 14px; border: 1px solid #ff3333; border-radius: 4px;")
            return

        self.preview_area.setPixmap(pixmap)
        
        # Обновляем информацию об изображении
        width = pixmap.width()
        height = pixmap.height()
        file_size_kb = 0
        try:
            if os.path.exists(temp_path):
                file_size_kb = os.path.getsize(temp_path) / 1024
        except:
            pass
        
        info_text = f"📐 {width}x{height}   •   💾 {file_size_kb:.1f} KB"
        self.image_info_label.setText(info_text)
        self.image_info_label.show()


    def _execute_drag(self, row):
        """Выполняет Drag-Out операцию для файлов из указанной строки."""
        files_to_drag = self._get_drag_files(row)
        if not files_to_drag:
            return

        urls = [QUrl.fromLocalFile(f) for f in files_to_drag]
        
        mime_data = QMimeData()
        mime_data.setUrls(urls)
        
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # Меняем курсор на сжатый кулак во время перетаскивания
        drag.setDragCursor(QPixmap(), Qt.CopyAction) # Сброс кастомного, если был
        self.table.viewport().setCursor(Qt.ClosedHandCursor)
        
        # Можно поставить иконку первого файла или общую иконку
        item = self.table.item(row, self.COL_TYPE)
        if item:
            icon = item.icon()
            if not icon.isNull():
                drag.setPixmap(icon.pixmap(32, 32))
        
        drag.exec_(Qt.CopyAction)
        
        # Возвращаем обычную ладонь после завершения
        self.table.viewport().setCursor(Qt.OpenHandCursor)

    def _get_drag_files(self, row):
        """Возвращает список путей к временным файлам для перетаскивания.
        Если затянутая строка выбрана галочкой - тянем все выбранные.
        Иначе - только одну текущую.
        """
        # Получаем данные текущей строки
        fname_item = self.table.item(row, self.COL_FILENAME)
        if not fname_item:
            return []
            
        res_key = fname_item.data(Qt.UserRole)
        
        target_keys = []
        if res_key in self.checked_keys:
            # Если тянем выделенный файл - берем все выделенные
            target_keys = list(self.checked_keys)
        else:
            # Иначе только этот один
            target_keys = [res_key]
            
        # [FIX] Создаем уникальную подпапку для этой конкретной операции перетаскивания,
        # чтобы файлы имели свои оригинальные имена без суффиксов.
        drag_dir = tempfile.mkdtemp(prefix="dcs_drag_")
        
        temp_paths = []
        # Находим все файлы по ключам (нужно достать оригинальные имена)
        for r in range(self.table.rowCount()):
            it = self.table.item(r, self.COL_FILENAME)
            if it and it.data(Qt.UserRole) in target_keys:
                k = it.data(Qt.UserRole)
                fn = it.text()
                # Извлекаем в специальную папку БЕЗ суффикса
                path = self._extract_resource_to_temp(k, fn, target_dir=drag_dir)
                if path and os.path.exists(path):
                    temp_paths.append(path)
                    
        return temp_paths

    def _extract_resource_to_temp(self, res_key, filename, target_dir=None):
        """Извлекает ресурс из .miz во временный файл.
        
        Args:
            res_key: ключ ресурса
            filename: имя файла
            target_dir: если указан, файл будет извлечен туда под своим именем (без суффикса)
            
        Returns:
            str: путь к временному файлу или None
        """
        if not self.miz_path:
            return None

        mgr = self.miz_resource_manager
        
        # Определяем локаль и путь
        if res_key.startswith("KneeboardKey_"):
            target_path = f"KNEEBOARD/IMAGES/{filename}"
        else:
            is_current = res_key in mgr.map_resource_current
            folder = mgr.current_folder if is_current else "DEFAULT"
            target_path = f"l10n/{folder}/{filename}"

        # Проверяем pending_files
        if target_path in mgr.pending_files:
            src = mgr.pending_files[target_path]
            if os.path.exists(src):
                # Если указан target_dir и это не тот же файл — копируем
                if target_dir:
                    dst = os.path.join(target_dir, filename)
                    if src != dst:
                        shutil.copy2(src, dst)
                    return dst
                return src

        # Извлекаем из ZIP
        try:
            if target_dir:
                # Для Drag-Out используем оригинальное имя
                temp_path = os.path.join(target_dir, filename)
            else:
                # [FIX] Для предпросмотра используем res_key и суффикс для полной уникальности.
                # Это предотвращает конфликты, если есть файлы с одинаковыми именами.
                suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                temp_dir = tempfile.gettempdir()
                # Очищаем res_key от символов, которые могут быть недопустимы в пути
                safe_key = "".join([c if c.isalnum() else "_" for c in res_key])
                temp_path = os.path.join(temp_dir, f"dcs_preview_{suffix}_{safe_key}_{filename}")

            with zipfile.ZipFile(self.miz_path, 'r') as z:
                actual_path = target_path
                if actual_path not in z.namelist():
                    # Регистронезависимый поиск
                    found = False
                    for name in z.namelist():
                        if name.lower() == target_path.lower():
                            actual_path = name
                            found = True
                            break
                    if not found:
                        if target_path.startswith("KNEEBOARD/"):
                            # Для KNEEBOARD нет fallback-а в DEFAULT
                            return None
                        else:
                            # Fallback: DEFAULT
                            fallback = f"l10n/DEFAULT/{filename}"
                            if fallback in z.namelist():
                                actual_path = fallback
                            else:
                                return None

                with z.open(actual_path) as src, open(temp_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)

                return temp_path

        except Exception as e:
            logger.error(f"Ошибка извлечения ресурса {filename}: {e}")
            return None




    def closeEvent(self, event):
        """Сохранение настроек при закрытии окна."""
        settings = QSettings("MissionTranslator", "DCSTranslatorTool")
        settings.setValue("fm_view_slider_value", self.view_slider.value())
        
        # Останавливаем аудио при закрытии
        self._stop_preview_audio()
        super().closeEvent(event)


    # ─── Локализация ──────────────────────────────────────────────────

    def retranslate_ui(self, current_language):
        """Обновляет переводы интерфейса."""
        # Сохраняем текущее выделение (по ключу ресурса)
        selected_res_key = None
        current_row = self.table.currentRow()
        if current_row >= 0:
            item = self.table.item(current_row, self.COL_FILENAME)
            if item:
                selected_res_key = item.data(Qt.UserRole)

        self.current_language = current_language
        self.search_input.setPlaceholderText(
            get_translation(current_language, 'fm_search_placeholder'))
        if hasattr(self, 'label_filter_audio'):
            self.label_filter_audio.setText(
                get_translation(current_language, 'fm_filter_audio'))
        if hasattr(self, 'label_filter_images'):
            self.label_filter_images.setText(
                get_translation(current_language, 'fm_filter_images'))
        if hasattr(self, 'label_filter_kneeboard'):
            self.label_filter_kneeboard.setText(
                get_translation(current_language, 'fm_filter_kneeboard'))
        
        # Обновляем кнопки пакетных действий
        if hasattr(self, 'btn_batch_export'):
            self.btn_batch_export.setText(get_translation(current_language, 'fm_btn_batch_export'))
        if hasattr(self, 'btn_batch_replace'):
            self.btn_batch_replace.setText(get_translation(current_language, 'fm_btn_batch_replace'))
            
        # Обновляем инфо в заголовке
        if hasattr(self, 'label_mission_prefix'):
            self.label_mission_prefix.setText(get_translation(current_language, 'mission_label'))
        if hasattr(self, 'label_locale_prefix'):
            self.label_locale_prefix.setText(get_translation(current_language, 'localization_label'))
            
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.setText(get_translation(current_language, 'fm_preview_placeholder'))

        # Обновляем аудиоплеер
        if hasattr(self, '_ap_replace_btn'):
            self._ap_replace_btn.setText(get_translation(current_language, 'replace_audio_btn'))
            
        if hasattr(self, 'shift_hint_label'):
            self.shift_hint_label.setText(get_translation(current_language, 'fm_shift_selection_hint'))

        self._update_table_headers()
        self._show_preview_placeholder()
        
        # Перезаполняем таблицу для обновления описаний
        if self._all_files:
            self._populate_table()
            
            # Восстанавливаем выделение
            if selected_res_key:
                for r in range(self.table.rowCount()):
                    it = self.table.item(r, self.COL_FILENAME)
                    if it and it.data(Qt.UserRole) == selected_res_key:
                        self.table.selectRow(r)
                        break
        
        # Принудительно обновляем цвета выделения
        self._on_table_selection_changed()
