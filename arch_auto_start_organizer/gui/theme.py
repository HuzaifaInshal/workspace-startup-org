#!/usr/bin/env python3
"""Modern dark theme styling and color palette for Arch Auto-Start Organizer."""

# Color Palette (Deep Slate / KDE Plasma Breeze Dark inspired)
PALETTE = {
    "bg_window": "#16171f",
    "bg_header": "#1c1e28",
    "bg_column": "#1e202c",
    "bg_column_header": "#252837",
    "bg_card": "#242735",
    "bg_card_hover": "#2c3042",
    "bg_chip": "#1a1b24",
    
    "border_subtle": "rgba(255, 255, 255, 0.08)",
    "border_card": "rgba(255, 255, 255, 0.10)",
    "border_hover": "rgba(61, 174, 233, 0.6)",
    "border_focus": "#3daee9",
    
    "accent_primary": "#3daee9",
    "accent_hover": "#55b9eb",
    "accent_active": "#2b98d3",
    "accent_subtle": "rgba(61, 174, 233, 0.15)",
    
    "text_primary": "#f3f4f8",
    "text_secondary": "#a1a7b8",
    "text_muted": "#6e7587",
    
    "status_green": "#4ade80",
    "status_green_bg": "rgba(74, 222, 128, 0.12)",
    "status_amber": "#fbbf24",
    "status_amber_bg": "rgba(251, 191, 36, 0.12)",
    "status_red": "#f87171",
    "status_red_bg": "rgba(248, 113, 113, 0.12)",
    "status_purple": "#c084fc",
    "status_purple_bg": "rgba(192, 132, 252, 0.12)",
}

# Desktop column top-accent stripe colors
DESKTOP_ACCENT_COLORS = [
    "#3daee9",  # Desktop 1: Breeze Blue
    "#2ac3de",  # Desktop 2: Cyan
    "#a855f7",  # Desktop 3: Purple
    "#34d399",  # Desktop 4: Emerald
    "#f59e0b",  # Desktop 5: Amber
    "#ec4899",  # Desktop 6: Pink
    "#6366f1",  # Desktop 7: Indigo
    "#14b8a6",  # Desktop 8: Teal
]

GLOBAL_STYLESHEET = """
QMainWindow {
    background-color: #16171f;
}

QWidget {
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", sans-serif;
    color: #f3f4f8;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 3px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(61, 174, 233, 0.6);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 6px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 3px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(61, 174, 233, 0.6);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Tooltips */
QToolTip {
    background-color: #1f2230;
    color: #f3f4f8;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
}

/* Text Inputs */
QLineEdit {
    background-color: #1a1c26;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    color: #f3f4f8;
    padding: 7px 12px;
    font-size: 13px;
}
QLineEdit:focus {
    border: 1px solid #3daee9;
    background-color: #1e202c;
}

/* Combobox */
QComboBox {
    background-color: #1a1c26;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    color: #f3f4f8;
    padding: 6px 12px;
    font-size: 12px;
    min-height: 20px;
}
QComboBox:hover {
    border: 1px solid rgba(61, 174, 233, 0.5);
}
QComboBox:focus {
    border: 1px solid #3daee9;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: none;
}
QComboBox QAbstractItemView {
    background-color: #1f2230;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    selection-background-color: #3daee9;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

/* Buttons */
QPushButton {
    background-color: #242735;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    color: #f3f4f8;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #2c3042;
    border: 1px solid rgba(61, 174, 233, 0.5);
}
QPushButton:pressed {
    background-color: #1f2230;
}
QPushButton:disabled {
    background-color: rgba(255, 255, 255, 0.04);
    color: #6e7587;
    border-color: rgba(255, 255, 255, 0.05);
}

/* Table Widget */
QTableWidget {
    background-color: #1a1c26;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    gridline-color: rgba(255, 255, 255, 0.05);
    outline: none;
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
QTableWidget::item:selected {
    background-color: rgba(61, 174, 233, 0.2);
    color: #ffffff;
}
QHeaderView::section {
    background-color: #1f2230;
    color: #a1a7b8;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 8px;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
"""
