from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TrayManager:
    def __init__(
        self,
        *,
        show_main_window: Callable[[], None],
        show_quick_menu: Callable[[], None],
        exit_application: Callable[[], None],
    ) -> None:
        self.show_main_window_callback = (
            show_main_window
        )
        self.show_quick_menu_callback = (
            show_quick_menu
        )
        self.exit_application_callback = (
            exit_application
        )

        icon_path = (
            PROJECT_ROOT
            / "assets"
            / "deniz_agent.ico"
        )

        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            icon = QApplication.style().standardIcon(
                QApplication.style().StandardPixmap.SP_ComputerIcon
            )

        self.tray_icon = QSystemTrayIcon(icon)
        self.tray_icon.setToolTip(
            "Deniz Agent — Ctrl + Shift + D"
        )

        self.menu = QMenu()

        open_action = QAction(
            "Deniz Agent'ı Aç",
            self.menu,
        )
        open_action.triggered.connect(
            self.show_main_window_callback
        )

        quick_menu_action = QAction(
            "Hızlı İşlem Menüsü",
            self.menu,
        )
        quick_menu_action.triggered.connect(
            self.show_quick_menu_callback
        )

        exit_action = QAction(
            "Çıkış",
            self.menu,
        )
        exit_action.triggered.connect(
            self.exit_application_callback
        )

        self.menu.addAction(open_action)
        self.menu.addAction(quick_menu_action)
        self.menu.addSeparator()
        self.menu.addAction(exit_action)

        self.tray_icon.setContextMenu(self.menu)

        self.tray_icon.activated.connect(
            self._on_tray_activated
        )

    def show(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError(
                "Windows sistem tepsisi kullanılamıyor."
            )

        self.tray_icon.show()

        self.tray_icon.showMessage(
            "Deniz Agent",
            (
                "Deniz Agent arka planda çalışıyor.\n"
                "Ctrl + Shift + D ile hızlı menüyü açabilirsiniz."
            ),
            QSystemTrayIcon.MessageIcon.Information,
            4_000,
        )

    def hide(self) -> None:
        self.tray_icon.hide()

    def _on_tray_activated(
        self,
        reason: QSystemTrayIcon.ActivationReason,
    ) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.show_main_window_callback()