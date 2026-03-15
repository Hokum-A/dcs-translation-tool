import os
import sys
import subprocess
import logging
import json
import urllib.request
import zipfile
import shutil
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TTS_Engine")

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

# Реестр доступных голосов Piper (язык -> список словарей моделей)
VOICE_REGISTRY = {
    'ru': [
        {'id': 'ru_RU-dmitri-medium', 'name': 'Dmitri (Medium)'},
        {'id': 'ru_RU-irina-medium', 'name': 'Irina (Medium)'},
        {'id': 'ru_RU-pavel-medium', 'name': 'Pavel (Low)'},
        {'id': 'ru_RU-ruslan-medium', 'name': 'Ruslan (Medium)'},
        {'id': 'ru_RU-denis-medium', 'name': 'Denis (Medium)'}
    ],
    'en': [
        {'id': 'en_US-amy-medium', 'name': 'Amy (US, Medium)'},
        {'id': 'en_US-ryan-medium', 'name': 'Ryan (US, Medium)'},
        {'id': 'en_GB-alba-medium', 'name': 'Alba (GB, Medium)'},
        {'id': 'en_GB-jenny_dioco-medium', 'name': 'Jenny (GB, Medium)'},
        {'id': 'en_GB-alan-medium', 'name': 'Alan (GB, Medium)'}
    ],
    'de': [
        {'id': 'de_DE-thorsten-medium', 'name': 'Thorsten (Medium)'},
        {'id': 'de_DE-eva_k-x_low', 'name': 'Eva (Low)'}
    ],
    'fr': [
        {'id': 'fr_FR-siwis-medium', 'name': 'Siwis (Medium)'},
        {'id': 'fr_FR-upmc-medium', 'name': 'UPMC (Medium)'}
    ],
    'es': [
        {'id': 'es_ES-carlitos-medium', 'name': 'Carlitos (Medium)'},
        {'id': 'es_ES-davefx-medium', 'name': 'DaveFX (Medium)'}
    ],
    'it': [
        {'id': 'it_IT-paola-medium', 'name': 'Paola (Medium)'}
    ],
    'zh': [
        {'id': 'zh_CN-huayan-medium', 'name': 'Huayan (Medium)'}
    ]
}

class TTSEngine:
    """
    Гибридный движок TTS: использует Piper (Нейросеть) если доступен,
    иначе откатывается на системный pyttsx3.
    """
    def __init__(self, base_dir=None):
        if base_dir is None:
            # По умолчанию создаем папку tts рядом со скриптом
            base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tts_data")
        
        self.base_dir = Path(base_dir)
        self.piper_dir = self.base_dir / "piper"
        self.models_dir = self.base_dir / "models"
        
        self.piper_exe = self.piper_dir / "piper.exe"
        
        # Создаем структуру папок
        self.base_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        
        self.use_piper = self._check_piper_available()
        self.system_engine = None
        
        if not self.use_piper:
            self._init_system_engine()

    def _check_piper_available(self):
        """Проверяет наличие исполняемого файла Piper (модели могут скачиваться отдельно)."""
        return self.piper_exe.exists()

    def _init_system_engine(self):
        """Инициализация pyttsx3."""
        if pyttsx3:
            try:
                self.system_engine = pyttsx3.init('sapi5')
                self.system_engine.setProperty('rate', 180)
            except Exception as e:
                logger.error(f"Ошибка SAPI5: {e}")

    def get_installed_voices(self):
        """Возвращает список ID установленных голосов Piper."""
        if not self.models_dir.exists():
            return []
        installed = []
        for file in self.models_dir.glob("*.onnx"):
            installed.append(file.stem) # Имя файла без расширения
        return installed

    def _get_model_path(self, voice_id):
        """Возвращает путь к модели .onnx по её ID."""
        return self.models_dir / f"{voice_id}.onnx"

    def generate_speech(self, text, output_path, lang='ru', voice_id=None, **kwargs):
        """Генерирует речь, выбирая лучший доступный движок.
        
        args:
            voice_id: ID модели Piper (например 'ru_RU-dmitri-medium'). Если None, ищется первая доступная для языка.
        kwargs:
            length_scale: float — длительность фонем (1.0 = норма, <1 = быстрее, >1 = медленнее)
            sentence_silence: float — пауза между предложениями в секундах
            noise_scale: float — вариативность генерации (0.0–1.0)
            noise_w: float — вариативность длительности фонем (0.0–1.0)
        """
        if self._check_piper_available():
            # Если voice_id не указан, берем первый установленный для этого языка
            if not voice_id:
                installed = self.get_installed_voices()
                for v_info in VOICE_REGISTRY.get(lang, []):
                    if v_info['id'] in installed:
                        voice_id = v_info['id']
                        break
            
            # Если модель найдена и существует
            if voice_id and self._get_model_path(voice_id).exists():
                return self._generate_piper(text, output_path, voice_id, **kwargs)
                
        # Фолбэк на системный движок
        return self._generate_system(text, output_path, lang)

    def _generate_piper(self, text, output_path, voice_id, **kwargs):
        """Генерация через нейросеть Piper."""
        try:
            model_path = self._get_model_path(voice_id)
            command = [
                str(self.piper_exe),
                "--model", str(model_path),
                "--output_file", str(output_path)
            ]
            
            # Добавляем опциональные параметры
            if 'length_scale' in kwargs:
                command.extend(["--length_scale", str(kwargs['length_scale'])])
            if 'sentence_silence' in kwargs:
                command.extend(["--sentence_silence", str(kwargs['sentence_silence'])])
            if 'noise_scale' in kwargs:
                command.extend(["--noise_scale", str(kwargs['noise_scale'])])
            if 'noise_w' in kwargs:
                command.extend(["--noise_w", str(kwargs['noise_w'])])
            
            # Запускаем без создания окна консоли на Windows
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                text=True,
                encoding='utf-8'
            )
            
            stdout, stderr = process.communicate(input=text)
            
            if process.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Piper: Аудио создано: {output_path}")
                return True
            else:
                logger.error(f"Piper error: {stderr}")
                return False
        except Exception as e:
            logger.error(f"Piper exception: {e}")
            return False


    def _generate_system(self, text, output_path, lang='ru'):
        """Запасной вариант через системный голос."""
        if not self.system_engine:
            return False
        try:
            # Настройка голоса
            voices = self.system_engine.getProperty('voices')
            target = "russian" if lang == 'ru' else "english"
            for v in voices:
                if target in v.name.lower():
                    self.system_engine.setProperty('voice', v.id)
                    break
            
            self.system_engine.save_to_file(text, output_path)
            self.system_engine.runAndWait()
            return os.path.exists(output_path)
        except Exception as e:
            logger.error(f"System TTS error: {e}")
            return False

    # ─── Система загрузки ─────────────────────────────────────────────

    def download_piper_components(self, progress_callback=None):
        """ Скачивает Piper движок (без моделей). """
        try:
            # 1. Скачиваем Piper (Win x64) — Windows-сборка только в релизе 2023.11.14-2
            piper_url = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
            zip_path = self.base_dir / "piper.zip"
            
            logger.info("Скачивание Piper...")
            if not self._download_file(piper_url, zip_path, "Piper engine", progress_callback):
                return False
            
            # Проверяем, что скачанный файл — валидный ZIP
            if not zipfile.is_zipfile(zip_path):
                logger.error(f"Скачанный файл не является ZIP-архивом: {zip_path}")
                os.remove(zip_path)
                return False
            
            logger.info("Распаковка...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.base_dir)
            
            # После распаковки Github-релиза внутри может быть вложенная папка 'piper'.
            # Если она называется иначе (например 'piper_windows_amd64'), переименуем.
            if not self.piper_exe.exists():
                for d in self.base_dir.iterdir():
                    if d.is_dir() and d.name != "models" and d != self.piper_dir:
                        # Ищем piper.exe рекурсивно
                        found_exe = list(d.rglob("piper.exe"))
                        if found_exe:
                            if self.piper_dir.exists():
                                shutil.rmtree(self.piper_dir)
                            # Если exe лежит прямо в папке d — переименовываем d
                            if found_exe[0].parent == d:
                                shutil.move(str(d), str(self.piper_dir))
                            else:
                                # Если он вложен глубже — перемещаем ту папку
                                shutil.move(str(found_exe[0].parent), str(self.piper_dir))
                                # Удаляем пустую внешнюю папку
                                if d.exists():
                                    shutil.rmtree(d, ignore_errors=True)
                            break

            # Удаляем архив
            if zip_path.exists():
                os.remove(zip_path)
                
            self.use_piper = self._check_piper_available()
            return self.use_piper
        except Exception as e:
            logger.error(f"Download orchestration failed: {e}", exc_info=True)
            return False

    def download_voice(self, voice_id, progress_callback=None):
        """Скачивает конкретную модель голоса (.onnx и .json) с HuggingFace."""
        try:
            # Парсим voice_id: пример ru_RU-dmitri-medium
            parts = voice_id.split('-')
            if len(parts) < 3:
                return False
            
            lang_code = parts[0] # ru_RU
            base_lang = lang_code.split('_')[0] # ru
            name = parts[1] # dmitri
            quality = parts[2] # medium (или x_low / low)
            
            # Особые случаи URL для Piper (HuggingFace structure)
            # https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx
            model_base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{base_lang}/{lang_code}/{name}/{quality}/"
            model_files = [f"{voice_id}.onnx", f"{voice_id}.onnx.json"]
            
            for f_name in model_files:
                logger.info(f"Скачивание файла {f_name}...")
                if not self._download_file(model_base_url + f_name, self.models_dir / f_name, f"Model {f_name}", progress_callback):
                    # Откат в случае ошибки - удаляем недокачанное
                    for file_to_delete in model_files:
                        path = self.models_dir / file_to_delete
                        if path.exists():
                            os.remove(path)
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to download voice {voice_id}: {e}")
            return False

    def _download_file(self, url, dest, label, external_callback=None):
        """Надежный метод загрузки файла с поддержкой заголовков и SSL."""
        import ssl
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, context=ctx, timeout=60) as response:
                total_size = int(response.getheader('Content-Length', 0))
                block_size = 8192
                read_so_far = 0
                
                with open(dest, 'wb') as f:
                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        f.write(buffer)
                        read_so_far += len(buffer)
                        
                        if external_callback and total_size > 0:
                            percent = int(read_so_far * 100 / total_size)
                            external_callback(percent, 1, 100)
                        
            logger.info(f"{label}: загружено {read_so_far} байт")
            return True
        except Exception as e:
            logger.error(f"Download of {label} failed: {e}")
            if os.path.exists(dest):
                os.remove(dest)
            return False
