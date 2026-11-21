#!/usr/bin/env bash
# ==============================================================================
# Installer for CachyOS / Arch Workspace Startup Organizer
# ==============================================================================
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"
AUTOSTART_DIR="${HOME}/.config/autostart"

echo "==> Installing Arch Auto-Start Organizer..."

# 1. Ensure bin and app directories exist
mkdir -p "${BIN_DIR}" "${APP_DIR}" "${AUTOSTART_DIR}"

# 2. Create CLI launcher wrapper in ~/.local/bin
cat <<EOF > "${BIN_DIR}/arch-auto-start-organizer"
#!/usr/bin/env bash
export PYTHONPATH="${SCRIPT_DIR}:\${PYTHONPATH}"
exec python3 "${SCRIPT_DIR}/arch_auto_start_organizer/main.py" "\$@"
EOF
chmod +x "${BIN_DIR}/arch-auto-start-organizer"
echo "✓ Created CLI wrapper in ${BIN_DIR}/arch-auto-start-organizer"

# 3. Install Desktop Application entry
cat <<EOF > "${APP_DIR}/arch-auto-start-organizer.desktop"
[Desktop Entry]
Type=Application
Name=Workspace Startup Organizer
GenericName=Startup Applications Manager
Comment=Manage and route auto-startup applications across KDE Plasma virtual desktops
Exec=${BIN_DIR}/arch-auto-start-organizer
Icon=${SCRIPT_DIR}/assets/icon.svg
Terminal=false
StartupNotify=true
Categories=Utility;Settings;System;
Keywords=startup;autostart;workspace;virtual desktop;kwin;cachyos;kde;
EOF
chmod +x "${APP_DIR}/arch-auto-start-organizer.desktop"

# Refresh desktop application database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APP_DIR}" 2>/dev/null || true
fi
echo "✓ Installed desktop entry to ${APP_DIR}/arch-auto-start-organizer.desktop"

# 4. Enable KDE Plasma login autostart runner
"${BIN_DIR}/arch-auto-start-organizer" --enable-autostart >/dev/null 2>&1 || true
echo "✓ Configured KDE Plasma login autostart runner (Phase 2)"

echo ""
echo "==> Installation complete!"
echo "You can now run 'arch-auto-start-organizer' from your terminal"
echo "or search for 'Workspace Startup Organizer' in your CachyOS application menu (Kickoff / KRunner)."
