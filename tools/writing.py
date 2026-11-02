"""
Refresh the Writing section of README.md from the blog's RSS feed.

    python tools/writing.py

The feed carries every post twice, once per language; only the English ones
are listed, newest first (the feed is already sorted). Rewrites the lines
between the writing markers and leaves the file untouched when nothing changed.
"""
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED = "https://hoijunkim.github.io/rss.xml"
COUNT = 5
START, END = "<!-- writing:start -->", "<!-- writing:end -->"
README = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "README.md")


def entries(xml):
    posts = [i for i in ET.fromstring(xml).iter("item") if i.findtext("language") == "en"]
    for p in posts[:COUNT]:
        title = p.findtext("title").replace("[", "\\[").replace("]", "\\]")
        day = parsedate_to_datetime(p.findtext("pubDate")).date().isoformat()
        yield f"- `{day}` [{title}]({p.findtext('link')})"


def main():
    with urllib.request.urlopen(FEED, timeout=30) as r:
        lines = list(entries(r.read()))
    if not lines:
        # an empty or reshaped feed should not blank the section
        sys.exit("feed has no English posts; README left as is")

    with open(README, encoding="utf-8") as f:
        readme = f.read()
    head, rest = readme.split(START, 1)
    _, tail = rest.split(END, 1)
    updated = head + START + "\n" + "\n".join(lines) + "\n" + END + tail
    if updated != readme:
        with open(README, "w", encoding="utf-8", newline="\n") as f:
            f.write(updated)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
