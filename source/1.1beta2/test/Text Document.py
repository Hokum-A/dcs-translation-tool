import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor


class FileTableWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Таблица файлов – тёмная тема")
        self.resize(800, 400)

        # Центральный виджет и компоновка
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создаём таблицу: 20 строк, 3 колонки
        self.table = QTableWidget(20, 3)
        self.table.setHorizontalHeaderLabels(["Имя файла", "Размер (байт)", "Дата изменения"])

        # Растягиваем последнюю колонку на всё доступное место
        self.table.horizontalHeader().setStretchLastSection(True)

        # Разрешаем пользователю менять ширину колонок
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        # Заполняем таблицу примерами
        for row in range(20):
            # Имя файла
            self.table.setItem(row, 0, QTableWidgetItem(f"file_{row:03d}.txt"))
            # Размер (случайный)
            size = (row * 1234) % 50000 + 100
            self.table.setItem(row, 1, QTableWidgetItem(str(size)))
            # Дата (пример)
            self.table.setItem(row, 2, QTableWidgetItem(f"2026-02-{row+10:02d}"))

        # Добавляем таблицу на слой
        layout.addWidget(self.table)


def apply_dark_theme(app):
    """Устанавливает тёмную палитру для всего приложения"""
    dark_palette = QPalette()

    # Основные цвета
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Highlight, QColor(142, 45, 197).lighter())
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(dark_palette)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Включаем современный стиль Fusion (лучше сочетается с тёмной палитрой)
    app.setStyle("Fusion")
    apply_dark_theme(app)

    window = FileTableWindow()
    window.show()

    sys.exit(app.exec_())