"""Web UI Aggregator Module for Antigravity Dual Ingress.
Combines modular styles, HTML templates, JavaScript client app, and markdown parser.
"""

from core.markdown_parser import MARKDOWN_JS_MODULE
from core.ui import UI_BUILD_VERSION
from core.ui.styles import CSS_STYLES
from core.ui.templates import HTML_BODY
from core.ui.scripts import JS_SCRIPTS

RENDERED_HTML_BODY = HTML_BODY.replace("{UI_BUILD_VERSION}", UI_BUILD_VERSION)

HTML_INDEX = f"""<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Google Antigravity Smart Home</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  <style>
{CSS_STYLES}
  </style>
</head>
<body>
{RENDERED_HTML_BODY}
  <script>
{MARKDOWN_JS_MODULE}

{JS_SCRIPTS}
  </script>
</body>
</html>
"""
