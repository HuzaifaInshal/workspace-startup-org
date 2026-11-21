"""GUI components for Arch Auto-Start Organizer."""

from arch_auto_start_organizer.gui.app_card import AppCard
from arch_auto_start_organizer.gui.app_dialog import AppDialog
from arch_auto_start_organizer.gui.app_picker_dialog import AppPickerDialog
from arch_auto_start_organizer.gui.desktop_column import AddDesktopColumn, DesktopColumn
from arch_auto_start_organizer.gui.main_window import MainWindow
from arch_auto_start_organizer.gui.settings_dialog import SettingsDialog
from arch_auto_start_organizer.gui.test_runner_dialog import TestRunnerDialog
from arch_auto_start_organizer.gui.theme import GLOBAL_STYLESHEET, PALETTE
from arch_auto_start_organizer.gui.toggle_switch import ToggleSwitch
from arch_auto_start_organizer.gui.window_inspector_dialog import WindowInspectorDialog

__all__ = [
    "MainWindow",
    "AppCard",
    "DesktopColumn",
    "AddDesktopColumn",
    "ToggleSwitch",
    "AppDialog",
    "AppPickerDialog",
    "SettingsDialog",
    "TestRunnerDialog",
    "WindowInspectorDialog",
    "GLOBAL_STYLESHEET",
    "PALETTE",
]
