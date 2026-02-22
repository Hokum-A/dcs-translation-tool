import os
from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QScrollBar, QLineEdit, QCheckBox, QLabel, QHBoxLayout, QFrame, QVBoxLayout, QScrollArea, QSizePolicy, QMenu
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QRect, QEasingCurve, QPoint, pyqtProperty, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QBrush, QPainterPath, QRegion, QTextCursor, QPixmap, QPen
from PyQt5.QtCore import QRectF
import sip


class LineNumberArea(QWidget):
    """Область для отображения номеров строк"""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return Qt.Size(self.editor.line_number_area_width(), 0)

    def mousePressEvent(self, event):
        """Выделение строки по клику на номер"""
        self.editor.select_lines_at_y(event.y())

    def mouseMoveEvent(self, event):
        """Выделение нескольких строк при перетаскивании"""
        if event.buttons() & Qt.LeftButton:
            self.editor.select_lines_at_y(event.y(), extend=True)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class NumberedTextEdit(QPlainTextEdit):
    """Текстовое поле с номерами строк на полях"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.max_line_count = None  # Лимит для отрисовки номеров строк

        font = QFont('Consolas', 10)
        self.setFont(font)
        self.viewport().setAutoFillBackground(False)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

        self.update_line_number_area_width()

    def line_number_area_width(self):
        """Вычисляет ширину области для номеров строк"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1

        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self):
        """Обновляет ширину области номеров строк"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Обновляет область номеров строк при скролле"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

    def resizeEvent(self, event):
        """Обработка изменения размера"""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(cr.left(), cr.top(),
                                         self.line_number_area_width(), cr.height())

    def select_lines_at_y(self, y, extend=False):
        """Выделяет строку (блоки) в зависимости от координаты Y"""
        if self.document().isEmpty():
            return
            
        block = self.cursorForPosition(QPoint(0, y)).block()
        if not block.isValid():
            return

        cursor = self.textCursor()
        
        if not extend:
            # Устанавливаем базу выделения (якорь)
            self._selection_start_block = block.blockNumber()
            cursor.setPosition(block.position())
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            if not cursor.atEnd():
                cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        else:
            # Расширяем выделение (драг)
            start_num = getattr(self, '_selection_start_block', block.blockNumber())
            current_num = block.blockNumber()
            
            anchor_block = self.document().findBlockByNumber(start_num)
            current_block = self.document().findBlockByNumber(current_num)
            
            if current_num >= start_num:
                # Тянем вниз: якорь в начале стартового блока, идем до конца текущего
                cursor.setPosition(anchor_block.position(), QTextCursor.MoveAnchor)
                cursor.setPosition(current_block.position(), QTextCursor.KeepAnchor)
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                if not cursor.atEnd():
                    cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
            else:
                # Тянем вверх: якорь в конце стартового блока (включая \n), идем до начала текущего
                # Находим позицию конца стартового блока
                anchor_end = anchor_block.position() + anchor_block.length()
                cursor.setPosition(anchor_end, QTextCursor.MoveAnchor)
                cursor.setPosition(current_block.position(), QTextCursor.KeepAnchor)

        self.setTextCursor(cursor)

    def paintEvent(self, event):
        """Отрисовка фона строк (зебра)"""
        painter = QPainter(self.viewport())
        
        # Определяем цвета для "зебры"
        # Основной фон #505050 (80, 80, 80), альтернативный чуть темнее #4a4a4a (74, 74, 74)
        color_even = QColor(80, 80, 80)
        color_odd = QColor(74, 74, 74)
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        
        # Смещение контента (скролл)
        offset = self.contentOffset()
        top = int(self.blockBoundingGeometry(block).translated(offset).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        
        viewport_width = self.viewport().width()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                # Чередуем цвета фона
                color = color_even if block_number % 2 == 0 else color_odd
                painter.fillRect(0, top, viewport_width, bottom - top, color)
            
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
            
        # Отрисовываем сам текст поверх нашего фона
        super().paintEvent(event)

    def line_number_area_paint_event(self, event):
        """Рисует номера строк в отдельной области"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(60, 60, 60))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        height = self.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                # Рисуем номер только если он не превышает лимит (если лимит установлен)
                if self.max_line_count is None or block_number < self.max_line_count:
                    number = str(block_number + 1)
                    painter.setPen(QColor(180, 180, 180))
                    painter.drawText(0, top, self.line_number_area.width() - 5, height,
                                    Qt.AlignRight, number)

            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def contextMenuEvent(self, event):
        """Переопределяем контекстное меню для применения стилей"""
        menu = self.createStandardContextMenu()
        menu.setStyleSheet("""
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
        menu.exec_(event.globalPos())
 
    def mousePressEvent(self, event):
        """Клик мыши снимает extra-выделения (поиск) перед обычным поведением"""
        try:
            self.setExtraSelections([])
        except Exception:
            pass
        super().mousePressEvent(event)


class CustomScrollBar(QScrollBar):
    """Кастомный скроллбар с оранжевым цветом"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QScrollBar:vertical {
                background: #454545;
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
                background: #454545;
                height: 16px;
                margin: 0px 18px 0px 18px;
                border-radius: 8px;
            }
            QScrollBar:horizontal:disabled {
                background: #505050; /* Цвет фона текстового поля */
            }
            QScrollBar::handle:horizontal {
                background: #ff9900;
                min-width: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:disabled {
                background: transparent;
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
            QScrollBar::left-arrow:horizontal:disabled, QScrollBar::right-arrow:horizontal:disabled {
                background: transparent;
            }
            QScrollBar::left-arrow:horizontal:hover, QScrollBar::right-arrow:horizontal:hover {
                background: #e68a00;
            }
        """)


class ToggleSwitch(QWidget):
    """Кастомный toggle-переключатель (как на мобильных)"""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(30, 14)
        self.setCursor(Qt.PointingHandCursor)

        self._checked = False
        self._circle_position = 2

        self.animation = QPropertyAnimation(self, b"circle_position")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.bg_color_unchecked = QColor(100, 100, 100)
        self.bg_color_checked = QColor(255, 153, 0)
        self.circle_color = QColor(240, 240, 240)

    def get_circle_position(self):
        return self._circle_position

    def set_circle_position(self, pos):
        self._circle_position = pos
        self.update()

    circle_position = pyqtProperty(int, get_circle_position, set_circle_position)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            if self.isVisible():
                self.start_animation()
            else:
                self._circle_position = 17 if checked else 2
                self.update()
            self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        """Обработка клика мышью"""
        self.setChecked(not self._checked)

    def start_animation(self):
        """Запускает анимацию переключения"""
        if self._checked:
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(17)
        else:
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(2)

        self.animation.start()

    def paintEvent(self, event):
        """Отрисовка toggle-переключателя"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.contentsRect()
        painter.setPen(Qt.NoPen)

        if self._checked:
            painter.setBrush(self.bg_color_checked)
        else:
            painter.setBrush(self.bg_color_unchecked)

        painter.drawRoundedRect(rect, 7, 7)

        painter.setBrush(self.circle_color)
        painter.drawEllipse(self._circle_position - 1, 0, 13, 13)


class CustomToolTip(QLabel):
    """Небольшой виджет-тултип, отображается как окно с флагом Qt.ToolTip"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self.setStyleSheet('''
            QLabel {
                color: #ffffff;
                background-color: transparent;
                border: none;
            }
        ''')
        self._padding = 6
        self._last_radius = 6
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        # Отключаем системный тултип, чтобы не было черного квадрата
        self.setToolTip("")
        self.hide()
    
    def show_tooltip(self, text, widget, side='bottom'):
        """Показывает тултип относительно виджета с нужной стороны (bottom, left, right, top)"""
        if not text or not widget:
            self.hide()
            return
            
        try:
            self.setText(text)
            
            # Используем fontMetrics для точного расчета
            metrics = self.fontMetrics()
            text_width = metrics.horizontalAdvance(text)
            text_height = metrics.height()
            padding = self._padding
            
            # Базовые размеры
            new_w = text_width + padding * 4
            new_h = text_height + padding * 2
            
            # ОГРАНИЧЕНИЕ ШИРИНЫ (по просьбе пользователя: 850px и ElideMiddle)
            max_tooltip_width = 850
            effective_max_width = max_tooltip_width - padding * 4
            
            if text_width > effective_max_width:
                # Обрезаем текст с середины (...)
                elided_text = metrics.elidedText(text, Qt.ElideMiddle, effective_max_width)
                self.setText(elided_text)
                
                # Пересчитываем ширину уже для обрезанного текста
                new_w = metrics.horizontalAdvance(elided_text) + padding * 4
                # Высота остается для одной строки
                new_h = text_height + padding * 2
            else:
                # Текст вмещается
                new_w = text_width + padding * 4
                new_h = text_height + padding * 2
            
            # Гарантируем минимальные размеры
            new_w = max(30, new_w)
            new_h = max(20, new_h)
            
            self.setFixedSize(new_w, new_h)
            
            self.setFixedSize(new_w, new_h)
            
            # РАСЧЕТ ПОЗИЦИИ
            target_rect = widget.rect()
            global_pos = widget.mapToGlobal(QPoint(0, 0))
            
            x, y = 0, 0
            offset = 8
            
            if side == 'bottom':
                x = global_pos.x() + (target_rect.width() - new_w) // 2
                y = global_pos.y() + target_rect.height() + offset
            elif side == 'top':
                x = global_pos.x() + (target_rect.width() - new_w) // 2
                y = global_pos.y() - new_h - offset
            elif side == 'left':
                x = global_pos.x() - new_w - offset
                y = global_pos.y() + (target_rect.height() - new_h) // 2
            elif side == 'right':
                x = global_pos.x() + target_rect.width() + offset
                y = global_pos.y() + (target_rect.height() - new_h) // 2
            elif side == 'bottom-right':
                x = global_pos.x() + target_rect.width() - 50
                y = global_pos.y() + target_rect.height() - 70
            elif side == 'bottom-left':
                # Выравнивание начала тултипа с началом строки (виджета)
                x = global_pos.x()
                y = global_pos.y() + target_rect.height() + offset
            
            self.move(x, y)
            self.show()
            self.raise_()
            
        except Exception as e:
            # Фолбэк на случай ошибки сложной отрисовки
            try:
                self.setText(text)
                self.adjustSize()
                self.move(pos)
                self.show()
                self.raise_()
            except Exception:
                pass

    def paintEvent(self, event):
        """Отрисовка тултипа с темным фоном и оранжевой рамкой"""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            rect = self.rect()
            
            # Фон (Темно-серый)
            painter.setBrush(QBrush(QColor(50, 50, 50, 245)))
            painter.setPen(QPen(QColor("#ff9900"), 1))
            
            radius = 5
            painter.drawRoundedRect(QRectF(0.5, 0.5, rect.width() - 1, rect.height() - 1), radius, radius)
            
            # Текст (Белый)
            painter.setPen(QColor("#ffffff"))
            padding = getattr(self, "_padding", 6)
            text_rect = rect.adjusted(padding, 0, -padding, 0)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text())
        except Exception:
            super().paintEvent(event)


class LanguageToggleSwitch(QWidget):
    """Кастомный toggle-переключатель для переключения языка с цветами EN/RU"""

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(30, 14)
        self.setCursor(Qt.PointingHandCursor)

        self._checked = True
        self._circle_position = 17

        self.animation = QPropertyAnimation(self, b"circle_position")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.bg_color_en = QColor(51, 102, 255)
        self.bg_color_ru = QColor(255, 51, 51)
        self.circle_color = QColor(240, 240, 240)

    def get_circle_position(self):
        return self._circle_position

    def set_circle_position(self, pos):
        self._circle_position = pos
        self.update()

    circle_position = pyqtProperty(int, get_circle_position, set_circle_position)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            if self.isVisible():
                self.start_animation()
            else:
                self._circle_position = 17 if checked else 2
                self.update()
            self.toggled.emit(self._checked)

    def mousePressEvent(self, event):
        """Обработка клика мышью"""
        new_state = not self._checked
        self._checked = new_state
        self.start_animation()
        self.toggled.emit(new_state)

    def start_animation(self):
        """Запускает анимацию переключения"""
        if self._checked:
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(17)
        else:
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(2)

        self.animation.start()

    def paintEvent(self, event):
        """Отрисовка toggle-переключателя"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.contentsRect()
        painter.setPen(Qt.NoPen)

        if self._checked:
            painter.setBrush(self.bg_color_ru)
        else:
            painter.setBrush(self.bg_color_en)

        painter.drawRoundedRect(rect, 7, 7)

        painter.setBrush(self.circle_color)
        painter.drawEllipse(self._circle_position - 1, 0, 13, 13)


class ClickableLine(QWidget):
    """Виджет строки предпросмотра, реагирующий на клики"""
    def __init__(self, index, callback, parent=None):
        super().__init__(parent)
        self.index = index
        self.callback = callback
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.callback:
                self.callback(self.index)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        """Обеспечиваем поддержку QSS для кастомного виджета"""
        from PyQt5.QtWidgets import QStyleOption, QStyle
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)


class ClickableLabel(QLabel):
    """QLabel, реагирующий на клики"""
    clicked = pyqtSignal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)


class CustomImageButton(QWidget):
    """Кастомная кнопка с изображением и подписью"""
    clicked = pyqtSignal()

    def __init__(self, icon_path, text, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self.setCursor(Qt.PointingHandCursor)
        
        self.text = text
        self.is_hovered = False
        self.is_pressed = False
        
        # Оффсеты для тонкой настройки положения картинки (по просьбе пользователя)
        self.img_x_offset = 11
        self.img_y_offset = 4
        
        # Загрузка изображения
        self.pixmap = None
        if os.path.exists(icon_path):
            self.pixmap = QPixmap(icon_path)
            self.pixmap = self.pixmap.scaled(55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
        # Настройка шрифта
        self.font = QFont("Segoe UI", 9, QFont.Bold)
        
    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_pressed = True
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_pressed:
            self.is_pressed = False
            self.update()
            if self.rect().contains(event.pos()):
                self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        bg_color = Qt.transparent
            
        if self.is_hovered or self.is_pressed:
            border_color = QColor("#ff9900")
            border_width = 2
        else:
            border_color = QColor("#8f8f8f")
            border_width = 1
            
        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(5, 5, -5, -5), 8, 8)
        
        if self.pixmap:
            painter.drawPixmap(self.img_x_offset, self.img_y_offset, self.pixmap)
            
        painter.setPen(QPen(QColor("#ffffff") if not (self.is_hovered) else QColor("#ff9900")))
        painter.setFont(self.font)
        
        text_rect = QRect(0, 55, rect.width(), 20)
        painter.drawText(text_rect, Qt.AlignCenter, self.text)


class PreviewTextEdit(QPlainTextEdit):
    """Специальное поле для предпросмотра с адаптивной высотой и синхронизацией с парой"""
    text_changed = pyqtSignal(int, str)
    line_inserted = pyqtSignal(int)  # index строки, после которой нужно вставить новую
    line_deleted = pyqtSignal(int)   # index строки, которую нужно удалить
    
    def __init__(self, index, text, read_only=False, parent=None):
        super().__init__(parent)
        self.index = index
        self._is_adjusting = False
        self._suppress_adjust = False
        self.partner = None  # Ссылка на парный виджет (оригинал-перевод)
        self.row_siblings = None  # (meta_widget, orig_widget, trans_widget) для синхронизации строк
        
        self.setPlainText(text)
        self.setReadOnly(read_only)
        
        # Сбрасываем курсор в начало
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.setTextCursor(cursor)
        
        # Стилизация
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("border-radius: 0px;")
        self.document().setDocumentMargin(0)
        
        # Обнуляем отступы между блоками (строками) и задаем стандартный интервал
        from PyQt5.QtGui import QTextBlockFormat
        it = self.document().begin()
        while it.isValid():
            cursor = QTextCursor(it)
            fmt = cursor.blockFormat()
            fmt.setTopMargin(0)
            fmt.setBottomMargin(0)
            fmt.setLineHeight(100, QTextBlockFormat.ProportionalHeight)
            cursor.setBlockFormat(fmt)
            it = it.next()
            
        self.setViewportMargins(0, 0, 0, 0)
        
        # Агрессивное отключение скролла и включение переноса строк
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        from PyQt5.QtGui import QTextOption
        self.setWordWrapMode(QTextOption.WordWrap)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalScrollBar().setEnabled(False)
        self.verticalScrollBar().setRange(0, 0)
        
        # Шрифт
        font = QFont("Consolas", 10) 
        self.setFont(font)
        
        # Авто-высота по изменению контента
        self.document().contentsChanged.connect(self.on_content_changed)
        
        # Политика размера
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    
    def keyPressEvent(self, event):
        """Перехватываем Enter для вставки и Backspace для удаления строки"""
        # 1. ENTER (Вставка новой)
        if not self.isReadOnly() and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            try:
                self.line_inserted.emit(self.index)
            except Exception:
                pass
            return
            
        # 2. BACKSPACE (Удаление текущей, если пустая)
        if not self.isReadOnly() and event.key() == Qt.Key_Backspace:
            # Если поле пустое и курсор в начале
            if self.toPlainText() == "" and self.textCursor().atStart():
                try:
                    self.line_deleted.emit(self.index)
                except Exception:
                    pass
                return

        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Клик мыши снимает extra-выделения (поиск) перед обычным поведением"""
        try:
            self.setExtraSelections([])
        except Exception:
            pass
        super().mousePressEvent(event)

    def set_partner(self, partner):
        """Устанавливает парный виджет для синхронизации высоты"""
        self.partner = partner

    def contextMenuEvent(self, event):
        """Пользовательское контекстное меню с унифицированной стилизацией для превью"""
        # Try to use the widget's built-in standard context menu, but apply app styling.
        try:
            menu = self.createStandardContextMenu()
            menu.setStyleSheet("QMenu{ color: #ffffff; background-color: #404040; } QMenu::item:selected{ background-color: #ff9900; color: #000000; }")
            menu.exec_(event.globalPos())
            return
        except Exception:
            # Fallback: construct a minimal standard-like menu
            menu = QMenu(self)
            menu.setStyleSheet("QMenu{ color: #ffffff; background-color: #404040; } QMenu::item:selected{ background-color: #ff9900; color: #000000; }")
            menu.addAction(self.tr('Copy'), self.copy)
            if not self.isReadOnly():
                menu.addAction(self.tr('Paste'), self.paste)
                menu.addAction(self.tr('Clear'), lambda: self.setPlainText(''))
            menu.addSeparator()
            menu.addAction(self.tr('Select all'), self.selectAll)
            menu.exec_(event.globalPos())

    def _replace_css_prop(self, css, prop, value):
        """Replace or add a css property in a stylesheet string."""
        import re
        if css is None:
            css = ''
        if not css.strip():
            return f"{prop}: {value};"
        # Replace only exact property occurrences (avoid matching 'background-color' when prop='color')
        pattern = re.compile(r'(^|;)\s*' + re.escape(prop) + r'\s*:\s*[^;]+;')
        if pattern.search(css):
            return pattern.sub(lambda m: (m.group(1) or '') + f'{prop}: {value};', css)
        else:
            return css + f' {prop}: {value};'

    def set_text_color(self, color):
        try:
            ss = self.styleSheet() or ''
            ss2 = self._replace_css_prop(ss, 'color', color)
            self.setStyleSheet(ss2)
        except Exception:
            pass

    def set_background_color(self, color):
        try:
            ss = self.styleSheet() or ''
            ss2 = self._replace_css_prop(ss, 'background-color', color)
            self.setStyleSheet(ss2)
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Проверка на удаление (RuntimeError protection)
        if sip.isdeleted(self):
            return
        try:
            vw = self.viewport().width()
            if vw > 10:
                self.document().setTextWidth(vw)
            QTimer.singleShot(0, self.adjust_height)
        except RuntimeError:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        def _init_wrap():
            if sip.isdeleted(self):
                return
            try:
                vw = self.viewport().width()
                if vw > 10:
                    self.document().setTextWidth(vw)
                self.adjust_height()
            except RuntimeError:
                pass
        QTimer.singleShot(50, _init_wrap)

    def on_content_changed(self):
        """Обработка изменения текста"""
        if sip.isdeleted(self):
            return
        try:
            if not self.isReadOnly():
                self.text_changed.emit(self.index, self.toPlainText())
            QTimer.singleShot(0, self.adjust_height)
        except RuntimeError:
            pass

    def calculate_required_height(self):
        """Вычисляет необходимую высоту для контента в пикселях."""
        doc = self.document()
        layout = doc.documentLayout()
        
        if layout is None:
            return max(20, self.fontMetrics().lineSpacing() + 4)
        
        # В QPlainTextEdit documentSize().height() возвращает количество визуальных строк
        line_count = layout.documentSize().height()
        line_spacing = self.fontMetrics().lineSpacing()
        
        # Рассчитываем высоту в пикселях
        h = line_count * line_spacing
        
        # Если документ пустой или высота подозрительно мала
        if h < 10:
            h = line_spacing
        
        # Добавляем небольшой запас для исключения микро-скролла
        h += 6
        
        return int(h)

    def sizeHint(self):
        """Возвращает предпочтительный размер на основе содержимого"""
        h = self.calculate_required_height()
        return QSize(super().sizeHint().width(), h)

    def adjust_height(self):
        """Настройка высоты с синхронизацией партнёра и row-siblings"""
        if sip.isdeleted(self):
            return
        if self._is_adjusting or getattr(self, '_suppress_adjust', False):
            return
        self._is_adjusting = True
        
        try:
            my_h = self.calculate_required_height()
            partner_h = 0
            if self.partner and not self.partner._is_adjusting:
                partner_h = self.partner.calculate_required_height()
            
            final_h = max(my_h, partner_h, 20)
            final_h = min(final_h, 500)
            
            # Устанавливаем высоту себе и партнёру только если она изменилась
            if abs(self.height() - final_h) >= 1:
                self.setFixedHeight(final_h)
                self.updateGeometry()
            
            if self.partner and abs(self.partner.height() - final_h) >= 1:
                self.partner.setFixedHeight(final_h)
                self.partner.updateGeometry()
            
            # Синхронизация row-siblings (meta, orig, trans виджеты-строки)
            # Это важная операция для выравнивания всех колонок группы по высоте.
            if self.row_siblings:
                meta_w, orig_w, trans_w = self.row_siblings
                
                heights = []
                # ВАЖНО: Перед замером sizeHint нужно "разблокировать" фиксированную высоту,
                # иначе layout вернет старое значение.
                for w in (meta_w, orig_w, trans_w):
                    if w:
                        # Временно разрешаем виджету менять размер для замера
                        w.setMinimumHeight(0)
                        w.setMaximumHeight(16777215) # QWIDGETSIZE_MAX
                        w.layout().invalidate()
                        w.layout().activate()
                        heights.append(w.sizeHint().height())
                
                if heights:
                    row_h = max(heights)
                    # Устанавливаем новую фиксированную высоту для всех трех колонок
                    for w in (meta_w, orig_w, trans_w):
                        if w:
                            w.setFixedHeight(row_h)
        finally:
            self._is_adjusting = False

    def enterEvent(self, event):
        super().enterEvent(event)
        try:
            # Highlight only translation (editable) fields
            if self.isReadOnly():
                return
            main_win = self.window()
            color = getattr(main_win, 'highlight_empty_color', '#555555')
            enabled = getattr(main_win, 'highlight_empty_fields', True)
            if enabled:
                # apply background only, keep text color intact
                base = getattr(self, '_original_style', '')
                if base:
                    self.set_background_color(color)
                    # Принудительно убираем скругление при наведении
                    ss = self.styleSheet()
                    if "border-radius" not in ss:
                        self.setStyleSheet(ss + " border-radius: 0px;")
                else:
                    self.setStyleSheet(f'background-color: {color}; border-radius: 0px;')
        except Exception:
            pass

    def leaveEvent(self, event):
        super().leaveEvent(event)
        try:
            base = getattr(self, '_original_style', None)
            # Determine if this widget's content is modified compared to saved value
            modified = False
            try:
                main_win = self.window()
                if hasattr(main_win, 'original_lines') and 0 <= getattr(self, 'index', -1) < len(main_win.original_lines):
                    orig_val = main_win.original_lines[self.index].get('original_translated_text', '')
                    curr = self.toPlainText()
                    modified = (curr != orig_val)
            except Exception:
                modified = False

            if base and not modified:
                # restore full original style only if content is NOT modified
                self.setStyleSheet(base)
            else:
                # if modified, keep current text color but clear hover background
                self.set_background_color('transparent')
        except Exception:
            pass
