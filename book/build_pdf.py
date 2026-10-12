#!/usr/bin/env python3
"""Build book/lab-book.pdf from book/lab-book.md.

Requires the Python "markdown" package (pip install markdown) and Google
Chrome, Chromium or Microsoft Edge for printing. Set CHROME to the browser
path if it is not found automatically.

    python3 book/build_pdf.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

BOOK = Path(__file__).resolve().parent
SOURCE = BOOK / "lab-book.md"
STYLE = BOOK / "style.css"
OUTPUT = BOOK / "lab-book.pdf"

CANDIDATES = [
    os.environ.get("CHROME", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
]


def find_browser():
    for candidate in CANDIDATES:
        if candidate and (Path(candidate).is_file() or shutil.which(candidate)):
            return shutil.which(candidate) or candidate
    sys.exit("No Chrome, Chromium or Edge found. Set CHROME to its path.")


def answer_blanks(text):
    # Runs of underscores are answer spaces. Markdown would read them as
    # emphasis, so turn them into underlined spans of a similar width.
    return re.sub(r"_{3,}", lambda m: f'<span class="blank" style="width:'
                  f'{len(m.group()) * 0.55:.1f}em"></span>', text)


def main():
    body = markdown.markdown(
        answer_blanks(SOURCE.read_text(encoding="utf-8")),
        extensions=["tables", "fenced_code", "md_in_html"],
    )
    html = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<title>Lab 2: The CourseDesk incident handover</title>"
        f"<style>{STYLE.read_text(encoding='utf-8')}</style></head>"
        f"<body>{body}</body></html>"
    )
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "lab-book.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run([
            find_browser(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
            # Bookmarks for each heading, so readers can jump to an experiment.
            "--generate-pdf-document-outline",
            f"--print-to-pdf={OUTPUT}", page.as_uri(),
        ], check=True, capture_output=True)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
