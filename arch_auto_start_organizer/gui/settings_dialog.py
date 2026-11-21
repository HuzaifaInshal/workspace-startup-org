#!/usr/bin/env python3
"""Global preferences and startup settings dialog."""

from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
)

from arch_auto_start_organizer.core.config import GlobalSettings


class SettingsDialog(QDialog):
    """Configuration dialog for system and runtime startup options."""

    def __init__(
        self,
        settings: GlobalSettings,
        desktops: Optional[List[Dict[str, Any]]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.settings = settings
        self.desktops = desktops or []
        self.setWindowTitle("Startup Settings & Preferences")
        self.resize(480, 380)

        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        group = QGroupBox("KDE Plasma & KWin Integration")
        form = QFormLayout(group)
        form.setSpacing(12)

        # Autostart Enabled
        self.autostart_check = QCheckBox("Launch automatically at login")
        self.autostart_check.setToolTip(
            "Registers an XDG Autostart entry with X-KDE-autostart-phase=2 in ~/.config/autostart."
        )
        form.addRow("Autostart on Login:", self.autostart_check)

        # Grace Period
        self.grace_spin = QSpinBox()
        self.grace_spin.setRange(1, 60)
        self.grace_spin.setSuffix(" seconds")
        self.grace_spin.setToolTip(
            "Duration the KWin window router listens and captures newly launched application windows before detaching."
        )
        form.addRow("Window Router Grace Period:", self.grace_spin)

        # Return Desktop
        self.return_combo = QComboBox()
        self._populate_return_desktops()
        form.addRow("Switch Focus to Desktop:", self.return_combo)

        # Minimum Desktops
        self.min_desktops_spin = QSpinBox()
        self.min_desktops_spin.setRange(1, 16)
        self.min_desktops_spin.setToolTip(
            "Automatically creates virtual desktops in KWin if the session has fewer than this count."
        )
        form.addRow("Ensure Minimum Desktops:", self.min_desktops_spin)

        # KWin DBus Wait Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 60)
        self.timeout_spin.setSuffix(" seconds")
        self.timeout_spin.setToolTip(
            "Maximum time the startup daemon waits for KWin to finish initializing during login."
        )
        form.addRow("KWin DBus Readiness Timeout:", self.timeout_spin)

        layout.addWidget(group)

        # Explanation note
        note = QLabel(
            "Tip: KDE Plasma 6 starts services asynchronously during boot. Phase 2 autostart "
            "guarantees that KWin Wayland DBus endpoints are ready before opening your apps."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(note)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._save_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _populate_return_desktops(self) -> None:
        self.return_combo.clear()
        self.return_combo.addItem("Do not change active desktop", userData=0)
        count = max(4, len(self.desktops))
        for i in range(1, count + 1):
            name = f"Desktop {i}"
            for d in self.desktops:
                if d.get("number") == i and d.get("name"):
                    name = f"{d['name']} (Desktop {i})"
                    break
            self.return_combo.addItem(name, userData=i)

    def _load_data(self) -> None:
        self.autostart_check.setChecked(self.settings.autostart_enabled)
        self.grace_spin.setValue(self.settings.grace_period_seconds)
        self.min_desktops_spin.setValue(self.settings.ensure_min_desktops)
        self.timeout_spin.setValue(self.settings.kwin_wait_timeout)

        idx = self.return_combo.findData(self.settings.return_to_desktop)
        if idx != -1:
            self.return_combo.setCurrentIndex(idx)

    def _save_and_accept(self) -> None:
        self.settings.autostart_enabled = self.autostart_check.isChecked()
        self.settings.grace_period_seconds = self.grace_spin.value()
        self.settings.ensure_min_desktops = self.min_desktops_spin.value()
        self.settings.kwin_wait_timeout = self.timeout_spin.value()
        self.settings.return_to_desktop = self.return_combo.currentData() or 1
        self.accept()

    def get_settings(self) -> GlobalSettings:
        return self.settings
