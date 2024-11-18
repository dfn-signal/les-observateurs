import logging
import os
import shlex
import subprocess
import threading
import time
from collections import deque

import psutil
import toml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Constants.
QUEUE = deque()
PROCESSED_FILES = set()
LOCK = threading.Lock()
PROCESSING = False
PROCESS_DELAY = 0.5

# TOML config variables.
output_dir = ""
watch_dir = ""
queue_file = ""
logfile = ""


# Load TOML config.
def load_config(toml_path):
    global output_dir, watch_dir, queue_file, logfile

    try:
        config = toml.load(toml_path)
        output_dir = config["paths"]["output_dir"]
        watch_dir = config["paths"]["watch_dir"]
        queue_file = config["paths"]["queue_file"]
        logfile = config["logging"]["logfile"]

        # Initialize logging.
        logging.basicConfig(
            filename=logfile, level=logging.INFO, format="%(asctime)s - %(message)s"
        )
        logging.info("Configuration loaded successfully.")

    except Exception as e:
        print(f"Error loading configuration file: {e}")
        exit(1)


# Load existing queue from file.
def load_queue():
    if os.path.exists(queue_file):
        with open(queue_file, "r") as f:
            for line in f:
                PROCESSED_FILES.add(line.strip())


def save_queue():
    with open(queue_file, "w") as f:
        for file in PROCESSED_FILES:
            f.write(f"{file}\n")


def check_whisper_running():
    """Check if the whisper process is currently running."""
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"]
            if "/bin/sh" in cmdline and "whisper" in cmdline:
                logging.info(f"Whisper process detected: {' '.join(cmdline)}")
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            continue
    return False


class FileEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        self.handle_event(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        if event.dest_path.endswith(".mp3"):
            self.handle_event(event.dest_path)

    def handle_event(self, file_path):
        filename = os.path.basename(file_path)
        if filename.lower().endswith((".mp3", ".m4a")):
            with LOCK:
                if filename not in PROCESSED_FILES and filename not in QUEUE:
                    logging.info(f"Detected new file event: {filename}")
                    QUEUE.append(filename)
                    if not PROCESSING:
                        threading.Thread(target=self.process_queue).start()

    def process_queue(self):
        global PROCESSING
        PROCESSING = True
        # Allow time for additional events to be captured.
        time.sleep(PROCESS_DELAY)

        while QUEUE:
            with LOCK:
                file_to_process = QUEUE.popleft()

            if check_whisper_running():
                logging.info("Whisper process is already running. Skipping processing.")
                QUEUE.appendleft(file_to_process)
                # Re-add to the queue for later processing.
                break

            logging.info(f"Processing file: {file_to_process}")

            # Escape the file paths using shlex.
            # See: Beyoncé Was Paid $10 Million For A 3 Minute Endorsement？! ｜ Candace Ep 103.mp3
            output_dir_escaped = shlex.quote(output_dir)
            watch_dir_escaped = shlex.quote(watch_dir)
            file_to_process_escaped = shlex.quote(file_to_process)

            command = (
                f"/home/nruest/.pyenv/shims/whisper "
                f"--threads 11 --model turbo --fp16 False --language en "
                f"--output_format vtt --output_dir {output_dir_escaped} "
                f"{watch_dir_escaped}/{file_to_process_escaped}"
            )

            try:
                subprocess.run(command, shell=True, check=True)
                logging.info(f"Processing completed for: {file_to_process}.")
                # Mark processed
                PROCESSED_FILES.add(file_to_process)
            except subprocess.CalledProcessError as e:
                logging.error(f"Error processing file: {file_to_process}: {e}")

            save_queue()

        PROCESSING = False


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python les-observateurs.py config.toml")
        exit(1)

    # Load TOML config.
    config_file = sys.argv[1]
    load_config(config_file)

    # Load queue and start watcher.
    load_queue()
    event_handler = FileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
