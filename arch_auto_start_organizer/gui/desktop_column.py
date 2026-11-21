#!/usr/bin/env python3
"""Dedicated responsive column widget for a virtual desktop in the Workspace Board."""

from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QSizePolicy,
)

from arch_auto_start_organizer.core.config import AppItem
from arch_auto_start_organizer.gui.app_card import AppCard
from arch_auto_start_organizer.gui.theme import DESKTOP_ACCENT_COLORS


class DesktopColumn(QFrame):
    """Full-height responsive column representing a single virtual desktop."""

    add_app_requested = pyqtSignal(int)
    app_edit_requested = pyqtSignal(str)
    app_delete_requested = pyqtSignal(str)
    app_toggle_enabled = pyqtSignal(str, bool)
    app_desktop_changed = pyqtSignal(str, int)
    app_test_launch_requested = pyqtSignal(str)

    def __init__(
        self,
        desktop_num: int,
        desktop_name: str,
        apps: List[AppItem],
        all_desktops: List[Dict[str, Any]],
        parent=None,
    ):
        super().__init__(parent)
        self.desktop_num = desktop_num
        self.desktop_name = desktop_name
        self.apps = apps
        self.all_desktops = all_desktops

        self._init_ui()

    def _init_ui(self) -> None:
        self.setObjectName("DesktopColumn")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(260)

        # Main layout of the column
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Accent Stripe
        accent_color = DESKTOP_ACCENT_COLORS[(self.desktop_num - 1) % len(DESKTOP_ACCENT_COLORS)]
        stripe = QFrame()
        stripe.setFixedHeight(4)
        stripe.setStyleSheet(f"background-color: {accent_color}; border-top-left-radius: 12px; border-top-right-radius: 12px;")
        main_layout.addWidget(stripe)

        # Column Inner Container
        inner = QFrame()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(12, 12, 12, 12)
        inner_layout.setSpacing(10)

        # 2. Header Frame
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Desktop title
        title_label = QLabel(self.desktop_name)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #f3f4f8;")
        header_layout.addWidget(title_label)

        # Count badge
        app_count = len(self.apps)
        count_text = f"{app_count} app" if app_count == 1 else f"{app_count} apps"
        count_badge = QLabel(count_text)
        count_badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: rgba(255, 255, 255, 0.08);
                color: #a1a7b8;
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            }}
            """
        )
        header_layout.addWidget(count_badge)

        header_layout.addStretch()

        # Quick Add Button in header
        add_icon_btn = QPushButton("+")
        add_icon_btn.setFixedSize(26, 26)
        add_icon_btn.setToolTip(f"Add application to {self.desktop_name}")
        add_icon_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 13px;
                color: #f3f4f8;
                font-size: 14px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #3daee9;
                border-color: #3daee9;
                color: #ffffff;
            }
            """
        )
        add_icon_btn.clicked.connect(lambda: self.add_app_requested.emit(self.desktop_num))
        header_layout.addWidget(add_icon_btn)

        inner_layout.addLayout(header_layout)

        # 3. Scrollable Cards Container (Takes full vertical space)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        cards_container = QWidget()
        cards_container.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(10)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        if not self.apps:
            # Elegant Empty State
            empty_frame = QFrame()
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setContentsMargins(10, 30, 10, 30)
            empty_layout.setSpacing(10)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            empty_icon = QLabel("🪟")
            empty_icon.setStyleSheet("font-size: 28px;")
            empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_icon)

            empty_title = QLabel("No apps assigned")
            empty_title.setStyleSheet("font-weight: 600; color: #a1a7b8; font-size: 13px;")
            empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_title)

            empty_desc = QLabel("Applications assigned to this virtual desktop will appear here.")
            empty_desc.setWordWrap(True)
            empty_desc.setStyleSheet("color: #6e7587; font-size: 11px;")
            empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_desc)

            cards_layout.addWidget(empty_frame)
        else:
            for app in self.apps:
                card = AppCard(app=app, desktops=self.all_desktops)
                card.edit_requested.connect(self.app_edit_requested.emit)
                card.delete_requested.connect(self.app_delete_requested.emit)
                card.toggle_enabled.connect(self.app_toggle_enabled.emit)
                card.desktop_changed.connect(self.app_desktop_changed.emit)
                card.test_launch_requested.connect(self.app_test_launch_requested.emit)
                cards_layout.addWidget(card)

        scroll.setWidget(cards_container)
        inner_layout.addWidget(scroll, stretch=1)

        # 4. Footer Add Button
        footer_add_btn = QPushButton(f"＋ Add to {self.desktop_name}")
        footer_add_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px dashed rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                color: #a1a7b8;
                padding: 8px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(61, 174, 233, 0.12);
                border-color: #3daee9;
                color: #3daee9;
            }
            """
        )
        footer_add_btn.clicked.connect(lambda: self.add_app_requested.emit(self.desktop_num))
        inner_layout.addWidget(footer_add_btn)

        main_layout.addWidget(inner)

        # Column Styling
        self.setStyleSheet(
            """
            QFrame#DesktopColumn {
                background-color: #1e202c;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
            """
        )


class AddDesktopColumn(QFrame):
    """Placeholder column inviting creation of a new Virtual Desktop."""

    create_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AddDesktopColumn")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(160)
        self.setMaximumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon_lbl = QLabel("➕")
        icon_lbl.setStyleSheet("font-size: 26px; color: #a1a7b8;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        title_lbl = QLabel("New Desktop")
        title_lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #f3f4f8;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        desc_lbl = QLabel("Create another virtual desktop in KWin")
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #6e7587; font-size: 11px;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_lbl)

        btn = QPushButton("Add Virtual Desktop")
        btn.setStyleSheet(
            """
            QPushButton {
                background-color: #242735;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                color: #f3f4f8;
                padding: 7px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                border-color: #3daee9;
                color: #3daee9;
                background-color: #2c3042;
            }
            """
        )
        btn.clicked.connect(self.create_requested.emit)
        layout.addWidget(btn)

        self.setStyleSheet(
            """
            QFrame#AddDesktopColumn {
                background-color: rgba(255, 255, 255, 0.02);
                border: 1px dashed rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
            QFrame#AddDesktopColumn:hover {
                border-color: rgba(61, 174, 233, 0.4);
                background-color: rgba(255, 255, 255, 0.03);
            }
            """
        )
