import os
import sys
import subprocess
import logging
import json
import urllib.request
import zipfile
import shutil
import traceback
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
from localization import get_translation

class TTSWorker(QThread):
    """Воркер для асинхронной генерации речи."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, engine, text, output_path, lang='ru', engine_type='piper', voice_id=None, **kwargs):
        super().__init__()
        self.engine = engine
        self.text = text
        self.output_path = output_path
        self.lang = lang
        self.engine_type = engine_type
        self.voice_id = voice_id
        self.kwargs = kwargs

    def run(self):
        try:
            success = self.engine.generate_speech(
                self.text,
                self.output_path,
                lang=self.lang,
                engine=self.engine_type,
                voice_id=self.voice_id,
                **self.kwargs
            )
            if success and os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 44:
                self.finished.emit(self.output_path)
            else:
                self.error.emit("Empty result: the neural network could not speak this text (possibly unsupported characters)")
        except Exception as e:
            self.error.emit(str(e))

class TTSInitWorker(QThread):
    """Поток для предварительной инициализации библиотек TTS."""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def run(self):
        try:
            # Вызываем проверку/подгрузку библиотек
            self.engine.prepare()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TTS_Engine")

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

# Список стандартных голосов XTTS v2 для проверки
XTTS_STANDARD_VOICES = [
    "Claribel Dervla", "Daisy Studer", "Gracie Wise", "Tammie Ema",
    "Alison Dietlinde", "Ana Maëlle", "Linda Ines", "Nathaniel Robert",
    "Adrawon Hamed", "Abrahan Mack", "Otto Reinhold", "Roosevelt Trajan",
    "Baldur Santeri", "Craig Gutsy", "Damien Sourav"
]

# Реестр доступных голосов Piper (язык -> список словарей моделей)
VOICE_REGISTRY = {
    "ar": [
        {
            "id": "ar_JO-kareem-low",
            "name": "kareem (low)"
        },
        {
            "id": "ar_JO-kareem-medium",
            "name": "kareem (medium)"
        }
    ],
    "bg": [
        {
            "id": "bg_BG-dimitar-medium",
            "name": "dimitar (medium)"
        }
    ],
    "ca": [
        {
            "id": "ca_ES-upc_ona-medium",
            "name": "upc_ona (medium)"
        },
        {
            "id": "ca_ES-upc_ona-x_low",
            "name": "upc_ona (x_low)"
        },
        {
            "id": "ca_ES-upc_pau-x_low",
            "name": "upc_pau (x_low)"
        }
    ],
    "cs": [
        {
            "id": "cs_CZ-jirka-low",
            "name": "jirka (low)"
        },
        {
            "id": "cs_CZ-jirka-medium",
            "name": "jirka (medium)"
        }
    ],
    "cy": [
        {
            "id": "cy_GB-bu_tts-medium",
            "name": "bu_tts (medium)"
        },
        {
            "id": "cy_GB-gwryw_gogleddol-medium",
            "name": "gwryw_gogleddol (medium)"
        }
    ],
    "da": [
        {
            "id": "da_DK-talesyntese-medium",
            "name": "talesyntese (medium)"
        }
    ],
    "de": [
        {
            "id": "de_DE-eva_k-x_low",
            "name": "eva_k (x_low)"
        },
        {
            "id": "de_DE-karlsson-low",
            "name": "karlsson (low)"
        },
        {
            "id": "de_DE-kerstin-low",
            "name": "kerstin (low)"
        },
        {
            "id": "de_DE-mls-medium",
            "name": "mls (medium)"
        },
        {
            "id": "de_DE-pavoque-low",
            "name": "pavoque (low)"
        },
        {
            "id": "de_DE-ramona-low",
            "name": "ramona (low)"
        },
        {
            "id": "de_DE-thorsten-high",
            "name": "thorsten (high)"
        },
        {
            "id": "de_DE-thorsten-low",
            "name": "thorsten (low)"
        },
        {
            "id": "de_DE-thorsten-medium",
            "name": "thorsten (medium)"
        },
        {
            "id": "de_DE-thorsten_emotional-medium",
            "name": "thorsten_emotional (medium)"
        }
    ],
    "el": [
        {
            "id": "el_GR-rapunzelina-low",
            "name": "rapunzelina (low)"
        },
        {
            "id": "el_GR-rapunzelina-medium",
            "name": "rapunzelina (medium)"
        }
    ],
    "en": [
        {
            "id": "en_GB-alan-low",
            "name": "alan (low)"
        },
        {
            "id": "en_GB-alan-medium",
            "name": "alan (medium)"
        },
        {
            "id": "en_GB-alba-medium",
            "name": "alba (medium)"
        },
        {
            "id": "en_US-amy-low",
            "name": "amy (low)"
        },
        {
            "id": "en_US-amy-medium",
            "name": "amy (medium)"
        },
        {
            "id": "en_US-arctic-medium",
            "name": "arctic (medium)"
        },
        {
            "id": "en_GB-aru-medium",
            "name": "aru (medium)"
        },
        {
            "id": "en_US-bryce-medium",
            "name": "bryce (medium)"
        },
        {
            "id": "en_GB-cori-high",
            "name": "cori (high)"
        },
        {
            "id": "en_GB-cori-medium",
            "name": "cori (medium)"
        },
        {
            "id": "en_US-danny-low",
            "name": "danny (low)"
        },
        {
            "id": "en_US-hfc_female-medium",
            "name": "hfc_female (medium)"
        },
        {
            "id": "en_US-hfc_male-medium",
            "name": "hfc_male (medium)"
        },
        {
            "id": "en_GB-jenny_dioco-medium",
            "name": "jenny_dioco (medium)"
        },
        {
            "id": "en_US-joe-medium",
            "name": "joe (medium)"
        },
        {
            "id": "en_US-john-medium",
            "name": "john (medium)"
        },
        {
            "id": "en_US-kathleen-low",
            "name": "kathleen (low)"
        },
        {
            "id": "en_US-kristin-medium",
            "name": "kristin (medium)"
        },
        {
            "id": "en_US-kusal-medium",
            "name": "kusal (medium)"
        },
        {
            "id": "en_US-l2arctic-medium",
            "name": "l2arctic (medium)"
        },
        {
            "id": "en_US-lessac-high",
            "name": "lessac (high)"
        },
        {
            "id": "en_US-lessac-low",
            "name": "lessac (low)"
        },
        {
            "id": "en_US-lessac-medium",
            "name": "lessac (medium)"
        },
        {
            "id": "en_US-libritts-high",
            "name": "libritts (high)"
        },
        {
            "id": "en_US-libritts_r-medium",
            "name": "libritts_r (medium)"
        },
        {
            "id": "en_US-ljspeech-high",
            "name": "ljspeech (high)"
        },
        {
            "id": "en_US-ljspeech-medium",
            "name": "ljspeech (medium)"
        },
        {
            "id": "en_US-norman-medium",
            "name": "norman (medium)"
        },
        {
            "id": "en_GB-northern_english_male-medium",
            "name": "northern_english_male (medium)"
        },
        {
            "id": "en_US-reza_ibrahim-medium",
            "name": "reza_ibrahim (medium)"
        },
        {
            "id": "en_US-ryan-high",
            "name": "ryan (high)"
        },
        {
            "id": "en_US-ryan-low",
            "name": "ryan (low)"
        },
        {
            "id": "en_US-ryan-medium",
            "name": "ryan (medium)"
        },
        {
            "id": "en_US-sam-medium",
            "name": "sam (medium)"
        },
        {
            "id": "en_GB-semaine-medium",
            "name": "semaine (medium)"
        },
        {
            "id": "en_GB-southern_english_female-low",
            "name": "southern_english_female (low)"
        },
        {
            "id": "en_GB-vctk-medium",
            "name": "vctk (medium)"
        }
    ],
    "es": [
        {
            "id": "es_MX-ald-medium",
            "name": "ald (medium)"
        },
        {
            "id": "es_ES-carlfm-x_low",
            "name": "carlfm (x_low)"
        },
        {
            "id": "es_MX-claude-high",
            "name": "claude (high)"
        },
        {
            "id": "es_AR-daniela-high",
            "name": "daniela (high)"
        },
        {
            "id": "es_ES-davefx-medium",
            "name": "davefx (medium)"
        },
        {
            "id": "es_ES-mls_10246-low",
            "name": "mls_10246 (low)"
        },
        {
            "id": "es_ES-mls_9972-low",
            "name": "mls_9972 (low)"
        },
        {
            "id": "es_ES-sharvard-medium",
            "name": "sharvard (medium)"
        }
    ],
    "fa": [
        {
            "id": "fa_IR-amir-medium",
            "name": "amir (medium)"
        },
        {
            "id": "fa_IR-ganji-medium",
            "name": "ganji (medium)"
        },
        {
            "id": "fa_IR-ganji_adabi-medium",
            "name": "ganji_adabi (medium)"
        },
        {
            "id": "fa_IR-gyro-medium",
            "name": "gyro (medium)"
        },
        {
            "id": "fa_IR-reza_ibrahim-medium",
            "name": "reza_ibrahim (medium)"
        }
    ],
    "fi": [
        {
            "id": "fi_FI-harri-low",
            "name": "harri (low)"
        },
        {
            "id": "fi_FI-harri-medium",
            "name": "harri (medium)"
        }
    ],
    "fr": [
        {
            "id": "fr_FR-gilles-low",
            "name": "gilles (low)"
        },
        {
            "id": "fr_FR-mls-medium",
            "name": "mls (medium)"
        },
        {
            "id": "fr_FR-mls_1840-low",
            "name": "mls_1840 (low)"
        },
        {
            "id": "fr_FR-siwis-low",
            "name": "siwis (low)"
        },
        {
            "id": "fr_FR-siwis-medium",
            "name": "siwis (medium)"
        },
        {
            "id": "fr_FR-tom-medium",
            "name": "tom (medium)"
        },
        {
            "id": "fr_FR-upmc-medium",
            "name": "upmc (medium)"
        }
    ],
    "hi": [
        {
            "id": "hi_IN-pratham-medium",
            "name": "pratham (medium)"
        },
        {
            "id": "hi_IN-priyamvada-medium",
            "name": "priyamvada (medium)"
        },
        {
            "id": "hi_IN-rohan-medium",
            "name": "rohan (medium)"
        }
    ],
    "hu": [
        {
            "id": "hu_HU-anna-medium",
            "name": "anna (medium)"
        },
        {
            "id": "hu_HU-berta-medium",
            "name": "berta (medium)"
        },
        {
            "id": "hu_HU-imre-medium",
            "name": "imre (medium)"
        }
    ],
    "id": [
        {
            "id": "id_ID-news_tts-medium",
            "name": "news_tts (medium)"
        }
    ],
    "is": [
        {
            "id": "is_IS-bui-medium",
            "name": "bui (medium)"
        },
        {
            "id": "is_IS-salka-medium",
            "name": "salka (medium)"
        },
        {
            "id": "is_IS-steinn-medium",
            "name": "steinn (medium)"
        },
        {
            "id": "is_IS-ugla-medium",
            "name": "ugla (medium)"
        }
    ],
    "it": [
        {
            "id": "it_IT-paola-medium",
            "name": "paola (medium)"
        },
        {
            "id": "it_IT-riccardo-x_low",
            "name": "riccardo (x_low)"
        }
    ],
    "ka": [
        {
            "id": "ka_GE-natia-medium",
            "name": "natia (medium)"
        }
    ],
    "kk": [
        {
            "id": "kk_KZ-iseke-x_low",
            "name": "iseke (x_low)"
        },
        {
            "id": "kk_KZ-issai-high",
            "name": "issai (high)"
        },
        {
            "id": "kk_KZ-raya-x_low",
            "name": "raya (x_low)"
        }
    ],
    "lb": [
        {
            "id": "lb_LU-marylux-medium",
            "name": "marylux (medium)"
        }
    ],
    "lv": [
        {
            "id": "lv_LV-aivars-medium",
            "name": "aivars (medium)"
        }
    ],
    "ml": [
        {
            "id": "ml_IN-arjun-medium",
            "name": "arjun (medium)"
        },
        {
            "id": "ml_IN-meera-medium",
            "name": "meera (medium)"
        }
    ],
    "ne": [
        {
            "id": "ne_NP-chitwan-medium",
            "name": "chitwan (medium)"
        },
        {
            "id": "ne_NP-google-medium",
            "name": "google (medium)"
        },
        {
            "id": "ne_NP-google-x_low",
            "name": "google (x_low)"
        }
    ],
    "nl": [
        {
            "id": "nl_NL-alex-medium",
            "name": "alex (medium)"
        },
        {
            "id": "nl_NL-mls-medium",
            "name": "mls (medium)"
        },
        {
            "id": "nl_NL-mls_5809-low",
            "name": "mls_5809 (low)"
        },
        {
            "id": "nl_NL-mls_7432-low",
            "name": "mls_7432 (low)"
        },
        {
            "id": "nl_BE-nathalie-medium",
            "name": "nathalie (medium)"
        },
        {
            "id": "nl_BE-nathalie-x_low",
            "name": "nathalie (x_low)"
        },
        {
            "id": "nl_NL-pim-medium",
            "name": "pim (medium)"
        },
        {
            "id": "nl_BE-rdh-medium",
            "name": "rdh (medium)"
        },
        {
            "id": "nl_BE-rdh-x_low",
            "name": "rdh (x_low)"
        },
        {
            "id": "nl_NL-ronnie-medium",
            "name": "ronnie (medium)"
        }
    ],
    "no": [
        {
            "id": "no_NO-nvcc-medium",
            "name": "nvcc (medium)"
        },
        {
            "id": "no_NO-talesyntese-medium",
            "name": "talesyntese (medium)"
        }
    ],
    "pl": [
        {
            "id": "pl_PL-bass-high",
            "name": "bass (high)"
        },
        {
            "id": "pl_PL-darkman-medium",
            "name": "darkman (medium)"
        },
        {
            "id": "pl_PL-gosia-medium",
            "name": "gosia (medium)"
        },
        {
            "id": "pl_PL-mc_speech-medium",
            "name": "mc_speech (medium)"
        },
        {
            "id": "pl_PL-mls_6892-low",
            "name": "mls_6892 (low)"
        }
    ],
    "pt": [
        {
            "id": "pt_BR-cadu-medium",
            "name": "cadu (medium)"
        },
        {
            "id": "pt_BR-edresson-low",
            "name": "edresson (low)"
        },
        {
            "id": "pt_BR-faber-medium",
            "name": "faber (medium)"
        },
        {
            "id": "pt_BR-jeff-medium",
            "name": "jeff (medium)"
        },
        {
            "id": "pt_PT-tugão-medium",
            "name": "tugão (medium)"
        }
    ],
    "ro": [
        {
            "id": "ro_RO-mihai-medium",
            "name": "mihai (medium)"
        }
    ],
    "ru": [
        {
            "id": "ru_RU-denis-medium",
            "name": "denis (medium)"
        },
        {
            "id": "ru_RU-dmitri-medium",
            "name": "dmitri (medium)"
        },
        {
            "id": "ru_RU-irina-medium",
            "name": "irina (medium)"
        },
        {
            "id": "ru_RU-ruslan-medium",
            "name": "ruslan (medium)"
        }
    ],
    "sk": [
        {
            "id": "sk_SK-lili-medium",
            "name": "lili (medium)"
        }
    ],
    "sl": [
        {
            "id": "sl_SI-artur-medium",
            "name": "artur (medium)"
        }
    ],
    "sr": [
        {
            "id": "sr_RS-serbski_institut-medium",
            "name": "serbski_institut (medium)"
        }
    ],
    "sv": [
        {
            "id": "sv_SE-alma-medium",
            "name": "alma (medium)"
        },
        {
            "id": "sv_SE-lisa-medium",
            "name": "lisa (medium)"
        },
        {
            "id": "sv_SE-nst-medium",
            "name": "nst (medium)"
        }
    ],
    "sw": [
        {
            "id": "sw_CD-lanfrica-medium",
            "name": "lanfrica (medium)"
        }
    ],
    "te": [
        {
            "id": "te_IN-maya-medium",
            "name": "maya (medium)"
        },
        {
            "id": "te_IN-padmavathi-medium",
            "name": "padmavathi (medium)"
        },
        {
            "id": "te_IN-venkatesh-medium",
            "name": "venkatesh (medium)"
        }
    ],
    "tr": [
        {
            "id": "tr_TR-dfki-medium",
            "name": "dfki (medium)"
        }
    ],
    "uk": [
        {
            "id": "uk_UA-lada-x_low",
            "name": "lada (x_low)"
        },
        {
            "id": "uk_UA-ukrainian_tts-medium",
            "name": "ukrainian_tts (medium)"
        }
    ],
    "vi": [
        {
            "id": "vi_VN-25hours_single-low",
            "name": "25hours_single (low)"
        },
        {
            "id": "vi_VN-vais1000-medium",
            "name": "vais1000 (medium)"
        },
        {
            "id": "vi_VN-vivos-x_low",
            "name": "vivos (x_low)"
        }
    ],
    "zh": [
        {
            "id": "zh_CN-chaowen-medium",
            "name": "chaowen (medium)"
        },
        {
            "id": "zh_CN-huayan-medium",
            "name": "huayan (medium)"
        },
        {
            "id": "zh_CN-huayan-x_low",
            "name": "huayan (x_low)"
        },
        {
            "id": "zh_CN-xiao_ya-medium",
            "name": "xiao_ya (medium)"
        }
    ]
}

# Реестр стандартных голосов XTTS v2 (вшитые в модель)
XTTS_STANDARD_VOICES = [
    "Claribel Dervla", "Daisy Studer", "Gracie Wise", "Tammie Ema",
    "Alison Dietlinde", "Ana Maëlle", "Linda Ines", "Nathaniel Robert",
    "Adrawon Hamed", "Abrahan Mack", "Otto Reinhold", "Roosevelt Trajan",
    "Baldur Santeri", "Craig Gutsy", "Damien Sourav"
]

class TTSAudioCache:
    """Кэш сгенерированных TTS аудиофайлов (res_key -> temp file path).
    Сохраняет сгенерированное аудио при переключении треков в плейлисте.
    """
    def __init__(self):
        self._cache = {}  # {res_key: filepath}

    def get(self, res_key):
        """Возвращает путь к кэшированному файлу, если он существует."""
        path = self._cache.get(res_key)
        if path and os.path.exists(path):
            return path
        if res_key in self._cache:
            del self._cache[res_key]
        return None

    def put(self, res_key, filepath):
        """Добавляет файл в кэш."""
        self._cache[res_key] = filepath

    def has(self, res_key):
        """Проверяет наличие кэша для ключа."""
        return self.get(res_key) is not None

    def clear(self):
        """Удаляет все кэшированные файлы."""
        for p in list(self._cache.values()):
            try:
                os.remove(p)
            except Exception:
                pass
        self._cache.clear()

    def remove(self, res_key):
        """Удаляет конкретный ключ из кэша."""
        path = self._cache.pop(res_key, None)
        if path:
            try:
                os.remove(path)
            except Exception:
                pass

class TTSEngine:
    """
    Гибридный движок TTS: использует Piper (Нейросеть) если доступен,
    иначе откатывается на системный pyttsx3.
    """
    def __init__(self, base_dir=None, current_language='ru'):
        self.current_language = current_language
        import sys
        if base_dir is None:
            # Если запущено из .exe, папка tts_data должна лежать рядом с .exe, а не во временной папке %TEMP%
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                base_dir = os.path.join(exe_dir, "tts_data")
            else:
                base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tts_data")

        self.base_dir = Path(base_dir)
        self.piper_dir = self.base_dir / "piper"
        self.models_dir = self.base_dir / "models"

        self.piper_exe = self.piper_dir / "piper.exe"

        # XTTS v2 пути
        self.xtts_dir = self.base_dir / "xtts"
        self.xtts_model_path = self.xtts_dir / "model.pth"
        self.xtts_instance = None # Для ленивой загрузки (legacy, не используется с сервером)

        # XTTS Background Server
        self._xtts_server_process = None
        self._xtts_server_speakers = []
        self._xtts_server_device = None
        # PyInstaller onefile: данные извлекаются в sys._MEIPASS, а не в папку с __file__
        if getattr(sys, 'frozen', False):
            _script_base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            _script_base = os.path.dirname(os.path.abspath(__file__))
        self._xtts_server_script = os.path.join(_script_base, "xtts_server.py")

        # Создаем структуру папок
        self.base_dir.mkdir(exist_ok=True)
        self.models_dir.mkdir(exist_ok=True)
        self.xtts_dir.mkdir(exist_ok=True)

        # Информационная подсказка об окружении
        is_venv = sys.prefix != sys.base_prefix
        env_type = f"VIRTUAL ENV ({sys.prefix})" if is_venv else f"SYSTEM PYTHON ({sys.prefix})"
        logger.info(f"--- TTS Engine Initialized ---")
        logger.info(f"Working Directory: {self.base_dir}")
        logger.info(f"Python Runtime: {env_type}")
        if not is_venv:
            logger.warning("Warning: You are using system Python. It is recommended to use venv.")

        self.use_piper = self._check_piper_available()
        self.system_engine = None
        self._init_system_engine()

    def _check_piper_available(self):
        """Проверяет наличие исполняемого файла Piper."""
        exists = self.piper_exe.exists()
        if not exists:
            logger.warning(f"Piper engine not found at {self.piper_exe}. Will use system TTS fallback.")
        return exists

    def is_xtts_available(self):
        """Проверяет наличие файлов модели XTTS v2."""
        required = ["model.pth", "config.json", "vocab.json", "speakers_xtts.pth"]
        return all((self.xtts_dir / f).exists() for f in required)

    def _get_python_exe(self):
        """Возвращает путь к python для XTTS (использует портативный .python или .venv рядом с EXE)."""
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
            # Приоритет 1: портативный Python (python.exe в корне .python/)
            portable_python = base_dir / ".python" / "python.exe"
            if portable_python.exists():
                return str(portable_python)
            # Приоритет 2: классический venv
            for venv_name in [".venv", "venv", "python"]:
                venv_python = base_dir / venv_name / "Scripts" / "python.exe"
                if venv_python.exists():
                    return str(venv_python)
            return "python"  # fallback — не найден
        return sys.executable

    def _check_pip_works(self, python_exe_path):
        """Проверяет, что pip работает в указанном Python."""
        try:
            creation_flags = 0x08000000 if sys.platform == "win32" else 0
            result = subprocess.run(
                [str(python_exe_path), "-m", "pip", "--version"],
                capture_output=True, text=True, creationflags=creation_flags, timeout=30
            )
            if result.returncode == 0 and "pip" in result.stdout:
                logger.info(f"pip is working: {result.stdout.strip()}")
                return True
            logger.warning(f"pip is not working: rc={result.returncode}, stdout={result.stdout}, stderr={result.stderr}")
            return False
        except Exception as e:
            logger.warning(f"pip check error: {e}")
            return False

    def _install_pip(self, python_dir, python_exe, text_callback=None):
        """Скачивает и устанавливает pip в portable Python."""
        creation_flags = 0x08000000 if sys.platform == "win32" else 0
        get_pip_path = python_dir / "get-pip.py"
        if text_callback: text_callback("📥 Установка pip...")
        logger.info("Downloading get-pip.py...")
        if not self._download_file("https://bootstrap.pypa.io/get-pip.py", get_pip_path, "get-pip.py", text_callback=text_callback):
            if text_callback: text_callback("❌ Не удалось скачать get-pip.py.")
            return False

        logger.info("Running get-pip.py...")
        # Увеличиваем таймаут pip (по умолчанию 15 сек — слишком мало)
        # Добавляем доверенные хосты и отключаем лишнее (setuptools/wheel) для облегчения веса
        env = os.environ.copy()
        env['PIP_DEFAULT_TIMEOUT'] = '300'
        
        pip_cmd = [
            str(python_exe), str(get_pip_path),
            "--trusted-host", "pypi.org",
            "--trusted-host", "files.pythonhosted.org",
            "--trusted-host", "bootstrap.pypa.io"
        ]
        
        result = subprocess.run(
            pip_cmd,
            capture_output=True, text=True, creationflags=creation_flags,
            env=env
        )
        logger.info(f"get-pip.py stdout: {result.stdout[-500:] if result.stdout else '(empty)'}")
        if result.stderr:
            logger.info(f"get-pip.py stderr: {result.stderr[-500:]}")
        get_pip_path.unlink(missing_ok=True)

        if result.returncode != 0:
            logger.error(f"get-pip.py failed with error (rc={result.returncode})")
            if text_callback:
                err_msg = result.stderr[-200:] if result.stderr else 'unknown error'
                text_callback(get_translation(self.current_language, 'tts_err_pip_install', error=err_msg))
            return False
        return True

    def _ensure_portable_python(self, progress_callback=None, text_callback=None):
        """Скачивает и настраивает портативный Python 3.11 (embeddable) рядом с EXE.
        Возвращает путь к python.exe или None при ошибке."""
        python_dir = Path(sys.executable).parent / ".python"
        python_exe = python_dir / "python.exe"

        if python_exe.exists():
            logger.info(f"Portable Python already exists: {python_exe}")
            # Проверяем, что pip реально работает
            if self._check_pip_works(str(python_exe)):
                return str(python_exe)
            # pip сломан — пробуем починить
            logger.warning("pip is not working in existing Python, reinstalling...")
            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_pip_fix'))
            # Проверяем/исправляем ._pth файл
            self._fix_pth_file(python_dir)
            if self._install_pip(python_dir, python_exe, text_callback):
                if self._check_pip_works(str(python_exe)):
                    return str(python_exe)
            if text_callback: text_callback(get_translation(self.current_language, 'tts_err_pip_fix'))
            return None

        try:
            creation_flags = 0x08000000 if sys.platform == "win32" else 0

            # --- Шаг 1: Скачать Python embeddable ---
            python_zip_url = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
            zip_path = Path(sys.executable).parent / "_python_embed.zip"

            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_dl_python'))
            logger.info("Downloading Python embeddable package...")
            if not self._download_file(python_zip_url, zip_path, "Python 3.11", progress_callback, text_callback):
                if text_callback: text_callback(get_translation(self.current_language, 'tts_err_dl_python'))
                return None

            # --- Шаг 2: Распаковать ---
            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_unpack_python'))
            logger.info(f"Unpacking to {python_dir}...")
            python_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(python_dir)
            zip_path.unlink(missing_ok=True)

            # --- Шаг 3: Модифицировать ._pth для включения pip/site-packages ---
            self._fix_pth_file(python_dir)

            # --- Шаг 4: Установить pip ---
            if not self._install_pip(python_dir, python_exe, text_callback):
                return None

            # --- Шаг 5: Проверить что pip реально работает ---
            if not self._check_pip_works(str(python_exe)):
                logger.error("pip installed but not working!")
                if text_callback: text_callback(get_translation(self.current_language, 'tts_err_pip_not_working'))
                return None

            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_python_ready'))
            logger.info(f"Portable Python installed: {python_exe}")
            return str(python_exe)

        except Exception as e:
            logger.error(f"Error installing portable Python: {e}", exc_info=True)
            if text_callback: text_callback(get_translation(self.current_language, 'tts_err_generic', error=str(e)))
            return None

    def _fix_pth_file(self, python_dir):
        """Модифицирует ._pth файл для включения site-packages."""
        pth_files = list(python_dir.glob("python*._pth"))
        if pth_files:
            pth_file = pth_files[0]
            content = pth_file.read_text(encoding='utf-8')
            # Раскомментируем "import site"
            if "#import site" in content:
                content = content.replace("#import site", "import site")
                pth_file.write_text(content, encoding='utf-8')
                logger.info(f"Modified {pth_file.name}: import site enabled.")
            elif "import site" in content:
                logger.info(f"{pth_file.name} already contains 'import site'.")
            else:
                # Добавляем в конец
                content += "\nimport site\n"
                pth_file.write_text(content, encoding='utf-8')
                logger.info(f"Added 'import site' to {pth_file.name}.")
        else:
            logger.warning("._pth file not found, pip might not work.")

    def is_tts_libraries_installed(self):
        """Проверяет, установлены ли необходимые Python-библиотеки для XTTS."""
        if hasattr(self, '_cached_libs_ok'):
            return self._cached_libs_ok

        try:
            python_exe = self._get_python_exe()
            check_code = "import TTS, torch; print('ok')"
            creation_flags = 0x08000000 if sys.platform == "win32" else 0
            result = subprocess.run([python_exe, "-c", check_code], capture_output=True, text=True, creationflags=creation_flags)
            if "ok" in result.stdout:
                self._cached_libs_ok = True
                return True
            else:
                logger.warning(f"Libraries not loading in {python_exe}:\n{result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Library validation error: {e}")
            return False

    def prepare(self):
        """Принудительная инициализация тяжелых библиотек (вызывается в фоне)."""
        _ = self.is_tts_libraries_installed()

    def install_tts_libraries(self, progress_callback=None, text_callback=None):
        """Устанавливает необходимые библиотеки через pip, позволяя pip самому выбрать совместимые версии."""
        # --- Создаём лог-файл рядом с EXE для диагностики ---
        if getattr(sys, 'frozen', False):
            install_log_path = os.path.join(os.path.dirname(sys.executable), "install_log.txt")
        else:
            install_log_path = os.path.join(os.path.dirname(__file__), "install_log.txt")
        
        install_log = None
        try:
            install_log = open(install_log_path, "w", encoding="utf-8")
            install_log.write(f"=== Install Log {__import__('datetime').datetime.now()} ===\n")
            install_log.flush()
        except Exception as e:
            logger.warning(f"Could not create install_log.txt: {e}")

        def log(msg):
            """Пишет в install_log.txt и в основной logger."""
            logger.info(msg)
            if install_log:
                try:
                    install_log.write(msg + "\n")
                    install_log.flush()
                except Exception:
                    pass

        # Оборачиваем text_callback чтобы ВСЕ сообщения также писались в лог-файл
        _original_text_callback = text_callback
        def logged_text_callback(msg):
            log(f"[UI]: {msg}")
            if _original_text_callback:
                _original_text_callback(msg)
        text_callback = logged_text_callback
        try:
            log(get_translation(self.current_language, 'tts_log_start_install'))
            log(get_translation(self.current_language, 'tts_log_vpn_hint'))

            creation_flags = 0x08000000 if sys.platform == "win32" else 0
            python_exe = self._get_python_exe()
            log(f"python_exe = {python_exe}")
            log(f"sys.frozen = {getattr(sys, 'frozen', False)}")
            log(f"sys.executable = {sys.executable}")
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
                log(f"base_dir = {base_dir}")
                expected_python = os.path.join(base_dir, ".python", "python.exe")
                log(f"expected .python/python.exe = {expected_python}, exists = {os.path.exists(expected_python)}")

            # Если EXE и Python не найден — скачиваем портативный Python автоматически
            if getattr(sys, 'frozen', False) and python_exe == "python":
                text_callback(get_translation(self.current_language, 'tts_status_dl_python'))
                if progress_callback: progress_callback(2, 0, 100)
                python_exe = self._ensure_portable_python(progress_callback, text_callback)
                if not python_exe:
                    text_callback(get_translation(self.current_language, 'tts_err_dl_python'))
                    log(get_translation(self.current_language, 'tts_log_portable_python_failed'))
                    return False
                log(get_translation(self.current_language, 'tts_log_portable_python_ready', python_exe=python_exe))

            # --- ВСЕГДА проверяем pip перед установкой ---
            if getattr(sys, 'frozen', False):
                log(get_translation(self.current_language, 'tts_status_check_pip'))
                if text_callback: text_callback(get_translation(self.current_language, 'tts_status_check_pip'))
                if not self._check_pip_works(python_exe):
                    log(get_translation(self.current_language, 'tts_log_pip_not_working'))
                    if text_callback: text_callback(get_translation(self.current_language, 'tts_status_pip_fix'))
                    python_dir = Path(python_exe).parent
                    self._fix_pth_file(python_dir)
                    if not self._install_pip(python_dir, Path(python_exe), text_callback):
                        log(get_translation(self.current_language, 'tts_log_pip_reinstall_failed'))
                        if text_callback: text_callback(get_translation(self.current_language, 'tts_err_pip_fix'))
                        return False
                    if not self._check_pip_works(python_exe):
                        log(get_translation(self.current_language, 'tts_log_pip_reinstalled_not_working'))
                        if text_callback: text_callback(get_translation(self.current_language, 'tts_err_pip_reinstalled_not_working'))
                        return False
                    log(get_translation(self.current_language, 'tts_log_pip_fixed'))
                else:
                    log(get_translation(self.current_language, 'tts_log_pip_ok'))

            def run_streamed_pip(cmd, base_progress):
                log(f"Running command: {' '.join(cmd)}")
                # Увеличиваем таймаут pip (по умолчанию 15 сек — слишком мало)
                env = os.environ.copy()
                env['PIP_DEFAULT_TIMEOUT'] = '300'
                
                # Добавляем флаги доверенных хостов для стабильности
                if "install" in cmd:
                    cmd.extend([
                        "--trusted-host", "pypi.org",
                        "--trusted-host", "files.pythonhosted.org"
                    ])

                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                    creationflags=creation_flags, env=env
                )
                prog_val = base_progress
                while True:
                    line = process.stdout.readline()
                    if not line: break
                    line = line.strip()
                    if not line: continue
                    log(f"[PIP]: {line}")
                    if progress_callback:
                        prog_val = (prog_val + 1) % 100
                        progress_callback(prog_val, 0, 100)
                    if text_callback:
                        # Усекаем слишком длинный вывод
                        short_line = line[:80] + "..." if len(line) > 80 else line
                        text_callback(short_line)
                
                process.wait()
                log(f"Command completed with code: {process.returncode}")
                return process.returncode == 0

            log(get_translation(self.current_language, 'tts_log_install_foundation'))
            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_install_numpy'))
            cmd0 = [
                python_exe, "-m", "pip", "install",
                "setuptools", "wheel", "numpy<2.0.0"
            ]
            if not run_streamed_pip(cmd0, 5):
                if text_callback: text_callback(get_translation(self.current_language, 'tts_err_install_tools'))
                log(get_translation(self.current_language, 'tts_log_install_foundation_failed'))
                return False

            log(get_translation(self.current_language, 'tts_log_install_xtts_libs'))
            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_install_xtts_libs'))
            # Используем исправленные имена пакетов и версии из вашего .venv
            # Они имеют готовые бинарные колеса (wheels), поэтому компилятор не потребуется.
            cmd1 = [
                python_exe, "-m", "pip", "install",
                "PyQt5", "pygame", "pyttsx3",
                "coqui-tts==0.27.5",
                "transformers==4.57.6"
            ]
            
            if not run_streamed_pip(cmd1, 15):
                if text_callback: text_callback(get_translation(self.current_language, 'tts_err_install_xtts_libs'))
                if text_callback: text_callback(get_translation(self.current_language, 'tts_err_install_xtts_libs_log'))
                log(get_translation(self.current_language, 'tts_log_install_xtts_libs_failed'))
                return False

            log(get_translation(self.current_language, 'tts_log_install_torch'))
            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_install_torch'))
            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_install_torch_gpu'))
            cmd2 = [
                self._get_python_exe(), "-m", "pip", "install",
                "torch==2.5.1", "torchaudio==2.5.1",
                "--index-url", "https://download.pytorch.org/whl/cu121"
            ]
            
            if not run_streamed_pip(cmd2, 50):
                if text_callback: text_callback(get_translation(self.current_language, 'tts_err_install_torch'))
                log(get_translation(self.current_language, 'tts_log_install_torch_failed'))
                return False

            self._cached_libs_ok = True
            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_install_success'))
            log(get_translation(self.current_language, 'tts_log_install_success'))
            return True
        except Exception as e:
            logger.error(f"Library installation error: {e}", exc_info=True)
            if install_log:
                try:
                    install_log.write(f"ИСКЛЮЧЕНИЕ: {e}\n{traceback.format_exc()}\n")
                except Exception:
                    pass
            if text_callback: text_callback(get_translation(self.current_language, 'tts_err_generic', error=str(e)))
            return False
        finally:
            if install_log:
                try:
                    install_log.close()
                except Exception:
                    pass

    def _init_system_engine(self):
        """Инициализация pyttsx3."""
        if pyttsx3:
            try:
                self.system_engine = pyttsx3.init('sapi5')
                self.system_engine.setProperty('rate', 180)
            except Exception as e:
                logger.error(f"SAPI5 error: {e}")

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

    def generate_speech(self, text, output_path, lang='ru', engine='piper', voice_id=None, **kwargs):
        """Генерирует речь, выбирая указанный движок.

        args:
            engine: 'piper', 'xtts' или 'system'
            voice_id: ID модели Piper или путь к speaker_wav для XTTS.
        kwargs:
            piper-specific: length_scale, sentence_silence, noise_scale
            xtts-specific: speaker_wav (путь к образцу), language (ru/en...)
        """
        # Если принудительно выбран XTTS
        if engine == 'xtts':
            if self.is_xtts_available():
                return self._generate_xtts(text, output_path, lang, voice_id=voice_id, **kwargs)
            else:
                logger.warning("XTTS v2 not installed, falling back to Piper")
                engine = 'piper'

        # Логика Piper
        if engine == 'piper' and self._check_piper_available():
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

    def _is_xtts_server_running(self):
        """Проверяет, работает ли фоновый сервер XTTS."""
        return (self._xtts_server_process is not None 
                and self._xtts_server_process.poll() is None)

    def _start_stdout_reader(self):
        """Запускает фоновый поток для чтения stdout сервера в очередь."""
        import threading
        from queue import Queue

        self._xtts_stdout_queue = Queue()

        def reader_thread(proc, q):
            try:
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        q.put(line.strip())
                    if proc.poll() is not None:
                        break
            except Exception:
                pass
            # Сигнал о завершении потока
            q.put(None)

        t = threading.Thread(target=reader_thread,
                             args=(self._xtts_server_process, self._xtts_stdout_queue),
                             daemon=True)
        t.start()

    def _read_server_response(self, timeout=120):
        """Читает JSON-ответ из очереди stdout сервера с таймаутом."""
        from queue import Empty
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            # Проверяем, жив ли процесс
            if not self._is_xtts_server_running():
                # Читаем лог-файл сервера для диагностики
                log_msg = ""
                try:
                    log_path = os.path.join(self.xtts_dir, "xtts_server.log")
                    if os.path.exists(log_path):
                        with open(log_path, 'r', encoding='utf-8') as f:
                            log_msg = f.read()[-500:]
                except Exception:
                    pass
                self._xtts_server_process = None
                return {"status": "error",
                        "message": f"XTTS server exited unexpectedly. Log: {log_msg}"}

            try:
                line = self._xtts_stdout_queue.get(timeout=1.0)
            except Empty:
                continue

            if line is None:
                # Поток чтения завершился — сервер упал
                self._xtts_server_process = None
                return {"status": "error", "message": "XTTS server stopped responding"}

            try:
                return json.loads(line)
            except json.JSONDecodeError:
                logger.warning(f"XTTS server: invalid response: {line}")
                continue

        return {"status": "error", "message": "Timeout waiting for XTTS server response"}

    def _init_xtts(self):
        """Запускает фоновый сервер XTTS, если он еще не работает."""
        if self._is_xtts_server_running():
            return True

        if not self.is_xtts_available():
            logger.error("XTTS v2 model files not found.")
            return False

        if not os.path.exists(self._xtts_server_script):
            logger.error(f"XTTS server script not found: {self._xtts_server_script}")
            return False

        try:
            logger.info("Starting background XTTS server...")

            # Запускаем xtts_server.py как отдельный процесс
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self._xtts_server_process = subprocess.Popen(
                [self._get_python_exe(), self._xtts_server_script, str(self.xtts_dir)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,  # Не перехватываем stderr — предотвращаем deadlock
                text=True,
                encoding='utf-8',
                startupinfo=startupinfo,
                bufsize=1  # Line-buffered
            )

            # Запускаем фоновый поток чтения stdout
            self._start_stdout_reader()

            # Ждём сигнала "ready" от сервера (до 2 минут на загрузку модели)
            response = self._read_server_response(timeout=120)

            if response.get("status") == "ready":
                self._xtts_server_speakers = response.get("speakers", [])
                self._xtts_server_device = response.get("device", "cpu")
                logger.info(f"XTTS server ready. Device: {self._xtts_server_device}, "
                            f"Speakers: {len(self._xtts_server_speakers)}")
                return True
            else:
                error_msg = response.get("message", "Unknown error during server startup")
                logger.error(f"XTTS server failed to start: {error_msg}")
                self.shutdown_xtts_server()
                return False

        except Exception as e:
            logger.error(f"Error starting XTTS server: {e}\n{traceback.format_exc()}")
            self._xtts_server_process = None
            return False

    def _send_xtts_command(self, cmd_dict, timeout=300):
        """Отправляет команду серверу XTTS и ждёт ответ."""
        if not self._is_xtts_server_running():
            return {"status": "error", "message": "XTTS server not running"}

        try:
            cmd_line = json.dumps(cmd_dict, ensure_ascii=False) + "\n"
            self._xtts_server_process.stdin.write(cmd_line)
            self._xtts_server_process.stdin.flush()

            return self._read_server_response(timeout=timeout)

        except (BrokenPipeError, OSError) as e:
            logger.error(f"XTTS server disconnected: {e}")
            self._xtts_server_process = None
            return {"status": "error", "message": f"Connection to XTTS server lost: {e}"}
        except Exception as e:
            logger.error(f"Error sending XTTS command: {e}")
            return {"status": "error", "message": str(e)}

    def shutdown_xtts_server(self):
        """Корректно останавливает фоновый сервер XTTS."""
        if self._xtts_server_process is None:
            return

        try:
            if self._xtts_server_process.poll() is None:
                # Сервер ещё жив — отправляем команду shutdown
                try:
                    self._xtts_server_process.stdin.write(
                        json.dumps({"cmd": "shutdown"}) + "\n"
                    )
                    self._xtts_server_process.stdin.flush()
                    self._xtts_server_process.wait(timeout=10)
                    logger.info("XTTS server stopped gracefully.")
                except Exception:
                    # Принудительное завершение
                    self._xtts_server_process.kill()
                    logger.warning("XTTS server killed forcefully.")
            else:
                logger.info("XTTS server already terminated.")
        except Exception as e:
            logger.error(f"Error stopping XTTS server: {e}")
        finally:
            self._xtts_server_process = None
            self._xtts_server_speakers = []
            self._xtts_server_device = None

    def _generate_xtts(self, text, output_path, lang='ru', voice_id=None, **kwargs):
        """Генерация через XTTS v2 (через фоновый сервер)."""
        if not self._init_xtts():
            return False

        try:
            cmd = {
                "cmd": "generate",
                "text": text,
                "output_path": output_path,
                "lang": lang,
                "voice_id": voice_id,
                "speed": kwargs.get('speed', 1.0),
                "temperature": kwargs.get('temperature', 0.75),
                "repetition_penalty": kwargs.get('repetition_penalty', 2.0),
                "top_k": kwargs.get('top_k', 50),
                "top_p": kwargs.get('top_p', 0.8),
                "length_penalty": kwargs.get('length_penalty', 1.0),
            }
            
            # Добавляем все доп. параметры из kwargs (например speaker_wav, speaker)
            for k, v in kwargs.items():
                if k not in cmd:
                    cmd[k] = v

            # Если voice_id — это путь к файлу, передаём как speaker_wav
            if voice_id and voice_id not in XTTS_STANDARD_VOICES:
                if os.path.exists(str(voice_id)):
                    cmd["voice_id"] = str(voice_id)

            result = self._send_xtts_command(cmd)

            if result.get("status") == "ok":
                return os.path.exists(output_path)
            else:
                error_msg = result.get("message", "Unknown error")
                logger.error(f"XTTS generation failed: {error_msg}")
                return False

        except Exception as e:
            logger.error(f"XTTS generation failed: {e}\n{traceback.format_exc()}")
            return False

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

            logger.info(f"Piper: Running command: {' '.join(command)}")
            # Запускаем без создания окна консоли на Windows
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # ВАЖНО: устанавливаем CWD в папку Piper, чтобы он нашел свои DLL (onnxruntime.dll и др.)
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                text=True,
                encoding='utf-8',
                cwd=str(self.piper_dir)
            )

            stdout, stderr = process.communicate(input=text)

            if process.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Piper: Audio created: {output_path}")
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

    def download_piper_components(self, progress_callback=None, text_callback=None):
        """ Скачивает Piper движок (без моделей). """
        try:
            # 1. Скачиваем Piper (Win x64) — Windows-сборка только в релизе 2023.11.14-2
            piper_url = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
            zip_path = self.base_dir / "piper.zip"

            logger.info("Скачивание Piper...")
            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_dl_piper_core'))
            if not self._download_file(piper_url, zip_path, "Piper engine", progress_callback, text_callback):
                if text_callback: text_callback(get_translation(self.current_language, 'tts_err_dl_piper'))
                return False

            # Проверяем, что скачанный файл — валидный ZIP
            if not zipfile.is_zipfile(zip_path):
                logger.error(f"Скачивание файл не является ZIP-архивом: {zip_path}")
                os.remove(zip_path)
                if text_callback: text_callback(get_translation(self.current_language, 'tts_err_piper_zip'))
                return False

            logger.info("Распаковка...")
            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_unpack_piper'))
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.base_dir)

            # После распаковки Github-релиза внутри может быть вложенная папка 'piper'.
            if not self.piper_exe.exists():
                for d in self.base_dir.iterdir():
                    if d.is_dir() and d.name != "models" and d != self.piper_dir:
                        found_exe = list(d.rglob("piper.exe"))
                        if found_exe:
                            if self.piper_dir.exists():
                                shutil.rmtree(self.piper_dir)
                            if found_exe[0].parent == d:
                                shutil.move(str(d), str(self.piper_dir))
                            else:
                                shutil.move(str(found_exe[0].parent), str(self.piper_dir))
                                if d.exists():
                                    shutil.rmtree(d, ignore_errors=True)
                            break

            # Удаляем архив
            if zip_path.exists():
                os.remove(zip_path)

            self.use_piper = self._check_piper_available()
            if text_callback and self.use_piper: text_callback(get_translation(self.current_language, 'tts_status_piper_install_done'))
            return self.use_piper
        except Exception as e:
            logger.error(f"Download orchestration failed: {e}", exc_info=True)
            if text_callback: text_callback(get_translation(self.current_language, 'tts_err_generic', error=str(e)))
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

    def _download_file(self, url, dest, label, external_callback=None, text_callback=None):
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
                            
                            # Отправляем текстовый апдейт (но не на каждый блок, чтоб не спамить UI)
                            if text_callback and (read_so_far % (1024 * 1024 * 5) < block_size):
                                text_callback(get_translation(self.current_language, 'tts_status_dl_progress', label=label, current=read_so_far // 1024 // 1024, total=total_size // 1024 // 1024))
                            external_callback(percent, 1, 100)

            logger.info(f"{label}: загружено {read_so_far} байт")
            return True
        except Exception as e:
            logger.error(f"Download of {label} failed: {e}")
            if text_callback: text_callback(get_translation(self.current_language, 'tts_err_generic', error=str(e)))
            if os.path.exists(dest):
                os.remove(dest)
            return False

    def download_xtts_model(self, progress_callback=None, text_callback=None):
        """Скачивает модель XTTS v2 (~1.5GB) с HuggingFace."""
        try:
            # Файлы модели XTTS v2
            base_url = "https://huggingface.co/coqui/XTTS-v2/resolve/main/"
            files = ["model.pth", "config.json", "vocab.json", "speakers_xtts.pth"]

            for f_name in files:
                dest = self.xtts_dir / f_name
                logger.info(f"XTTS: Скачивание {f_name}...")
                if text_callback: text_callback(get_translation(self.current_language, 'tts_status_dl_model_file', f_name=f_name))

                # Общий прогресс будет сложнее, так как файлы разного размера.
                # model.pth самый тяжелый.
                if not self._download_file(base_url + f_name, dest, f"XTTS {f_name}", progress_callback, text_callback):
                    # Если один файл не скачался, прерываем
                    if text_callback: text_callback(get_translation(self.current_language, 'tts_err_generic', error=f_name))
                    return False

            if text_callback: text_callback(get_translation(self.current_language, 'tts_status_model_loaded'))
            return True
        except Exception as e:
            logger.error(f"Failed to download XTTS model: {e}")
            if text_callback: text_callback(get_translation(self.current_language, 'tts_err_model_load'))
            return False
