#!/usr/bin/env python3
"""Dialog for browsing and selecting installed system applications."""

from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QDialogButtonBox,
)

from arch_auto_start_organizer.core.app_scanner import AppScanner


class AppPickerDialog(QDialog):
    """Searchable dialog displaying installed system applications."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Browse Installed Applications")
        self.resize(580, 520)

        self.selected_app: Optional[Dict[str, Any]] = None
        self.all_apps: List[Dict[str, Any]] = []

        self._init_ui()
        self._load_applications()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header description
        info_label = QLabel(
            "Select an installed application to automatically fill in its name, executable, and window matching rules:"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search by application name, executable, or category...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(32, 32))
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

        # Details preview label
        self.preview_label = QLabel("Select an application from the list above.")
        self.preview_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self.preview_label)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("Select Application")
        self.ok_button.setEnabled(False)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _load_applications(self) -> None:
        self.all_apps = AppScanner.scan_all()
        self._populate_list(self.all_apps)

    def _populate_list(self, apps: List[Dict[str, Any]]) -> None:
        self.list_widget.clear()
        for app in apps:
            item = QListWidgetItem()
            item.setText(app.get("name", "Unknown"))
            
            icon_name = app.get("icon", "application-x-executable")
            icon = QIcon.fromTheme(icon_name)
            if icon.isNull() and "/" in icon_name:
                icon = QIcon(icon_name)
            if icon.isNull():
                icon = QIcon.fromTheme("application-x-executable")
            item.setIcon(icon)

            # Store app dict in item data
            item.setData(Qt.ItemDataRole.UserRole, app)
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.preview_label.setText(f"Showing {self.list_widget.count()} applications.")

    def _on_search_changed(self, text: str) -> None:
        filtered = AppScanner.filter_apps(text, self.all_apps)
        self._populate_list(filtered)

    def _on_selection_changed(self) -> None:
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            app = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.selected_app = app
            self.ok_button.setEnabled(True)
            details = f"<b>Executable:</b> {app.get('exec', '')}"
            if app.get("comment"):
                details += f" &nbsp;|&nbsp; <i>{app.get('comment')}</i>"
            self.preview_label.setText(details)
        else:
            self.selected_app = None
            self.ok_button.setEnabled(False)
            self.preview_label.setText("Select an application from the list above.")

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        self.selected_app = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def get_selected_app(self) -> Optional[Dict[str, Any]]:
        """Returns the chosen application metadata dictionary."""
        return self.selected_app
