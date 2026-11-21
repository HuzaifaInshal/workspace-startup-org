#!/usr/bin/env python3
"""Interactive test runner dialog with live log streaming."""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QCheckBox,
    QTextEdit,
    QLabel,
    QProgressBar,
)

from arch_auto_start_organizer.core.config import ConfigManager
from arch_auto_start_organizer.runner import WorkspaceRunner


class RunnerWorker(QThread):
    """Background worker thread to run startup sequence without blocking UI."""

    log_signal = pyqtSignal(str, str)  # (level, message)
    finished_signal = pyqtSignal(bool)

    def __init__(self, config_mgr: ConfigManager, dry_run: bool = False):
        super().__init__()
        self.config_mgr = config_mgr
        self.dry_run = dry_run
        self.is_aborted = False

    def run(self) -> None:
        def callback(level: str, msg: str):
            if not self.is_aborted:
                self.log_signal.emit(level, msg)

        runner = WorkspaceRunner(
            config_mgr=self.config_mgr,
            log_callback=callback,
        )
        success = runner.run(dry_run=self.dry_run)
        self.finished_signal.emit(success)

    def abort(self) -> None:
        self.is_aborted = True


class TestRunnerDialog(QDialog):
    """Dialog providing live interactive testing of the startup sequence."""

    def __init__(self, config_mgr: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.worker: Optional[RunnerWorker] = None

        self.setWindowTitle("Test Startup Sequence")
        self.resize(640, 440)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        top_layout = QHBoxLayout()
        self.dry_run_check = QCheckBox("Dry Run (Simulate without launching apps)")
        self.dry_run_check.setChecked(False)
        top_layout.addWidget(self.dry_run_check)

        top_layout.addStretch()

        self.start_btn = QPushButton("▶ Start Test Run")
        self.start_btn.clicked.connect(self._start_run)
        top_layout.addWidget(self.start_btn)

        layout.addLayout(top_layout)

        # Log console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            """
            QTextEdit {
                background-color: #1a1b26;
                color: #c0caf5;
                font-family: monospace;
                font-size: 11px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 8px;
            }
            """
        )
        layout.addWidget(self.console)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate pulse
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        self.status_label = QLabel("Click 'Start Test Run' to verify your workspace startup.")
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(self.close_btn)

        layout.addLayout(bottom_layout)

    def _start_run(self) -> None:
        self.console.clear()
        self.start_btn.setEnabled(False)
        self.dry_run_check.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Running startup sequence...")

        self.worker = RunnerWorker(
            config_mgr=self.config_mgr,
            dry_run=self.dry_run_check.isChecked(),
        )
        self.worker.log_signal.connect(self._append_log)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _append_log(self, level: str, message: str) -> None:
        color_map = {
            "info": "#7aa2f7",
            "success": "#9ece6a",
            "warn": "#e0af68",
            "error": "#f7768e",
        }
        color = color_map.get(level.lower(), "#c0caf5")
        tag = level.upper()

        html_line = f"<span style='color: {color}; font-weight: bold;'>[{tag}]</span> {message}<br>"
        self.console.insertHtml(html_line)
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def _on_finished(self, success: bool) -> None:
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        self.dry_run_check.setEnabled(True)

        if success:
            self.status_label.setText("<span style='color: #9ece6a; font-weight: bold;'>Startup sequence completed successfully!</span>")
        else:
            self.status_label.setText("<span style='color: #f7768e; font-weight: bold;'>Startup sequence failed. Check logs above.</span>")

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.abort()
            self.worker.wait(1000)
        super().closeEvent(event)
