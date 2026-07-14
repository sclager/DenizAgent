from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

from src.automation.sharepoint_writer import SharePointWriter


load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIRECTORY = PROJECT_ROOT / "browser_profile"


ProgressCallback = Callable[[int, str], None]


def open_new_item_form(page: Page) -> None:
    add_button = page.get_by_role(
        "menuitem",
        name="Add new item",
        exact=True,
    )

    if add_button.count() == 0:
        add_button = page.get_by_role(
            "button",
            name="Add new item",
            exact=True,
        )

    if add_button.count() == 0:
        add_button = page.get_by_text(
            "Add new item",
            exact=True,
        )

    if add_button.count() == 0:
        raise RuntimeError(
            "'Add new item' butonu bulunamadı."
        )

    add_button.first.click()

    customer_field = page.locator(
        "[aria-label^='Müşteri/Firma Ünvanı']"
    )

    customer_field.wait_for(
        state="visible",
        timeout=30_000,
    )


def run_sharepoint_form(
    form_data: dict[str, Any],
    *,
    auto_save: bool,
    progress_callback: ProgressCallback | None = None,
) -> None:
    def report(value: int, message: str) -> None:
        if progress_callback is not None:
            progress_callback(value, message)

    sharepoint_url = os.getenv(
        "SHAREPOINT_URL",
        "",
    ).strip()

    if not sharepoint_url:
        raise ValueError(
            "SHAREPOINT_URL .env dosyasında tanımlı değil."
        )

    PROFILE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    report(50, "SharePoint tarayıcısı açılıyor")

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIRECTORY),
            headless=False,
            viewport={
                "width": 1600,
                "height": 900,
            },
            slow_mo=200,
        )

        try:
            page = (
                context.pages[0]
                if context.pages
                else context.new_page()
            )

            page.goto(
                sharepoint_url,
                wait_until="domcontentloaded",
                timeout=120_000,
            )

            page.wait_for_timeout(2_000)

            report(60, "Yeni SharePoint kayıt formu açılıyor")
            open_new_item_form(page)

            report(70, "SharePoint alanları dolduruluyor")

            writer = SharePointWriter(page)
            writer.fill_form(form_data)

            if auto_save:
                report(90, "SharePoint kaydı kaydediliyor")
                writer.save_form()

                report(
                    100,
                    "SharePoint kaydı başarıyla oluşturuldu",
                )

                page.wait_for_timeout(2_000)
            else:
                report(
                    100,
                    (
                        "SharePoint formu hazır. "
                        "Kontrol edip Save butonuna basabilirsiniz."
                    ),
                )

                # Taslak modunda kullanıcı formu kendisi kaydeder
                # veya tarayıcıyı kapatır.
                while not page.is_closed():
                    page.wait_for_timeout(1_000)

        finally:
            try:
                context.close()
            except Exception:
                # Kullanıcı tarayıcıyı manuel kapatmış olabilir.
                pass