"""Rich Markdown viewer using QTextBrowser with custom dark CSS.

Replaces QWebEngineView (which has async paint issues) with a lightweight
QTextBrowser that renders HTML synchronously so content appears immediately.
"""

import html
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTextBrowser

from .theme import QuantumTheme


class MarkdownViewer(QTextBrowser):
    """A dark-themed markdown renderer for the job detail pane."""

    # ── lightweight regex-based markdown → HTML converter ────────────
    _HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
    _BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
    _ITALIC_RE = re.compile(r"\*(.+?)\*")
    _HR_RE = re.compile(r"^\s*---\s*$", re.MULTILINE)
    _LIST_ITEM_RE = re.compile(r"^\s*[-*]\s+(.*)$", re.MULTILINE)
    _LINK_RE = re.compile(r"\[(.+?)\]\((.+?)\)")
    _CODE_INLINE_RE = re.compile(r"`([^`]+)`")

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(300)
        self.setMinimumWidth(200)
        self.setOpenExternalLinks(True)
        self.setReadOnly(True)
        # Remove default white QTextBrowser chrome
        self.setFrameStyle(0)
        self.viewport().setAutoFillBackground(False)
        # Prevent internal scrollbars — the card handles scrolling
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def set_markdown(self, markdown: str | None) -> None:
        """Render *markdown* as styled HTML inside the text browser."""
        if not markdown:
            markdown = "No description available."
        html_body = self._md_to_html(markdown)
        full_html = self._wrap(html_body)
        self.setHtml(full_html)

    # ── Internal helpers ─────────────────────────────────────────────

    @classmethod
    def _md_to_html(cls, text: str) -> str:
        """Convert simple markdown to HTML (safe, no external deps)."""
        # Escape raw HTML first so user content can't inject scripts
        text = html.escape(text)

        # Horizontal rules
        text = cls._HR_RE.sub("<hr/>", text)

        # Headers
        def _header_repl(m: re.Match) -> str:
            level = len(m.group(1))
            tag = f"h{level}"
            return f"<{tag}>{m.group(2)}</{tag}>"
        text = cls._HEADER_RE.sub(_header_repl, text)

        # Bold / italic
        text = cls._BOLD_RE.sub(r"<strong>\1</strong>", text)
        text = cls._ITALIC_RE.sub(r"<em>\1</em>", text)

        # Inline code
        text = cls._CODE_INLINE_RE.sub(r"<code>\1</code>", text)

        # Links
        text = cls._LINK_RE.sub(r'<a href="\2">\1</a>', text)

        # Lists: group consecutive list items into <ul> blocks
        lines = text.splitlines()
        out_lines: list[str] = []
        in_list = False
        for line in lines:
            m = cls._LIST_ITEM_RE.match(line)
            if m:
                if not in_list:
                    out_lines.append("<ul>")
                    in_list = True
                out_lines.append(f"<li>{m.group(1)}</li>")
            else:
                if in_list:
                    out_lines.append("</ul>")
                    in_list = False
                out_lines.append(line)
        if in_list:
            out_lines.append("</ul>")

        # Paragraphs: wrap non-empty, non-block lines in <p>
        result_lines: list[str] = []
        for line in out_lines:
            stripped = line.strip()
            if not stripped:
                result_lines.append("")
                continue
            if stripped.startswith("<"):
                result_lines.append(line)
            else:
                result_lines.append(f"<p>{stripped}</p>")

        return "\n".join(result_lines)

    @classmethod
    def _wrap(cls, body: str) -> str:
        """Wrap HTML body in a full dark-themed document."""
        t = QuantumTheme
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  :root {{
    --bg: {t.BG_INPUT};
    --fg: {t.TEXT_SECONDARY};
    --heading: {t.TEXT_PRIMARY};
    --accent: {t.ACCENT_PRIMARY};
    --border: {t.BORDER};
    --font: {t.FONT_FAMILY};
    --font-mono: {t.FONT_MONO};
  }}
  body {{
    margin: 0;
    padding: 14px 18px;
    background-color: var(--bg);
    color: var(--fg);
    font-family: var(--font);
    font-size: 13px;
    line-height: 1.65;
  }}
  h1, h2, h3, h4, h5, h6 {{
    color: var(--heading);
    margin-top: 18px;
    margin-bottom: 8px;
    font-weight: 700;
    letter-spacing: -0.3px;
  }}
  h1 {{ font-size: 20px; }}
  h2 {{ font-size: 17px; color: var(--accent); border-bottom: 1px solid var(--border); padding-bottom: 4px; }}
  h3 {{ font-size: 15px; }}
  p {{ margin: 0 0 10px 0; }}
  ul {{
    margin: 0 0 12px 0;
    padding-left: 20px;
  }}
  li {{ margin-bottom: 4px; }}
  strong {{ color: var(--heading); font-weight: 700; }}
  em {{ font-style: italic; opacity: 0.9; }}
  code {{
    font-family: var(--font-mono);
    background: rgba(0, 229, 255, 0.08);
    color: var(--accent);
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 12px;
  }}
  a {{
    color: var(--accent);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-bottom 0.2s;
  }}
  a:hover {{ border-bottom: 1px solid var(--accent); }}
  hr {{
    border: none;
    border-top: 1px solid var(--border);
    margin: 14px 0;
  }}
</style>
</head>
<body>
{body}
</body>
</html>"""
