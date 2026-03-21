import os
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QAbstractItemView, QApplication,
    QStyle, QSlider, QFrame, QStyledItemDelegate, QStyleOptionViewItem, QMenu
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize, QRect, QPoint, QModelIndex, QEvent
from PyQt5.QtGui import QColor, QFont, QCursor, QIcon, QPainter, QPen
from widgets import (
    CheckboxHeader, ToolTipFilter, ButtonToolTipFilter, CustomScrollBar,
    FileManagerStyle, SortableTableWidgetItem, NaturalSortTableWidgetItem
)

from localization import get_translation


logger = logging.getLogger(__name__)

class ColorKeepingDelegate(QStyledItemDelegate):
    """Делегат, который сохраняет ForegroundRole (цвет текста) при выделении."""
    def initStyleOption(self, option, index):
        if option.state & QStyle.State_Selected:
            fg = index.data(Qt.ForegroundRole)
            if fg:
                color = fg.color() if hasattr(fg, 'color') else fg
                option.palette.setColor(option.palette.HighlightedText, color)
            
            # [FIX] Гарантируем, что текст не станет черным при потере фокуса (State_Active)
            if not (option.state & QStyle.State_Active):
                option.palette.setColor(option.palette.Highlight, QColor("#3d4256"))
        
        super().initStyleOption(option, index)

class FilenameDelegate(ColorKeepingDelegate):
    """Делегат для отрисовки имени файла с приглушенным расширением."""
    def paint(self, painter, option, index):
        if not index.isValid():
            return

        painter.save()
        
        # Настройка состояния
        self.initStyleOption(option, index)
        # Очищаем текст в опции, чтобы стандартный метод его не рисовал (CE_ItemViewItem)
        option.text = ""
        
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, option, painter, option.widget)

        # Отрисовка текста поверх фона
        text = index.data(Qt.DisplayRole) or ""
        rect = option.rect.adjusted(5, 0, -5, 0) # Отступы
        
        # Определяем основной цвет текста из палитры (уже настроенной в initStyleOption)
        base_color = option.palette.text().color()
        if option.state & QStyle.State_Selected:
            base_color = option.palette.highlightedText().color()

        # Разделяем имя и расширение
        name, ext = os.path.splitext(text)
        
        painter.setFont(option.font)
        fm = painter.fontMetrics()
        
        # Рисуем имя основным цветом
        painter.setPen(base_color)
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, name)
        
        # Рисуем расширение серым цветом
        if ext:
            name_width = fm.horizontalAdvance(name)
            ext_rect = rect.adjusted(name_width + 4, 0, 0, 0) # +4px как в manager.py
            painter.setPen(QColor("#888888"))
            painter.drawText(ext_rect, Qt.AlignLeft | Qt.AlignVCenter, ext)

        painter.restore()

class AudioPlaylistWidget(QWidget):
    """Виджет со списком аудиофайлов миссии (таблица в стиле FileManagerWidget)."""

    # Сигнал: пользователь кликнул по файлу (res_key)
    file_clicked = pyqtSignal(str)
    # Сигнал: пользователь дважды кликнул по файлу (res_key)
    file_double_clicked = pyqtSignal(str)
    # Сигнал: запрос остановки воспроизведения
    stop_requested = pyqtSignal()
    # Сигнал: файл выбран (res_key, filename)
    file_selected = pyqtSignal(str, str)
    # Сигнал: переход к ключу в основном редакторе
    editor_jump_requested = pyqtSignal(str) # (dict_key)
    # Сигнал: запрос замены файла (res_key)
    replace_requested = pyqtSignal(str)
    # Сигнал: запрос сохранения на диск (res_key)
    download_requested = pyqtSignal(str)
    # Сигнал: изменился набор выделенных ключей
    checked_keys_changed = pyqtSignal(set)

    def __init__(self, current_language, parent=None, shared_duration_cache=None, show_checkboxes=True, show_link_column=True):
        super().__init__(parent)
        self.current_language = current_language
        self.show_checkboxes = show_checkboxes
        self.show_link_column = show_link_column
        self.shared_duration_cache = shared_duration_cache
        
        # Индексы колонок (динамические)
        current_col = 0
        
        if self.show_checkboxes:
            self.COL_CHECK = current_col
            current_col += 1
        else:
            self.COL_CHECK = -1
            
        if self.show_link_column:
            self.COL_LINK = current_col
            current_col += 1
        else:
            self.COL_LINK = -1
            
        self.COL_FILENAME = current_col; current_col += 1
        self.COL_GENERATED = current_col; current_col += 1
        self.COL_INFO = current_col; current_col += 1
        self.COL_STATUS = current_col; current_col += 1
        
        self.total_cols = current_col

        self._duration_cache = shared_duration_cache if shared_duration_cache is not None else {}
        # print(f"DEBUG: AudioPlaylistWidget init. Cache size: {len(self._duration_cache)}")
        self._all_audio_files = []  # Данные аудиофайлов
        self._first_load = True     # Флаг для первой автоматической сортировки
        self._current_sort_col = self.COL_FILENAME
        self._current_sort_order = Qt.AscendingOrder
        self.checked_keys = set()
        self._last_checked_row = None
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(0)

        # ─── Таблица аудиофайлов ───
        self.table = QTableWidget()
        self.table.setColumnCount(self.total_cols)

        # Вертикальный заголовок (нумерация)
        v_header = self.table.verticalHeader()
        v_header.setVisible(True)
        v_header.setDefaultSectionSize(26)
        v_header.setMinimumWidth(35)
        v_header.setHighlightSections(False)
        v_header.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        v_header.setSectionResizeMode(QHeaderView.Fixed)

        # Кастомный заголовок с чекбоксом в первой колонке (только если нужно)
        if self.show_checkboxes:
            self.table.setHorizontalHeader(CheckboxHeader(Qt.Horizontal, self.table))
        
        # Заголовки колонок
        self._update_table_headers()

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False) # [NEW] Ручная сортировка
        self.table.setShowGrid(False)
        self.table.setMouseTracking(True)
        self.table.viewport().setMouseTracking(True)
        
        # Контекстное меню
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Настройка колонок
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.setSortIndicator(self._current_sort_col, self._current_sort_order) # [NEW] Начальный индикатор
        header.sectionClicked.connect(self._on_header_clicked)
        # Устанавливаем фильтр событий на заголовок для кастомных тултипов
        header.installEventFilter(self)
        header.setSectionResizeMode(self.COL_FILENAME, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_GENERATED, QHeaderView.Fixed)

        if self.show_checkboxes:
            self.table.setColumnWidth(self.COL_CHECK, 50)
        self.table.setColumnWidth(self.COL_LINK, 35)
        self.table.setColumnWidth(self.COL_GENERATED, 80 if self.show_checkboxes else 30)
        self.table.setColumnWidth(self.COL_INFO, 80)
        self.table.setColumnWidth(self.COL_STATUS, 70)

        # Скрываем колонку генерации в обычном плеере
        if not self.show_checkboxes:
            self.table.hideColumn(self.COL_GENERATED)

        # Применяем общий стиль к таблице
        self.table.setStyle(FileManagerStyle())

        # Стиль таблицы (тёмная тема, как в FileManagerWidget)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                color: #ffffff;
                border: none;
                border-radius: 0;
                gridline-color: transparent;
                font-size: 12px;
                outline: 0;
            }
            QTableWidget::item {
                padding: 3px 5px;
                border-bottom: 1px solid #2d2d30;
            }
            QTableWidget::item:selected {
                background-color: #3d4256;
            }
            QTableWidget::item:selected:!active {
                background-color: #3d4256;
            }
            QHeaderView {
                background-color: #1e1e1e;
            }
            QHeaderView::section:horizontal {
                background-color: #2b2d30;
                color: #ff9900;
                padding: 5px 8px;
                border: none;
                border-bottom: 1px solid #ff9900;
                font-weight: bold;
                font-size: 12px;
            }
            QHeaderView::section:vertical {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
                border-right: 1px solid #3d4256;
                padding-right: 4px;
                font-size: 12px;
            }
            QHeaderView::option {
                background-color: transparent;
            }
            QTableCornerButton::section {
                background-color: #2b2d30;
                border: none;
                border-bottom: 1px solid #ff9900;
            }
        """)

        # [FIX] Скроллбары (используем виджеты из widgets.py для корректных отступов)
        self.table.setVerticalScrollBar(CustomScrollBar())
        self.table.setHorizontalScrollBar(CustomScrollBar())

        # Фирменные тултипы
        self._tooltip_filter = ToolTipFilter(self.table, self)
        self._btn_tooltip_filter = ButtonToolTipFilter(self._tooltip_filter.custom_tooltip, self)

        # Кэш и очередь для длительностей (как в manager.py)
        # _duration_cache уже инициализирован в __init__ из shared_duration_cache
        self._duration_queue = []
        self._duration_timer = QTimer(self)
        self._duration_timer.setSingleShot(True)
        self._duration_timer.timeout.connect(self._process_duration_queue)

        # Выбор аудио по одному клику / навигация стрелочками
        self.table.currentCellChanged.connect(self._on_cell_changed)
        # Клик по ячейке (для индикатора связи)
        self.table.cellClicked.connect(self._on_cell_clicked)
        # Двойной клик по строке
        self.table.doubleClicked.connect(self._on_table_double_click)
        # Enter для воспроизведения как двойной клик
        self.table.keyPressEvent = self._table_key_press_event
        # Отслеживание выделения для оранжевого текста
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        if self.show_checkboxes:
            self.table.itemChanged.connect(self._on_item_changed)
            self.table.viewport().installEventFilter(self)

        # Применяем делегаты
        self.color_delegate = ColorKeepingDelegate(self.table)
        self.filename_delegate = FilenameDelegate(self.table)
        
        for col in range(self.table.columnCount()):
            if col == self.COL_FILENAME:
                self.table.setItemDelegateForColumn(col, self.filename_delegate)
            else:
                self.table.setItemDelegateForColumn(col, self.color_delegate)

        layout.addWidget(self.table)

        # ─── Статусная строка (общее время) ───
        self.status_widget = QWidget()
        self.status_widget.setFixedHeight(24)
        self.status_widget.setStyleSheet("background-color: #2b2d30; border-top: 1px solid #444;")
        status_layout = QHBoxLayout(self.status_widget)
        status_layout.setContentsMargins(10, 0, 10, 0)
        status_layout.setSpacing(0)

        self.lbl_total_duration = QLabel("")
        self.lbl_total_duration.setStyleSheet("color: #aaaaaa; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        status_layout.addStretch()
        status_layout.addWidget(self.lbl_total_duration)

        layout.addWidget(self.status_widget)

    def _process_duration_queue(self):
        """Фоновая обработка длительности аудио (копия логики из manager.py)."""
        try:
            if not self or not self._duration_queue:
                return
                
            orig_row, res_key, filename = self._duration_queue.pop(0)
            
            # Находим актуальную строку (она могла сместиться из-за сортировки)
            row = -1
            for r in range(self.table.rowCount()):
                it = self.table.item(r, self.COL_FILENAME)
                if it and it.data(Qt.UserRole) == res_key:
                    row = r
                    break
            
            if row == -1:
                # logger.debug(f"Duration extraction: row not found for {res_key}, skipping.")
                if self._duration_queue: self._duration_timer.start(50)
                return

            try:
                # В плейлисте они передаются через диалог AudioPlayerDialog
                parent_dlg = self.window()
                miz_manager = getattr(parent_dlg, 'miz_resource_manager', None)
                miz_path = getattr(parent_dlg, 'current_miz_path', None)
                
                if not miz_manager or not miz_path:
                    # Фоллбек на экземпляр приложения (на всякий случай)
                    main_win = QApplication.instance().activeWindow()
                    miz_path = getattr(main_win, 'current_miz_path', None)
                    miz_manager = getattr(main_win, 'miz_resource_manager', None)
                    
                # Обновляем статусную строку после каждого вычисления длительности
                # (вызываем в конце, даже если произошла ошибка — чтобы не пропускать обновления)

                if miz_manager and miz_path:
                    temp_path = miz_manager.extract_resource_to_temp(miz_path, res_key)
                    duration = 0
                    if temp_path and os.path.exists(temp_path):
                        import pygame
                        if not pygame.mixer.get_init():
                            pygame.mixer.init()
                        sound = pygame.mixer.Sound(temp_path)
                        duration = sound.get_length()
                        del sound
                    else:
                        logger.warning(f"Duration extraction failed: extracted file not found at {temp_path}")
                    
                    info_item = self.table.item(row, self.COL_INFO)
                    if info_item:
                        m = int(duration // 60)
                        s = int(duration % 60)
                        duration_text = f"{m:02}:{s:02}"
                        info_item.setText(duration_text)
                        info_item.sort_value = duration
                        self._duration_cache[res_key] = (duration, duration_text)
                        # print(f"DEBUG: Duration cached for {res_key}: {duration_text}")

            except Exception as e:
                logger.error(f"Error processing duration for {filename}: {e}")
                
            if self._duration_queue:
                self._duration_timer.start(50)
            else:
                self._update_total_duration()
        except RuntimeError:
            return

    def eventFilter(self, obj, event):
        """Перехват событий для реализации Shift+Click."""
        if obj == self.table.viewport():
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
                                self.checked_keys_changed.emit(set(self.checked_keys))
                                event.accept()
                                return True
                            else:
                                self._last_checked_row = row
            return False
            
        elif obj == self.table.horizontalHeader():
            if event.type() == QEvent.ToolTip:
                pos = event.pos()
                logical_index = self.table.horizontalHeader().logicalIndexAt(pos)
                if self.show_link_column and logical_index == self.COL_LINK:
                    text = get_translation(self.current_language, 'fm_tooltip_has_link')
                    header = self.table.horizontalHeader()
                    rect = QRect(header.sectionViewportPosition(logical_index), 0, 
                                 header.sectionSize(logical_index), header.height())
                    global_rect = QRect(header.mapToGlobal(rect.topLeft()), rect.size())
                    if hasattr(self, '_tooltip_filter'):
                        self._tooltip_filter.custom_tooltip.show_tooltip_at_rect(text, global_rect, side='top')
                    return True
                else:
                    if hasattr(self, '_tooltip_filter'):
                        self._tooltip_filter.custom_tooltip.hide()
            elif event.type() in (QEvent.Leave, QEvent.MouseButtonPress):
                if hasattr(self, '_tooltip_filter'):
                    self._tooltip_filter.custom_tooltip.hide()
            return False
            
        return super().eventFilter(obj, event)

    def _on_table_selection_changed(self):
        """Обновляет цвета текста при смене выделения (Имя и Описание становятся оранжевыми)."""
        selection_model = self.table.selectionModel()
        for row in range(self.table.rowCount()):
            # Проверяем, выделена ли строка
            is_selected = selection_model.isRowSelected(row, QModelIndex())
            
            # Колонки для обновления (только Имя файла)
            cols_to_update = [self.COL_FILENAME]
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
            
            # Принудительно обновляем статус (чтобы не был белым)
            status_item = self.table.item(row, self.COL_STATUS)
            if status_item:
                scolor = status_item.data(Qt.UserRole + 3)
                if scolor:
                    status_item.setForeground(QColor(scolor))

    def _update_table_headers(self):
        """Обновляет заголовки таблицы из локализации."""
        lang = self.current_language
        headers = []
        if self.show_checkboxes:
            headers.append("") # COL_CHECK
        
        if self.show_link_column:
            headers.append(get_translation(lang, 'fm_col_link'))
        
        gen_title = get_translation(lang, 'fm_col_gen_duration') if self.show_checkboxes else ""
        info_title = get_translation(lang, 'fm_col_orig_duration') if self.show_checkboxes else get_translation(lang, 'fm_col_info')
        
        headers.extend([
            get_translation(lang, 'fm_col_filename'),
            gen_title,
            info_title,
            get_translation(lang, 'fm_col_status'),
        ])
        self.table.setHorizontalHeaderLabels(headers)
        
        # Подключаем клик по заголовку для "Выбрать все"
        if self.show_checkboxes:
            header = self.table.horizontalHeader()
            if isinstance(header, CheckboxHeader):
                try:
                    header.checkboxToggled.disconnect()
                except Exception: pass
                header.checkboxToggled.connect(self._on_header_checkbox_toggled)

    def _show_context_menu(self, pos):
        """Отображает контекстное меню для элементов плейлиста."""
        index = self.table.indexAt(pos)
        if not index.isValid():
            return

        row = index.row()
        name_item = self.table.item(row, self.COL_FILENAME)
        if not name_item:
            return

        res_key = name_item.data(Qt.UserRole)
        if not res_key:
            return

        menu = QMenu(self)
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
                border_radius: 3px;
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

        # 1. Сохранить на диск
        save_action = menu.addAction(get_translation(self.current_language, 'fm_tooltip_download'))

        action = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if action == save_action:
            self.download_requested.emit(res_key)

    def _on_header_checkbox_toggled(self, new_state):
        """Обработка переключения чекбокса в заголовке."""
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            it = self.table.item(r, self.COL_CHECK)
            if it:
                it.setCheckState(new_state)
                # Синхронизируем checked_keys
                key = it.data(Qt.UserRole)
                if key:
                    if new_state == Qt.Checked:
                        self.checked_keys.add(key)
                    else:
                        self.checked_keys.discard(key)
        self.table.blockSignals(False)
        self._update_header_checkbox()
        self.checked_keys_changed.emit(set(self.checked_keys))

    def _on_item_changed(self, item):
        """Отслеживает ручное переключение чекбоксов."""
        if item.column() == self.COL_CHECK:
            key = item.data(Qt.UserRole)
            if not key: return
            
            if item.checkState() == Qt.Checked:
                self.checked_keys.add(key)
                item.sort_value = 1
            else:
                self.checked_keys.discard(key)
                item.sort_value = 0
            
            self._update_header_checkbox()
            self.checked_keys_changed.emit(set(self.checked_keys))

    def _update_header_checkbox(self):
        """Обновляет состояние чекбокса в заголовке на основе строк."""
        header = self.table.horizontalHeader()
        if not isinstance(header, CheckboxHeader): return
        
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

    def retranslate_ui(self, current_language):
        """Обновляет переводы виджета."""
        self.current_language = current_language
        self._update_table_headers()
        self._update_total_duration()

    def update_generated_indicator(self, res_key, is_generated, duration_sec=None):
        """Устанавливает или убирает значок 🧠 для указанного файла."""
        for r in range(self.table.rowCount()):
            it = self.table.item(r, self.COL_FILENAME)
            if it and it.data(Qt.UserRole) == res_key:
                gen_item = self.table.item(r, self.COL_GENERATED)
                if gen_item:
                    if is_generated:
                        if duration_sec is not None:
                            m = int(duration_sec // 60)
                            s = int(duration_sec % 60)
                            gen_item.setText(f"🧠 {m:02}:{s:02}")
                            # Сортируем по длительности, чтобы можно было фильтровать по задержке
                            gen_item.sort_value = duration_sec
                        else:
                            gen_item.setText("🧠")
                            gen_item.sort_value = 1
                    else:
                        curr_text = gen_item.text()
                        if "🧠 " in curr_text:
                            gen_item.setText(curr_text.replace("🧠 ", ""))
                        elif curr_text == "🧠":
                            gen_item.setText("")
                            gen_item.sort_value = 0
                break

    def update_duration(self, res_key, duration_sec):
        """Принудительно обновляет длительность для конкретного файла в таблице (например после генерации)."""
        m = int(duration_sec // 60)
        s = int(duration_sec % 60)
        duration_text = f"{m:02}:{s:02}"
        
        # Обновляем кэш
        self._duration_cache[res_key] = (duration_sec, duration_text)
        
        # Обновляем UI
        for r in range(self.table.rowCount()):
            it = self.table.item(r, self.COL_FILENAME)
            if it and it.data(Qt.UserRole) == res_key:
                info_item = self.table.item(r, self.COL_INFO)
                if info_item:
                    info_item.setText(duration_text)
                    info_item.sort_value = duration_sec
                break

    def set_audio_files(self, audio_files):
        """Заполняет таблицу списком аудиофайлов."""
        self.table.blockSignals(True)
        try:
            self._all_audio_files = audio_files
            self._populate_table()
        finally:
            self.table.blockSignals(False)

    def select_file_by_key(self, res_key, auto_play=False):
        """Выделяет строку в таблице по ключу ресурса."""
        self.table.blockSignals(True)
        try:
            for row in range(self.table.rowCount()):
                it = self.table.item(row, self.COL_FILENAME)
                if it and it.data(Qt.UserRole) == res_key:
                    self.table.setCurrentCell(row, self.COL_FILENAME)
                    self.table.selectRow(row)
                    # Прокручиваем к выделенной строке
                    self.table.scrollToItem(it)
                    break
            
            # [NEW] Принудительно вызываем обновление цветов, так как сигналы заблокированы
            self._on_table_selection_changed()
        finally:
            self.table.blockSignals(False)

    def _populate_table(self):
        """Заполняет таблицу данными из _all_audio_files."""
        self.table.blockSignals(True)
        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        
        self.table.setRowCount(0)
        self.table.setRowCount(len(self._all_audio_files))

        self._duration_queue = []

        for row, file_info in enumerate(self._all_audio_files):
            try:
                self._update_row(row, file_info)
            except Exception as e:
                logger.error(f"Error populating playlist row {row}: {e}")
    
        self.table.viewport().setUpdatesEnabled(True)
        self.table.setUpdatesEnabled(True)
        self.table.blockSignals(False)
        
        # Восстанавливаем сортировку или применяем её впервые
        if self._first_load and self.table.rowCount() > 0:
            self.table.setSortingEnabled(True)
            self.table.sortByColumn(self.COL_FILENAME, Qt.AscendingOrder)
            # Синхронизируем внутренние переменные
            self._current_sort_col = self.COL_FILENAME
            self._current_sort_order = Qt.AscendingOrder
            self._first_load = False
        elif getattr(self, '_current_sort_col', -1) >= 0:
            self.table.setSortingEnabled(True)
            self.table.sortByColumn(self._current_sort_col, self._current_sort_order)
            
        if self.show_checkboxes:
            self._update_header_checkbox() # [NEW] Обновляем заголовок после загрузки
        # Гарантируем, что динамическая сортировка выключена, но стрелка видна
        self.table.setSortingEnabled(False)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.viewport().update()
        
        if self._duration_queue:
            self._duration_timer.start(5)
        
        self._update_total_duration()

    def update_item_by_key(self, res_key, file_info):
        """Точечно обновляет одну строку в таблице по ключу ресурса.
        Позволяет избежать перерисовки всей таблицы и потери фокуса/выделения.
        """
        for r in range(self.table.rowCount()):
            it = self.table.item(r, self.COL_FILENAME)
            if it and it.data(Qt.UserRole) == res_key:
                # Обновляем данные в списке _all_audio_files
                for i, info in enumerate(self._all_audio_files):
                    if info.get('res_key') == res_key:
                        self._all_audio_files[i] = file_info
                        break
                
                # Обновляем UI строки
                self.table.blockSignals(True)
                # Сортировка и так отключена, просто обновляем
                self._update_row(r, file_info)
                self.table.blockSignals(False)
                
                # [NEW] После включения сортировки строка могла улететь в другое место.
                # Находим её заново и выделяем, чтобы фокус не пропадал.
                self.select_file_by_key(res_key)
                
                # [FIX] Запускаем таймер для пересчета длительности в фоне, если файл попал в очередь
                if self._duration_queue:
                    self._duration_timer.start(5)
                return True
        return False

    def _update_row(self, row, file_info):
        """Заполняет или обновляет конкретную строку таблицы данными file_info."""
        res_key = file_info.get('res_key', '')
        filename = file_info.get('filename', '')
        in_current = file_info.get('in_current_locale', False)
        link_key = file_info.get('linked_dict_key')
        
        # COL_CHECK — чекбокс
        if self.show_checkboxes:
            is_checked = res_key in self.checked_keys
            cb_item = self.table.item(row, self.COL_CHECK)
            if not cb_item:
                cb_item = SortableTableWidgetItem("", 1 if is_checked else 0)
                cb_item.setCheckState(Qt.Checked if is_checked else Qt.Unchecked)
                self.table.setItem(row, self.COL_CHECK, cb_item)
            else:
                cb_item.setCheckState(Qt.Checked if is_checked else Qt.Unchecked)
                cb_item.sort_value = 1 if is_checked else 0
            cb_item.setData(Qt.UserRole, res_key)
        
        # COL_LINK — наличие связи с текстом
        if self.show_link_column:
            link_item = self.table.item(row, self.COL_LINK)
            if not link_item:
                link_item = SortableTableWidgetItem("", 1 if link_key else 0)
                link_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, self.COL_LINK, link_item)
            else:
                link_item.sort_value = 1 if link_key else 0
                
            if link_key:
                link_item.setText("✔")
                link_item.setForeground(QColor('#888888')) # Нейтральный цвет
                # Тултип теперь на заголовке колонки
                link_item.setToolTip("")
                link_item.setData(Qt.UserRole, link_key)
            else:
                link_item.setText("")
                link_item.setToolTip("")
                link_item.setData(Qt.UserRole, None)
        
        # COL_FILENAME — имя файла
        fname_item = self.table.item(row, self.COL_FILENAME)
        if not fname_item:
            fname_item = NaturalSortTableWidgetItem(filename)
            self.table.setItem(row, self.COL_FILENAME, fname_item)
        else:
            fname_item.setText(filename)
            
        fname_item.setData(Qt.UserRole, res_key)
        
        # Определяем базовый цвет текста (для делегата)
        base_color = '#ffffff'
        fname_item.setData(Qt.UserRole + 3, base_color)
        
        # Если строка выделена, делегат сам покрасит в оранжевый, 
        # но нам нужно инициализировать текущее состояние.
        is_selected = self.table.selectionModel().isRowSelected(row, QModelIndex())
        fname_item.setForeground(QColor('#ff9900' if is_selected else base_color))

        # COL_GENERATED — значок 🧠
        gen_item = self.table.item(row, self.COL_GENERATED)
        if not gen_item:
            gen_item = SortableTableWidgetItem("", 0)
            gen_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, self.COL_GENERATED, gen_item)
            
        gen_item.setForeground(QColor('#888888'))
        gen_item.setData(Qt.UserRole + 3, '#888888')

        # COL_INFO — длительность
        info_text = "⏳"
        sort_val = 0
        if res_key in self._duration_cache:
            sort_val, info_text = self._duration_cache[res_key]
        else:
            self._duration_queue.append((row, res_key, filename))
        
        info_item = self.table.item(row, self.COL_INFO)
        if not info_item:
            info_item = SortableTableWidgetItem(info_text, sort_val)
            info_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, self.COL_INFO, info_item)
        else:
            info_item.setText(info_text)
            info_item.sort_value = sort_val
            
        info_item.setForeground(QColor('#888888'))

        # COL_STATUS — статус
        is_replaced = False
        try:
            parent_dlg = self.window()
            miz_manager = getattr(parent_dlg, 'miz_resource_manager', None)
            if miz_manager:
                is_replaced = miz_manager.is_audio_replaced(res_key)
        except Exception:
            pass

        if is_replaced:
            color = '#ff0000' # Ярко-красный для индикатора замены
            status_tooltip = get_translation(self.current_language, 'fm_status_replaced')
            sort_weight = -1 
        else:
            color = '#33cc33' if in_current else '#999999'
            status_tooltip = get_translation(self.current_language, 'fm_status_in_locale' if in_current else 'fm_status_default_only')
            sort_weight = 0 if in_current else 1

        status_item = self.table.item(row, self.COL_STATUS)
        if not status_item:
            status_item = SortableTableWidgetItem("●", sort_weight)
            status_item.setTextAlignment(Qt.AlignCenter)
            font = status_item.font()
            font.setPointSize(18)
            font.setBold(True)
            status_item.setFont(font)
            self.table.setItem(row, self.COL_STATUS, status_item)
        else:
            status_item.sort_value = sort_weight
            
        status_item.setForeground(QColor(color))
        status_item.setData(Qt.UserRole + 3, color)
        status_item.setToolTip(status_tooltip)


    def _on_cell_changed(self, current_row, current_column, previous_row, previous_column):
        """Обработка выделения файла (ЛКМ или стрелки клавиатуры) - выбирает аудио без автовоспроизведения."""
        if current_row < 0:
            return
            
        name_item = self.table.item(current_row, self.COL_FILENAME)
        if name_item:
            res_key = name_item.data(Qt.UserRole)
            if res_key:
                # Отправляем один универсальный сигнал о смене/выборе
                self.file_clicked.emit(res_key)
    
    def _on_cell_clicked(self, row, col):
        """Обработка клика по ячейке."""
        if self.show_link_column and col == self.COL_LINK:
            item = self.table.item(row, col)
            if item:
                dict_key = item.data(Qt.UserRole)
                if dict_key:
                    # Эмитим сигнал для перехода в редактор
                    self.editor_jump_requested.emit(dict_key)

    def _on_table_double_click(self, index):
        """Обработка двойного клика по строке - запуск воспроизведения."""
        row = index.row()
        name_item = self.table.item(row, self.COL_FILENAME)
        if name_item:
            res_key = name_item.data(Qt.UserRole)
            if res_key:
                self.file_double_clicked.emit(res_key)

    def _on_header_clicked(self, logical_index):
        """Ручная сортировка по клику на заголовок."""
        header = self.table.horizontalHeader()
        
        # Определяем порядок на основе наших переменных (Qt забывает состояние из-за setSortingEnabled)
        if self._current_sort_col == logical_index:
            new_order = Qt.DescendingOrder if self._current_sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            new_order = Qt.AscendingOrder
            
        self._current_sort_col = logical_index
        self._current_sort_order = new_order
            
        # 1. Включаем сортировку временно
        self.table.setSortingEnabled(True)
        
        # 2. Сортируем (Qt сам обновит индикатор)
        self.table.sortByColumn(logical_index, new_order)
        
        # 3. Выключаем постоянную сортировку, но возвращаем видимость стрелки
        self.table.setSortingEnabled(False)
        header.setSortIndicatorShown(True)
                
    def _table_key_press_event(self, event):
        """Перехват нажатия клавиш таблицы для обработки Enter"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            row = self.table.currentRow()
            if row >= 0:
                name_item = self.table.item(row, self.COL_FILENAME)
                if name_item:
                    res_key = name_item.data(Qt.UserRole)
                    if res_key:
                        self.file_double_clicked.emit(res_key)
            event.accept()
            return
        # Вызов стандартного обработчика
        QTableWidget.keyPressEvent(self.table, event)

    def get_file_count(self):
        """Возвращает количество файлов в таблице."""
        return self.table.rowCount()

    def _update_total_duration(self):
        """Пересчитывает и отображает общее время всех аудиофайлов в статусной строке."""
        total_sec = 0
        for r in range(self.table.rowCount()):
            info_item = self.table.item(r, self.COL_INFO)
            if info_item and hasattr(info_item, 'sort_value') and isinstance(info_item.sort_value, (int, float)) and info_item.sort_value > 0:
                total_sec += info_item.sort_value
        
        hours = int(total_sec // 3600)
        mins = int((total_sec % 3600) // 60)
        secs = int(total_sec % 60)
        
        if hours > 0:
            duration_str = f"{hours:02}:{mins:02}:{secs:02}"
        else:
            duration_str = f"{mins:02}:{secs:02}"
        
        if hasattr(self, 'lbl_total_duration'):
            self.lbl_total_duration.setText(
                get_translation(self.current_language, 'playlist_total_duration', duration=duration_str)
            )
