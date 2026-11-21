#!/usr/bin/env python3
"""Unified entry point for Arch Auto-Start Organizer (GUI and CLI modes)."""

import argparse
import os
import sys
from pathlib import Path

# Ensure package directory is importable
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from arch_auto_start_organizer.core.config import ConfigManager
from arch_auto_start_organizer.core.autostart import AutostartManager
from arch_auto_start_organizer.runner import WorkspaceRunner


def run_gui() -> int:
    """Launches the PyQt6 desktop user interface."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    from arch_auto_start_organizer.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Arch Auto-Start Organizer")
    app.setApplicationDisplayName("Workspace Startup Organizer")
    app.setDesktopFileName("arch-auto-start-organizer.desktop")

    # App icon
    icon_path = PACKAGE_ROOT / "assets" / "icon.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        app.setWindowIcon(QIcon.fromTheme("preferences-system-windows"))

    window = MainWindow()
    window.show()
    return app.exec()


def print_list(config_mgr: ConfigManager) -> None:
    """Prints configured applications to stdout."""
    cfg = config_mgr.config
    print(f"\n{'='*70}")
    print("CachyOS / Arch Workspace Startup Applications")
    print(f"{'='*70}")
    print(f"Autostart at Login : {'ENABLED' if cfg.settings.autostart_enabled else 'DISABLED'}")
    print(f"Grace Period       : {cfg.settings.grace_period_seconds}s")
    print(f"Return to Desktop  : Desktop {cfg.settings.return_to_desktop}")
    print(f"Minimum Desktops   : {cfg.settings.ensure_min_desktops}")
    print(f"{'-'*70}")
    print(f"{'Desktop':<10} {'Status':<10} {'App Name':<22} {'Match Rule':<15} {'Command'}")
    print(f"{'-'*70}")
    for a in sorted(cfg.apps, key=lambda x: (x.desktop, x.name)):
        status = "Active" if a.enabled else "Disabled"
        print(f"Desktop {a.desktop:<2} {status:<10} {a.name:<22} {a.match_rule:<15} {a.command}")
    print(f"{'='*70}\n")


def main() -> None:
    """Parses command-line arguments and routes execution."""
    parser = argparse.ArgumentParser(
        description="CachyOS / Arch Workspace Startup Organizer",
        prog="arch-auto-start-organizer",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute headless startup sequence (launches apps & positions them across desktops)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the startup sequence without executing commands or routing windows",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print list of configured startup applications and settings",
    )
    parser.add_argument(
        "--enable-autostart",
        action="store_true",
        help="Register the application to run automatically at KDE Plasma login",
    )
    parser.add_argument(
        "--disable-autostart",
        action="store_true",
        help="Remove the application from KDE Plasma autostart",
    )

    args = parser.parse_args()
    config_mgr = ConfigManager()
    autostart_mgr = AutostartManager()

    if args.run or args.dry_run:
        runner = WorkspaceRunner(config_mgr=config_mgr)
        success = runner.run(dry_run=args.dry_run)
        sys.exit(0 if success else 1)

    if args.list:
        print_list(config_mgr)
        sys.exit(0)

    if args.enable_autostart:
        config_mgr.config.settings.autostart_enabled = True
        config_mgr.save()
        autostart_mgr.install()
        print("✓ Autostart enabled for login.")
        sys.exit(0)

    if args.disable_autostart:
        config_mgr.config.settings.autostart_enabled = False
        config_mgr.save()
        autostart_mgr.uninstall()
        print("✓ Autostart disabled.")
        sys.exit(0)

    # Default: launch GUI
    sys.exit(run_gui())


if __name__ == "__main__":
    main()
