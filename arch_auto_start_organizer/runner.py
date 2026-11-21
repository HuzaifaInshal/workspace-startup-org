#!/usr/bin/env python3
"""Startup runner daemon / CLI for Arch Auto-Start Organizer."""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Callable, Optional

# Ensure package is in path when running standalone
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from arch_auto_start_organizer.core.config import ConfigManager
from arch_auto_start_organizer.core.kwin import KWinManager
from arch_auto_start_organizer.core.launcher import AppLauncher

LOG_DIR = Path.home() / ".local" / "state" / "arch-auto-start-organizer"
LOG_FILE = LOG_DIR / "startup.log"


class WorkspaceRunner:
    """Executes the full workspace startup and window routing sequence."""

    def __init__(
        self,
        config_mgr: Optional[ConfigManager] = None,
        log_callback: Optional[Callable[[str, str], None]] = None,
    ):
        self.config_mgr = config_mgr or ConfigManager()
        self.kwin = KWinManager()
        self.log_callback = log_callback or self._default_log
        self.launcher = AppLauncher(log_callback=self.log_callback)
        self._ensure_log_file()

    def _ensure_log_file(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    def _default_log(self, level: str, message: str) -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[{level.upper()}]"
        line = f"[{timestamp}] {prefix:<9} {message}"
        print(line)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def run(self, dry_run: bool = False) -> bool:
        """Executes the complete startup workflow."""
        cfg = self.config_mgr.config
        settings = cfg.settings
        apps = [a for a in cfg.apps if a.enabled]

        self.log_callback("info", "Starting CachyOS Workspace Startup Sequence...")

        # 1. KWin / DBus readiness check
        self.log_callback(
            "info",
            f"Checking KWin window manager status (timeout: {settings.kwin_wait_timeout}s)...",
        )
        if not dry_run and not self.kwin.wait_for_kwin(settings.kwin_wait_timeout):
            self.log_callback("error", "Timeout waiting for KWin DBus service. Aborting.")
            return False

        self.log_callback("success", "KWin is ready and responsive.")

        # 2. Virtual desktops assurance
        current_desktops = self.kwin.get_desktop_count()
        self.log_callback(
            "info",
            f"Current virtual desktops: {current_desktops} (Required minimum: {settings.ensure_min_desktops})",
        )
        if not dry_run and current_desktops < settings.ensure_min_desktops:
            self.log_callback(
                "warn",
                f"Creating virtual desktops up to {settings.ensure_min_desktops}...",
            )
            total = self.kwin.ensure_minimum_desktops(settings.ensure_min_desktops)
            self.log_callback("success", f"Virtual desktops updated to: {total}")

        # 3. Compile and attach KWin routing script
        routing_rules = []
        for a in apps:
            if a.match_rule.strip():
                routing_rules.append(
                    {
                        "match_rule": a.match_rule.strip(),
                        "desktop": a.desktop,
                    }
                )

        script_id = None
        if not dry_run and routing_rules:
            self.log_callback(
                "info",
                f"Generating KWin window router for {len(routing_rules)} rule(s)...",
            )
            script_js = self.kwin.generate_router_script(routing_rules)
            script_id = self.kwin.load_and_run_script(script_js)
            if script_id:
                self.log_callback("success", f"KWin router active (Script ID: {script_id})")
            else:
                self.log_callback(
                    "warn", "Could not load KWin DBus script. Continuing with standard launch."
                )

        try:
            # 4. Launch enabled applications
            self.log_callback("info", f"Launching {len(apps)} enabled applications...")
            for app in apps:
                if dry_run:
                    self.log_callback(
                        "info",
                        f"[DRY RUN] Would launch '{app.name}' on Desktop {app.desktop} (command: '{app.command}')",
                    )
                else:
                    self.launcher.launch(app)

            # 5. Maintain routing listener for grace period
            grace_period = settings.grace_period_seconds
            if not dry_run and script_id and grace_period > 0:
                self.log_callback(
                    "info",
                    f"Waiting {grace_period}s grace period for opening windows to be routed...",
                )
                time.sleep(grace_period)

        finally:
            # 6. Clean up KWin router script
            if not dry_run and script_id:
                self.log_callback("info", "Unloading temporary KWin router...")
                self.kwin.stop_script(script_id)
                self.log_callback("success", "KWin router detached.")

        # 7. Focus designated initial desktop
        return_desktop = settings.return_to_desktop
        if not dry_run and return_desktop > 0:
            self.log_callback(
                "info", f"Switching active view to Desktop {return_desktop}..."
            )
            self.kwin.set_current_desktop(return_desktop)

        self.log_callback("success", "Workspace initialization sequence complete!")
        return True


def main() -> None:
    """CLI entry point for runner."""
    parser = argparse.ArgumentParser(
        description="Arch / CachyOS Workspace Startup Runner",
        prog="arch-auto-start-organizer-runner",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the startup sequence without launching apps or modifying KWin",
    )
    args = parser.parse_args()

    runner = WorkspaceRunner()
    success = runner.run(dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
