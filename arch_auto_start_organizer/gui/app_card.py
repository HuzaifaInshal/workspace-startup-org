#!/usr/bin/env python3
"""Redesigned modern application card widget with vertical hierarchy and clean spacing."""

from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QWidget,
    QSizePolicy,
)

from arch_auto_start_organizer.core.config import AppItem
from arch_auto_start_organizer.gui.toggle_switch import ToggleSwitch


class AppCard(QFrame):
    """Modern card widget representing an application in the Workspace Board."""

    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    toggle_enabled = pyqtSignal(str, bool)
    desktop_changed = pyqtSignal(str, int)
    test_launch_requested = pyqtSignal(str)

    def __init__(
        self,
        app: AppItem,
        desktops: Optional[List[Dict[str, Any]]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.app = app
        self.desktops = desktops or []
        self._init_ui()

    def _init_ui(self) -> None:
        self.setObjectName("AppCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(10)

        # -------------------------------------------------------------
        # Row 1: Header (Icon, App Name + Status, Toggle Switch)
        # -------------------------------------------------------------
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        # App Icon inside a soft badge
        self.icon_badge = QLabel()
        self.icon_badge.setFixedSize(40, 40)
        self.icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_badge.setStyleSheet(
            """
            QLabel {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
            }
            """
        )
        self._load_icon()
        header_row.addWidget(self.icon_badge)

        # Title & Subtitle container
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        self.name_label = QLabel(self.app.name)
        self.name_label.setToolTip(self.app.name)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.name_label.setFont(title_font)
        self.name_label.setStyleSheet("color: #f3f4f8;")
        title_box.addWidget(self.name_label)

        # Status indicator text
        status_text = "Enabled on startup" if self.app.enabled else "Disabled"
        status_color = "#4ade80" if self.app.enabled else "#6e7587"
        self.status_label = QLabel(f"● {status_text}")
        self.status_label.setStyleSheet(f"color: {status_color}; font-size: 11px;")
        title_box.addWidget(self.status_label)

        header_row.addLayout(title_box, stretch=1)

        # Modern Toggle Switch
        self.toggle_switch = ToggleSwitch(checked=self.app.enabled)
        self.toggle_switch.setToolTip("Toggle startup status")
        self.toggle_switch.toggled.connect(self._on_toggle)
        header_row.addWidget(self.toggle_switch)

        card_layout.addLayout(header_row)

        # -------------------------------------------------------------
        # Row 2: Command & Rule Chips
        # -------------------------------------------------------------
        chips_layout = QVBoxLayout()
        chips_layout.setSpacing(4)

        # Executable chip with smart elision for long commands
        raw_cmd = self.app.command if self.app.command else "(no command specified)"
        display_cmd = raw_cmd if len(raw_cmd) <= 38 else raw_cmd[:35] + "..."
        cmd_chip = QLabel(f"▶ <code>{display_cmd}</code>")
        cmd_chip.setToolTip(f"Launch Command:\n{raw_cmd}")
        cmd_chip.setStyleSheet(
            """
            QLabel {
                background-color: #1a1c26;
                color: #a1a7b8;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }
            """
        )
        chips_layout.addWidget(cmd_chip)

        # Match Rule & Delay Chips (Horizontal)
        tags_row = QHBoxLayout()
        tags_row.setSpacing(6)

        if self.app.match_rule:
            raw_rule = self.app.match_rule
            display_rule = raw_rule if len(raw_rule) <= 22 else raw_rule[:19] + "..."
            rule_chip = QLabel(f"🎯 Match: {display_rule}")
            rule_chip.setToolTip(f"KWin Window Match Rule:\n{raw_rule}")
            rule_chip.setStyleSheet(
                """
                QLabel {
                    background-color: rgba(61, 174, 233, 0.12);
                    color: #55b9eb;
                    border-radius: 4px;
                    padding: 2px 6px;
                    font-size: 10px;
                    font-weight: 500;
                }
                """
            )
            tags_row.addWidget(rule_chip)

        if self.app.delay > 0:
            delay_chip = QLabel(f"⏱ +{self.app.delay}s delay")
            delay_chip.setStyleSheet(
                """
                QLabel {
                    background-color: rgba(251, 191, 36, 0.12);
                    color: #fbbf24;
                    border-radius: 4px;
                    padding: 2px 6px;
                    font-size: 10px;
                }
                """
            )
            tags_row.addWidget(delay_chip)

        tags_row.addStretch()
        chips_layout.addLayout(tags_row)
        card_layout.addLayout(chips_layout)

        # -------------------------------------------------------------
        # Row 3: Footer Controls (Move Desktop Dropdown + Action Buttons)
        # -------------------------------------------------------------
        footer_row = QHBoxLayout()
        footer_row.setSpacing(6)

        # Move Desktop Combobox
        self.desktop_combo = QComboBox()
        self.desktop_combo.setToolTip("Move application to another Virtual Desktop")
        self.desktop_combo.setMinimumWidth(95)
        self.desktop_combo.setMaximumWidth(125)
        self._populate_desktops()
        self.desktop_combo.currentIndexChanged.connect(self._on_desktop_combo_changed)
        footer_row.addWidget(self.desktop_combo)

        footer_row.addStretch()

        # Action Buttons (Icon-only, compact & modern)
        # Test Run Button
        self.run_btn = QPushButton("▶")
        self.run_btn.setFixedSize(30, 30)
        self.run_btn.setToolTip("Test launch this application now")
        self.run_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(74, 222, 128, 0.12);
                color: #4ade80;
                border: 1px solid rgba(74, 222, 128, 0.3);
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(74, 222, 128, 0.28);
                border-color: #4ade80;
            }
            """
        )
        self.run_btn.clicked.connect(lambda: self.test_launch_requested.emit(self.app.id))
        footer_row.addWidget(self.run_btn)

        # Edit Button
        self.edit_btn = QPushButton("✏")
        self.edit_btn.setFixedSize(30, 30)
        self.edit_btn.setToolTip("Edit application details and rules")
        self.edit_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #242735;
                color: #f3f4f8;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                font-size: 12px;
                padding: 0;
            }
            QPushButton:hover {
                border-color: #3daee9;
                color: #3daee9;
                background-color: rgba(61, 174, 233, 0.15);
            }
            """
        )
        self.edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.app.id))
        footer_row.addWidget(self.edit_btn)

        # Delete Button
        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(30, 30)
        self.del_btn.setToolTip("Remove application from startup")
        self.del_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(248, 113, 113, 0.1);
                color: #f87171;
                border: 1px solid rgba(248, 113, 113, 0.25);
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(248, 113, 113, 0.28);
                border-color: #f87171;
            }
            """
        )
        self.del_btn.clicked.connect(lambda: self.delete_requested.emit(self.app.id))
        footer_row.addWidget(self.del_btn)

        card_layout.addLayout(footer_row)
        self._update_card_style()

    def _load_icon(self) -> None:
        icon = QIcon.fromTheme(self.app.icon)
        if icon.isNull() and "/" in self.app.icon:
            icon = QIcon(self.app.icon)
        if icon.isNull():
            icon = QIcon.fromTheme("application-x-executable")
        self.icon_badge.setPixmap(icon.pixmap(28, 28))

    def _populate_desktops(self) -> None:
        self.desktop_combo.blockSignals(True)
        self.desktop_combo.clear()
        count = max(4, len(self.desktops), self.app.desktop)
        for i in range(1, count + 1):
            name = f"Desktop {i}"
            for d in self.desktops:
                if d.get("number") == i and d.get("name"):
                    name = d["name"]
                    break
            self.desktop_combo.addItem(name, userData=i)

        idx = self.desktop_combo.findData(self.app.desktop)
        if idx != -1:
            self.desktop_combo.setCurrentIndex(idx)
        self.desktop_combo.blockSignals(False)

    def _on_desktop_combo_changed(self, index: int) -> None:
        new_desktop = self.desktop_combo.currentData()
        if new_desktop and new_desktop != self.app.desktop:
            self.desktop_changed.emit(self.app.id, new_desktop)

    def _on_toggle(self, checked: bool) -> None:
        self.app.enabled = checked
        status_text = "Enabled on startup" if checked else "Disabled"
        status_color = "#4ade80" if checked else "#6e7587"
        self.status_label.setText(f"● {status_text}")
        self.status_label.setStyleSheet(f"color: {status_color}; font-size: 11px;")
        self._update_card_style()
        self.toggle_enabled.emit(self.app.id, checked)

    def _update_card_style(self) -> None:
        if self.app.enabled:
            self.setStyleSheet(
                """
                QFrame#AppCard {
                    background-color: #242735;
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 12px;
                }
                QFrame#AppCard:hover {
                    border: 1px solid rgba(61, 174, 233, 0.6);
                    background-color: #282c3c;
                }
                """
            )
            self.name_label.setStyleSheet("color: #f3f4f8; font-weight: bold; font-size: 13px;")
            self.icon_badge.setStyleSheet(
                """
                QLabel {
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 10px;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                QFrame#AppCard {
                    background-color: rgba(22, 23, 31, 0.7);
                    border: 1px dashed rgba(255, 255, 255, 0.08);
                    border-radius: 12px;
                }
                QFrame#AppCard:hover {
                    border: 1px dashed rgba(255, 255, 255, 0.2);
                }
                """
            )
            self.name_label.setStyleSheet("color: #6e7587; font-weight: bold; font-size: 13px;")
            self.icon_badge.setStyleSheet(
                """
                QLabel {
                    background-color: rgba(255, 255, 255, 0.02);
                    border: 1px solid rgba(255, 255, 255, 0.04);
                    border-radius: 10px;
                    opacity: 0.5;
                }
                """
            )
