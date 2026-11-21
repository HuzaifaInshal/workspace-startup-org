#!/usr/bin/env python3
"""Modern, responsive Main Window for CachyOS Workspace Startup Organizer."""

from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
    QButtonGroup,
    QStatusBar,
    QSizePolicy,
)

from arch_auto_start_organizer.core.config import AppConfig, AppItem, ConfigManager
from arch_auto_start_organizer.core.kwin import KWinManager
from arch_auto_start_organizer.core.autostart import AutostartManager
from arch_auto_start_organizer.core.launcher import AppLauncher
from arch_auto_start_organizer.gui.desktop_column import DesktopColumn, AddDesktopColumn
from arch_auto_start_organizer.gui.app_dialog import AppDialog
from arch_auto_start_organizer.gui.settings_dialog import SettingsDialog
from arch_auto_start_organizer.gui.test_runner_dialog import TestRunnerDialog
from arch_auto_start_organizer.gui.toggle_switch import ToggleSwitch
from arch_auto_start_organizer.gui.theme import GLOBAL_STYLESHEET


class MainWindow(QMainWindow):
    """Modern, responsive dashboard for managing startup applications and virtual desktops."""

    def __init__(self, config_mgr: Optional[ConfigManager] = None):
        super().__init__()
        self.config_mgr = config_mgr or ConfigManager()
        self.kwin = KWinManager()
        self.autostart_mgr = AutostartManager()
        self.launcher = AppLauncher()

        self.desktops: List[Dict[str, Any]] = []
        self.search_query: str = ""

        self.setWindowTitle("CachyOS Workspace Startup Organizer")
        self.resize(1200, 780)
        self.setMinimumSize(960, 600)
        self.setStyleSheet(GLOBAL_STYLESHEET)

        self._refresh_desktops_data()
        self._init_ui()
        self._refresh_views()

    def _refresh_desktops_data(self) -> None:
        """Fetches active virtual desktops from KWin DBus."""
        self.desktops = self.kwin.get_virtual_desktops()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(14)

        # 1. Top Header & Toolbar Area
        header_widget = self._create_header_area()
        main_layout.addWidget(header_widget)

        # 2. Main Stacked View Area (Board vs List)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Page 0: Workspace Board View (Horizontal scroll, full vertical stretch)
        self.board_scroll = QScrollArea()
        self.board_scroll.setWidgetResizable(True)
        self.board_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.board_scroll.setStyleSheet("background: transparent;")
        self.board_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.board_container = QWidget()
        self.board_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.board_layout = QHBoxLayout(self.board_container)
        self.board_layout.setContentsMargins(0, 0, 0, 0)
        self.board_layout.setSpacing(16)
        self.board_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.board_scroll.setWidget(self.board_container)
        self.stacked_widget.addWidget(self.board_scroll)

        # Page 1: List / Table View
        self.table_widget = self._create_table_view()
        self.stacked_widget.addWidget(self.table_widget)

        main_layout.addWidget(self.stacked_widget, stretch=1)

        # Set initial view mode
        initial_mode = self.config_mgr.config.settings.view_mode
        if initial_mode == "list":
            self.list_btn.setChecked(True)
            self.stacked_widget.setCurrentIndex(1)
        else:
            self.board_btn.setChecked(True)
            self.stacked_widget.setCurrentIndex(0)

        # 3. Status Bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(
            "background-color: #1a1c26; color: #a1a7b8; font-size: 11px; border-top: 1px solid rgba(255, 255, 255, 0.08);"
        )
        self.setStatusBar(self.status_bar)
        self._update_status_bar()

    def _create_header_area(self) -> QWidget:
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_frame.setStyleSheet(
            """
            QFrame#HeaderFrame {
                background-color: #1c1e28;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
                padding: 4px;
            }
            """
        )

        frame_layout = QVBoxLayout(header_frame)
        frame_layout.setContentsMargins(16, 12, 16, 12)
        frame_layout.setSpacing(10)

        # -------------------------------------------------------------
        # Row 1: Logo & Title, Search Bar, Main Action Buttons
        # -------------------------------------------------------------
        row1 = QHBoxLayout()
        row1.setSpacing(14)

        # App Logo & Title
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title_label = QLabel("Workspace Startup Organizer")
        title_font = QFont()
        title_font.setPointSize(15)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        title_box.addWidget(title_label)

        subtitle = QLabel("KDE Plasma 6 Virtual Desktop Automation")
        subtitle.setStyleSheet("color: #6e7587; font-size: 11px;")
        title_box.addWidget(subtitle)

        row1.addLayout(title_box)

        # Search / Filter Bar (Real-time filter)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Filter applications...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setFixedWidth(240)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        row1.addWidget(self.search_edit)

        row1.addStretch()

        # View Mode Switcher (Board vs List Pill)
        view_toggle_frame = QFrame()
        view_toggle_frame.setStyleSheet(
            """
            QFrame {
                background-color: #16171f;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 2px;
            }
            """
        )
        view_toggle_layout = QHBoxLayout(view_toggle_frame)
        view_toggle_layout.setContentsMargins(2, 2, 2, 2)
        view_toggle_layout.setSpacing(2)

        self.board_btn = QPushButton("📋 Board")
        self.board_btn.setCheckable(True)
        self.list_btn = QPushButton("📑 List")
        self.list_btn.setCheckable(True)

        pill_btn_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: #a1a7b8;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:checked {
                background-color: #3daee9;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover:!checked {
                color: #ffffff;
                background-color: rgba(255, 255, 255, 0.05);
            }
        """
        self.board_btn.setStyleSheet(pill_btn_style)
        self.list_btn.setStyleSheet(pill_btn_style)

        self.view_btn_group = QButtonGroup(self)
        self.view_btn_group.addButton(self.board_btn, 0)
        self.view_btn_group.addButton(self.list_btn, 1)
        self.view_btn_group.idClicked.connect(self._on_view_mode_changed)

        view_toggle_layout.addWidget(self.board_btn)
        view_toggle_layout.addWidget(self.list_btn)
        row1.addWidget(view_toggle_frame)

        # Primary Add Button
        self.add_app_btn = QPushButton("＋ Add Application")
        self.add_app_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3daee9;
                color: #ffffff;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #55b9eb;
            }
            QPushButton:pressed {
                background-color: #2b98d3;
            }
            """
        )
        self.add_app_btn.clicked.connect(lambda: self._open_add_app_dialog())
        row1.addWidget(self.add_app_btn)

        # Test Run Button
        self.test_run_btn = QPushButton("▶ Test Run")
        self.test_run_btn.setToolTip("Test run startup sequence with live logs")
        self.test_run_btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(74, 222, 128, 0.12);
                color: #4ade80;
                border: 1px solid rgba(74, 222, 128, 0.3);
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(74, 222, 128, 0.22);
                border-color: #4ade80;
            }
            """
        )
        self.test_run_btn.clicked.connect(self._open_test_runner)
        row1.addWidget(self.test_run_btn)

        # Settings Button
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        row1.addWidget(self.settings_btn)

        # Refresh Button
        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setToolTip("Refresh Virtual Desktops and Applications")
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #242735;
                color: #f3f4f8;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                border-color: #3daee9;
                color: #3daee9;
                background-color: #2c3042;
            }
            """
        )
        self.refresh_btn.clicked.connect(self._on_refresh_all)
        row1.addWidget(self.refresh_btn)

        frame_layout.addLayout(row1)

        # -------------------------------------------------------------
        # Row 2: Status Badges & Autostart Toggle
        # -------------------------------------------------------------
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        # KWin Status Pill
        kwin_ready = self.kwin.is_kwin_running()
        kwin_text = "● KWin Wayland (Ready)" if kwin_ready else "○ KWin Offline"
        kwin_bg = "rgba(74, 222, 128, 0.12)" if kwin_ready else "rgba(248, 113, 113, 0.12)"
        kwin_fg = "#4ade80" if kwin_ready else "#f87171"
        self.kwin_badge = QLabel(kwin_text)
        self.kwin_badge.setStyleSheet(
            f"background-color: {kwin_bg}; color: {kwin_fg}; border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 500;"
        )
        row2.addWidget(self.kwin_badge)

        # Desktops Count Pill
        self.desktops_badge = QLabel(f"🖥️ {len(self.desktops)} Virtual Desktops")
        self.desktops_badge.setStyleSheet(
            "background-color: rgba(192, 132, 252, 0.12); color: #c084fc; border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 500;"
        )
        row2.addWidget(self.desktops_badge)

        # Autostart Phase Pill
        self.phase_badge = QLabel("⚡ Phase 2 Autostart")
        self.phase_badge.setStyleSheet(
            "background-color: rgba(61, 174, 233, 0.12); color: #55b9eb; border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 500;"
        )
        row2.addWidget(self.phase_badge)

        row2.addStretch()

        # Autostart on Login Switch
        autostart_box = QHBoxLayout()
        autostart_box.setSpacing(8)
        autostart_lbl = QLabel("Launch on Login:")
        autostart_lbl.setStyleSheet("color: #a1a7b8; font-size: 12px; font-weight: 500;")
        autostart_box.addWidget(autostart_lbl)

        is_autostart_active = (
            self.config_mgr.config.settings.autostart_enabled and self.autostart_mgr.is_installed()
        )
        self.autostart_toggle = ToggleSwitch(checked=is_autostart_active)
        self.autostart_toggle.toggled.connect(self._on_autostart_toggled)
        autostart_box.addWidget(self.autostart_toggle)

        row2.addLayout(autostart_box)
        frame_layout.addLayout(row2)

        return header_frame

    def _create_table_view(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Icon", "Application Name", "Target Desktop", "Command", "Match Rule", "Active", "Actions"
        ])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.verticalHeader().setDefaultSectionSize(52)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return table

    def _refresh_views(self) -> None:
        """Rerenders both the Board and List views."""
        self._render_board_view()
        self._render_table_view()
        self._update_status_bar()

    def _render_board_view(self) -> None:
        """Constructs full-height responsive columns for each virtual desktop."""
        # Clear existing layout items
        while self.board_layout.count():
            item = self.board_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        apps_by_desktop = self.config_mgr.get_apps_by_desktop()
        max_desktop_num = max(
            [d.get("number", 1) for d in self.desktops] + [4] + list(apps_by_desktop.keys())
        )

        for desktop_num in range(1, max_desktop_num + 1):
            desktop_name = f"Desktop {desktop_num}"
            for d in self.desktops:
                if d.get("number") == desktop_num and d.get("name"):
                    desktop_name = d["name"]
                    break

            desktop_apps = apps_by_desktop.get(desktop_num, [])

            # Filter by search query if any
            if self.search_query:
                desktop_apps = [
                    a for a in desktop_apps
                    if self.search_query in a.name.lower()
                    or self.search_query in a.command.lower()
                    or self.search_query in a.match_rule.lower()
                ]

            col = DesktopColumn(
                desktop_num=desktop_num,
                desktop_name=desktop_name,
                apps=desktop_apps,
                all_desktops=self.desktops,
            )
            col.add_app_requested.connect(self._open_add_app_dialog)
            col.app_edit_requested.connect(self._on_edit_app)
            col.app_delete_requested.connect(self._on_delete_app)
            col.app_toggle_enabled.connect(self._on_toggle_app_enabled)
            col.app_desktop_changed.connect(self._on_change_app_desktop)
            col.app_test_launch_requested.connect(self._on_test_launch_app)

            self.board_layout.addWidget(col)

        # "+ Add Virtual Desktop" Placeholder Column
        add_desktop_col = AddDesktopColumn()
        add_desktop_col.create_requested.connect(self._on_create_virtual_desktop)
        self.board_layout.addWidget(add_desktop_col)

    def _render_table_view(self) -> None:
        """Populates the tabular list view."""
        self.table_widget.setRowCount(0)
        apps = self.config_mgr.config.apps

        if self.search_query:
            apps = [
                a for a in apps
                if self.search_query in a.name.lower()
                or self.search_query in a.command.lower()
                or self.search_query in a.match_rule.lower()
            ]

        self.table_widget.setRowCount(len(apps))

        for row, app in enumerate(apps):
            # 0: Icon
            icon_item = QTableWidgetItem()
            icon = QIcon.fromTheme(app.icon)
            if icon.isNull() and "/" in app.icon:
                icon = QIcon(app.icon)
            if icon.isNull():
                icon = QIcon.fromTheme("application-x-executable")
            icon_item.setIcon(icon)
            self.table_widget.setItem(row, 0, icon_item)

            # 1: Name
            name_item = QTableWidgetItem(app.name)
            font = QFont()
            font.setBold(True)
            name_item.setFont(font)
            self.table_widget.setItem(row, 1, name_item)

            # 2: Target Desktop
            d_name = f"Desktop {app.desktop}"
            for d in self.desktops:
                if d.get("number") == app.desktop and d.get("name"):
                    d_name = f"{d['name']} ({app.desktop})"
                    break
            d_item = QTableWidgetItem(d_name)
            self.table_widget.setItem(row, 2, d_item)

            # 3: Command
            cmd_item = QTableWidgetItem(app.command)
            self.table_widget.setItem(row, 3, cmd_item)

            # 4: Match Rule
            match_item = QTableWidgetItem(app.match_rule)
            self.table_widget.setItem(row, 4, match_item)

            # 5: Active Toggle Switch
            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            check_layout.setContentsMargins(6, 0, 6, 0)
            check_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            toggle = ToggleSwitch(checked=app.enabled)
            toggle.toggled.connect(
                (lambda a_id=app.id: lambda checked: self._on_toggle_app_enabled(a_id, checked))()
            )
            check_layout.addWidget(toggle)
            self.table_widget.setCellWidget(row, 5, check_widget)

            # 6: Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            run_btn = QPushButton("▶")
            run_btn.setFixedSize(28, 28)
            run_btn.setToolTip("Test Launch")
            run_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: rgba(74, 222, 128, 0.12);
                    color: #4ade80;
                    border: 1px solid rgba(74, 222, 128, 0.3);
                    border-radius: 5px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0;
                }
                QPushButton:hover {
                    background-color: rgba(74, 222, 128, 0.28);
                    border-color: #4ade80;
                }
                """
            )
            run_btn.clicked.connect(
                (lambda a_id=app.id: lambda: self._on_test_launch_app(a_id))()
            )
            actions_layout.addWidget(run_btn)

            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setToolTip("Edit")
            edit_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #242735;
                    color: #f3f4f8;
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 5px;
                    font-size: 12px;
                    padding: 0;
                }
                QPushButton:hover {
                    border-color: #3daee9;
                    color: #3daee9;
                    background-color: rgba(61, 174, 233, 0.15);
                }
                """
            )
            edit_btn.clicked.connect(
                (lambda a_id=app.id: lambda: self._on_edit_app(a_id))()
            )
            actions_layout.addWidget(edit_btn)

            del_btn = QPushButton("✕")
            del_btn.setFixedSize(28, 28)
            del_btn.setToolTip("Delete")
            del_btn.setStyleSheet(
                """
                QPushButton {
                    background-color: rgba(248, 113, 113, 0.1);
                    color: #f87171;
                    border: 1px solid rgba(248, 113, 113, 0.25);
                    border-radius: 5px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 0;
                }
                QPushButton:hover {
                    background-color: rgba(248, 113, 113, 0.28);
                    border-color: #f87171;
                }
                """
            )
            del_btn.clicked.connect(
                (lambda a_id=app.id: lambda: self._on_delete_app(a_id))()
            )
            actions_layout.addWidget(del_btn)

            self.table_widget.setCellWidget(row, 6, actions_widget)

    def _update_status_bar(self) -> None:
        total_apps = len(self.config_mgr.config.apps)
        enabled_apps = len([a for a in self.config_mgr.config.apps if a.enabled])
        config_file = self.config_mgr.config_path
        self.status_bar.showMessage(
            f"Config: {config_file} | Total: {total_apps} apps ({enabled_apps} enabled on startup) | Desktops: {len(self.desktops)}"
        )

    # -----------------------------------------------------------------
    # User Actions
    # -----------------------------------------------------------------
    def _on_search_text_changed(self, text: str) -> None:
        self.search_query = text.strip().lower()
        self._refresh_views()

    def _on_view_mode_changed(self, mode_id: int) -> None:
        mode_str = "board" if mode_id == 0 else "list"
        self.stacked_widget.setCurrentIndex(mode_id)
        self.config_mgr.config.settings.view_mode = mode_str
        self.config_mgr.save()

    def _on_autostart_toggled(self, checked: bool) -> None:
        self.config_mgr.config.settings.autostart_enabled = checked
        self.config_mgr.save()
        self.autostart_mgr.sync(checked)
        status_text = "enabled" if checked else "disabled"
        self.status_bar.showMessage(f"Autostart on login {status_text}.", 3000)

    def _open_add_app_dialog(self, target_desktop: int = 1) -> None:
        dlg = AppDialog(
            desktops=self.desktops,
            default_desktop=target_desktop,
            parent=self,
        )
        if dlg.exec() == AppDialog.DialogCode.Accepted:
            new_app = dlg.get_app_item()
            if new_app:
                self.config_mgr.add_app(new_app)
                self._refresh_views()
                self.status_bar.showMessage(f"Added '{new_app.name}'.", 3000)

    def _on_edit_app(self, app_id: str) -> None:
        app = next((a for a in self.config_mgr.config.apps if a.id == app_id), None)
        if not app:
            return
        dlg = AppDialog(
            app_item=app,
            desktops=self.desktops,
            parent=self,
        )
        if dlg.exec() == AppDialog.DialogCode.Accepted:
            updated_app = dlg.get_app_item()
            if updated_app:
                self.config_mgr.update_app(app_id, updated_app)
                self._refresh_views()
                self.status_bar.showMessage(f"Updated '{updated_app.name}'.", 3000)

    def _on_delete_app(self, app_id: str) -> None:
        app = next((a for a in self.config_mgr.config.apps if a.id == app_id), None)
        if not app:
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove '{app.name}' from your startup apps?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.config_mgr.remove_app(app_id)
            self._refresh_views()
            self.status_bar.showMessage(f"Removed '{app.name}'.", 3000)

    def _on_toggle_app_enabled(self, app_id: str, enabled: bool) -> None:
        app = next((a for a in self.config_mgr.config.apps if a.id == app_id), None)
        if app:
            app.enabled = enabled
            self.config_mgr.save()
            self._update_status_bar()

    def _on_change_app_desktop(self, app_id: str, new_desktop: int) -> None:
        app = next((a for a in self.config_mgr.config.apps if a.id == app_id), None)
        if app:
            app.desktop = new_desktop
            self.config_mgr.save()
            self._refresh_views()
            self.status_bar.showMessage(f"Moved '{app.name}' to Desktop {new_desktop}.", 3000)

    def _on_test_launch_app(self, app_id: str) -> None:
        app = next((a for a in self.config_mgr.config.apps if a.id == app_id), None)
        if app:
            self.launcher.launch(app)
            self.status_bar.showMessage(f"Launched '{app.name}'.", 3000)

    def _on_create_virtual_desktop(self) -> None:
        count = self.kwin.get_desktop_count()
        new_count = self.kwin.ensure_minimum_desktops(count + 1)
        self._refresh_desktops_data()
        self._refresh_views()
        self.status_bar.showMessage(f"Created Desktop {new_count}.", 3000)

    def _open_test_runner(self) -> None:
        dlg = TestRunnerDialog(config_mgr=self.config_mgr, parent=self)
        dlg.exec()

    def _open_settings(self) -> None:
        dlg = SettingsDialog(
            settings=self.config_mgr.config.settings,
            desktops=self.desktops,
            parent=self,
        )
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            self.config_mgr.config.settings = dlg.get_settings()
            self.config_mgr.save()
            self.autostart_mgr.sync(self.config_mgr.config.settings.autostart_enabled)
            self.autostart_toggle.setChecked(self.config_mgr.config.settings.autostart_enabled)
            self._refresh_views()
            self.status_bar.showMessage("Saved settings.", 3000)

    def _on_refresh_all(self) -> None:
        self._refresh_desktops_data()
        self.config_mgr.config = self.config_mgr.load()
        self._refresh_views()
        self.kwin_badge.setText(
            "● KWin Wayland (Ready)" if self.kwin.is_kwin_running() else "○ KWin Offline"
        )
        self.desktops_badge.setText(f"🖥️ {len(self.desktops)} Virtual Desktops")
        self.status_bar.showMessage("Refreshed desktops and configuration.", 3000)
