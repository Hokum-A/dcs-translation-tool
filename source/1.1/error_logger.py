import logging
from datetime import datetime


class ErrorLogger:
    """Класс для логгирования ошибок в файл"""

    LOG_FILE = "translation_tool_errors.log"
    ENABLED = True  # Глобальный флаг управления логами

    @staticmethod
    def setup():
        """Настройка системы логгирования (вызывается при старте и смене настроек)"""
        logger = logging.getLogger()
        
        # Очищаем старые хендлеры, чтобы не дублировать их при повторном вызове
        while logger.hasHandlers():
            logger.removeHandler(logger.handlers[0])
            
        handlers = [logging.StreamHandler()]
        if ErrorLogger.ENABLED:
            try:
                handlers.append(logging.FileHandler(ErrorLogger.LOG_FILE, encoding='utf-8'))
            except Exception:
                pass
                
        # Настраиваем форматтер сразу для всех хендлеров
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        for h in handlers:
            h.setFormatter(formatter)
            logger.addHandler(h)
            
        logger.setLevel(logging.ERROR)

    @staticmethod
    def log_error(error_type, error_message, details=""):
        """Запись ошибки в лог"""
        if not ErrorLogger.ENABLED:
            return

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
    def log_audio_change(action, key, filename, folder, details=""):
        """Логирование изменений аудиофайлов (замена, удаление)"""
        if not ErrorLogger.ENABLED:
            return

        audio_log_file = "translation_tool_audio_changes.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"[{timestamp}] {action.upper()} | Key: {key} | File: {filename} | Folder: {folder}"
        if details:
            log_entry += f" | Details: {details}"
        log_entry += "\n"
        
        try:
            with open(audio_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            # Также выведем в консоль для видимости
            print(f"📁 AUDIO LOG: {log_entry.strip()}")
        except Exception as e:
            print(f"⚠ Не удалось записать лог аудиофайла: {e}")

    @staticmethod
    def log_debug(message):
        """Логирование DEBUG информации в файл для отладки"""
        if not ErrorLogger.ENABLED:
            return

        debug_log_file = "translation_tool_debug.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # С миллисекундами
        
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            with open(debug_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            # Также выведем в консоль
            print(log_entry.strip())
        except Exception as e:
            print(f"⚠ Не удалось записать DEBUG лог: {e}")

    @staticmethod
    def get_recent_errors(count=10):
        """Получить последние ошибки из лога"""
        try:
            with open(ErrorLogger.LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-count*15:]
        except:
            return ["Лог-файл не найден или пуст"]

