#!/usr/bin/env python3
"""KWin DBus client for KDE Plasma 6 (Wayland & X11)."""

import os
import re
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional


class KWinManager:
    """Manages virtual desktops, KWin scripting, and window routing via DBus."""

    def __init__(self, qdbus_cmd: str = "qdbus6"):
        self.qdbus = qdbus_cmd

    def is_kwin_running(self) -> bool:
        """Checks if KWin DBus service is responsive."""
        try:
            res = subprocess.run(
                [self.qdbus, "org.kde.KWin", "/KWin", "org.kde.KWin.currentDesktop"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    def wait_for_kwin(self, timeout_seconds: int = 20) -> bool:
        """Polls until KWin is available or timeout occurs."""
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            if self.is_kwin_running():
                return True
            time.sleep(1)
        return False

    def get_virtual_desktops(self) -> List[Dict[str, Any]]:
        """Retrieves list of virtual desktops with index, number (1-based), id, and name."""
        try:
            res = subprocess.run(
                [
                    self.qdbus,
                    "--literal",
                    "org.kde.KWin",
                    "/VirtualDesktopManager",
                    "org.kde.KWin.VirtualDesktopManager.desktops",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                matches = re.findall(
                    r'\(uss\)\s*(\d+),\s*"([^"]+)",\s*"([^"]+)"', res.stdout
                )
                if matches:
                    return [
                        {
                            "index": int(m[0]),
                            "number": int(m[0]) + 1,
                            "id": m[1],
                            "name": m[2],
                        }
                        for m in matches
                    ]
        except Exception as e:
            print(f"[KWinManager] Error querying desktops: {e}")

        # Fallback using count
        count = self.get_desktop_count()
        return [
            {
                "index": i,
                "number": i + 1,
                "id": f"desktop-{i+1}",
                "name": f"Desktop {i+1}",
            }
            for i in range(max(1, count))
        ]

    def get_desktop_count(self) -> int:
        """Returns the total number of virtual desktops."""
        try:
            res = subprocess.run(
                [
                    self.qdbus,
                    "org.kde.KWin",
                    "/VirtualDesktopManager",
                    "org.kde.KWin.VirtualDesktopManager.count",
                ],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.returncode == 0 and res.stdout.strip().isdigit():
                return int(res.stdout.strip())
        except Exception:
            pass
        return 1

    def ensure_minimum_desktops(self, min_count: int) -> int:
        """Ensures at least min_count virtual desktops exist, creating any missing."""
        current = self.get_desktop_count()
        if current < min_count:
            for i in range(current + 1, min_count + 1):
                try:
                    subprocess.run(
                        [
                            self.qdbus,
                            "org.kde.KWin",
                            "/VirtualDesktopManager",
                            "org.kde.KWin.VirtualDesktopManager.createDesktop",
                            str(i),
                            f"Desktop {i}",
                        ],
                        capture_output=True,
                        timeout=3,
                    )
                except Exception as e:
                    print(f"[KWinManager] Could not create desktop {i}: {e}")
            return self.get_desktop_count()
        return current

    def get_current_desktop(self) -> int:
        """Returns currently active desktop number (1-based)."""
        try:
            res = subprocess.run(
                [self.qdbus, "org.kde.KWin", "/KWin", "org.kde.KWin.currentDesktop"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.returncode == 0 and res.stdout.strip().isdigit():
                return int(res.stdout.strip())
        except Exception:
            pass
        return 1

    def set_current_desktop(self, desktop_number: int) -> bool:
        """Switches view to the given desktop number (1-based)."""
        try:
            res = subprocess.run(
                [
                    self.qdbus,
                    "org.kde.KWin",
                    "/KWin",
                    "org.kde.KWin.setCurrentDesktop",
                    str(desktop_number),
                ],
                capture_output=True,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    def generate_router_script(self, app_rules: List[Dict[str, Any]]) -> str:
        """Generates ECMAScript for KWin router to intercept and assign windows."""
        # Convert rules to JS objects: { match: string, desktop: 0-indexed int }
        rules_js = []
        for r in app_rules:
            match_str = r.get("match_rule", "").strip().lower()
            desktop_idx = max(0, int(r.get("desktop", 1)) - 1)
            if match_str:
                escaped_match = match_str.replace("\\", "\\\\").replace('"', '\\"')
                rules_js.append(f'    {{ match: "{escaped_match}", desktop: {desktop_idx} }}')

        rules_body = ",\n".join(rules_js)

        return f"""// KWin Workspace Startup Router
const rules = [
{rules_body}
];

function assignDesktop(w) {{
    if (!w || !w.normalWindow) return;
    const identifier = ((w.resourceClass || "") + " " + (w.desktopFileName || "")).toLowerCase();
    for (let i = 0; i < rules.length; i++) {{
        const rule = rules[i];
        if (identifier.indexOf(rule.match) !== -1) {{
            if (workspace.desktops.length > rule.desktop) {{
                w.desktops = [workspace.desktops[rule.desktop]];
                console.log("[KWin AutoPlace] Routed " + (w.resourceClass || w.caption) + " to desktop index " + rule.desktop);
            }}
            break;
        }}
    }}
}}

// Route any existing windows
workspace.windowList().forEach(assignDesktop);

// Intercept newly opened windows
workspace.windowAdded.connect(assignDesktop);
"""

    def load_and_run_script(self, script_content: str) -> Optional[str]:
        """Loads and activates a temporary script in KWin Scripting engine."""
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", prefix="kwin_router_", delete=False
        )
        try:
            temp_file.write(script_content)
            temp_file.flush()
            temp_path = temp_file.name
        finally:
            temp_file.close()

        script_id = None
        try:
            res = subprocess.run(
                [
                    self.qdbus,
                    "org.kde.KWin",
                    "/Scripting",
                    "org.kde.kwin.Scripting.loadScript",
                    temp_path,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            out = res.stdout.strip()
            if out.isdigit():
                script_id = out
                # Start script
                subprocess.run(
                    [
                        self.qdbus,
                        "org.kde.KWin",
                        f"/Scripting/Script{script_id}",
                        "org.kde.kwin.Script.run",
                    ],
                    capture_output=True,
                    timeout=3,
                )
                return script_id
        except Exception as e:
            print(f"[KWinManager] Failed to load/run script: {e}")
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

        return None

    def stop_script(self, script_id: str) -> None:
        """Stops and unloads a running KWin script by id."""
        if not script_id:
            return
        try:
            subprocess.run(
                [
                    self.qdbus,
                    "org.kde.KWin",
                    f"/Scripting/Script{script_id}",
                    "org.kde.kwin.Script.stop",
                ],
                capture_output=True,
                timeout=3,
            )
        except Exception as e:
            print(f"[KWinManager] Error stopping script {script_id}: {e}")

    def inspect_open_windows(self) -> List[Dict[str, str]]:
        """Probes KWin to inspect all currently open normal windows."""
        token = f"ORG_PROBE_{int(time.time() * 1000)}"
        script = f"""
const list = workspace.windowList();
for (let i = 0; i < list.length; i++) {{
    const w = list[i];
    if (w.normalWindow) {{
        console.log('{token}:' + (w.resourceClass || '') + '|' + (w.desktopFileName || '') + '|' + (w.caption || ''));
    }}
}}
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", prefix="kwin_probe_", delete=False
        ) as f:
            f.write(script)
            f_path = f.name

        results: List[Dict[str, str]] = []
        try:
            proc = subprocess.run(
                [
                    self.qdbus,
                    "org.kde.KWin",
                    "/Scripting",
                    "org.kde.kwin.Scripting.loadScript",
                    f_path,
                ],
                capture_output=True,
                text=True,
                timeout=4,
            )
            script_id = proc.stdout.strip()
            if script_id.isdigit():
                subprocess.run(
                    [
                        self.qdbus,
                        "org.kde.KWin",
                        f"/Scripting/Script{script_id}",
                        "org.kde.kwin.Script.run",
                    ],
                    capture_output=True,
                    timeout=2,
                )
                time.sleep(0.3)
                subprocess.run(
                    [
                        self.qdbus,
                        "org.kde.KWin",
                        f"/Scripting/Script{script_id}",
                        "org.kde.kwin.Script.stop",
                    ],
                    capture_output=True,
                    timeout=2,
                )

            # Retrieve from journalctl for kwin_wayland
            j_proc = subprocess.run(
                [
                    "journalctl",
                    "--user",
                    "-u",
                    "plasma-kwin_wayland",
                    "-n",
                    "60",
                    "--no-pager",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            seen_identifiers = set()
            for line in j_proc.stdout.splitlines():
                if token in line:
                    payload = line.split(token + ":", 1)[1].strip()
                    parts = payload.split("|", 2)
                    if len(parts) == 3:
                        res_class, desktop_file, caption = parts
                        key = (res_class, desktop_file)
                        if key not in seen_identifiers:
                            seen_identifiers.add(key)
                            results.append(
                                {
                                    "resourceClass": res_class,
                                    "desktopFileName": desktop_file,
                                    "caption": caption,
                                }
                            )
        except Exception as e:
            print(f"[KWinManager] Window inspection failed: {e}")
        finally:
            if os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except OSError:
                    pass

        return results
