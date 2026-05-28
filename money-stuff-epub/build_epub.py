#!/usr/bin/env python3
"""
Money Stuff -> EPUB 生成器
============================

一个不依赖任何第三方库的 EPUB 3 生成器（仅用 Python 标准库 zipfile）。

两种用法：
1. 直接运行本脚本：用 content.py 里的「中文导读」数据生成一本 EPUB。
   $ python3 build_epub.py

2. 作为可复用工具：把你自己保存的 Money Stuff 邮件（HTML/EML）解析后，
   按 build_epub(meta, chapters) 的格式喂进来，即可生成全文 EPUB。
   见文末 build_epub() 的 docstring。

设计目标：
- 纯标准库，CI / 任何机器上都能跑。
- 生成的 EPUB 通过 epubcheck 基本结构校验（mimetype 不压缩、container.xml、nav 文档等）。
"""

import html
import os
import uuid
import zipfile
from datetime import datetime, timezone


def _xhtml(title, body_html, lang="zh-CN"):
    """把一段 body HTML 包成合法的 XHTML 文档。"""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang}" lang="{lang}">
<head>
  <meta charset="utf-8"/>
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
{body_html}
</body>
</html>
"""


CSS = """\
body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
       line-height: 1.75; margin: 5% 6%; color: #1a1a1a; }
h1 { font-size: 1.5em; line-height: 1.3; margin: 0.2em 0 0.1em; }
h2 { font-size: 1.15em; border-left: 4px solid #ff7a00; padding-left: 0.5em; margin-top: 1.6em; }
.meta { color: #888; font-size: 0.85em; margin-bottom: 1.5em; }
.topics { color: #555; font-size: 0.9em; background: #f6f6f6; padding: 0.6em 0.9em;
          border-radius: 6px; margin: 1em 0; }
.note { color: #999; font-size: 0.8em; font-style: italic; border-top: 1px dashed #ccc;
        margin-top: 2em; padding-top: 0.8em; }
p { margin: 0.7em 0; }
a { color: #0a66c2; text-decoration: none; }
ul { padding-left: 1.4em; }
"""


def build_epub(meta, chapters, out_path):
    """
    生成 EPUB 3 文件。

    meta: dict，包含
        title, author, language(默认 zh-CN), description(可选)
    chapters: list[dict]，每个章节包含
        title:   章节标题（必填）
        body:    章节正文 HTML 片段（必填，会被原样放进 <body>）
    out_path: 输出 .epub 路径
    """
    lang = meta.get("language", "zh-CN")
    book_id = "urn:uuid:" + str(uuid.uuid4())
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 章节文件
    chapter_files = []
    for i, ch in enumerate(chapters, 1):
        fname = f"chap{i:02d}.xhtml"
        chapter_files.append((fname, ch["title"], _xhtml(ch["title"], ch["body"], lang)))

    # content.opf —— manifest + spine + metadata
    manifest_items = [
        '<item id="css" href="style.css" media-type="text/css"/>',
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
    ]
    spine_items = []
    for i, (fname, _title, _content) in enumerate(chapter_files, 1):
        manifest_items.append(
            f'<item id="chap{i:02d}" href="{fname}" media-type="application/xhtml+xml"/>'
        )
        spine_items.append(f'<itemref idref="chap{i:02d}"/>')

    desc = ""
    if meta.get("description"):
        desc = f'<dc:description>{html.escape(meta["description"])}</dc:description>'

    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="{lang}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">{book_id}</dc:identifier>
    <dc:title>{html.escape(meta["title"])}</dc:title>
    <dc:creator>{html.escape(meta.get("author", "Unknown"))}</dc:creator>
    <dc:language>{lang}</dc:language>
    {desc}
    <meta property="dcterms:modified">{modified}</meta>
  </metadata>
  <manifest>
    {chr(10).join("    " + m for m in manifest_items).strip()}
  </manifest>
  <spine>
    {chr(10).join("    " + s for s in spine_items).strip()}
  </spine>
</package>
"""

    # nav.xhtml —— 目录
    nav_lis = "\n".join(
        f'      <li><a href="{fname}">{html.escape(title)}</a></li>'
        for fname, title, _ in chapter_files
    )
    nav_body = f"""<nav epub:type="toc" id="toc">
  <h1>目录</h1>
  <ol>
{nav_lis}
  </ol>
</nav>"""
    nav = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{lang}" lang="{lang}">
<head><meta charset="utf-8"/><title>目录</title><link rel="stylesheet" href="style.css"/></head>
<body>
{nav_body}
</body>
</html>
"""

    container = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with zipfile.ZipFile(out_path, "w") as z:
        # mimetype 必须第一个写入且不压缩
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/style.css", CSS, compress_type=zipfile.ZIP_DEFLATED)
        for fname, _title, content in chapter_files:
            z.writestr(f"OEBPS/{fname}", content, compress_type=zipfile.ZIP_DEFLATED)

    return out_path


if __name__ == "__main__":
    from content import META, EDITIONS

    chapters = []

    # 封面/说明页
    cover_body = f"""<h1>{html.escape(META['title'])}</h1>
<p class="meta">{html.escape(META['author'])} · 中文导读合集 · 生成于 {datetime.now().strftime('%Y-%m-%d')}</p>
<p>本书收录 Matt Levine「Money Stuff」专栏最近 {len(EDITIONS)} 期的<strong>中文导读/概要</strong>，
按时间倒序排列。每期列出当期涵盖的主题，并附一段中文导读，帮助快速了解内容要点。</p>
<p class="note">说明：本书为中文「导读/概要」，并非原文全文翻译。Money Stuff 为 Bloomberg
版权专栏，原文请通过你的订阅在 Bloomberg Opinion 阅读。每期均附原文链接。</p>"""
    chapters.append({"title": "关于本书", "body": cover_body})

    for ed in EDITIONS:
        topics = ""
        if ed.get("topics"):
            lis = "".join(f"<li>{html.escape(t)}</li>" for t in ed["topics"])
            topics = f'<div class="topics"><strong>本期涵盖：</strong><ul>{lis}</ul></div>'
        link = ""
        if ed.get("url"):
            link = f'<p><a href="{html.escape(ed["url"])}">↗ 在 Bloomberg 阅读原文</a></p>'
        body = f"""<h1>{html.escape(ed['title_zh'])}</h1>
<p class="meta">{html.escape(ed.get('date', ''))} · 原题：{html.escape(ed['title_en'])}</p>
{topics}
<h2>中文导读</h2>
{ed['summary_html']}
{link}
<p class="note">以上为中文导读/概要，非原文翻译。</p>"""
        chapters.append({"title": ed["title_zh"], "body": body})

    out = os.path.join(os.path.dirname(__file__), "MoneyStuff_中文导读合集.epub")
    build_epub(META, chapters, out)
    print("已生成：", out)
