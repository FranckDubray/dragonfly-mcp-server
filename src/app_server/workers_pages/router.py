











from __future__ import annotations
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import time
import os

router = APIRouter()

FONT_HEAD = (
    "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">\n"
    "<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>\n"
    "<link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap\" rel=\"stylesheet\">\n"
)

# Simple cache-busting version for static assets (changes at server start)
ASSETS_VER = str(int(time.time()))

# Optional default language for SPA (from env). If set, injected as a meta tag the front can read.
LANG_DEFAULT = os.environ.get("WORKERS_UI_LANG_DEFAULT", "").strip()
LANG_META = (f"<meta name=\"workers-ui-lang-default\" content=\"{LANG_DEFAULT}\">\n" if LANG_DEFAULT else "")

HTML_SHELL = """\
<!doctype html><html lang=fr><head>
<meta charset=utf-8><meta name=viewport content=\"width=device-width,initial-scale=1\">\n{LANG_META}
<title>Workers</title>
{FONT_HEAD}
<link rel=\"icon\" href=\"/assets/logo.svg\" type=\"image/svg+xml\">\n
<link rel=\"stylesheet\" href=\"/static/workers/index.css?v={VER}\">\n<script type=\"module\" src=\"/static/workers/spa_main.js?v={VER}\" defer></script>
</head><body>
<div id=\"app-workers-list\" class=\"workers-list\"></div>
</body></html>
"""

@router.get("/workers", response_class=HTMLResponse)
async def workers_spa(req: Request):
    return HTMLResponse(HTML_SHELL.format(FONT_HEAD=FONT_HEAD, VER=ASSETS_VER, LANG_META=LANG_META))

@router.get("/workers/{worker_name}", response_class=HTMLResponse)
async def workers_spa_deeplink(worker_name: str):
    # Sert la même SPA et transmet le worker à ouvrir via un script inline
    html = HTML_SHELL.replace("</head>", f"<script>window.__OPEN_WORKER__='{worker_name}';</script></head>")
    return HTMLResponse(html.format(FONT_HEAD=FONT_HEAD, VER=ASSETS_VER, LANG_META=LANG_META))
