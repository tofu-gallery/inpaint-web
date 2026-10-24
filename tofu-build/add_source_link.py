#!/usr/bin/env python3
"""Tofu, 2026-10-24: add visible source access to the finished site without rebuilding it.

Run from outside the checkout: python3 -I /path/to/tofu-build/add_source_link.py /path/to/site/index.html
Update URL and both SOURCE.txt files when publishing a changed copy. See TOFU.md.
"""
from pathlib import Path
import re
import sys

URL = "https://github.com/tofu-gallery/inpaint-web/tree/pin/2026-10-24"
UPSTREAM = "https://github.com/lxfater/inpaint-web"
NOTE = "/* Tofu, 2026-10-24: About links point to this copy's source; see TOFU.md. */\n"
STYLE = """    <!-- Tofu, 2026-10-24: source access has its own row above the app; see TOFU.md. -->
    <style>
      #root { position: relative; height: calc(100vh - 32px); height: calc(100dvh - 32px) }
      #root main { height: calc(100vh - 88px) !important; height: calc(100dvh - 88px) !important }
      .tofu-source { display: flex; justify-content: flex-start; min-height: 32px; margin: 0; font-size: 14px; background: #fff }
      .tofu-source a { display: inline-flex; align-items: center; min-height: 32px; padding: 0 12px; color: #2563eb; text-decoration: underline }
      .tofu-source a:hover { color: #1d4ed8 }
    </style>
"""
LINK = f"""    <!-- Tofu, 2026-10-24: complete source of this copy, visible before the app loads. -->
    <nav class="tofu-source" aria-label="Source code"><a href="{URL}" target="_blank" rel="noopener noreferrer">Source code</a></nav>
"""


def main(path):
    page = path.read_text(encoding="utf-8")
    head_end = "  </head>\n"
    body_start = '  <body class="h-screen">\n'
    scripts = re.findall(r'<script type="module" crossorigin src="(/assets/[^"/]+\.js)"></script>', page)
    if "tofu-source" in page or page.count(head_end) != 1 or page.count(body_start) != 1 or len(scripts) != 1:
        sys.exit("Unexpected page or source link already present; nothing changed")
    bundle_path = path.parent / scripts[0].lstrip("/")
    bundle = bundle_path.read_text(encoding="utf-8")
    old_href = f'href:"{UPSTREAM}"'
    new_href = f'href:"{URL}"'
    if bundle.count(old_href) == 2 and bundle.count(new_href) == 0:
        bundle = bundle.replace(old_href, new_href)
    elif bundle.count(old_href) != 0 or bundle.count(new_href) != 2:
        sys.exit("Unexpected About links; nothing changed")
    page = page.replace(head_end, STYLE + head_end).replace(body_start, body_start + LINK)
    path.write_text(page, encoding="utf-8")
    bundle_path.write_text(NOTE + bundle, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python3 -I add_source_link.py /path/to/site/index.html")
    main(Path(sys.argv[1]))
