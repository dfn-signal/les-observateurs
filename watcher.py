import logging
import os
import time
from pathlib import Path

import toml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from tasks import transcribe_file

PROCESSED_FILES = set()


def load_config(toml_path):
    config = toml.load(toml_path)
    logging.basicConfig(
        filename=config["logging"]["logfile"],
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
    )
    return config["paths"]["base_podcast_dir"], config["paths"]["queue_file"]


def load_queue(queue_file):
    if os.path.exists(queue_file):
        with open(queue_file, "r") as f:
            return set(line.strip() for line in f)
    return set()


def save_queue(queue_file, processed_files):
    with open(queue_file, "w") as f:
        for file in processed_files:
            f.write(f"{file}\n")


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, queue_file):
        self.queue_file = queue_file

    def handle_event(self, file_path):
        logging.info(f"Event detected: {file_path}")
        if not file_path.lower().endswith(".mp3"):
            return

        if file_path in PROCESSED_FILES:
            return

        filename = os.path.basename(file_path)
        base_name, _ = os.path.splitext(filename)

        podcast_root = Path(file_path).parents[1]

        vtt_path = podcast_root / "vtt" / f"{base_name}.vtt"

        if vtt_path.exists():
            logging.info(f"Skipping {filename}, .vtt already exists.")
            PROCESSED_FILES.add(file_path)
            save_queue(self.queue_file, PROCESSED_FILES)
            return

        mp3_dir = podcast_root / "mp3"
        vtt_dir = podcast_root / "vtt"

        if not vtt_dir.exists():
            vtt_dir.mkdir(parents=True)

        logging.info(f"Queuing file for transcription: {file_path}")
        transcribe_file.delay(str(mp3_dir), str(vtt_dir), os.path.basename(file_path))

        PROCESSED_FILES.add(file_path)
        save_queue(self.queue_file, PROCESSED_FILES)

    def on_created(self, event):
        logging.info(f"Created event triggered: {event.src_path}")
        if not event.is_directory:
            self.handle_event(event.src_path)

    def on_moved(self, event):
        logging.info(f"Moved event triggered: {event.dest_path}")
        if not event.is_directory:
            self.handle_event(event.dest_path)


def find_mp3_directories(base_dir):
    mp3_dirs = []
    for root, dirs, _ in os.walk(base_dir):
        if "mp3" in dirs:
            mp3_dirs.append(os.path.join(root, "mp3"))
    return mp3_dirs


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python watcher.py config.toml")
        exit(1)

    base_podcast_dir, queue_file = load_config(sys.argv[1])
    PROCESSED_FILES = load_queue(queue_file)

    observer = Observer()
    event_handler = FileEventHandler(queue_file)

    for mp3_dir in find_mp3_directories(base_podcast_dir):
        observer.schedule(event_handler, mp3_dir, recursive=False)
        logging.info(f"Watching directory: {mp3_dir}")

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
