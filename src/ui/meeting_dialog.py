from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from PySide6.QtCore import QDate, QThread
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from src.meeting.meeting_data_builder import (
    build_meeting_form_data,
)
from src.ui.workers import SharePointWorker


class MeetingDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Toplantı Kaydı Oluştur")
        self.setMinimumSize(720, 480)

        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[SharePointWorker] = None

        self._build_ui()
        self._apply_styles()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Toplantı Kaydı Oluştur")
        title.setObjectName("titleLabel")

        description = QLabel(
            "Toplantı bilgilerini girin. Taslak modunda "
            "SharePoint formu doldurulur ancak kaydedilmez. "
            "Direkt oluştur modunda kayıt otomatik kaydedilir."
        )
        description.setObjectName("descriptionLabel")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)

        layout.addWidget(QLabel("Müşteri adı *"))

        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText(
            "Örnek: BTT"
        )
        layout.addWidget(self.customer_input)

        layout.addWidget(QLabel("Toplantı konusu *"))

        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText(
            "Örnek: Ürün limitli satış değerlendirmesi"
        )
        layout.addWidget(self.subject_input)

        layout.addWidget(QLabel("Toplantı tarihi *"))

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        self.date_input.setDate(QDate.currentDate())

        layout.addWidget(self.date_input)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat(
            "İşlem bekleniyor — %p%"
        )

        self.status_label = QLabel(
            "Toplantı bilgilerini girin."
        )
        self.status_label.setObjectName("statusLabel")

        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)
        layout.addStretch()

        button_row = QHBoxLayout()

        back_button = QPushButton("Geri")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.reject)

        self.draft_button = QPushButton(
            "Taslak Olarak Aç"
        )
        self.draft_button.setObjectName("draftButton")
        self.draft_button.clicked.connect(
            lambda: self.start_process(auto_save=False)
        )

        self.direct_button = QPushButton(
            "Direkt Oluştur"
        )
        self.direct_button.setObjectName("primaryButton")
        self.direct_button.clicked.connect(
            lambda: self.start_process(auto_save=True)
        )

        button_row.addWidget(back_button)
        button_row.addStretch()
        button_row.addWidget(self.draft_button)
        button_row.addWidget(self.direct_button)

        layout.addLayout(button_row)

    def collect_meeting_data(self) -> dict:
        customer_name = self.customer_input.text().strip()
        meeting_subject = self.subject_input.text().strip()

        if not customer_name:
            raise ValueError(
                "Müşteri adı boş bırakılamaz."
            )

        if not meeting_subject:
            raise ValueError(
                "Toplantı konusu boş bırakılamaz."
            )

        selected_date = self.date_input.date()

        meeting_date = selected_date.toString(
            "dd.MM.yyyy"
        )

        meeting_input = {
            "customer_name": customer_name,
            "meeting_subject": meeting_subject,
            "meeting_date": meeting_date,
        }

        return build_meeting_form_data(
            meeting_input
        )

    def start_process(self, auto_save: bool) -> None:
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
                    "Toplantı kaydı SharePoint'e otomatik "
                    "olarak kaydedilecek.\n\n"
                    "Devam edilsin mi?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                return

        try:
            self.update_progress(
                20,
                "Toplantı bilgileri kontrol ediliyor",
            )

            form_data = self.collect_meeting_data()

            self.update_progress(
                40,
                "Toplantı form verisi hazırlandı",
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
            "Toplantı Kaydı Başarısız",
            error_message,
        )

    def clear_worker(self) -> None:
        self.worker = None
        self.worker_thread = None
        self.set_buttons_enabled(True)

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

            QLineEdit,
            QDateEdit {
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