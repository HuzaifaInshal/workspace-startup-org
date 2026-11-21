#!/usr/bin/env python3
"""Application launcher and process management."""

import shutil
import subprocess
import time
from typing import Callable, Optional

from arch_auto_start_organizer.core.config import AppItem


class AppLauncher:
    """Manages application status checking and execution."""

    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        """
        log_callback: Optional function (level: str, message: str) -> None.
                      level can be 'info', 'success', 'warn', 'error'.
        """
        self.log_callback = log_callback or self._default_log

    def _default_log(self, level: str, message: str) -> None:
        prefix = f"[{level.upper()}]"
        print(f"{prefix:<9} {message}")

    def is_running(self, check_proc: str) -> bool:
        """Checks if a process matching check_proc pattern is currently running."""
        if not check_proc or not check_proc.strip():
            return False
        try:
            res = subprocess.run(
                ["pgrep", "-f", check_proc.strip()],
                capture_output=True,
                timeout=2,
            )
            return res.returncode == 0
        except Exception:
            return False

    def launch(self, app: AppItem) -> bool:
        """Launches an application if it is enabled and not already running."""
        if not app.enabled:
            self.log_callback("info", f"'{app.name}' is disabled; skipping.")
            return False

        if app.check_proc and self.is_running(app.check_proc):
            self.log_callback(
                "warn",
                f"'{app.name}' is already running (matched '{app.check_proc}'). Skipping launch.",
            )
            return False

        if app.delay > 0:
            self.log_callback("info", f"Waiting {app.delay}s delay before launching '{app.name}'...")
            time.sleep(app.delay)

        self.log_callback("info", f"Launching '{app.name}' (Target: Desktop {app.desktop})...")

        has_gtk_launch = shutil.which("gtk-launch") is not None
        launched = False

        # Attempt 1: gtk-launch with desktop file name if available
        if has_gtk_launch and app.desktop_file:
            desktop_name = app.desktop_file
            if desktop_name.endswith(".desktop"):
                desktop_name = desktop_name[:-8]
            try:
                proc = subprocess.Popen(
                    ["gtk-launch", desktop_name],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                launched = True
            except Exception as e:
                self.log_callback(
                    "warn", f"gtk-launch failed for '{desktop_name}': {e}. Falling back to command."
                )

        # Attempt 2: Command execution
        if not launched and app.command:
            try:
                proc = subprocess.Popen(
                    app.command,
                    shell=True,
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                launched = True
            except Exception as e:
                self.log_callback("error", f"Failed to launch command '{app.command}': {e}")
                return False

        if launched:
            self.log_callback("success", f"Successfully started '{app.name}'.")
            return True
        else:
            self.log_callback(
                "error", f"No valid command or desktop file specified for '{app.name}'."
            )
            return False
