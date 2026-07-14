from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class QuickMenu(QWidget):
    def __init__(
        self,
        open_document_creation: Callable[[], None],
        open_existing_document: Callable[[], None],
        open_meeting_creation: Callable[[], None],
    ) -> None:
        super().__init__()

        self.open_document_creation_callback = (
            open_document_creation
        )
        self.open_existing_document_callback = (
            open_existing_document
        )
        self.open_meeting_creation_callback = (
            open_meeting_creation
        )

        self.setWindowTitle("Deniz Agent")

        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )

        self.setFixedSize(430, 330)

        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("quickMenuCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        header_row = QHBoxLayout()

        title_area = QVBoxLayout()
        title_area.setSpacing(2)

        title = QLabel("DENİZ AGENT")
        title.setObjectName("quickMenuTitle")

        subtitle = QLabel(
            "Yapmak istediğiniz işlemi seçin"
        )
        subtitle.setObjectName("quickMenuSubtitle")

        title_area.addWidget(title)
        title_area.addWidget(subtitle)

        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(34, 34)
        close_button.clicked.connect(self.hide)

        header_row.addLayout(title_area)
        header_row.addStretch()
        header_row.addWidget(close_button)

        layout.addLayout(header_row)

        document_button = self._create_action_button(
            shortcut="1",
            title="Doküman Oluştur + SharePoint",
            callback=self._open_document_creation,
        )

        existing_button = self._create_action_button(
            shortcut="2",
            title="Mevcut Dokümandan SharePoint",
            callback=self._open_existing_document,
        )

        meeting_button = self._create_action_button(
            shortcut="3",
            title="Toplantı Kaydı Oluştur",
            callback=self._open_meeting_creation,
        )

        layout.addWidget(document_button)
        layout.addWidget(existing_button)
        layout.addWidget(meeting_button)

        hint = QLabel(
            "1, 2 veya 3 tuşuna basabilirsiniz • Esc ile kapanır"
        )
        hint.setObjectName("hintLabel")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(hint)

        root_layout.addWidget(card)

    def _create_action_button(
        self,
        shortcut: str,
        title: str,
        callback: Callable[[], None],
    ) -> QPushButton:
        button = QPushButton(
            f"{shortcut}     {title}"
        )

        button.setObjectName("quickActionButton")
        button.setMinimumHeight(52)
        button.clicked.connect(callback)

        return button

    def show_centered(self) -> None:
        screen = self.screen()

        if screen is None:
            return

        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()

        window_geometry.moveCenter(
            screen_geometry.center()
        )

        self.move(window_geometry.topLeft())

        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def keyPressEvent(
        self,
        event: QKeyEvent,
    ) -> None:
        if event.key() == Qt.Key.Key_1:
            self._open_document_creation()
            return

        if event.key() == Qt.Key.Key_2:
            self._open_existing_document()
            return

        if event.key() == Qt.Key.Key_3:
            self._open_meeting_creation()
            return

        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return

        super().keyPressEvent(event)

    def _open_document_creation(self) -> None:
        self.hide()
        self.open_document_creation_callback()

    def _open_existing_document(self) -> None:
        self.hide()
        self.open_existing_document_callback()

    def _open_meeting_creation(self) -> None:
        self.hide()
        self.open_meeting_creation_callback()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QFrame#quickMenuCard {
                background-color: #f8fafc;
                border: 1px solid #cfd8e5;
                border-radius: 18px;
            }

            QLabel#quickMenuTitle {
                font-family: "Segoe UI";
                font-size: 22px;
                font-weight: 700;
                color: #123d6a;
            }

            QLabel#quickMenuSubtitle {
                font-family: "Segoe UI";
                font-size: 13px;
                color: #667085;
            }

            QPushButton#closeButton {
                background-color: transparent;
                color: #667085;
                border: none;
                border-radius: 17px;
                font-size: 23px;
                font-weight: 500;
            }

            QPushButton#closeButton:hover {
                background-color: #e7edf4;
                color: #1f2937;
            }

            QPushButton#quickActionButton {
                background-color: white;
                color: #1c3553;
                border: 1px solid #dce3ec;
                border-radius: 10px;
                padding: 10px 16px;
                text-align: left;
                font-family: "Segoe UI";
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton#quickActionButton:hover {
                background-color: #e8f1fb;
                border: 1px solid #6b94bd;
            }

            QPushButton#quickActionButton:pressed {
                background-color: #d8e9fa;
            }

            QLabel#hintLabel {
                font-family: "Segoe UI";
                color: #667085;
                font-size: 12px;
                padding-top: 4px;
            }
            """
        )