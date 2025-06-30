# les observateurs

A [RabbitMQ](https://www.rabbitmq.com/) and [`celery`](https://github.com/celery/celery) backed utility to watch a set of directories for incoming podcast downloads and transcribe them with [`whisper`](https://github.com/openai/whisper).

## Usage

* `apt install rabbitmq-server`
* `poetry install`
* `poetry run watcher config.toml`
* `poetry run bash celery_worker.sh`

## License

The Unlicense

## Acknowledgments

This project is part of the [Digital Feminist Network](https://digfemnet.org/) and is funded by the [Social Sciences and Humanities Research Council](https://www.sshrc-crsh.gc.ca/). Additional financial and in-kind support comes from [York University](https://www.yorku.ca/), [York University Libraries](https://www.library.yorku.ca/web/), the [Faculty of Arts](https://uwaterloo.ca/arts/), and the [David R. Cheriton School of Computer Science](https://cs.uwaterloo.ca/) at the [University of Waterloo](https://uwaterloo.ca/).
