import os
import re
import sys

import feedparser

if len(sys.argv) != 2:
    print("Usage: python pill-feeder.py <rss_feed_url>")
    sys.exit(1)

rss_feed_url = sys.argv[1]

feed = feedparser.parse(rss_feed_url)


def clean_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title) + ".txt"


output_dir = "data"
os.makedirs(output_dir, exist_ok=True)

for entry in feed.entries:
    title = entry.title
    description = entry.description

    filename = clean_filename(title)
    file_path = os.path.join(output_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(description)

    print(f"Written: {file_path}")

print("Processing completed.")
