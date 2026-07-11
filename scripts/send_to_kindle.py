#!/usr/bin/env python3
"""Send an article to Kindle, Instapaper-style.

Fetches a URL, extracts the readable article content, packages it as an
EPUB (with images embedded), and emails it to a Kindle address via SMTP.

Usage:
    python scripts/send_to_kindle.py <url>

Environment variables:
    KINDLE_EMAIL    destination @kindle.com address (required to send)
    SMTP_USERNAME   SMTP login, e.g. a Gmail address (required to send)
    SMTP_PASSWORD   SMTP password / Gmail app password (required to send)
    SMTP_HOST       default: smtp.gmail.com
    SMTP_PORT       default: 465 (SSL)
    DRY_RUN         set to "1" to build the EPUB but skip sending
    OUTPUT_DIR      where to write the .epub (default: current directory)
"""

import html
import mimetypes
import os
import re
import smtplib
import sys
import unicodedata
from datetime import datetime, timezone
from email.message import EmailMessage
from urllib.parse import urljoin, urlparse

import requests
from ebooklib import epub
from lxml import html as lhtml
from readability import Document

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
MAX_IMAGES = 30
MAX_IMAGE_BYTES = 5 * 1024 * 1024
REQUEST_TIMEOUT = 30


def log(msg):
    print(msg, flush=True)


def slugify(text, fallback="article"):
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\w一-鿿-]+", "-", text).strip("-")
    return text[:60] or fallback


def fetch_article(url):
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    if resp.encoding == "ISO-8859-1":
        resp.encoding = resp.apparent_encoding
    doc = Document(resp.text)
    title = doc.short_title() or urlparse(url).netloc
    content_html = doc.summary(html_partial=True)
    return title, content_html


def clean_tree(tree, title):
    """Drop non-article chrome readability may have kept, and the duplicate title."""
    for tag in ("nav", "aside", "footer", "form", "script", "style", "iframe"):
        for el in tree.findall(f".//{tag}"):
            el.drop_tree()
    for h1 in tree.findall(".//h1"):
        text = "".join(h1.itertext()).strip()
        if text and (text in title or title in text):
            h1.drop_tree()
        break


def embed_images(book, content_html, base_url, title):
    """Download <img> targets and rewrite them to embedded EPUB resources."""
    tree = lhtml.fromstring(f"<div>{content_html}</div>")
    clean_tree(tree, title)
    count = 0
    for img in tree.iter("img"):
        src = img.get("src") or img.get("data-src") or ""
        if not src or src.startswith("data:"):
            continue
        if count >= MAX_IMAGES:
            img.drop_tree()
            continue
        abs_url = urljoin(base_url, src)
        try:
            r = requests.get(
                abs_url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT
            )
            r.raise_for_status()
            data = r.content
            if len(data) > MAX_IMAGE_BYTES:
                raise ValueError("image too large")
            ctype = r.headers.get("Content-Type", "").split(";")[0].strip()
            ext = mimetypes.guess_extension(ctype) if ctype else None
            if ext in (None, ".jpe"):
                ext = os.path.splitext(urlparse(abs_url).path)[1] or ".jpg"
            name = f"images/img{count}{ext}"
            book.add_item(
                epub.EpubItem(
                    uid=f"img{count}",
                    file_name=name,
                    media_type=ctype or "image/jpeg",
                    content=data,
                )
            )
            img.set("src", name)
            for attr in ("srcset", "data-src", "loading", "width", "height"):
                img.attrib.pop(attr, None)
            count += 1
        except Exception as e:  # noqa: BLE001 - best effort per image
            log(f"  skipping image {abs_url}: {e}")
            img.drop_tree()
    log(f"embedded {count} image(s)")
    inner = lhtml.tostring(tree, encoding="unicode")
    # strip the wrapper <div> we added
    return re.sub(r"^<div>|</div>$", "", inner, count=2)


def build_epub(title, content_html, url, output_dir):
    book = epub.EpubBook()
    book.set_identifier(url)
    book.set_title(title)
    book.set_language("zh")
    book.add_author(urlparse(url).netloc)

    content_html = embed_images(book, content_html, url, title)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = (
        f"<h1>{html.escape(title)}</h1>"
        f'<p class="meta">来源：<a href="{html.escape(url)}">{html.escape(url)}</a>'
        f" · 保存于 {date_str}</p>"
        f"{content_html}"
    )
    style = epub.EpubItem(
        uid="style",
        file_name="style/main.css",
        media_type="text/css",
        content=(
            "body{line-height:1.6;}"
            "h1{font-size:1.5em;margin-bottom:0.2em;}"
            ".meta{color:#666;font-size:0.85em;margin-bottom:1.5em;}"
            "img{max-width:100%;}"
        ),
    )
    book.add_item(style)

    chapter = epub.EpubHtml(title=title, file_name="article.xhtml", lang="zh")
    chapter.set_content(body)
    chapter.add_item(style)
    book.add_item(chapter)

    book.toc = [chapter]
    book.spine = [chapter]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    path = os.path.join(output_dir, f"{slugify(title)}.epub")
    epub.write_epub(path, book)
    return path


def send_email(epub_path, title):
    kindle_email = os.environ["KINDLE_EMAIL"]
    username = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))

    msg = EmailMessage()
    msg["From"] = username
    msg["To"] = kindle_email
    msg["Subject"] = title
    msg.set_content(f"Sent to Kindle: {title}")
    with open(epub_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="epub+zip",
            filename=os.path.basename(epub_path),
        )
    with smtplib.SMTP_SSL(host, port, timeout=60) as smtp:
        smtp.login(username, password)
        smtp.send_message(msg)
    log(f"sent to {kindle_email}")


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: send_to_kindle.py <url>")
    url = sys.argv[1]
    if not re.match(r"^https?://", url):
        sys.exit(f"not a valid http(s) URL: {url}")

    log(f"fetching {url}")
    title, content_html = fetch_article(url)
    log(f"extracted article: {title}")

    output_dir = os.environ.get("OUTPUT_DIR", ".")
    epub_path = build_epub(title, content_html, url, output_dir)
    size_kb = os.path.getsize(epub_path) // 1024
    log(f"built {epub_path} ({size_kb} KB)")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"title={title}\n")
            f.write(f"epub={epub_path}\n")

    if os.environ.get("DRY_RUN") == "1":
        log("DRY_RUN=1, skipping email")
        return
    missing = [
        k for k in ("KINDLE_EMAIL", "SMTP_USERNAME", "SMTP_PASSWORD") if not os.environ.get(k)
    ]
    if missing:
        sys.exit(f"missing secrets: {', '.join(missing)} — see SEND_TO_KINDLE.md")
    send_email(epub_path, title)


if __name__ == "__main__":
    main()
