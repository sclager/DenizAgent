
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QCoreApplication, QThread, Qt

from src.services.form_data_service import (
    build_form_data_from_document,
)
from src.ui.workers import SharePointWorker

from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.document.document_generator import generate_request_document
from src.input.request_text_parser import parse_request_text
from src.ui.existing_document_dialog import (
    ExistingDocumentDialog,
)
from src.ui.meeting_dialog import MeetingDialog

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Deniz Agent v0.1")
        self.setMinimumSize(1000, 740)

        self.last_created_document: Optional[Path] = None
        self.sharepoint_thread: Optional[QThread] = None
        self.sharepoint_worker: Optional[SharePointWorker] = None

        self.stack = QStackedWidget()

        root_widget = QWidget()
        root_layout = QVBoxLayout(root_widget)
        root_layout.setContentsMargins(24, 20, 24, 24)
        root_layout.setSpacing(18)

        root_layout.addWidget(self._create_header())
        root_layout.addWidget(self._create_separator())
        root_layout.addWidget(self.stack, stretch=1)

        self.setCentralWidget(root_widget)

        self.home_page = self._create_home_page()
        self.document_creation_page = (
            self._create_document_creation_page()
        )

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.document_creation_page)

        self.apply_styles()

    def _create_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title_area = QVBoxLayout()
        title_area.setSpacing(3)

        title = QLabel("DENİZ AGENT")
        title.setObjectName("headerTitle")

        subtitle = QLabel(
            "Talep dokümanı ve SharePoint kayıt otomasyonu"
        )
        subtitle.setObjectName("headerSubtitle")

        title_area.addWidget(title)
        title_area.addWidget(subtitle)

        version = QLabel("v0.1")
        version.setObjectName("versionLabel")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setFixedSize(65, 32)

        layout.addLayout(title_area)
        layout.addStretch()
        layout.addWidget(version)

        return header

    @staticmethod
    def _create_separator() -> QFrame:
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        return separator

    def _create_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(16)

        heading = QLabel("Yapmak istediğiniz işlemi seçin")
        heading.setObjectName("pageHeading")

        description = QLabel(
            "Her işlem, mevcut Deniz Agent modüllerini kullanarak "
            "adım adım ilerleyecektir."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(heading)
        layout.addWidget(description)
        layout.addSpacing(10)

        layout.addWidget(
            self._create_operation_card(
                number="1",
                title="Doküman Oluştur + SharePoint Kaydı",
                description=(
                    "Müşteri bilgilerini ve 7 başlıklı talep metnini "
                    "kullanarak şirket Word dokümanını oluşturur ve "
                    "SharePoint formunu doldurur."
                ),
                button_text="Doküman Oluştur",
                callback=self.open_document_creation,
            )
        )

        layout.addWidget(
            self._create_operation_card(
                number="2",
                title="Mevcut Dokümandan SharePoint Kaydı",
                description=(
                    "Daha önce hazırlanmış bir DOCX dosyasını seçer, "
                    "verileri ayrıştırır ve SharePoint formunu doldurur."
                ),
                button_text="Doküman Seç",
                callback=self.open_existing_document,
            )
        )

        layout.addWidget(
            self._create_operation_card(
                number="3",
                title="Toplantı Kaydı Oluştur",
                description=(
                    "Müşteri, toplantı konusu ve toplantı tarihini "
                    "alarak dokümansız SharePoint toplantı kaydı oluşturur."
                ),
                button_text="Toplantı Kaydı",
                callback=self.open_meeting_creation,
            )
        )

        layout.addStretch()

        status = QLabel(
            "Sistem Durumu: Arayüz ve Word üretim modülü hazır."
        )
        status.setObjectName("statusLabel")
        layout.addWidget(status)

        return page

    def _create_operation_card(
        self,
        number: str,
        title: str,
        description: str,
        button_text: str,
        callback,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("operationCard")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(18)

        number_label = QLabel(number)
        number_label.setObjectName("operationNumber")
        number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        number_label.setFixedSize(50, 50)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("operationTitle")

        description_label = QLabel(description)
        description_label.setObjectName("operationDescription")
        description_label.setWordWrap(True)

        content_layout.addWidget(title_label)
        content_layout.addWidget(description_label)

        action_button = QPushButton(button_text)
        action_button.setObjectName("primaryButton")
        action_button.setMinimumWidth(170)
        action_button.setMinimumHeight(42)
        action_button.clicked.connect(callback)

        layout.addWidget(number_label)
        layout.addLayout(content_layout, stretch=1)
        layout.addWidget(action_button)

        return card

    def _create_document_creation_page(self) -> QWidget:
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(10, 16, 10, 10)
        main_layout.setSpacing(14)

        heading_row = QHBoxLayout()

        heading_area = QVBoxLayout()
        heading_area.setSpacing(4)

        heading = QLabel("Talep Dokümanı Oluştur")
        heading.setObjectName("pageHeading")

        description = QLabel(
            "Müşteri bilgilerini girin ve hazırlanan 7 başlıklı "
            "talep metnini aşağıdaki alana yapıştırın."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        heading_area.addWidget(heading)
        heading_area.addWidget(description)

        back_button = QPushButton("← Ana Menü")
        back_button.setObjectName("secondaryButton")
        back_button.clicked.connect(self.go_home)

        heading_row.addLayout(heading_area, stretch=1)
        heading_row.addWidget(back_button)

        main_layout.addLayout(heading_row)

        form_card = QFrame()
        form_card.setObjectName("formCard")

        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(20, 18, 20, 18)
        form_layout.setSpacing(12)

        first_row = QHBoxLayout()
        first_row.setSpacing(12)

        customer_area = QVBoxLayout()
        customer_area.addWidget(QLabel("Müşteri adı *"))

        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText(
            "Örnek: AYDINLI"
        )
        customer_area.addWidget(self.customer_input)

        itsm_area = QVBoxLayout()
        itsm_area.addWidget(QLabel("ITSM numarası"))

        self.itsm_input = QLineEdit()
        self.itsm_input.setPlaceholderText(
            "Yoksa boş bırakın"
        )
        itsm_area.addWidget(self.itsm_input)

        first_row.addLayout(customer_area, stretch=1)
        first_row.addLayout(itsm_area, stretch=1)

        second_row = QHBoxLayout()
        second_row.setSpacing(12)

        country_area = QVBoxLayout()
        country_area.addWidget(QLabel("Ülke"))

        self.country_input = QLineEdit("Türkiye")
        country_area.addWidget(self.country_input)

        priority_area = QVBoxLayout()
        priority_area.addWidget(QLabel("İstek kategorisi"))

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(
            ["Standart", "Normal", "Acil"]
        )
        priority_area.addWidget(self.priority_combo)

        second_row.addLayout(country_area, stretch=1)
        second_row.addLayout(priority_area, stretch=1)

        text_label = QLabel("7 başlıklı talep metni *")

        self.request_text_input = QTextEdit()
        self.request_text_input.setPlaceholderText(
            "1. Talep ve Genel Bilgiler\n"
            "...\n\n"
            "2. Talebin Tanımlanması\n"
            "...\n\n"
            "3. İsteğin Ayrıntılı Açıklaması\n"
            "...\n\n"
            "4. Kasa Tarafı Çalışmaları\n"
            "...\n\n"
            "5. Servis Tarafı Çalışmaları\n"
            "...\n\n"
            "6. Database Bilgileri\n"
            "...\n\n"
            "7. Başarılı / Başarısız Senaryo Açıklamaları\n"
            "..."
        )
        self.request_text_input.setMinimumHeight(280)

        form_layout.addLayout(first_row)
        form_layout.addLayout(second_row)
        form_layout.addWidget(text_label)
        form_layout.addWidget(
            self.request_text_input,
            stretch=1,
        )

        main_layout.addWidget(form_card, stretch=1)

        self.document_progress = QProgressBar()
        self.document_progress.setRange(0, 100)
        self.document_progress.setValue(0)
        self.document_progress.setTextVisible(True)
        self.document_progress.setFormat(
            "İşlem bekleniyor — %p%"
        )

        self.document_status = QLabel(
            "Bilgileri doldurduktan sonra bir işlem seçin."
        )
        self.document_status.setObjectName("statusLabel")

        button_layout = QHBoxLayout()

        clear_button = QPushButton("Temizle")
        clear_button.setObjectName("secondaryButton")
        clear_button.clicked.connect(
            self.clear_document_form
        )

        draft_button = QPushButton("Taslak Oluştur")
        draft_button.setObjectName("draftButton")
        draft_button.clicked.connect(
            self.create_draft_document
        )

        self.continue_from_draft_button = QPushButton(
            "Oluşan Taslaktan Devam Et"
        )
        self.continue_from_draft_button.setObjectName(
            "continueButton"
        )
        self.continue_from_draft_button.setEnabled(False)
        self.continue_from_draft_button.clicked.connect(
            self.continue_from_created_draft
        )

        complete_button = QPushButton(
            "Doğrudan Oluştur ve Devam Et"
        )
        complete_button.setObjectName("primaryButton")
        complete_button.clicked.connect(
            self.start_full_document_process
        )

        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        button_layout.addWidget(draft_button)
        button_layout.addWidget(
            self.continue_from_draft_button
        )
        button_layout.addWidget(complete_button)

        main_layout.addWidget(self.document_progress)
        main_layout.addWidget(self.document_status)
        main_layout.addLayout(button_layout)

        return page

    def open_document_creation(self) -> None:
        self.document_progress.setValue(0)
        self.document_progress.setFormat(
            "İşlem bekleniyor — %p%"
        )
        self.document_status.setText(
            "Bilgileri doldurun ve metni yapıştırın."
        )
        self.stack.setCurrentWidget(
            self.document_creation_page
        )

    def go_home(self) -> None:
        self.stack.setCurrentWidget(self.home_page)

    def clear_document_form(self) -> None:
        answer = QMessageBox.question(
            self,
            "Formu Temizle",
            "Girilen bütün bilgiler temizlensin mi?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.customer_input.clear()
        self.itsm_input.clear()
        self.country_input.setText("Türkiye")
        self.priority_combo.setCurrentText("Standart")
        self.request_text_input.clear()

        self.document_progress.setValue(0)
        self.document_progress.setFormat(
            "İşlem bekleniyor — %p%"
        )
        self.document_status.setText(
            "Form temizlendi."
        )

    def collect_request_data(self) -> dict:
        customer_name = self.customer_input.text().strip()
        itsm_no = self.itsm_input.text().strip()
        country = (
            self.country_input.text().strip()
            or "Türkiye"
        )
        priority = self.priority_combo.currentText()
        raw_text = (
            self.request_text_input
            .toPlainText()
            .strip()
        )

        if not customer_name:
            raise ValueError(
                "Müşteri adı boş bırakılamaz."
            )

        if not raw_text:
            raise ValueError(
                "7 başlıklı talep metni boş bırakılamaz."
            )

        return parse_request_text(
            raw_text=raw_text,
            customer_name=customer_name,
            itsm_no=itsm_no,
            country=country,
            priority=priority,
        )

    def set_document_progress(
        self,
        value: int,
        message: str,
    ) -> None:
        self.document_progress.setValue(value)
        self.document_progress.setFormat(
            f"{message} — %p%"
        )
        self.document_status.setText(message)
        QCoreApplication.processEvents()

    def generate_document_from_form(self) -> Path:
        self.set_document_progress(
            10,
            "Girilen bilgiler kontrol ediliyor",
        )

        request_data = self.collect_request_data()

        self.set_document_progress(
            35,
            "7 başlıklı metin ayrıştırıldı",
        )

        output_file = generate_request_document(
            request_data=request_data,
        )

        self.last_created_document = Path(output_file)

        self.set_document_progress(
            100,
            "Word dokümanı başarıyla oluşturuldu",
        )

        return self.last_created_document

    def create_draft_document(self) -> None:
        try:
            output_file = self.generate_document_from_form()
            self.continue_from_draft_button.setEnabled(True)

        except Exception as error:
            self.document_progress.setValue(0)
            self.document_progress.setFormat(
                "İşlem başarısız — %p%"
            )
            self.document_status.setText(
                f"Hata: {error}"
            )

            QMessageBox.critical(
                self,
                "Doküman Oluşturulamadı",
                str(error),
            )
            return

        answer = QMessageBox.question(
            self,
            "Taslak Oluşturuldu",
            (
                "Word dokümanı başarıyla oluşturuldu.\n\n"
                f"{output_file}\n\n"
                "Doküman şimdi açılsın mı?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if answer == QMessageBox.StandardButton.Yes:
            os.startfile(str(output_file))

    def continue_from_created_draft(self) -> None:
        if self.last_created_document is None:
            QMessageBox.warning(
                self,
                "Taslak Bulunamadı",
                "Önce bir Word taslağı oluşturun.",
            )
            return

        if not self.last_created_document.exists():
            QMessageBox.critical(
                self,
                "Dosya Bulunamadı",
                (
                    "Oluşturulan Word taslağı bulunamadı:\n\n"
                    f"{self.last_created_document}"
                ),
            )
            return

        answer = QMessageBox.question(
            self,
            "Taslaktan Devam Et",
            (
                "Word üzerindeki değişiklikleri kaydettiğinizden "
                "emin olun.\n\n"
                "SharePoint formu doldurulacak fakat otomatik "
                "kaydedilmeyecek.\n\n"
                "Devam edilsin mi?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.set_document_progress(
                20,
                "Düzenlenmiş Word dokümanı okunuyor",
            )

            form_data = build_form_data_from_document(
                self.last_created_document
            )

            self.set_document_progress(
                40,
                "SharePoint verisi hazırlandı",
            )

            self.start_sharepoint_process(
                form_data=form_data,
                auto_save=False,
            )

        except Exception as error:
            self.on_sharepoint_failed(str(error))

    def start_sharepoint_process(
        self,
        form_data: dict,
        *,
        auto_save: bool,
    ) -> None:
        if (
            self.sharepoint_thread is not None
            and self.sharepoint_thread.isRunning()
        ):
            QMessageBox.warning(
                self,
                "İşlem Devam Ediyor",
                "Zaten çalışan bir SharePoint işlemi var.",
            )
            return

        self.sharepoint_thread = QThread(self)

        self.sharepoint_worker = SharePointWorker(
            form_data=form_data,
            auto_save=auto_save,
        )

        self.sharepoint_worker.moveToThread(
            self.sharepoint_thread
        )

        self.sharepoint_thread.started.connect(
            self.sharepoint_worker.run
        )

        self.sharepoint_worker.progress.connect(
            self.set_document_progress
        )

        self.sharepoint_worker.completed.connect(
            self.on_sharepoint_completed
        )

        self.sharepoint_worker.failed.connect(
            self.on_sharepoint_failed
        )

        self.sharepoint_worker.finished.connect(
            self.sharepoint_thread.quit
        )

        self.sharepoint_worker.finished.connect(
            self.sharepoint_worker.deleteLater
        )

        self.sharepoint_thread.finished.connect(
            self.sharepoint_thread.deleteLater
        )

        self.sharepoint_thread.finished.connect(
            self.clear_sharepoint_worker
        )

        self.sharepoint_thread.start()

    def on_sharepoint_completed(
        self,
        message: str,
    ) -> None:
        self.document_status.setText(message)

        QMessageBox.information(
            self,
            "İşlem Tamamlandı",
            message,
        )

    def on_sharepoint_failed(
        self,
        error_message: str,
    ) -> None:
        self.document_progress.setValue(0)
        self.document_progress.setFormat(
            "İşlem başarısız — %p%"
        )

        self.document_status.setText(
            f"Hata: {error_message}"
        )

        QMessageBox.critical(
            self,
            "SharePoint İşlemi Başarısız",
            error_message,
        )

    def clear_sharepoint_worker(self) -> None:
        self.sharepoint_worker = None
        self.sharepoint_thread = None

    def start_full_document_process(self) -> None:
        answer = QMessageBox.question(
            self,
            "Direkt Oluştur",
            (
                "Word dokümanı oluşturulacak ve SharePoint kaydı "
                "otomatik olarak kaydedilecek.\n\n"
                "Devam edilsin mi?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            output_file = self.generate_document_from_form()

            self.set_document_progress(
                35,
                "Oluşturulan Word yeniden okunuyor",
            )

            form_data = build_form_data_from_document(
                output_file
            )

            self.set_document_progress(
                45,
                "SharePoint verisi hazırlandı",
            )

            self.start_sharepoint_process(
                form_data=form_data,
                auto_save=True,
            )

        except Exception as error:
            self.on_sharepoint_failed(str(error))
            
    def open_existing_document(self) -> None:
        
        dialog = ExistingDocumentDialog(self)
        dialog.exec()

    def open_meeting_creation(self) -> None:
        
        dialog = MeetingDialog(self)
        dialog.exec()

    def apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f4f6f9;
            }

            QWidget {
                font-family: "Segoe UI";
                font-size: 14px;
                color: #1f2937;
            }

            QLabel#headerTitle {
                font-size: 26px;
                font-weight: 700;
                color: #123d6a;
            }

            QLabel#headerSubtitle {
                font-size: 13px;
                color: #667085;
            }

            QLabel#versionLabel {
                background-color: #123d6a;
                color: white;
                border-radius: 8px;
                font-weight: 700;
            }

            QFrame#separator {
                color: #d8dee8;
                background-color: #d8dee8;
                max-height: 1px;
            }

            QLabel#pageHeading {
                font-size: 22px;
                font-weight: 650;
                color: #172b4d;
            }

            QLabel#pageDescription {
                color: #667085;
            }

            QFrame#operationCard,
            QFrame#formCard {
                background-color: white;
                border: 1px solid #dce3ec;
                border-radius: 12px;
            }

            QFrame#operationCard:hover {
                border: 1px solid #6b94bd;
            }

            QLabel#operationNumber {
                background-color: #e8f1fb;
                color: #123d6a;
                border-radius: 25px;
                font-size: 20px;
                font-weight: 700;
            }

            QLabel#operationTitle {
                font-size: 17px;
                font-weight: 650;
                color: #1c3553;
            }

            QLabel#operationDescription {
                color: #667085;
                font-size: 13px;
            }

            QLineEdit,
            QTextEdit,
            QComboBox {
                background-color: white;
                border: 1px solid #cfd8e5;
                border-radius: 8px;
                padding: 9px;
                selection-background-color: #185b96;
            }

            QLineEdit:focus,
            QTextEdit:focus,
            QComboBox:focus {
                border: 1px solid #185b96;
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

            QPushButton#primaryButton:hover {
                background-color: #124b7e;
            }

            QPushButton#draftButton {
                background-color: #e8f1fb;
                color: #164f82;
                border: 1px solid #98b9d8;
            }

            QPushButton#draftButton:hover {
                background-color: #d8e9fa;
            }

            QPushButton#secondaryButton {
                background-color: white;
                color: #344054;
                border: 1px solid #cfd8e5;
            }

            QPushButton#secondaryButton:hover {
                background-color: #f1f4f8;
            }

            QProgressBar {
                min-height: 22px;
                border: 1px solid #cfd8e5;
                border-radius: 9px;
                background-color: white;
                text-align: center;
                font-weight: 600;
                color: #344054;
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
            QPushButton#continueButton {
                background-color: #fff4d6;
                color: #8a5a00;
                border: 1px solid #e2bd63;
            }

            QPushButton#continueButton:hover {
                background-color: #ffeab2;
            }

            QPushButton#continueButton:disabled {
                background-color: #f1f3f5;
                color: #98a2b3;
                border: 1px solid #d0d5dd;
            }
            """
        )