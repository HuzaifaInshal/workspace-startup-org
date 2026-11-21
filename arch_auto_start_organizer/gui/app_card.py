#!/usr/bin/env python3
"""Card widget representing an application in the Workspace Board view."""

from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,
    QMenu,
)

from arch_auto_start_organizer.core.config import AppItem


class AppCard(QFrame):
    """Visual card representing an application configured for a virtual desktop."""

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
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setStyleSheet(
            """
            AppCard {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 6px;
            }
            AppCard:hover {
                border: 1px solid rgba(61, 174, 233, 0.5);
                background-color: rgba(255, 255, 255, 0.07);
            }
            """
        )

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(10)

        # 1. App Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(36, 36)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_icon()
        main_layout.addWidget(self.icon_label)

        # 2. Name & Details (VBox)
        details_layout = QVBoxLayout()
        details_layout.setSpacing(2)

        self.name_label = QLabel(self.app.name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        details_layout.addWidget(self.name_label)

        cmd_text = self.app.command
        if len(cmd_text) > 35:
            cmd_text = cmd_text[:32] + "..."
        self.cmd_label = QLabel(f"<code>{cmd_text}</code>")
        self.cmd_label.setStyleSheet("color: #999999; font-size: 11px;")
        details_layout.addWidget(self.cmd_label)

        # Extra tags / pills
        tags = []
        if self.app.match_rule:
            tags.append(f"Rule: {self.app.match_rule}")
        if self.app.delay > 0:
            tags.append(f"+{self.app.delay}s delay")
        if tags:
            self.tag_label = QLabel(" • ".join(tags))
            self.tag_label.setStyleSheet("color: #777777; font-size: 10px;")
            details_layout.addWidget(self.tag_label)

        main_layout.addLayout(details_layout, stretch=1)

        # 3. Quick Move Desktop Dropdown
        self.desktop_combo = QComboBox()
        self.desktop_combo.setToolTip("Move to Virtual Desktop")
        self.desktop_combo.setFixedWidth(105)
        self._populate_desktops()
        self.desktop_combo.currentIndexChanged.connect(self._on_desktop_combo_changed)
        main_layout.addWidget(self.desktop_combo)

        # 4. Action Buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(4)

        # Enable / Disable Checkbox
        self.enable_check = QCheckBox()
        self.enable_check.setToolTip("Enable/Disable on startup")
        self.enable_check.setChecked(self.app.enabled)
        self.enable_check.toggled.connect(self._on_toggle)
        actions_layout.addWidget(self.enable_check)

        # Test Launch button
        self.run_btn = QPushButton("▶")
        self.run_btn.setFixedSize(28, 28)
        self.run_btn.setToolTip("Test Launch Application Now")
        self.run_btn.clicked.connect(lambda: self.test_launch_requested.emit(self.app.id))
        actions_layout.addWidget(self.run_btn)

        # Edit button
        self.edit_btn = QPushButton("✏")
        self.edit_btn.setFixedSize(28, 28)
        self.edit_btn.setToolTip("Edit Application")
        self.edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.app.id))
        actions_layout.addWidget(self.edit_btn)

        # Delete button
        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(28, 28)
        self.del_btn.setToolTip("Remove Application")
        self.del_btn.setStyleSheet("color: #e06c75;")
        self.del_btn.clicked.connect(lambda: self.delete_requested.emit(self.app.id))
        actions_layout.addWidget(self.del_btn)

        main_layout.addLayout(actions_layout)
        self._update_enabled_style()

    def _load_icon(self) -> None:
        icon = QIcon.fromTheme(self.app.icon)
        if icon.isNull() and "/" in self.app.icon:
            icon = QIcon(self.app.icon)
        if icon.isNull():
            icon = QIcon.fromTheme("application-x-executable")
        self.icon_label.setPixmap(icon.pixmap(32, 32))

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
        self._update_enabled_style()
        self.toggle_enabled.emit(self.app.id, checked)

    def _update_enabled_style(self) -> None:
        if not self.app.enabled:
            self.setStyleSheet(
                """
                AppCard {
                    background-color: rgba(0, 0, 0, 0.2);
                    border: 1px dashed rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    opacity: 0.6;
                }
                """
            )
            self.name_label.setStyleSheet("color: #777777; font-size: 13px;")
        else:
            self.setStyleSheet(
                """
                AppCard {
                    background-color: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 8px;
                    padding: 6px;
                }
                AppCard:hover {
                    border: 1px solid rgba(61, 174, 233, 0.5);
                    background-color: rgba(255, 255, 255, 0.07);
                }
                """
            )
            self.name_label.setStyleSheet("font-weight: bold; font-size: 13px;")
