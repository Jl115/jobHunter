"""Quantum Dark Theme — a cohesive 2027-era visual system for PySide6.

Usage::

    from widgets.theme import QuantumTheme
    QuantumTheme.apply(app)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication


class QuantumTheme:
    """Modern dark theme with cyan accents, rounded cards, and subtle glows.

    Inspired by glass-morphism design language adapted for native desktop performance.
    """

    # ── Palette ──────────────────────────────────────────────────────
    BG_DEEP = "#060a14"          # Deepest background layer
    BG_BASE = "#0b0f1a"          # Base application background
    BG_CARD = "#111827"          # Elevated card surfaces
    BG_INPUT = "#0f1420"         # Input / editor backgrounds
    BG_HOVER = "#1a2035"         # Hover state overlay
    BG_GLASS = "rgba(17, 24, 39, 0.92)"  # Translucent glass card

    BORDER = "#1e2538"           # Subtle dividers
    BORDER_FOCUS = "#00e5ff"     # Cyan glow on focus
    BORDER_DANGER = "#ff4d6d"    # Error / destructive accent
    BORDER_SUCCESS = "#00f5a0"   # Success / positive accent
    BORDER_WARNING = "#f59e0b"   # Warning / gold accent

    TEXT_PRIMARY = "#e2e8f0"     # Headings, primary labels
    TEXT_SECONDARY = "#94a3b8"   # Body text, descriptions
    TEXT_MUTED = "#64748b"       # Placeholders, hints

    ACCENT_PRIMARY = "#00e5ff"   # Cyan — interactive highlights
    ACCENT_SECONDARY = "#7c3aed" # Violet — badges, tags
    ACCENT_GOLD = "#f59e0b"      # Gold — scores, ratings

    # Platform brand colours
    BADGE_LINKEDIN = "#0A66C2"
    BADGE_INDEED = "#FF5A1F"
    BADGE_XING = "#069B3E"

    # Score colour thresholds
    SCORE_HIGH = "#00f5a0"
    SCORE_MID = "#f59e0b"
    SCORE_LOW = "#ff4d6d"

    SHADOW_RGBA = "0, 0, 0, 120" # Card drop-shadow colour

    # ── Typography ──────────────────────────────────────────────────
    FONT_FAMILY = "-apple-system, SF Pro Display, Segoe UI, Roboto, Inter, sans-serif"
    FONT_MONO = "JetBrains Mono, SF Mono, Consolas, monospace"

    # Font sizes
    SIZE_HERO = "26px"
    SIZE_TITLE = "18px"
    SIZE_SUBTITLE = "14px"
    SIZE_BODY = "13px"
    SIZE_SMALL = "11px"
    SIZE_TINY = "10px"

    @classmethod
    def apply(cls, app: QApplication) -> None:
        """Install the Quantum Dark stylesheet and palette on *app*."""
        cls._set_palette(app)
        app.setStyleSheet(cls.build_stylesheet())
        cls._set_global_font(app)

    # ── QSS Factory ──────────────────────────────────────────────────
    @classmethod
    def build_stylesheet(cls) -> str:
        """Return the full Quantum Dark QSS string."""
        return f"""
        /* ── Application shell ──────────────────────────────────── */
        QMainWindow {{
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {cls.BG_DEEP}, stop:1 #0d1321);
            border: none;
        }}
        QWidget {{
            background-color: transparent;
            color: {cls.TEXT_PRIMARY};
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.SIZE_BODY};
        }}

        /* ── Toolbar ─────────────────────────────────────────────── */
        QToolBar {{
            background-color: {cls.BG_CARD};
            border-bottom: 1px solid {cls.BORDER};
            padding: 8px 16px;
            spacing: 12px;
        }}
        QToolBar QToolButton {{
            background-color: transparent;
            color: {cls.TEXT_SECONDARY};
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 500;
        }}
        QToolBar QToolButton:hover {{
            background-color: {cls.BG_HOVER};
            color: {cls.TEXT_PRIMARY};
        }}
        QToolBar QToolButton:pressed {{
            background-color: {cls.BG_INPUT};
        }}

        /* ── Status bar ──────────────────────────────────────────── */
        QStatusBar {{
            background-color: {cls.BG_CARD};
            color: {cls.TEXT_MUTED};
            border-top: 1px solid {cls.BORDER};
            font-size: {cls.SIZE_SMALL};
            padding: 4px 16px;
        }}
        QStatusBar QLabel {{
            background: transparent;
            color: {cls.TEXT_MUTED};
        }}

        /* ── Push Buttons ────────────────────────────────────────── */
        QPushButton {{
            background-color: {cls.BG_CARD};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 12px;
            padding: 10px 24px;
            font-weight: 600;
            outline: none;
        }}
        QPushButton:hover {{
            background-color: {cls.BG_HOVER};
            border-color: {cls.BORDER_FOCUS};
            color: {cls.ACCENT_PRIMARY};
        }}
        QPushButton:pressed {{
            background-color: {cls.BG_INPUT};
        }}
        QPushButton:disabled {{
            background-color: {cls.BG_BASE};
            color: {cls.TEXT_MUTED};
            border-color: {cls.BORDER};
        }}
        /* Primary action variant (set objectName="primary") */
        QPushButton#primary {{
            background-color: {cls.ACCENT_PRIMARY};
            color: {cls.BG_DEEP};
            border: none;
        }}
        QPushButton#primary:hover {{
            background-color: #33ebff;
        }}
        QPushButton#primary:pressed {{
            background-color: #00c2d4;
        }}
        /* Success variant */
        QPushButton#success {{
            background-color: {cls.BORDER_SUCCESS};
            color: {cls.BG_DEEP};
            border: none;
        }}
        QPushButton#success:hover {{
            background-color: #33ffbb;
        }}
        /* Danger variant */
        QPushButton#danger {{
            background-color: {cls.BORDER_DANGER};
            color: {cls.BG_DEEP};
            border: none;
        }}
        QPushButton#danger:hover {{
            background-color: #ff6b85;
        }}

        /* ── Line Edit ───────────────────────────────────────────── */
        QLineEdit {{
            background-color: {cls.BG_INPUT};
            color: {cls.TEXT_PRIMARY};
            border: 1px solid {cls.BORDER};
            border-radius: 10px;
            padding: 10px 14px;
            selection-background-color: {cls.ACCENT_PRIMARY};
            selection-color: {cls.BG_DEEP};
        }}
        QLineEdit:focus {{
            border-color: {cls.BORDER_FOCUS};
        }}
        QLineEdit::placeholder {{
            color: {cls.TEXT_MUTED};
        }}

        /* ── Text Edit ───────────────────────────────────────────── */
        QTextEdit {{
            background-color: {cls.BG_INPUT};
            color: {cls.TEXT_SECONDARY};
            border: 1px solid {cls.BORDER};
            border-radius: 12px;
            padding: 14px;
            selection-background-color: {cls.ACCENT_PRIMARY};
            selection-color: {cls.BG_DEEP};
            font-family: {cls.FONT_FAMILY};
            font-size: {cls.SIZE_BODY};
            line-height: 1.6;
        }}
        QTextEdit:focus {{
            border-color: {cls.BORDER_FOCUS};
        }}
        QTextEdit::placeholder {{
            color: {cls.TEXT_MUTED};
        }}

        /* ── Table Widget ──────────────────────────────────────────── */
        QTableWidget {{
            background-color: {cls.BG_BASE};
            alternate-background-color: {cls.BG_CARD};
            border: 1px solid {cls.BORDER};
            border-radius: 16px;
            gridline-color: transparent;
            selection-background-color: {cls.BG_HOVER};
            selection-color: {cls.TEXT_PRIMARY};
            outline: none;
        }}
        QTableWidget::item {{
            padding: 12px 16px;
            border-bottom: 1px solid {cls.BORDER};
        }}
        QTableWidget::item:selected {{
            background-color: {cls.BG_HOVER};
            color: {cls.ACCENT_PRIMARY};
        }}
        QHeaderView::section {{
            background-color: {cls.BG_CARD};
            color: {cls.TEXT_PRIMARY};
            padding: 12px 16px;
            border: none;
            border-bottom: 2px solid {cls.BORDER};
            font-weight: 600;
            font-size: {cls.SIZE_SMALL};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        QHeaderView::section:hover {{
            background-color: {cls.BG_HOVER};
        }}
        QTableCornerButton::section {{
            background-color: {cls.BG_CARD};
            border-bottom: 2px solid {cls.BORDER};
        }}

        /* ── Scroll Bars ──────────────────────────────────────────── */
        QScrollBar:vertical {{
            background-color: transparent;
            width: 6px;
            border-radius: 3px;
            margin: 4px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {cls.BORDER};
            border-radius: 3px;
            min-height: 40px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {cls.BORDER_FOCUS};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background-color: transparent;
            height: 6px;
            border-radius: 3px;
            margin: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {cls.BORDER};
            border-radius: 3px;
            min-width: 40px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {cls.BORDER_FOCUS};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* ── Labels ───────────────────────────────────────────────── */
        QLabel {{
            background: transparent;
            color: {cls.TEXT_SECONDARY};
        }}
        QLabel#heading {{
            color: {cls.TEXT_PRIMARY};
            font-size: {cls.SIZE_HERO};
            font-weight: 800;
            letter-spacing: -0.5px;
        }}
        QLabel#title {{
            color: {cls.TEXT_PRIMARY};
            font-size: {cls.SIZE_TITLE};
            font-weight: 700;
        }}
        QLabel#subtitle {{
            color: {cls.TEXT_SECONDARY};
            font-size: {cls.SIZE_SUBTITLE};
            font-weight: 500;
        }}
        QLabel#muted {{
            color: {cls.TEXT_MUTED};
            font-size: {cls.SIZE_BODY};
            font-weight: 400;
        }}
        QLabel#badge {{
            background-color: {cls.ACCENT_SECONDARY};
            color: {cls.TEXT_PRIMARY};
            border-radius: 8px;
            padding: 3px 12px;
            font-size: {cls.SIZE_TINY};
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        QLabel#badge-linkedin {{
            background-color: {cls.BADGE_LINKEDIN};
            color: #ffffff;
            border-radius: 8px;
            padding: 3px 12px;
            font-size: {cls.SIZE_TINY};
            font-weight: 700;
        }}
        QLabel#badge-indeed {{
            background-color: {cls.BADGE_INDEED};
            color: #ffffff;
            border-radius: 8px;
            padding: 3px 12px;
            font-size: {cls.SIZE_TINY};
            font-weight: 700;
        }}
        QLabel#badge-xing {{
            background-color: {cls.BADGE_XING};
            color: #ffffff;
            border-radius: 8px;
            padding: 3px 12px;
            font-size: {cls.SIZE_TINY};
            font-weight: 700;
        }}
        QLabel#success-badge {{
            background-color: {cls.BORDER_SUCCESS};
            color: {cls.BG_DEEP};
            border-radius: 8px;
            padding: 3px 12px;
            font-size: {cls.SIZE_TINY};
            font-weight: 700;
        }}
        QLabel#gold-badge {{
            background-color: {cls.ACCENT_GOLD};
            color: {cls.BG_DEEP};
            border-radius: 8px;
            padding: 3px 12px;
            font-size: {cls.SIZE_TINY};
            font-weight: 700;
        }}
        QLabel#danger-badge {{
            background-color: {cls.BORDER_DANGER};
            color: {cls.BG_DEEP};
            border-radius: 8px;
            padding: 3px 12px;
            font-size: {cls.SIZE_TINY};
            font-weight: 700;
        }}
        QLabel#score-label {{
            color: {cls.ACCENT_PRIMARY};
            font-size: 36px;
            font-weight: 800;
            letter-spacing: -1px;
        }}

        /* ── Form / Card Containers ──────────────────────────────── */
        QWidget#card {{
            background-color: {cls.BG_CARD};
            border: 1px solid {cls.BORDER};
            border-radius: 18px;
        }}
        QFrame#card {{
            background-color: {cls.BG_CARD};
            border: 1px solid {cls.BORDER};
            border-radius: 18px;
        }}

        /* ── Dialog / Message Box ─────────────────────────────────── */
        QMessageBox {{
            background-color: {cls.BG_CARD};
            border: 1px solid {cls.BORDER};
            border-radius: 18px;
        }}
        QMessageBox QLabel {{
            color: {cls.TEXT_PRIMARY};
        }}

        /* ── File Dialog ──────────────────────────────────────────── */
        QFileDialog {{
            background-color: {cls.BG_BASE};
        }}
        """

    # ── Palette ─────────────────────────────────────────────────────
    @classmethod
    def _set_palette(cls, app: QApplication) -> None:
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(cls.BG_BASE))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(cls.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Base, QColor(cls.BG_INPUT))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(cls.BG_CARD))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(cls.BG_CARD))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(cls.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Text, QColor(cls.TEXT_SECONDARY))
        palette.setColor(QPalette.ColorRole.Button, QColor(cls.BG_CARD))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.TEXT_PRIMARY))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(cls.ACCENT_PRIMARY))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(cls.BG_DEEP))
        app.setPalette(palette)

    @classmethod
    def _set_global_font(cls, app: QApplication) -> None:
        font = QFont(cls.FONT_FAMILY.split(",")[0].strip(), 13)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        app.setFont(font)

    # ── Runtime helpers ──────────────────────────────────────────────
    @staticmethod
    def apply_card_shadow(widget) -> None:
        """Attach a subtle drop-shadow effect to a widget."""
        from PySide6.QtWidgets import QGraphicsDropShadowEffect

        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(32)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 100))
        widget.setGraphicsEffect(shadow)

    @staticmethod
    def glow_border(widget, color: str = "#00e5ff") -> None:
        """Attach a glowing border effect."""
        from PySide6.QtWidgets import QGraphicsDropShadowEffect

        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(color))
        widget.setGraphicsEffect(shadow)

    @classmethod
    def score_color(cls, score: float) -> str:
        """Return a colour for the given match score."""
        if score >= 0.7:
            return cls.SCORE_HIGH
        if score >= 0.4:
            return cls.SCORE_MID
        return cls.SCORE_LOW

    @classmethod
    def score_label(cls, score: float) -> str:
        """Return a human label for the given match score."""
        if score >= 0.7:
            return "Strong Match"
        if score >= 0.4:
            return "Good Match"
        return "Weak Match"
