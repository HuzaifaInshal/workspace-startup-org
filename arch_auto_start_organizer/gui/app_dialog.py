#!/usr/bin/env python3
"""Dialog for adding or editing an application configuration."""

import uuid
from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton,
    QLabel,
    QDialogButtonBox,
    QGroupBox,
    QMessageBox,
)

from arch_auto_start_organizer.core.config import AppItem
from arch_auto_start_organizer.gui.app_picker_dialog import AppPickerDialog
from arch_auto_start_organizer.gui.window_inspector_dialog import WindowInspectorDialog


class AppDialog(QDialog):
    """Add or edit an application's startup and placement rules."""

    def __init__(
        self,
        app_item: Optional[AppItem] = None,
        desktops: Optional[List[Dict[str, Any]]] = None,
        default_desktop: int = 1,
        parent=None,
    ):
        super().__init__(parent)
        self.app_item = app_item
        self.desktops = desktops or []
        self.default_desktop = default_desktop
        self.is_edit_mode = app_item is not None

        title = "Edit Application" if self.is_edit_mode else "Add Application to Startup"
        self.setWindowTitle(title)
        self.resize(540, 560)

        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # Helper buttons bar
        helper_group = QGroupBox("Quick Setup Helpers")
        helper_layout = QHBoxLayout(helper_group)
        
        self.browse_btn = QPushButton("📦 Browse Installed Applications...")
        self.browse_btn.clicked.connect(self._open_app_picker)
        helper_layout.addWidget(self.browse_btn)

        self.inspect_btn = QPushButton("🪟 Detect from Open Window...")
        self.inspect_btn.clicked.connect(self._open_window_inspector)
        helper_layout.addWidget(self.inspect_btn)

        main_layout.addWidget(helper_group)

        # Form layout
        form_group = QGroupBox("Application Settings")
        form = QFormLayout(form_group)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Google Chrome")
        form.addRow("Application Name*:", self.name_edit)

        # Target Virtual Desktop
        self.desktop_combo = QComboBox()
        self._populate_desktop_combo()
        form.addRow("Target Virtual Desktop*:", self.desktop_combo)

        # Executable / Command
        self.cmd_edit = QLineEdit()
        self.cmd_edit.setPlaceholderText("e.g., google-chrome-stable or /usr/bin/kwrite")
        form.addRow("Launch Command*:", self.cmd_edit)

        # Process Check
        self.check_edit = QLineEdit()
        self.check_edit.setPlaceholderText("e.g., chrome (avoids launching if already running)")
        self.check_edit.setToolTip("Pattern passed to pgrep -f. If matched, app is considered already running.")
        form.addRow("Process Check Pattern:", self.check_edit)

        # Window Match Rule
        self.match_edit = QLineEdit()
        self.match_edit.setPlaceholderText("e.g., chrome or org.kde.kwrite")
        self.match_edit.setToolTip("Substrings matched against window resource class or desktop file name in KWin.")
        form.addRow("Window Match Rule*:", self.match_edit)

        # Desktop File / ID
        self.desktop_file_edit = QLineEdit()
        self.desktop_file_edit.setPlaceholderText("e.g., google-chrome.desktop")
        form.addRow("Desktop File Name:", self.desktop_file_edit)

        # Icon Name / Path
        icon_layout = QHBoxLayout()
        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("e.g., google-chrome or full path to icon")
        self.icon_edit.textChanged.connect(self._update_icon_preview)
        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(28, 28)
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(self.icon_preview)
        form.addRow("Icon Identifier:", icon_layout)

        # Launch Delay
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.0, 60.0)
        self.delay_spin.setSingleStep(0.5)
        self.delay_spin.setSuffix(" seconds")
        form.addRow("Stagger Delay:", self.delay_spin)

        # Enabled Checkbox
        self.enabled_check = QCheckBox("Enable this application on startup")
        self.enabled_check.setChecked(True)
        form.addRow("Active Status:", self.enabled_check)

        main_layout.addWidget(form_group)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._validate_and_save)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _populate_desktop_combo(self) -> None:
        self.desktop_combo.clear()
        desktop_count = max(4, len(self.desktops))
        for i in range(1, desktop_count + 1):
            desktop_name = f"Desktop {i}"
            for d in self.desktops:
                if d.get("number") == i and d.get("name"):
                    desktop_name = f"{d['name']} (Desktop {i})"
                    break
            self.desktop_combo.addItem(desktop_name, userData=i)

    def _update_icon_preview(self, icon_str: str) -> None:
        icon = QIcon.fromTheme(icon_str.strip())
        if icon.isNull() and "/" in icon_str:
            icon = QIcon(icon_str.strip())
        if not icon.isNull():
            self.icon_preview.setPixmap(icon.pixmap(24, 24))
        else:
            self.icon_preview.clear()

    def _load_data(self) -> None:
        if self.app_item:
            self.name_edit.setText(self.app_item.name)
            self.cmd_edit.setText(self.app_item.command)
            self.check_edit.setText(self.app_item.check_proc)
            self.match_edit.setText(self.app_item.match_rule)
            self.desktop_file_edit.setText(self.app_item.desktop_file)
            self.icon_edit.setText(self.app_item.icon)
            self.delay_spin.setValue(self.app_item.delay)
            self.enabled_check.setChecked(self.app_item.enabled)

            # Set desktop index
            idx = self.desktop_combo.findData(self.app_item.desktop)
            if idx != -1:
                self.desktop_combo.setCurrentIndex(idx)
        else:
            # New application: set default desktop
            idx = self.desktop_combo.findData(self.default_desktop)
            if idx != -1:
                self.desktop_combo.setCurrentIndex(idx)
            self.icon_edit.setText("application-x-executable")

    def _open_app_picker(self) -> None:
        dlg = AppPickerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            app = dlg.get_selected_app()
            if app:
                if not self.name_edit.text().strip():
                    self.name_edit.setText(app.get("name", ""))
                self.cmd_edit.setText(app.get("exec", ""))
                self.desktop_file_edit.setText(app.get("id", ""))
                self.icon_edit.setText(app.get("icon", ""))
                if not self.check_edit.text().strip():
                    self.check_edit.setText(app.get("smart_check", ""))
                if not self.match_edit.text().strip():
                    self.match_edit.setText(app.get("smart_match", ""))

    def _open_window_inspector(self) -> None:
        dlg = WindowInspectorDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            rule = dlg.get_selected_rule()
            w = dlg.get_selected_window()
            if rule:
                self.match_edit.setText(rule)
            if w and not self.check_edit.text().strip():
                # Default process check to resourceClass
                self.check_edit.setText(w.get("resourceClass", ""))

    def _validate_and_save(self) -> None:
        name = self.name_edit.text().strip()
        cmd = self.cmd_edit.text().strip()
        match_rule = self.match_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Please provide an application name.")
            self.name_edit.setFocus()
            return

        if not cmd:
            QMessageBox.warning(self, "Validation Error", "Please provide a launch command.")
            self.cmd_edit.setFocus()
            return

        if not match_rule:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please specify a window match rule (or use 'Detect from Open Window').",
            )
            self.match_edit.setFocus()
            return

        desktop_num = self.desktop_combo.currentData() or 1
        item_id = self.app_item.id if self.app_item else str(uuid.uuid4())

        self.app_item = AppItem(
            id=item_id,
            name=name,
            enabled=self.enabled_check.isChecked(),
            desktop=desktop_num,
            command=cmd,
            check_proc=self.check_edit.text().strip(),
            match_rule=match_rule,
            icon=self.icon_edit.text().strip() or "application-x-executable",
            delay=self.delay_spin.value(),
            desktop_file=self.desktop_file_edit.text().strip(),
            description=f"Assigned to Desktop {desktop_num}",
        )
        self.accept()

    def get_app_item(self) -> Optional[AppItem]:
        """Returns the configured AppItem."""
        return self.app_item
