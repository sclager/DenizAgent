from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.ui.hotkey_manager import HotkeyManager
from src.ui.main_window import MainWindow
from src.ui.quick_menu import QuickMenu
from src.ui.tray_manager import TrayManager


class DenizAgentApplication:
    def __init__(self) -> None:
        self.application = QApplication(sys.argv)

        self.application.setApplicationName(
            "Deniz Agent"
        )
        self.application.setOrganizationName(
            "Deniz Agent"
        )

        project_root = Path(__file__).resolve().parent

        icon_path = (
            project_root
            / "assets"
            / "deniz_agent.ico"
        )

        if icon_path.exists():
            application_icon = QIcon(str(icon_path))
            self.application.setWindowIcon(application_icon)
        else:
            application_icon = QIcon()

        # Ana pencere kapandığında uygulama tamamen kapanmaz.
        # Sistem tepsisinde çalışmaya devam eder.
        self.application.setQuitOnLastWindowClosed(False)

        self.main_window = MainWindow()

        if not application_icon.isNull():
            self.main_window.setWindowIcon(application_icon)

        self.quick_menu = QuickMenu(
            open_document_creation=(
                self.open_document_creation
            ),
            open_existing_document=(
                self.open_existing_document
            ),
            open_meeting_creation=(
                self.open_meeting_creation
            ),
        )

        if not application_icon.isNull():
            self.quick_menu.setWindowIcon(application_icon)

        self.tray_manager = TrayManager(
            show_main_window=self.show_main_window,
            show_quick_menu=self.show_quick_menu,
            exit_application=self.exit_application,
        )

        self.hotkey_manager = HotkeyManager(
            "ctrl+shift+d"
        )

        self.hotkey_manager.hotkey_pressed.connect(
            self.show_quick_menu
        )

    def start(self) -> int:
        self.hotkey_manager.register()
        self.tray_manager.show()

        # Windows başladığında uygulama sessizce tray'e gider.
        self.main_window.hide()

        return self.application.exec()

    def show_main_window(self) -> None:
        self.main_window.showNormal()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def show_quick_menu(self) -> None:
        if self.quick_menu.isVisible():
            self.quick_menu.hide()
        else:
            self.quick_menu.show_centered()

    def open_document_creation(self) -> None:
        self.show_main_window()
        self.main_window.open_document_creation()

    def open_existing_document(self) -> None:
        self.show_main_window()
        self.main_window.open_existing_document()

    def open_meeting_creation(self) -> None:
        self.show_main_window()
        self.main_window.open_meeting_creation()

    def exit_application(self) -> None:
        self.hotkey_manager.unregister()
        self.tray_manager.hide()
        self.application.quit()


def main() -> None:
    deniz_agent = DenizAgentApplication()

    exit_code = deniz_agent.start()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()