"""
XTTS Background Server
Запускается как отдельный процесс, загружает модель XTTS v2 в память
и ожидает команды на генерацию через stdin (JSON-протокол).

Протокол:
  -> stdin:  JSON-строка с командой (одна строка, UTF-8)
  <- stdout: JSON-строка с результатом (одна строка, UTF-8)

Команды:
  {"cmd": "generate", "text": "...", "output_path": "...", "lang": "ru", "voice_id": "...", ...}
  {"cmd": "ping"}
  {"cmd": "shutdown"}

Ответы:
  {"status": "ok", "path": "..."}
  {"status": "error", "message": "..."}
  {"status": "pong"}
  {"status": "ready", "speakers": [...], "device": "cuda"}
"""

import os
import sys
import json
import traceback
import logging
import io

# =====================================================================
# КРИТИЧЕСКИ ВАЖНО: Настройка кодировки ДО любых импортов.
# В Windows stdout по умолчанию использует системную кодировку (CP1251),
# что ломает JSON при наличии имен вроде 'Maëlle'.
# =====================================================================
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

_protocol_out = sys.stdout  # Сохраняем ссылку на UTF-8 stdout для протокола

# Перенаправляем sys.stdout (print библиотек) в devnull
_devnull = open(os.devnull, 'w', encoding='utf-8')
sys.stdout = _devnull

# Список стандартных голосов XTTS v2
XTTS_STANDARD_VOICES = [
    "Claribel Dervla", "Daisy Studer", "Gracie Wise", "Tammie Ema",
    "Alison Dietlinde", "Ana Maëlle", "Linda Ines", "Nathaniel Robert",
    "Adrawon Hamed", "Abrahan Mack", "Otto Reinhold", "Roosevelt Trajan",
    "Baldur Santeri", "Craig Gutsy", "Damien Sourav"
]

logger = logging.getLogger("XTTS_SERVER")


def setup_logging(xtts_dir):
    """Настраивает логирование в файл внутри папки модели."""
    log_file = os.path.join(xtts_dir, "xtts_server.log")
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - XTTS_SERVER - %(levelname)s - %(message)s',
            filename=log_file,
            filemode='w',
            encoding='utf-8'
        )
        logger.info(f"Logging configured: {log_file}")
    except Exception as e:
        # Если не удалось создать файл, логируем в stderr (хотя он заглушен)
        pass


def send_response(data):
    """Отправляет JSON-ответ через протокольный канал (UTF-8 stdout)."""
    try:
        line = json.dumps(data, ensure_ascii=False)
        _protocol_out.write(line + "\n")
        _protocol_out.flush()
    except Exception as e:
        logger.error(f"Failed to send JSON response: {e}\n{traceback.format_exc()}")


def init_xtts(xtts_dir):
    """Загружает модель XTTS v2 и возвращает экземпляр TTS."""
    logger.info(f"Loading XTTS v2 model from {xtts_dir}...")

    # Подавляем вывод библиотек в stderr (чтобы PIPE не забивался)
    _original_stderr = sys.stderr
    sys.stderr = _devnull

    try:
        from TTS.api import TTS
        import torch
    finally:
        sys.stderr = _original_stderr

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Torch device: {device}, CUDA available: {torch.cuda.is_available()}")

    config_path = os.path.join(xtts_dir, "config.json")

    # Снова подавляем вывод при самой загрузке модели
    sys.stderr = _devnull
    try:
        tts_instance = TTS(model_path=xtts_dir, config_path=config_path).to(device)
    finally:
        sys.stderr = _original_stderr

    speakers = []
    try:
        if hasattr(tts_instance, 'speakers') and tts_instance.speakers:
            speakers = list(tts_instance.speakers)
            logger.info(f"XTTS voices loaded. Total: {len(speakers)}")
    except Exception as e:
        logger.warning(f"Failed to get speakers list: {e}")

    logger.info(f"XTTS v2 loaded successfully on {device}")
    return tts_instance, speakers, device


def handle_generate(tts_instance, speakers, cmd):
    """Обрабатывает команду генерации."""
    text = cmd.get("text", "")
    output_path = cmd.get("output_path", "")
    lang = cmd.get("lang", "ru")
    voice_id = cmd.get("voice_id")

    if not text or not output_path:
        return {"status": "error", "message": "Text or output path not specified"}

    xtts_lang = lang.split('_')[0] if '_' in lang else lang
    
    logger.info(f"Генерация: voice_id='{voice_id}', lang={xtts_lang}, text_len={len(text)}")
    logger.info(f"CWD: {os.getcwd()}")
    
    speaker_wav = None
    speaker_name = None

    if voice_id in XTTS_STANDARD_VOICES:
        speaker_name = voice_id
        logger.info(f"Standard voice: {speaker_name}")
    elif voice_id:
        # Нормализуем путь (убираем лишние слэши, переводим в стиль ОС)
        norm_voice_path = os.path.normpath(str(voice_id).strip())
        exists = os.path.exists(norm_voice_path)
        logger.info(f"Checking path: '{norm_voice_path}' (exists: {exists})")
        
        if exists:
            speaker_wav = norm_voice_path
            logger.info(f"WAV path confirmed: {speaker_wav}")
        else:
            # Если не существует, пробуем поискать в доп. параметрах
            speaker_wav = cmd.get("speaker_wav")
            speaker_name = cmd.get("speaker")
            logger.info(f"Searching in extra params: speaker_wav='{speaker_wav}', speaker='{speaker_name}'")
    else:
        speaker_wav = cmd.get("speaker_wav")
        speaker_name = cmd.get("speaker")
        logger.info(f"Voice not specified in voice_id, searching in extra params: speaker_wav='{speaker_wav}', speaker='{speaker_name}'")

    if not speaker_wav and not speaker_name:
        logger.error("Error: voice not defined")
        return {"status": "error", "message": "Neither speaker_wav nor standard voice name specified"}

    if speaker_name and speakers and speaker_name not in speakers:
        logger.warning(f"Voice '{speaker_name}' not found. Using {speakers[0] if speakers else 'None'}")
        if speakers:
            speaker_name = speakers[0]

    speed = cmd.get("speed", 1.0)
    temp = cmd.get("temperature", 0.75)
    rep_pen = cmd.get("repetition_penalty", 2.0)
    top_k = cmd.get("top_k", 50)
    top_p = cmd.get("top_p", 0.8)
    len_pen = cmd.get("length_penalty", 1.0)

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    logger.info(f"Генерация: text_len={len(text)}, lang={xtts_lang}, voice={speaker_name or speaker_wav}")

    _original_stderr = sys.stderr
    sys.stderr = _devnull
    try:
        # Прямой вызов tts_to_file
        tts_instance.tts_to_file(
            text=text,
            speaker=speaker_name,
            speaker_wav=speaker_wav,
            language=xtts_lang,
            file_path=output_path,
            speed=speed,
            temperature=temp,
            repetition_penalty=float(rep_pen),
            top_k=int(top_k),
            top_p=float(top_p),
            length_penalty=float(len_pen)
        )
    finally:
        sys.stderr = _original_stderr

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        logger.info(f"Generation completed successfully: {output_path}")
        return {"status": "ok", "path": output_path}
    else:
        return {"status": "error", "message": f"File was not created or is empty: {output_path}"}


def start_watchdog():
    """Следит за смертью родителя и убивает сервер."""
    import threading
    import time
    import os

    try:
        parent_pid = os.getppid()
    except Exception:
        return # На некоторых системах может не работать

    def watchdog():
        while True:
            time.sleep(3)
            try:
                if os.getppid() != parent_pid:
                    os._exit(0)
            except Exception:
                os._exit(0)

    t = threading.Thread(target=watchdog, daemon=True)
    t.start()


def main():
    start_watchdog()
    _stdin = sys.stdin

    if len(sys.argv) < 2:
        send_response({"status": "error", "message": "XTTS model directory path not specified"})
        sys.exit(1)

    xtts_dir = sys.argv[1]

    if not os.path.isdir(xtts_dir):
        send_response({"status": "error", "message": f"XTTS directory not found: {xtts_dir}"})
        sys.exit(1)

    # Настраиваем логирование после получения пути
    setup_logging(xtts_dir)

    try:
        tts_instance, speakers, device = init_xtts(xtts_dir)
        send_response({
            "status": "ready",
            "speakers": speakers,
            "device": device
        })
    except Exception as e:
        err = f"Critical error during XTTS initialization: {e}\n{traceback.format_exc()}"
        logger.error(err)
        send_response({"status": "error", "message": err})
        sys.exit(2)

    logger.info("Server entered command waiting loop.")
    for line in _stdin:
        line = line.strip()
        if not line:
            continue

        try:
            cmd = json.loads(line)
        except json.JSONDecodeError as e:
            send_response({"status": "error", "message": f"Invalid JSON: {e}"})
            continue

        command = cmd.get("cmd", "")

        if command == "ping":
            send_response({"status": "pong"})
        elif command == "shutdown":
            logger.info("Shutdown command received.")
            send_response({"status": "ok", "message": "Server stopped"})
            break
        elif command == "generate":
            try:
                result = handle_generate(tts_instance, speakers, cmd)
                send_response(result)
            except Exception as e:
                err_msg = f"Error during generation: {e}"
                logger.error(f"{err_msg}\n{traceback.format_exc()}")
                send_response({"status": "error", "message": err_msg})
        else:
            send_response({"status": "error", "message": f"Unknown command: {command}"})

    logger.info("XTTS server shut down gracefully.")


if __name__ == "__main__":
    main()
