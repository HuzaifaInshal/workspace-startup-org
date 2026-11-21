#!/usr/bin/env python3
"""Scans and indexes installed desktop applications."""

import configparser
import glob
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class AppScanner:
    """Scans system directories for .desktop files and parses metadata."""

    DESKTOP_DIRS = [
        Path.home() / ".local" / "share" / "applications",
        Path("/usr/share/applications"),
        Path("/usr/local/share/applications"),
        Path.home() / ".local" / "share" / "flatpak" / "exports" / "share" / "applications",
        Path("/var/lib/flatpak/exports/share/applications"),
    ]

    @classmethod
    def clean_exec(cls, exec_line: str) -> str:
        """Removes field codes (%f, %F, %u, %U, etc.) from Exec line."""
        cleaned = re.sub(r"%[a-zA-Z]", "", exec_line).strip()
        return cleaned

    @classmethod
    def scan_all(cls) -> List[Dict[str, Any]]:
        """Scans all desktop directories and returns sorted application metadata."""
        seen_ids = set()
        apps: List[Dict[str, Any]] = []

        for d in cls.DESKTOP_DIRS:
            if not d.exists():
                continue
            for file_path in glob.glob(os.path.join(d, "*.desktop")):
                desktop_id = os.path.basename(file_path)
                if desktop_id in seen_ids:
                    continue

                info = cls.parse_desktop_file(file_path)
                if info and not info.get("no_display", False):
                    seen_ids.add(desktop_id)
                    apps.append(info)

        # Sort alphabetically by display name
        apps.sort(key=lambda x: x.get("name", "").lower())
        return apps

    @classmethod
    def parse_desktop_file(cls, path: str) -> Optional[Dict[str, Any]]:
        """Parses a single .desktop file into an application dictionary."""
        config = configparser.ConfigParser(interpolation=None)
        try:
            config.read(path, encoding="utf-8")
        except Exception:
            return None

        if not config.has_section("Desktop Entry"):
            return None

        entry = config["Desktop Entry"]

        # Only standard applications
        entry_type = entry.get("Type", "Application")
        if entry_type != "Application":
            return None

        no_display = entry.getboolean("NoDisplay", fallback=False)
        hidden = entry.getboolean("Hidden", fallback=False)
        if hidden:
            return None

        name = entry.get("Name", "").strip()
        if not name:
            return None

        exec_cmd = cls.clean_exec(entry.get("Exec", "").strip())
        icon = entry.get("Icon", "application-x-executable").strip()
        comment = entry.get("Comment", "").strip()
        wm_class = entry.get("StartupWMClass", "").strip()
        categories = entry.get("Categories", "").strip()

        # Deducing smart process check pattern
        # Usually first token of exec or wm_class
        cmd_binary = os.path.basename(exec_cmd.split()[0]) if exec_cmd else ""
        smart_check = wm_class.lower() if wm_class else cmd_binary.lower()

        # Smart window match rule: StartupWMClass or binary name or desktop file base
        desktop_base = os.path.splitext(os.path.basename(path))[0].lower()
        smart_match = wm_class.lower() if wm_class else (smart_check or desktop_base)

        return {
            "id": os.path.basename(path),
            "name": name,
            "exec": exec_cmd,
            "icon": icon,
            "comment": comment,
            "wm_class": wm_class,
            "categories": categories,
            "no_display": no_display,
            "path": path,
            "smart_check": smart_check,
            "smart_match": smart_match,
        }

    @classmethod
    def filter_apps(cls, query: str, apps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters applications matching the query string in name, exec, or comment."""
        if not query or not query.strip():
            return apps

        q = query.strip().lower()
        results = []
        for app in apps:
            name_m = q in app.get("name", "").lower()
            exec_m = q in app.get("exec", "").lower()
            comment_m = q in app.get("comment", "").lower()
            id_m = q in app.get("id", "").lower()
            if name_m or exec_m or comment_m or id_m:
                results.append(app)

        return results
