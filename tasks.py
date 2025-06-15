import logging
import os
import shlex
import subprocess

import toml
from celery import Celery

CONFIG_PATH = "config.toml"
if os.path.exists(CONFIG_PATH):
    config = toml.load(CONFIG_PATH)
    log_file = config["logging"]["logfile"]
else:
    log_file = "logs/default-worker.log"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.info("Celery worker started and logging initialized.")

app = Celery(
    "tasks",
    broker="amqp://guest:guest@localhost:5672//",
)


@app.task
def transcribe_file(mp3_dir, vtt_dir, filename):
    logging.info(f"Transcribing {filename} from {mp3_dir}")
    command = (
        f"/home/nruest/.pyenv/shims/whisper "
        f"--threads 12 --model turbo --fp16 False --language en "
        f"--output_format vtt --output_dir {shlex.quote(vtt_dir)} "
        f"{shlex.quote(mp3_dir)}/{shlex.quote(filename)}"
    )
    try:
        subprocess.run(command, shell=True, check=True)
        logging.info(f"Transcription complete: {filename}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error processing {filename}: {e}")
        return False
