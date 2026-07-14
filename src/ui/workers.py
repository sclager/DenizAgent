from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from src.automation.sharepoint_runner import (
    run_sharepoint_form,
)


class SharePointWorker(QObject):
    progress = Signal(int, str)
    completed = Signal(str)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        form_data: dict[str, Any],
        auto_save: bool,
    ) -> None:
        super().__init__()

        self.form_data = form_data
        self.auto_save = auto_save

    @Slot()
    def run(self) -> None:
        try:
            run_sharepoint_form(
                form_data=self.form_data,
                auto_save=self.auto_save,
                progress_callback=self._report_progress,
            )

            if self.auto_save:
                message = (
                    "SharePoint kaydı başarıyla oluşturuldu."
                )
            else:
                message = (
                    "SharePoint taslak form işlemi tamamlandı."
                )

            self.completed.emit(message)

        except Exception as error:
            self.failed.emit(str(error))

        finally:
            self.finished.emit()

    def _report_progress(
        self,
        value: int,
        message: str,
    ) -> None:
        self.progress.emit(value, message)