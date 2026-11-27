#!/usr/bin/env python3
"""Configuration management and schema for Arch Auto-Start Organizer."""

import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

CONFIG_DIR = Path.home() / ".config" / "arch-auto-start-organizer"
CONFIG_FILE = CONFIG_DIR / "config.json"
LEGACY_SCRIPT_PATH = (
    Path.home()
    / "huzaifa"
    / "projects"
    / "miscellanious-scripts"
    / "cachyos_workspace_startup"
    / "workspace_startup.sh"
)


@dataclass
class AppItem:
    """Represents an application configured for auto-startup and workspace placement."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    enabled: bool = True
    desktop: int = 1  # 1-indexed desktop number (e.g., Desktop 1)
    command: str = ""
    check_proc: str = ""  # string pattern checked via pgrep -f
    match_rule: str = ""  # matched against (resourceClass + " " + desktopFileName).lower()
    icon: str = "application-x-executable"
    delay: float = 0.0  # delay in seconds before launching this app
    desktop_file: str = ""  # desktop file ID or path (e.g. org.kde.kwrite.desktop)
    description: str = ""


@dataclass
class GlobalSettings:
    """Global startup runner and desktop environment settings."""

    autostart_enabled: bool = True
    grace_period_seconds: int = 12
    return_to_desktop: int = 1  # 1-indexed desktop to focus when startup completes
    ensure_min_desktops: int = 4
    kwin_wait_timeout: int = 20
    view_mode: str = "board"  # "board" or "list"


@dataclass
class AppConfig:
    """Full application configuration."""

    version: int = 1
    settings: GlobalSettings = field(default_factory=GlobalSettings)
    apps: List[AppItem] = field(default_factory=list)


def get_default_apps() -> List[AppItem]:
    """Provides the initial seeded list of apps matching the original CachyOS script."""
    return [
        AppItem(
            id="antigravity-ide",
            name="Antigravity IDE",
            enabled=True,
            desktop=1,
            command="antigravity-ide",
            check_proc="antigravity-ide",
            match_rule="antigravity",
            icon="antigravity-ide",
            desktop_file="antigravity-ide.desktop",
            description="Antigravity IDE development environment",
        ),
        AppItem(
            id="google-chrome",
            name="Google Chrome",
            enabled=True,
            desktop=2,
            command="google-chrome-stable",
            check_proc="google-chrome",
            match_rule="google-chrome",
            icon="google-chrome",
            desktop_file="google-chrome.desktop",
            description="Google Chrome web browser",
        ),
        AppItem(
            id="spotify",
            name="Spotify",
            enabled=True,
            desktop=3,
            command="spotify-launcher",
            check_proc="spotify",
            match_rule="spotify",
            icon="spotify-launcher",
            desktop_file="spotify-launcher.desktop",
            description="Spotify music player",
        ),
        AppItem(
            id="kwrite",
            name="KWrite",
            enabled=True,
            desktop=4,
            command="kwrite",
            check_proc="kwrite",
            match_rule="kwrite",
            icon="org.kde.kwrite",
            desktop_file="org.kde.kwrite.desktop",
            description="KDE text editor",
        ),
    ]


class ConfigManager:
    """Handles loading, saving, migrating, and updating configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self.config: AppConfig = self.load()

    def load(self) -> AppConfig:
        """Loads configuration from JSON file or generates migrated default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return self._parse_data(data)
            except Exception as e:
                print(f"[ConfigManager] Error reading config: {e}. Falling back to defaults.")

        # Check legacy script migration
        cfg = AppConfig(
            version=1,
            settings=GlobalSettings(autostart_enabled=True),
            apps=get_default_apps(),
        )
        self.save(cfg)
        return cfg

    def _parse_data(self, data: Dict[str, Any]) -> AppConfig:
        settings_data = data.get("settings", {})
        settings = GlobalSettings(
            autostart_enabled=settings_data.get("autostart_enabled", True),
            grace_period_seconds=int(settings_data.get("grace_period_seconds", 12)),
            return_to_desktop=int(settings_data.get("return_to_desktop", 1)),
            ensure_min_desktops=int(settings_data.get("ensure_min_desktops", 4)),
            kwin_wait_timeout=int(settings_data.get("kwin_wait_timeout", 20)),
            view_mode=settings_data.get("view_mode", "board"),
        )

        apps: List[AppItem] = []
        for a in data.get("apps", []):
            match_rule = a.get("match_rule", "")
            # Migration: If match_rule starts with "crx_", strip "crx_" to match Wayland PWA resourceClass
            if match_rule.startswith("crx_"):
                match_rule = match_rule[4:]
            # Migration: Ensure Google Chrome matches "google-chrome" rather than generic "chrome"
            # to avoid false-matching Chrome PWAs/WebApps
            if a.get("id") == "google-chrome" and match_rule == "chrome":
                match_rule = "google-chrome"

            check_proc = a.get("check_proc", "")
            if check_proc.startswith("crx_"):
                check_proc = check_proc[4:]

            apps.append(
                AppItem(
                    id=a.get("id", str(uuid.uuid4())),
                    name=a.get("name", "Unnamed Application"),
                    enabled=bool(a.get("enabled", True)),
                    desktop=int(a.get("desktop", 1)),
                    command=a.get("command", ""),
                    check_proc=check_proc,
                    match_rule=match_rule,
                    icon=a.get("icon", "application-x-executable"),
                    delay=float(a.get("delay", 0.0)),
                    desktop_file=a.get("desktop_file", ""),
                    description=a.get("description", ""),
                )
            )

        return AppConfig(
            version=data.get("version", 1),
            settings=settings,
            apps=apps,
        )

    def save(self, config: Optional[AppConfig] = None) -> None:
        """Saves current or provided config atomically to disk."""
        if config is not None:
            self.config = config

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.config_path.with_suffix(".tmp")

        data = {
            "version": self.config.version,
            "settings": asdict(self.config.settings),
            "apps": [asdict(a) for a in self.config.apps],
        }

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        shutil.move(temp_file, self.config_path)

    def get_apps_by_desktop(self) -> Dict[int, List[AppItem]]:
        """Groups applications by virtual desktop number."""
        grouped: Dict[int, List[AppItem]] = {}
        for app in self.config.apps:
            grouped.setdefault(app.desktop, []).append(app)
        return grouped

    def add_app(self, app: AppItem) -> None:
        """Appends a new application and saves."""
        self.config.apps.append(app)
        self.save()

    def update_app(self, app_id: str, updated_app: AppItem) -> bool:
        """Updates an existing application by id and saves."""
        for i, a in enumerate(self.config.apps):
            if a.id == app_id:
                self.config.apps[i] = updated_app
                self.save()
                return True
        return False

    def remove_app(self, app_id: str) -> bool:
        """Deletes an application by id and saves."""
        initial_len = len(self.config.apps)
        self.config.apps = [a for a in self.config.apps if a.id != app_id]
        if len(self.config.apps) < initial_len:
            self.save()
            return True
        return False
