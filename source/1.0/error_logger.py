import logging
from datetime import datetime


class ErrorLogger:
    """Класс для логгирования ошибок в файл"""

    LOG_FILE = "translation_tool_errors.log"

    @staticmethod
    def setup():
        """Настройка системы логгирования"""
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(ErrorLogger.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    @staticmethod
    def log_error(error_type, error_message, details=""):
        """Запись ошибки в лог"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"\n{'='*60}\n"
        log_entry += f"ВРЕМЯ: {timestamp}\n"
        log_entry += f"ТИП ОШИБКИ: {error_type}\n"
        log_entry += f"СООБЩЕНИЕ: {error_message}\n"
        if details:
            log_entry += f"ДЕТАЛИ: {details}\n"
        log_entry += f"{'='*60}\n"

        try:
            with open(ErrorLogger.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"⚠ Не удалось записать лог ошибки: {e}")

        try:
            print(log_entry)
        except UnicodeEncodeError:
            # Фолбэк для систем, где консоль не поддерживает UTF-8 (например, Windows)
            print(log_entry.encode('ascii', 'replace').decode('ascii'))

    @staticmethod
    def get_recent_errors(count=10):
        """Получить последние ошибки из лога"""
        try:
            with open(ErrorLogger.LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-count*15:]
        except:
            return ["Лог-файл не найден или пуст"]
