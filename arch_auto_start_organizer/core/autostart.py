#!/usr/bin/env python3
"""Autostart integration management via XDG Autostart specification."""

from pathlib import Path
from typing import Optional

AUTOSTART_DIR = Path.home() / ".config" / "autostart"
AUTOSTART_FILE = AUTOSTART_DIR / "arch-auto-start-organizer.desktop"
LEGACY_AUTOSTART_FILE = AUTOSTART_DIR / "workspace-startup.desktop"


class AutostartManager:
    """Manages KDE Plasma autostart desktop entry."""

    def __init__(self, autostart_file: Optional[Path] = None):
        self.autostart_file = autostart_file or AUTOSTART_FILE

    def is_installed(self) -> bool:
        """Checks if active autostart desktop entry is present."""
        return self.autostart_file.exists() or LEGACY_AUTOSTART_FILE.exists()

    def install(self, runner_command: Optional[str] = None) -> bool:
        """Creates or updates the autostart .desktop file."""
        if not runner_command:
            project_dir = Path(__file__).resolve().parent.parent.parent
            runner_command = f"python3 {project_dir / 'arch_auto_start_organizer' / 'runner.py'}"

        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)

        content = f"""[Desktop Entry]
Type=Application
Name=CachyOS Workspace Startup Organizer
Comment=Automatically launch and position apps across KDE Plasma virtual desktops
Exec={runner_command}
Terminal=false
StartupNotify=false
X-KDE-autostart-phase=2
Categories=Utility;
"""
        try:
            with open(self.autostart_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.autostart_file.chmod(0o755)

            # If legacy autostart exists and is pointing to the old bash script, remove it to avoid double runs
            if (
                LEGACY_AUTOSTART_FILE.exists()
                and LEGACY_AUTOSTART_FILE.resolve() != self.autostart_file.resolve()
            ):
                try:
                    LEGACY_AUTOSTART_FILE.unlink()
                except OSError:
                    pass

            return True
        except Exception as e:
            print(f"[AutostartManager] Error installing autostart entry: {e}")
            return False

    def uninstall(self) -> bool:
        """Removes all autostart desktop entries for this application."""
        removed = False
        for f in [self.autostart_file, LEGACY_AUTOSTART_FILE]:
            if f.exists():
                try:
                    f.unlink()
                    removed = True
                except OSError as e:
                    print(f"[AutostartManager] Error removing {f}: {e}")
        return removed

    def sync(self, enabled: bool, runner_command: Optional[str] = None) -> bool:
        """Synchronizes file state with target enabled boolean."""
        if enabled:
            return self.install(runner_command)
        else:
            return self.uninstall()
