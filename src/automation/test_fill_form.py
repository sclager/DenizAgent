import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

from src.automation.sharepoint_writer import SharePointWriter


load_dotenv()


PROFILE_DIRECTORY = Path("browser_profile").resolve()
PREVIEW_FILE = Path("output/form_preview.json")


def load_preview_data() -> dict[str, Any]:
    if not PREVIEW_FILE.exists():
        raise FileNotFoundError(
            f"Önizleme dosyası bulunamadı: "
            f"{PREVIEW_FILE.resolve()}"
        )

    with PREVIEW_FILE.open(
        mode="r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def open_new_item_form(page: Page) -> None:
    add_button = page.get_by_role(
        "menuitem",
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


def main() -> None:
    sharepoint_url = os.getenv(
        "SHAREPOINT_URL",
        "",
    ).strip()

    if not sharepoint_url:
        raise ValueError(
            "SHAREPOINT_URL .env dosyasında tanımlı değil."
        )

    form_data = load_preview_data()

    PROFILE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIRECTORY),
            headless=False,
            viewport={
                "width": 1600,
                "height": 900,
            },
            slow_mo=250,
        )

        page = (
            context.pages[0]
            if context.pages
            else context.new_page()
        )

        print("SharePoint açılıyor...")

        page.goto(
            sharepoint_url,
            wait_until="domcontentloaded",
            timeout=120_000,
        )

        page.wait_for_timeout(3_000)

        print("Yeni kayıt formu açılıyor...")
        open_new_item_form(page)

        print("Form alanları dolduruluyor...")
        print()

        writer = SharePointWriter(page)
        writer.fill_form(form_data)

        print()
        print("Formu tarayıcıdan kontrol edin.")
        print("Henüz Save butonuna basılmadı.")
        print(
            "Tarayıcıyı kapatmak için "
            "terminalde Enter tuşuna basın."
        )

        input()

        context.close()


if __name__ == "__main__":
    main()