#!/usr/bin/env python3
"""Main application window for CachyOS Workspace Startup Organizer."""

from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QAction
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
    QButtonGroup,
    QToolButton,
    QStatusBar,
)

from arch_auto_start_organizer.core.config import AppConfig, AppItem, ConfigManager
from arch_auto_start_organizer.core.kwin import KWinManager
from arch_auto_start_organizer.core.autostart import AutostartManager
from arch_auto_start_organizer.core.launcher import AppLauncher
from arch_auto_start_organizer.gui.app_card import AppCard
from arch_auto_start_organizer.gui.app_dialog import AppDialog
from arch_auto_start_organizer.gui.settings_dialog import SettingsDialog
from arch_auto_start_organizer.gui.test_runner_dialog import TestRunnerDialog


class MainWindow(QMainWindow):
    """Main window featuring Workspace Board and List views for startup apps."""

    def __init__(self, config_mgr: Optional[ConfigManager] = None):
        super().__init__()
        self.config_mgr = config_mgr or ConfigManager()
        self.kwin = KWinManager()
        self.autostart_mgr = AutostartManager()
        self.launcher = AppLauncher()

        self.desktops: List[Dict[str, Any]] = []

        self.setWindowTitle("CachyOS Workspace Startup Organizer")
        self.resize(1120, 720)
        self.setMinimumSize(850, 550)

        self._refresh_desktops_data()
        self._init_ui()
        self._refresh_views()

    def _refresh_desktops_data(self) -> None:
        """Fetches active virtual desktops from KWin DBus."""
        self.desktops = self.kwin.get_virtual_desktops()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        # 1. Main Stacked View Area (Board vs List)
        self.stacked_widget = QStackedWidget()

        # Page 0: Workspace Board View
        self.board_scroll = QScrollArea()
        self.board_scroll.setWidgetResizable(True)
        self.board_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.board_container = QWidget()
        self.board_layout = QHBoxLayout(self.board_container)
        self.board_layout.setContentsMargins(0, 0, 0, 0)
        self.board_layout.setSpacing(14)
        self.board_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.board_scroll.setWidget(self.board_container)
        self.stacked_widget.addWidget(self.board_scroll)

        # Page 1: List / Table View
        self.table_widget = self._create_table_view()
        self.stacked_widget.addWidget(self.table_widget)

        # 2. Top Header Bar
        header_bar = self._create_header_bar()
        main_layout.addLayout(header_bar)

        main_layout.addWidget(self.stacked_widget, stretch=1)

        # 3. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()

    def _create_header_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(12)

        # Left: App Title and Badges
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_label = QLabel("Workspace Startup Organizer")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_box.addWidget(title_label)

        # System Badges
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)

        kwin_ready = self.kwin.is_kwin_running()
        kwin_text = "● KWin Wayland Ready" if kwin_ready else "○ KWin Offline"
        kwin_color = "#9ece6a" if kwin_ready else "#f7768e"
        self.kwin_badge = QLabel(kwin_text)
        self.kwin_badge.setStyleSheet(
            f"color: {kwin_color}; font-size: 11px; font-weight: bold;"
        )
        badges_layout.addWidget(self.kwin_badge)

        self.desktops_badge = QLabel(f"• {len(self.desktops)} Desktops")
        self.desktops_badge.setStyleSheet("color: #888888; font-size: 11px;")
        badges_layout.addWidget(self.desktops_badge)

        title_box.addLayout(badges_layout)
        bar.addLayout(title_box)

        bar.addStretch()

        # Autostart Toggle Switch
        self.autostart_checkbox = QCheckBox("Run at Login")
        self.autostart_checkbox.setToolTip("Automatically run on CachyOS / KDE login")
        self.autostart_checkbox.setChecked(
            self.config_mgr.config.settings.autostart_enabled and self.autostart_mgr.is_installed()
        )
        self.autostart_checkbox.toggled.connect(self._on_autostart_toggled)
        bar.addWidget(self.autostart_checkbox)

        # View Mode Toggle (Board vs Table)
        view_toggle_layout = QHBoxLayout()
        view_toggle_layout.setSpacing(0)
        self.board_btn = QPushButton("📋 Board")
        self.board_btn.setCheckable(True)
        self.list_btn = QPushButton("📑 List")
        self.list_btn.setCheckable(True)

        self.view_btn_group = QButtonGroup(self)
        self.view_btn_group.addButton(self.board_btn, 0)
        self.view_btn_group.addButton(self.list_btn, 1)
        self.view_btn_group.idClicked.connect(self._on_view_mode_changed)

        initial_mode = self.config_mgr.config.settings.view_mode
        if initial_mode == "list":
            self.list_btn.setChecked(True)
            self.stacked_widget.setCurrentIndex(1)
        else:
            self.board_btn.setChecked(True)
            self.stacked_widget.setCurrentIndex(0)

        view_toggle_layout.addWidget(self.board_btn)
        view_toggle_layout.addWidget(self.list_btn)
        bar.addLayout(view_toggle_layout)

        # Action: Add App
        self.add_app_btn = QPushButton("＋ Add App")
        self.add_app_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #3daee9;
                color: #ffffff;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #55b9eb;
            }
            """
        )
        self.add_app_btn.clicked.connect(lambda: self._open_add_app_dialog())
        bar.addWidget(self.add_app_btn)

        # Action: Test Run
        self.test_run_btn = QPushButton("▶ Test Run")
        self.test_run_btn.setToolTip("Execute live startup sequence and view log output")
        self.test_run_btn.clicked.connect(self._open_test_runner)
        bar.addWidget(self.test_run_btn)

        # Action: Settings
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        bar.addWidget(self.settings_btn)

        # Action: Refresh
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh Virtual Desktops and Applications")
        self.refresh_btn.clicked.connect(self._on_refresh_all)
        bar.addWidget(self.refresh_btn)

        return bar

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
        return table

    def _refresh_views(self) -> None:
        """Rerenders both the Board and List views."""
        self._render_board_view()
        self._render_table_view()
        self._update_status_bar()

    def _render_board_view(self) -> None:
        """Constructs columns for each virtual desktop with app cards."""
        # Clear existing layout items
        while self.board_layout.count():
            item = self.board_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        apps_by_desktop = self.config_mgr.get_apps_by_desktop()
        max_desktop_num = max([d.get("number", 1) for d in self.desktops] + [4] + list(apps_by_desktop.keys()))

        for desktop_num in range(1, max_desktop_num + 1):
            desktop_name = f"Desktop {desktop_num}"
            for d in self.desktops:
                if d.get("number") == desktop_num and d.get("name"):
                    desktop_name = d["name"]
                    break

            desktop_apps = apps_by_desktop.get(desktop_num, [])

            # Column Container Frame
            col_frame = QFrame()
            col_frame.setFixedWidth(290)
            col_frame.setStyleSheet(
                """
                QFrame {
                    background-color: rgba(255, 255, 255, 0.02);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 10px;
                }
                """
            )
            col_layout = QVBoxLayout(col_frame)
            col_layout.setContentsMargins(10, 10, 10, 10)
            col_layout.setSpacing(10)
            col_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Column Header
            header_layout = QHBoxLayout()
            d_label = QLabel(f"<b>{desktop_name}</b>")
            d_label.setStyleSheet("font-size: 13px;")
            header_layout.addWidget(d_label)

            count_pill = QLabel(f"{len(desktop_apps)}")
            count_pill.setStyleSheet(
                "background-color: rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 2px 7px; font-size: 11px;"
            )
            header_layout.addWidget(count_pill)
            header_layout.addStretch()

            add_btn = QPushButton("+")
            add_btn.setFixedSize(24, 24)
            add_btn.setToolTip(f"Add app to {desktop_name}")
            add_btn.clicked.connect(
                (lambda d_num=desktop_num: lambda: self._open_add_app_dialog(target_desktop=d_num))()
            )
            header_layout.addWidget(add_btn)
            col_layout.addLayout(header_layout)

            # App Cards List
            if not desktop_apps:
                empty_lbl = QLabel("No apps configured.\nClick + to assign an app.")
                empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_lbl.setStyleSheet("color: #666666; font-size: 11px; padding: 20px 0;")
                col_layout.addWidget(empty_lbl)
            else:
                for app in desktop_apps:
                    card = AppCard(app=app, desktops=self.desktops)
                    card.edit_requested.connect(self._on_edit_app)
                    card.delete_requested.connect(self._on_delete_app)
                    card.toggle_enabled.connect(self._on_toggle_app_enabled)
                    card.desktop_changed.connect(self._on_change_app_desktop)
                    card.test_launch_requested.connect(self._on_test_launch_app)
                    col_layout.addWidget(card)

            self.board_layout.addWidget(col_frame)

        # "+ Add Virtual Desktop" Card
        add_desktop_col = QFrame()
        add_desktop_col.setFixedWidth(160)
        add_desktop_col.setStyleSheet(
            """
            QFrame {
                background-color: rgba(255, 255, 255, 0.01);
                border: 1px dashed rgba(255, 255, 255, 0.15);
                border-radius: 10px;
            }
            """
        )
        add_d_layout = QVBoxLayout(add_desktop_col)
        add_d_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        new_d_btn = QPushButton("➕ Add Desktop")
        new_d_btn.clicked.connect(self._on_create_virtual_desktop)
        add_d_layout.addWidget(new_d_btn)
        self.board_layout.addWidget(add_desktop_col)

    def _render_table_view(self) -> None:
        """Populates the tabular list view."""
        self.table_widget.setRowCount(0)
        apps = self.config_mgr.config.apps
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

            # 5: Active Checkbox
            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            check_layout.setContentsMargins(0, 0, 0, 0)
            check_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk.setChecked(app.enabled)
            chk.toggled.connect(
                (lambda a_id=app.id: lambda checked: self._on_toggle_app_enabled(a_id, checked))()
            )
            check_layout.addWidget(chk)
            self.table_widget.setCellWidget(row, 5, check_widget)

            # 6: Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            run_btn = QPushButton("▶")
            run_btn.setFixedSize(26, 26)
            run_btn.setToolTip("Test Launch")
            run_btn.clicked.connect(
                (lambda a_id=app.id: lambda: self._on_test_launch_app(a_id))()
            )
            actions_layout.addWidget(run_btn)

            edit_btn = QPushButton("✏")
            edit_btn.setFixedSize(26, 26)
            edit_btn.setToolTip("Edit")
            edit_btn.clicked.connect(
                (lambda a_id=app.id: lambda: self._on_edit_app(a_id))()
            )
            actions_layout.addWidget(edit_btn)

            del_btn = QPushButton("✕")
            del_btn.setFixedSize(26, 26)
            del_btn.setToolTip("Delete")
            del_btn.setStyleSheet("color: #e06c75;")
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
            f"Config: {config_file} | Total: {total_apps} apps ({enabled_apps} enabled) | Desktops: {len(self.desktops)}"
        )

    # User Actions
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
        self.status_bar.showMessage(f"Autostart at login {status_text}.", 3000)

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
            self.autostart_checkbox.setChecked(self.config_mgr.config.settings.autostart_enabled)
            self._refresh_views()
            self.status_bar.showMessage("Saved settings.", 3000)

    def _on_refresh_all(self) -> None:
        self._refresh_desktops_data()
        self.config_mgr.config = self.config_mgr.load()
        self._refresh_views()
        self.kwin_badge.setText("● KWin Wayland Ready" if self.kwin.is_kwin_running() else "○ KWin Offline")
        self.desktops_badge.setText(f"• {len(self.desktops)} Desktops")
        self.status_bar.showMessage("Refreshed desktops and configuration.", 3000)
