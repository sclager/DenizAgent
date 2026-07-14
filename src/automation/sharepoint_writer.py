from __future__ import annotations

from datetime import datetime
from typing import Any

from playwright.sync_api import Locator, Page


class SharePointWriter:
    """
    SharePoint formunu alan adlarına göre doldurur.

    Element sırasına veya index numarasına güvenmez.
    Alanları aria-label başlangıcına göre bulur.
    Ana formdaki Save butonuna basmaz.
    """

    def __init__(self, page: Page) -> None:
        self.page = page

    def _field(self, field_name: str) -> Locator:
        locator = self.page.locator(
            f'[aria-label^="{field_name}"]'
        )

        count = locator.count()

        if count == 0:
            raise RuntimeError(
                f"Form alanı bulunamadı: {field_name}"
            )

        for index in range(count):
            candidate = locator.nth(index)

            try:
                if candidate.is_visible():
                    return candidate
            except Exception:
                continue

        raise RuntimeError(
            f"Form alanı bulundu ancak görünür değil: {field_name}"
        )

    def fill_text(
        self,
        field_name: str,
        value: Any,
        required: bool = True,
    ) -> None:
        text = self._normalize(value)

        if not text:
            if required:
                raise ValueError(
                    f"'{field_name}' alanına yazılacak değer boş."
                )
            return

        field = self._field(field_name)
        field.wait_for(state="visible", timeout=30_000)
        field.fill(text)

        print(f"[OK] Metin alanı: {field_name} = {text}")

    def fill_rich_text(
        self,
        field_name: str,
        value: Any,
        required: bool = True,
    ) -> None:
        """
        Sorun açıklaması ve Gereksinimler gibi alanları doldurur.

        Ana formdaki Edit düğmesine basar, açılan yan panelde
        metni yazar ve panelin Save düğmesine basar.
        """

        text = self._normalize(value)

        if not text:
            if required:
                raise ValueError(
                    f"'{field_name}' alanına yazılacak değer boş."
                )
            return

        field = self._field(field_name)
        field.wait_for(state="visible", timeout=30_000)

        field_container = field.locator(
            "xpath=ancestor::*[.//button[@title='Edit']][1]"
        )

        if field_container.count() == 0:
            raise RuntimeError(
                f"'{field_name}' alanının Edit düğmesi bulunamadı."
            )

        edit_button = field_container.locator(
            "button[title='Edit']"
        )

        if edit_button.count() == 0:
            raise RuntimeError(
                f"'{field_name}' için Edit düğmesi bulunamadı."
            )

        print(f"[BİLGİ] Edit paneli açılıyor: {field_name}")

        edit_button.first.click()

        panel_title = self.page.get_by_text(
            f"Edit {field_name}",
            exact=True,
        )

        panel_title.wait_for(
            state="visible",
            timeout=30_000,
        )

        editor_panel = panel_title.locator(
            "xpath=ancestor::*["
            ".//button[normalize-space()='Save'] "
            "and .//button[normalize-space()='Cancel']"
            "][1]"
        )

        if editor_panel.count() == 0:
            raise RuntimeError(
                f"'{field_name}' düzenleme paneli bulunamadı."
            )

        editor_candidates = editor_panel.locator(
            "[contenteditable='true'], "
            "[role='textbox'], "
            "textarea"
        )

        editor: Locator | None = None

        for index in range(editor_candidates.count()):
            candidate = editor_candidates.nth(index)

            try:
                if candidate.is_visible():
                    editor = candidate
                    break
            except Exception:
                continue

        if editor is None:
            raise RuntimeError(
                f"'{field_name}' düzenleme alanı bulunamadı."
            )

        editor.click()

        try:
            editor.fill(text)
        except Exception:
            editor.press("Control+A")
            editor.press("Backspace")
            self.page.keyboard.insert_text(text)

        print(f"[OK] Rich-text metni yazıldı: {field_name}")

        save_button = editor_panel.get_by_role(
            "button",
            name="Save",
            exact=True,
        )

        if save_button.count() == 0:
            save_button = editor_panel.get_by_text(
                "Save",
                exact=True,
            )

        if save_button.count() == 0:
            raise RuntimeError(
                f"'{field_name}' panelindeki Save düğmesi bulunamadı."
            )

        save_button.first.click()

        panel_title.wait_for(
            state="hidden",
            timeout=30_000,
        )

        field.wait_for(
            state="visible",
            timeout=30_000,
        )

        print(f"[OK] Rich-text alanı kaydedildi: {field_name}")

    def fill_date(
        self,
        field_name: str,
        value: Any,
        required: bool = True,
    ) -> None:
        raw_value = self._normalize(value)

        if not raw_value:
            if required:
                raise ValueError(
                    f"'{field_name}' tarih değeri boş."
                )
            return

        formatted_date = self._format_date(raw_value)

        field = self._field(field_name)
        field.wait_for(state="visible", timeout=30_000)
        field.fill(formatted_date)
        field.press("Tab")

        print(
            f"[OK] Tarih alanı: "
            f"{field_name} = {formatted_date}"
        )

    def select_dropdown(
        self,
        field_name: str,
        option_text: Any,
        required: bool = True,
    ) -> None:
        """
        SharePoint seçim alanından görünür seçeneği seçer.

        Arka plandaki liste satırlarını değil, yalnızca açılmış olan
        dropdown veya portal içindeki görünür seçenekleri kullanır.
        """

        value = self._normalize(option_text)

        if not value:
            if required:
                raise ValueError(
                    f"'{field_name}' seçim değeri boş."
                )
            return

        field = self._field(field_name)
        field.wait_for(state="visible", timeout=30_000)

        current_text = ""

        try:
            current_text = self._normalize(field.inner_text())
        except Exception:
            pass

        if current_text.casefold() == value.casefold():
            print(
                f"[OK] Seçim zaten doğru: "
                f"{field_name} = {value}"
            )
            return

        field.click()
        self.page.wait_for_timeout(800)

        selected_option: Locator | None = None

        listboxes = self.page.locator(
            "[role='listbox']"
        )

        for listbox_index in range(listboxes.count()):
            listbox = listboxes.nth(listbox_index)

            try:
                if not listbox.is_visible():
                    continue
            except Exception:
                continue

            options = listbox.locator(
                "[role='option']"
            )

            for option_index in range(options.count()):
                option = options.nth(option_index)

                try:
                    if not option.is_visible():
                        continue

                    option_value = self._normalize(
                        option.inner_text()
                    )

                    if option_value.casefold() == value.casefold():
                        selected_option = option
                        break
                except Exception:
                    continue

            if selected_option is not None:
                break

        if selected_option is None:
            portals = self.page.locator(
                "[data-portal-node='true']"
            )

            for portal_index in range(portals.count()):
                portal = portals.nth(portal_index)

                try:
                    if not portal.is_visible():
                        continue
                except Exception:
                    continue

                candidates = portal.locator(
                    "[role='option'], "
                    "[role='menuitem'], "
                    "button"
                )

                for candidate_index in range(candidates.count()):
                    candidate = candidates.nth(candidate_index)

                    try:
                        if not candidate.is_visible():
                            continue

                        candidate_text = self._normalize(
                            candidate.inner_text()
                        )

                        if candidate_text.casefold() == value.casefold():
                            selected_option = candidate
                            break
                    except Exception:
                        continue

                if selected_option is not None:
                    break

        if selected_option is None:
            field.press("Escape")

            raise RuntimeError(
                f"'{field_name}' alanında görünür "
                f"'{value}' seçeneği bulunamadı."
            )

        selected_option.scroll_into_view_if_needed()
        selected_option.click()

        self.page.wait_for_timeout(500)

        print(
            f"[OK] Seçim alanı: "
            f"{field_name} = {value}"
        )

    def fill_lookup(
        self,
        field_name: str,
        search_text: Any,
        required: bool = False,
    ) -> None:
        """
        İlgili sorun gibi mevcut SharePoint kayıtlarından
        seçim yapılan lookup alanları için kullanılır.

        Eşleşme bulunamazsa alanı boş bırakır.
        """

        value = self._normalize(search_text)

        if not value:
            if required:
                raise ValueError(
                    f"'{field_name}' değeri boş."
                )
            return

        field = self._field(field_name)
        field.wait_for(state="visible", timeout=30_000)
        field.click()
        field.fill(value)

        self.page.wait_for_timeout(1_500)

        selected_option: Locator | None = None

        options = self.page.locator(
            "[role='option']"
        )

        for index in range(options.count()):
            option = options.nth(index)

            try:
                if not option.is_visible():
                    continue

                option_text = self._normalize(
                    option.inner_text()
                )

                if value.casefold() in option_text.casefold():
                    selected_option = option
                    break
            except Exception:
                continue

        if selected_option is None:
            field.press("Escape")
            field.fill("")

            print(
                f"[UYARI] '{field_name}' alanında eşleşme bulunamadı. "
                "Alan boş bırakıldı."
            )
            return

        selected_option.click()

        print(
            f"[OK] Lookup alanı: "
            f"{field_name} = {value}"
        )

    def fill_person(
        self,
        field_name: str,
        person_name: Any,
        required: bool = True,
    ) -> None:
        value = self._normalize(person_name)

        if not value:
            if required:
                raise ValueError(
                    f"'{field_name}' kişi değeri boş."
                )
            return

        # Kapsayıcı grubu değil, gerçek kişi arama inputunu bulur.
        field = self.page.locator(
            f'input[role="combobox"][aria-label^="{field_name}"]'
        )

        visible_field: Locator | None = None

        for index in range(field.count()):
            candidate = field.nth(index)

            try:
                if candidate.is_visible():
                    visible_field = candidate
                    break
            except Exception:
                continue

        if visible_field is None:
            raise RuntimeError(
                f"'{field_name}' kişi giriş alanı bulunamadı."
            )

        # Önce açık kalmış dialog/dropdown katmanlarının kapanmasını bekler.
        backdrops = self.page.locator(
            "div[aria-hidden='true'].fui-DialogSurface__backdrop"
        )

        for index in range(backdrops.count()):
            backdrop = backdrops.nth(index)

            try:
                if backdrop.is_visible():
                    backdrop.wait_for(
                        state="hidden",
                        timeout=10_000,
                    )
            except Exception:
                pass

        visible_field.scroll_into_view_if_needed()
        visible_field.click()
        visible_field.fill(value)

        self.page.wait_for_timeout(2_000)

        selected_person: Locator | None = None

        candidates = self.page.locator(
            "[role='option']:visible, "
            "[role='listitem']:visible"
        )

        for index in range(candidates.count()):
            candidate = candidates.nth(index)

            try:
                candidate_text = self._normalize(
                    candidate.inner_text()
                )

                if value.casefold() in candidate_text.casefold():
                    selected_person = candidate
                    break
            except Exception:
                continue

        if selected_person is None:
            visible_field.press("Escape")

            raise RuntimeError(
                f"'{field_name}' alanında "
                f"'{value}' kişisi bulunamadı."
            )

        selected_person.click()
        self.page.wait_for_timeout(500)

        print(
            f"[OK] Kişi alanı: "
            f"{field_name} = {value}"
        )

    def fill_form(
        self,
        form_data: dict[str, Any],
    ) -> None:
        """
        Önizleme JSON verisini SharePoint formuna yazar.

        Ana formun Save düğmesine basmaz.
        """

        self.fill_text(
            "Müşteri/Firma Ünvanı",
            form_data.get("Müşteri/Firma Ünvanı"),
        )

        self.select_dropdown(
            "Uygulama Türü",
            form_data.get("Uygulama Türü"),
        )

        self.fill_text(
            "Sorun",
            form_data.get("Sorun"),
        )

        self.fill_rich_text(
            "Sorun açıklaması",
            form_data.get("Sorun açıklaması"),
        )

        self.fill_lookup(
            "İlgili sorun",
            form_data.get("İlgili sorun"),
            required=False,
        )

        self.fill_date(
            "İlk Geliş Tarihi",
            form_data.get("İlk Geliş Tarihi"),
        )

        self.fill_text(
            "ITSM Kayıt No",
            form_data.get("ITSM Kayıt No"),
            required=False,
        )

        self.select_dropdown(
            "Öncelik",
            form_data.get("Öncelik"),
        )

        self.select_dropdown(
            "Zorluk derecesi",
            form_data.get("Zorluk derecesi"),
        )

        self.fill_rich_text(
            "Gereksinimler",
            form_data.get("Gereksinimler"),
        )

        self.fill_text(
            "Planlanan Çalışma Süresi",
            form_data.get("Planlanan Çalışma Süresi"),
        )

       
        self.fill_person(
            "Atanan",
            form_data.get("Atanan"),
        )

        self.fill_person(
            "İlşikili MDH Uzmanı",
            form_data.get("İlişkili MDH Uzmanı"),
        )

        self.select_dropdown(
            "Durum Kategorisi",
            form_data.get("Durum Kategorisi"),
        )

        self.select_dropdown(
            "Kategori",
            form_data.get("Kategori"),
        )

        self.select_dropdown(
            "Etki seviyesi",
            form_data.get("Etki seviyesi"),
        )

        print()
        print("=" * 80)
        print("FORM DOLDURMA TAMAMLANDI")
        print("Ana formdaki Save butonuna basılmadı.")
        print("=" * 80)
    
    def save_form(self) -> None:
        """
        Ana SharePoint formundaki Save butonuna basar
        ve formun kapanmasını bekler.
        """

        save_buttons = self.page.get_by_role(
            "button",
            name="Save",
            exact=True,
        )

        visible_save_button: Locator | None = None

        for index in range(save_buttons.count()):
            candidate = save_buttons.nth(index)

            try:
                if candidate.is_visible():
                    visible_save_button = candidate
                    break
            except Exception:
                continue

        if visible_save_button is None:
            raise RuntimeError(
                "Ana SharePoint formundaki Save butonu bulunamadı."
            )

        print("[BİLGİ] SharePoint kaydı kaydediliyor...")

        visible_save_button.scroll_into_view_if_needed()
        visible_save_button.click()

        self.page.wait_for_timeout(2_000)

        try:
            visible_save_button.wait_for(
                state="hidden",
                timeout=30_000,
            )
        except Exception:
            pass

        print("[OK] SharePoint kaydı kaydedildi.")
        
    @staticmethod
    def _normalize(value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def _format_date(value: str) -> str:
        supported_formats = (
            "%d.%m.%Y",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y-%m-%d",
        )

        for date_format in supported_formats:
            try:
                parsed_date = datetime.strptime(
                    value,
                    date_format,
                )

                return parsed_date.strftime("%m/%d/%Y")

            except ValueError:
                continue

        raise ValueError(
            f"Desteklenmeyen tarih biçimi: {value}"
        )