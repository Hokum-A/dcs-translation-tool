from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QScrollBar, QLineEdit, QCheckBox, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QRect, QEasingCurve, QPoint, pyqtProperty
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QBrush, QPainterPath, QRegion, QTextCursor
from PyQt5.QtCore import QRectF


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

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1


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
            self.start_animation()
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
                color: #000000;
                background-color: transparent;
                border: none;
            }
        ''')
        self._padding = 6
        self._last_radius = 6
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
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
            
            # Рассчитываем радиус скругления
            radius = int(new_h // 2)
            self._last_radius = radius
            
            # Создаем маску для скругленных углов
            path = QPainterPath()
            path.addRoundedRect(QRectF(0.0, 0.0, float(new_w), float(new_h)), float(radius), float(radius))
            region = QRegion(path.toFillPolygon().toPolygon())
            self.setMask(region)
            
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
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            rect = self.rect()
            radius = max(1, int(getattr(self, '_last_radius', 6)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor('#ff9900')))
            painter.drawRoundedRect(rect, radius, radius)
            painter.setPen(QColor('#000000'))
            padding = getattr(self, '_padding', 6)
            text_rect = rect.adjusted(padding, padding, -padding, -padding)
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
            self.start_animation()
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

