import glob
import os
import shlex
import subprocess
import sys

if len(sys.argv) != 2:
    print("Usage: python careless-whisper-pill.py <directory_path>")
    sys.exit(1)

directory_path = sys.argv[1]

model = "turbo"
threads = 44
fp16 = "False"
language = "en"
output_format = "vtt"

media_files = glob.glob(os.path.join(directory_path, "*.m*"))


def process_file(media_file):
    quoted_file = shlex.quote(media_file)
    cmd_str = (
        f"whisper --threads {threads} --model {model} "
        f"--fp16 {fp16} --language {language} {quoted_file} "
        f"--output_format {output_format}"
    )

    try:
        subprocess.run(cmd_str, shell=True, check=True)
        print(f"Successfully processed {media_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {media_file}: {e}")


for media_file in media_files:
    if os.path.isfile(media_file):
        process_file(media_file)
    else:
        print(f"File does not exist: {media_file}")

print("Processing completed.")
