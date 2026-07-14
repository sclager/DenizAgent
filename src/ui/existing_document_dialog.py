from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from src.services.form_data_service import (
    build_form_data_from_document,
)
from src.ui.workers import SharePointWorker


class ExistingDocumentDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle(
            "Mevcut Dokümandan SharePoint Kaydı"
        )
        self.setMinimumSize(760, 360)

        self.selected_document: Optional[Path] = None
        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[SharePointWorker] = None

        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(
            "Mevcut Dokümandan SharePoint Kaydı"
        )
        title.setObjectName("titleLabel")

        description = QLabel(
            "Daha önce hazırlanmış şirket Word dokümanını "
            "seçin. Deniz Agent dokümanı okuyarak SharePoint "
            "formunu dolduracaktır."
        )
        description.setObjectName("descriptionLabel")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)

        file_row = QHBoxLayout()

        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        self.file_input.setPlaceholderText(
            "Bir DOCX dosyası seçin"
        )

        select_button = QPushButton("Doküman Seç")
        select_button.setObjectName("secondaryButton")
        select_button.clicked.connect(
            self.select_document
        )

        file_row.addWidget(self.file_input, stretch=1)
        file_row.addWidget(select_button)

        layout.addLayout(file_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat(
            "İşlem bekleniyor — %p%"
        )

        self.status_label = QLabel(
            "Önce bir Word dokümanı seçin."
        )
        self.status_label.setObjectName("statusLabel")

        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)
        layout.addStretch()

        button_row = QHBoxLayout()

        close_button = QPushButton("Geri")
        close_button.setObjectName("secondaryButton")
        close_button.clicked.connect(self.reject)

        self.draft_button = QPushButton(
            "Taslak Olarak Aç"
        )
        self.draft_button.setObjectName("draftButton")
        self.draft_button.setEnabled(False)
        self.draft_button.clicked.connect(
            lambda: self.start_process(auto_save=False)
        )

        self.direct_button = QPushButton(
            "Direkt Oluştur"
        )
        self.direct_button.setObjectName("primaryButton")
        self.direct_button.setEnabled(False)
        self.direct_button.clicked.connect(
            lambda: self.start_process(auto_save=True)
        )

        button_row.addWidget(close_button)
        button_row.addStretch()
        button_row.addWidget(self.draft_button)
        button_row.addWidget(self.direct_button)

        layout.addLayout(button_row)

    def select_document(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Word Dokümanı Seç",
            str(Path("documents").resolve()),
            "Word Documents (*.docx)",
        )

        if not file_path:
            return

        self.selected_document = Path(file_path)
        self.file_input.setText(str(self.selected_document))

        self.draft_button.setEnabled(True)
        self.direct_button.setEnabled(True)

        self.progress.setValue(0)
        self.status_label.setText(
            "Doküman seçildi. İşlem modunu seçebilirsiniz."
        )

    def start_process(self, auto_save: bool) -> None:
        if self.selected_document is None:
            QMessageBox.warning(
                self,
                "Doküman Seçilmedi",
                "Önce bir Word dokümanı seçin.",
            )
            return

        if (
            self.worker_thread is not None
            and self.worker_thread.isRunning()
        ):
            QMessageBox.warning(
                self,
                "İşlem Devam Ediyor",
                "Zaten çalışan bir SharePoint işlemi var.",
            )
            return

        if auto_save:
            answer = QMessageBox.question(
                self,
                "Direkt Oluştur",
                (
                    "SharePoint formu doldurulacak ve kayıt "
                    "otomatik olarak kaydedilecek.\n\n"
                    "Devam edilsin mi?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                return

        try:
            self.update_progress(
                15,
                "Word dokümanı okunuyor",
            )

            form_data = build_form_data_from_document(
                self.selected_document
            )

            self.update_progress(
                40,
                "SharePoint verisi hazırlandı",
            )

        except Exception as error:
            self.handle_failure(str(error))
            return

        self.worker_thread = QThread(self)

        self.worker = SharePointWorker(
            form_data=form_data,
            auto_save=auto_save,
        )

        self.worker.moveToThread(
            self.worker_thread
        )

        self.worker_thread.started.connect(
            self.worker.run
        )

        self.worker.progress.connect(
            self.update_progress
        )

        self.worker.completed.connect(
            self.handle_completed
        )

        self.worker.failed.connect(
            self.handle_failure
        )

        self.worker.finished.connect(
            self.worker_thread.quit
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.worker_thread.finished.connect(
            self.worker_thread.deleteLater
        )

        self.worker_thread.finished.connect(
            self.clear_worker
        )

        self.set_buttons_enabled(False)
        self.worker_thread.start()

    def update_progress(
        self,
        value: int,
        message: str,
    ) -> None:
        self.progress.setValue(value)
        self.progress.setFormat(
            f"{message} — %p%"
        )
        self.status_label.setText(message)

    def handle_completed(self, message: str) -> None:
        self.status_label.setText(message)

        QMessageBox.information(
            self,
            "İşlem Tamamlandı",
            message,
        )

    def handle_failure(self, error_message: str) -> None:
        self.progress.setValue(0)
        self.progress.setFormat(
            "İşlem başarısız — %p%"
        )
        self.status_label.setText(
            f"Hata: {error_message}"
        )

        QMessageBox.critical(
            self,
            "İşlem Başarısız",
            error_message,
        )

    def clear_worker(self) -> None:
        self.worker = None
        self.worker_thread = None
        self.set_buttons_enabled(
            self.selected_document is not None
        )

    def set_buttons_enabled(
        self,
        enabled: bool,
    ) -> None:
        self.draft_button.setEnabled(enabled)
        self.direct_button.setEnabled(enabled)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background-color: #f4f6f9;
            }

            QWidget {
                font-family: "Segoe UI";
                font-size: 14px;
                color: #1f2937;
            }

            QLabel#titleLabel {
                font-size: 22px;
                font-weight: 700;
                color: #172b4d;
            }

            QLabel#descriptionLabel {
                color: #667085;
            }

            QLineEdit {
                background-color: white;
                border: 1px solid #cfd8e5;
                border-radius: 8px;
                padding: 10px;
            }

            QPushButton {
                min-height: 40px;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: 600;
            }

            QPushButton#primaryButton {
                background-color: #185b96;
                color: white;
                border: none;
            }

            QPushButton#draftButton {
                background-color: #fff4d6;
                color: #8a5a00;
                border: 1px solid #e2bd63;
            }

            QPushButton#secondaryButton {
                background-color: white;
                color: #344054;
                border: 1px solid #cfd8e5;
            }

            QPushButton:disabled {
                background-color: #eaecf0;
                color: #98a2b3;
                border: 1px solid #d0d5dd;
            }

            QProgressBar {
                min-height: 23px;
                border: 1px solid #cfd8e5;
                border-radius: 9px;
                background-color: white;
                text-align: center;
                font-weight: 600;
            }

            QProgressBar::chunk {
                background-color: #2377b9;
                border-radius: 8px;
            }

            QLabel#statusLabel {
                background-color: #eaf7ee;
                color: #237a3b;
                border: 1px solid #b8dfc3;
                border-radius: 8px;
                padding: 10px;
            }
            """
        )