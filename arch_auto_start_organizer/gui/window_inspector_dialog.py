#!/usr/bin/env python3
"""Dialog for detecting window classes and desktop file names from active KWin windows."""

from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QDialogButtonBox,
)

from arch_auto_start_organizer.core.kwin import KWinManager


class WindowInspectorDialog(QDialog):
    """Probes open KWin windows so the user can easily pick the exact match rule."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detect from Open Windows (KWin Wayland)")
        self.resize(680, 420)

        self.kwin = KWinManager()
        self.selected_rule: Optional[str] = None
        self.selected_window: Optional[Dict[str, str]] = None

        self._init_ui()
        self._refresh_windows()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info_label = QLabel(
            "Below are the normal application windows currently open in your KWin session. "
            "Select one to automatically extract its window match identifier:"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Refresh button bar
        bar_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Refresh Open Windows")
        self.refresh_btn.clicked.connect(self._refresh_windows)
        bar_layout.addWidget(self.refresh_btn)
        bar_layout.addStretch()
        layout.addLayout(bar_layout)

        # Table of open windows
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Window Title", "Resource Class", "Desktop File Name"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemDoubleClicked.connect(self._on_double_clicked)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

        # Status / selection preview
        self.status_label = QLabel("Probing active windows...")
        self.status_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self.status_label)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("Use Window Rule")
        self.ok_button.setEnabled(False)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _refresh_windows(self) -> None:
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("Querying KWin DBus compositor...")
        self.table.setRowCount(0)

        windows = self.kwin.inspect_open_windows()

        self.table.setRowCount(len(windows))
        for row, w in enumerate(windows):
            caption_item = QTableWidgetItem(w.get("caption", "Untitled Window"))
            res_item = QTableWidgetItem(w.get("resourceClass", ""))
            desktop_item = QTableWidgetItem(w.get("desktopFileName", ""))

            caption_item.setData(Qt.ItemDataRole.UserRole, w)

            self.table.setItem(row, 0, caption_item)
            self.table.setItem(row, 1, res_item)
            self.table.setItem(row, 2, desktop_item)

        self.refresh_btn.setEnabled(True)
        if windows:
            self.status_label.setText(f"Found {len(windows)} active window(s).")
        else:
            self.status_label.setText("No normal application windows detected.")

    def _on_selection_changed(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            w = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.selected_window = w

            # Match rule: prefer resourceClass if not empty, otherwise desktopFileName
            rule = w.get("resourceClass") or w.get("desktopFileName") or ""
            self.selected_rule = rule.lower()
            self.ok_button.setEnabled(bool(self.selected_rule))
            self.status_label.setText(f"Selected Rule: <b>{self.selected_rule}</b>")
        else:
            self.selected_window = None
            self.selected_rule = None
            self.ok_button.setEnabled(False)

    def _on_double_clicked(self, item: QTableWidgetItem) -> None:
        self._on_selection_changed()
        if self.selected_rule:
            self.accept()

    def get_selected_rule(self) -> Optional[str]:
        """Returns the chosen window match string."""
        return self.selected_rule

    def get_selected_window(self) -> Optional[Dict[str, str]]:
        """Returns the full window metadata dict."""
        return self.selected_window
