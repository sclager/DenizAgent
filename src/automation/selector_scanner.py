import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright


load_dotenv()


OUTPUT_FILE = Path("output/sharepoint_form_elements.json")
PROFILE_DIRECTORY = Path("browser_profile").resolve()


def clean_value(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def scan_elements(page: Page) -> list[dict[str, Any]]:
    """
    Sayfadaki form elemanlarını ve faydalı HTML özelliklerini toplar.
    """

    selectors = (
        "input, textarea, select, button, "
        "[contenteditable='true'], [role='combobox'], "
        "[role='textbox'], [role='spinbutton']"
    )

    elements = page.locator(selectors)
    count = elements.count()

    results: list[dict[str, Any]] = []

    for index in range(count):
        element = elements.nth(index)

        try:
            visible = element.is_visible()
        except Exception:
            visible = False

        if not visible:
            continue

        try:
            element_data = element.evaluate(
                """
                (element) => {
                    const labels = [];

                    if (element.labels) {
                        for (const label of element.labels) {
                            const text = label.innerText || label.textContent || "";
                            if (text.trim()) {
                                labels.push(text.trim());
                            }
                        }
                    }

                    if (element.id) {
                        const explicitLabel =
                            document.querySelector(`label[for="${CSS.escape(element.id)}"]`);

                        if (explicitLabel) {
                            const text =
                                explicitLabel.innerText ||
                                explicitLabel.textContent ||
                                "";

                            if (text.trim() && !labels.includes(text.trim())) {
                                labels.push(text.trim());
                            }
                        }
                    }

                    let parentText = "";
                    const parent = element.closest(
                        "div, fieldset, section, form"
                    );

                    if (parent) {
                        parentText = (
                            parent.innerText ||
                            parent.textContent ||
                            ""
                        ).trim();
                    }

                    return {
                        tag: element.tagName.toLowerCase(),
                        type: element.getAttribute("type") || "",
                        id: element.id || "",
                        name: element.getAttribute("name") || "",
                        role: element.getAttribute("role") || "",
                        aria_label:
                            element.getAttribute("aria-label") || "",
                        aria_labelledby:
                            element.getAttribute("aria-labelledby") || "",
                        placeholder:
                            element.getAttribute("placeholder") || "",
                        title: element.getAttribute("title") || "",
                        value:
                            "value" in element
                                ? String(element.value || "")
                                : "",
                        text:
                            (
                                element.innerText ||
                                element.textContent ||
                                ""
                            ).trim(),
                        labels: labels,
                        parent_text: parentText.substring(0, 500)
                    };
                }
                """
            )

            element_data["index"] = index
            results.append(element_data)

        except Exception as error:
            results.append(
                {
                    "index": index,
                    "scan_error": str(error),
                }
            )

    return results


def print_summary(elements: list[dict[str, Any]]) -> None:
    print()
    print("=" * 100)
    print("SHAREPOINT FORM ELEMENTLERİ")
    print("=" * 100)

    for item in elements:
        if "scan_error" in item:
            print(
                f"[{item['index']}] Tarama hatası: "
                f"{item['scan_error']}"
            )
            continue

        possible_name = (
            item.get("aria_label")
            or ", ".join(item.get("labels", []))
            or item.get("placeholder")
            or item.get("title")
            or item.get("text")
            or item.get("name")
            or item.get("id")
            or "İsimsiz alan"
        )

        print(
            f"[{item['index']}] "
            f"{item.get('tag', '')} "
            f"type={item.get('type', '')!r}"
        )
        print(f"  Tahmini alan : {possible_name[:200]}")
        print(f"  id           : {item.get('id', '')}")
        print(f"  name         : {item.get('name', '')}")
        print(f"  role         : {item.get('role', '')}")
        print(f"  aria-label   : {item.get('aria_label', '')}")
        print(f"  placeholder  : {item.get('placeholder', '')}")
        print()


def main() -> None:
    sharepoint_url = clean_value(os.getenv("SHAREPOINT_URL"))

    if not sharepoint_url:
        raise ValueError(
            "SHAREPOINT_URL bulunamadı. "
            ".env dosyasını kontrol edin."
        )

    PROFILE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.parent.mkdir(
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
            slow_mo=200,
        )

        page = context.pages[0] if context.pages else context.new_page()

        print("SharePoint açılıyor...")

        page.goto(
            sharepoint_url,
            wait_until="domcontentloaded",
            timeout=120_000,
        )

        page.wait_for_timeout(3000)

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
                "'Add new item' düğmesi bulunamadı."
            )

        print("'Add new item' düğmesine basılıyor...")

        add_button.first.click()

        print("Formun açılması bekleniyor...")
        page.wait_for_timeout(5000)

        print(
            "Form açıldıysa terminale dönüp Enter tuşuna basın. "
            "Form henüz açılmadıysa tarayıcıda açılmasını bekleyin."
        )
        input()

        elements = scan_elements(page)

        with OUTPUT_FILE.open(
            mode="w",
            encoding="utf-8",
        ) as file:
            json.dump(
                elements,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print_summary(elements)

        print()
        print(f"Bulunan görünür eleman sayısı: {len(elements)}")
        print(f"JSON çıktısı: {OUTPUT_FILE.resolve()}")
        print()
        print("Tarayıcıyı kapatmak için Enter tuşuna basın.")

        input()

        context.close()


if __name__ == "__main__":
    main()