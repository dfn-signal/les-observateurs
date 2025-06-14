import logging
import shlex
import subprocess

from celery import Celery

app = Celery(
    "tasks",
    broker="filesystem://",
    broker_transport_options={
        "data_folder_in": "tmp/celery-in",
        "data_folder_out": "tmp/celery-out",
        "data_folder_processed": "tmp/celery-done",
    },
)


@app.task
def transcribe_file(mp3_dir, vtt_dir, filename):
    logging.info(f"Transcribing {filename} from {mp3_dir}")
    command = (
        f"/home/nruest/.pyenv/shims/whisper "
        f"--threads 11 --model turbo --fp16 False --language en "
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
