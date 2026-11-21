#!/usr/bin/env bash
# ==============================================================================
# Uninstaller for CachyOS / Arch Workspace Startup Organizer
# ==============================================================================
set -eo pipefail

BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"
AUTOSTART_DIR="${HOME}/.config/autostart"

echo "==> Uninstalling Arch Auto-Start Organizer..."

rm -f "${BIN_DIR}/arch-auto-start-organizer"
rm -f "${APP_DIR}/arch-auto-start-organizer.desktop"
rm -f "${AUTOSTART_DIR}/arch-auto-start-organizer.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APP_DIR}" 2>/dev/null || true
fi

echo "✓ Removed CLI wrapper, desktop launcher, and autostart registration."
echo "Note: Configuration files at ~/.config/arch-auto-start-organizer/ have been preserved."
