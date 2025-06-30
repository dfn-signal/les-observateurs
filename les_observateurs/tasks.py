import logging
import os
import shlex
import subprocess

import toml
from celery import Celery
from celery.utils.log import get_task_logger

CONFIG_PATH = "config.toml"
if os.path.exists(CONFIG_PATH):
    config = toml.load(CONFIG_PATH)
    log_file = config["logging"]["logfile"]
else:
    log_file = "logs/default-worker.log"

os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,  # Python 3.8+
)

logger = get_task_logger(__name__)
logger.info("Celery worker started and logging initialized.")

app = Celery(
    "tasks",
    broker="amqp://guest:guest@localhost:5672//",
)


@app.task
def transcribe_file(mp3_dir, vtt_dir, filename):
    logger.info(f"Transcribing {filename} from {mp3_dir}")
    command = (
        f"/home/nruest/.pyenv/shims/whisper "
        f"--threads 12 --model turbo --fp16 False --language en "
        f"--output_format vtt --output_dir {shlex.quote(vtt_dir)} "
        f"{shlex.quote(mp3_dir)}/{shlex.quote(filename)}"
    )
    try:
        subprocess.run(command, shell=True, check=True)
        logger.info("Transcription complete for: %s", filename)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Error processing %s: %s", filename, e)
        return False
