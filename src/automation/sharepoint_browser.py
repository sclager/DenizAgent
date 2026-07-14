import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import BrowserContext, Playwright, sync_playwright


load_dotenv()


def create_browser_context(playwright: Playwright) -> BrowserContext:
    profile_directory = Path("browser_profile").resolve()

    profile_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return playwright.chromium.launch_persistent_context(
        user_data_dir=str(profile_directory),
        headless=False,
        viewport={
            "width": 1600,
            "height": 900,
        },
        slow_mo=200,
    )


def open_sharepoint() -> None:
    sharepoint_url = os.getenv("SHAREPOINT_URL", "").strip()

    if not sharepoint_url:
        raise ValueError(
            "SHAREPOINT_URL bulunamadı. "
            ".env dosyasına SharePoint adresini ekleyin."
        )

    with sync_playwright() as playwright:
        browser_context = create_browser_context(playwright)

        if browser_context.pages:
            page = browser_context.pages[0]
        else:
            page = browser_context.new_page()

        print("SharePoint açılıyor...")

        page.goto(
            sharepoint_url,
            wait_until="domcontentloaded",
            timeout=120_000,
        )

        print()
        print("Tarayıcı açıldı.")
        print("Gerekirse kurumsal hesabınızla giriş yapın.")
        print("SharePoint listesi tamamen açıldığında terminale dönün.")
        print("Tarayıcıyı kapatmak için Enter tuşuna basın.")

        input()

        browser_context.close()


if __name__ == "__main__":
    open_sharepoint()