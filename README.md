# Arch Auto-Start Organizer (CachyOS / KDE Plasma)

A native desktop application and automation engine designed specifically for **CachyOS / Arch Linux running KDE Plasma 6 (Wayland & X11)** to visually manage auto-startup applications and route them to dedicated virtual desktops upon login or on demand.

---

## Features

- 🖥️ **Workspace Board View**: View your startup applications arranged under dedicated columns for each **Virtual Desktop** (Desktop 1, Desktop 2, Desktop 3, etc.).
- 📑 **List / Table View**: Toggle between the visual board and a compact table view showing app icons, desktop targets, launch commands, and match rules.
- 📦 **Installed Applications Browser**: Instant search across system `.desktop` files in `/usr/share/applications` and `~/.local/share/applications`. Auto-populates application names, executables, icons, and categories.
- 🪟 **Live KWin Window Inspector**: Click **"Detect from Open Window"** to probe open windows on your desktop and automatically capture their exact KWin `resourceClass` without manual guessing.
- 🚀 **Interactive Test Runner**: Run the startup sequence on demand with live colored log streaming (INFO, SUCCESS, WARNING, ERROR) and dry-run simulation mode.
- ⚙️ **One-Click Autostart Integration**: Toggle login autostart directly from the GUI. Automatically generates standards-compliant `~/.config/autostart/*.desktop` entries with `X-KDE-autostart-phase=2` (guaranteeing that KWin Wayland DBus endpoints are ready before launching).
- 🔄 **Safe Migration**: Automatically imports existing apps and settings from legacy startup scripts (`workspace_startup.sh`).
- 🛠️ **Full CLI Support**: Headless runner support for cron, scripts, or login autostart.

---

## Workspace Layout (Default Migration)

| Virtual Desktop | Application | Command | Match Rule |
| :--- | :--- | :--- | :--- |
| **Desktop 1** | **Antigravity IDE** | `antigravity-ide` | `antigravity` |
| **Desktop 2** | **Google Chrome** | `google-chrome-stable` | `chrome` |
| **Desktop 3** | **Spotify** | `spotify-launcher` | `spotify` |
| **Desktop 4** | **KWrite** | `kwrite` | `kwrite` |

---

## Installation

Run the installation script inside the project directory:

```bash
cd /home/huzaifai/huzaifa/projects/arch-auto-start-organizer
./install.sh
```

This will:
1. Create the CLI wrapper executable at `~/.local/bin/arch-auto-start-organizer`.
2. Install the desktop launcher to `~/.local/share/applications/arch-auto-start-organizer.desktop` (so it appears in your CachyOS application launcher, Kickoff, and KRunner).
3. Register the autostart service for KDE Plasma login (Phase 2).

---

## Usage

### 1. Launch the Desktop GUI
You can open the organizer by:
- Searching for **"Workspace Startup Organizer"** in Kickoff / KRunner (`Alt+Space` or `Super`), or
- Running from the terminal:
  ```bash
  arch-auto-start-organizer
  ```

### 2. Command Line Operations

- **Run Startup Sequence Now**:
  ```bash
  arch-auto-start-organizer --run
  ```

- **Simulate / Dry Run**:
  ```bash
  arch-auto-start-organizer --dry-run
  ```

- **List Configured Apps & Desktops**:
  ```bash
  arch-auto-start-organizer --list
  ```

- **Enable / Disable Login Autostart**:
  ```bash
  arch-auto-start-organizer --enable-autostart
  arch-auto-start-organizer --disable-autostart
  ```

---

## How It Works Under The Hood

1. **Window Manager Readiness**: Queries `org.kde.KWin /KWin org.kde.KWin.currentDesktop` via DBus to ensure the compositor is ready.
2. **Virtual Desktop Assurance**: Verifies that at least $N$ virtual desktops exist in KDE Plasma 6's `VirtualDesktopManager`, creating missing ones automatically.
3. **Wayland Routing**: Compiles and injects a dynamic ECMAScript router into `org.kde.kwin.Scripting`. It listens to `workspace.windowAdded` and routes matching `resourceClass` or `desktopFileName` windows directly to their assigned desktop without race conditions or screen flicker.
4. **Process Deduplication**: Checks `pgrep -f` before launching to prevent opening duplicate instances if an app is already running.
5. **Grace Period & Teardown**: Keeps the router active for the configured grace period (default 12s), unloads the script, and sets focus to the configured target desktop (default Desktop 1).

---

## Configuration File

Settings and apps are stored in JSON at:
`~/.config/arch-auto-start-organizer/config.json`

Example:
```json
{
  "version": 1,
  "settings": {
    "autostart_enabled": true,
    "grace_period_seconds": 12,
    "return_to_desktop": 1,
    "ensure_min_desktops": 4,
    "kwin_wait_timeout": 20,
    "view_mode": "board"
  },
  "apps": [
    {
      "id": "antigravity-ide",
      "name": "Antigravity IDE",
      "enabled": true,
      "desktop": 1,
      "command": "antigravity-ide",
      "check_proc": "antigravity-ide",
      "match_rule": "antigravity",
      "icon": "antigravity-ide",
      "delay": 0.0,
      "desktop_file": "antigravity-ide.desktop"
    }
  ]
}
```

---

## Uninstallation

To remove the CLI launcher and desktop entry:

```bash
./uninstall.sh
```
*(Your configuration file in `~/.config/arch-auto-start-organizer/` is safely preserved).*
