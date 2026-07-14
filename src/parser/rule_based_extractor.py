import re

from src.models.request_model import RequestModel


def _get_field_value(text: str, field_name: str) -> str:
    """
    'Alan Adı | Değer' formatındaki ilk eşleşmeyi bulur.
    """

    pattern = rf"(?im)^{re.escape(field_name)}\s*\|\s*(.+)$"
    match = re.search(pattern, text)

    if not match:
        return ""

    value = match.group(1).strip()

    # DOCX tablo hücreleri tekrar edebildiği için ilk değeri alır.
    if " | " in value:
        value = value.split(" | ")[0].strip()

    return value


def _get_multiline_field(
    text: str,
    start_field: str,
    next_fields: list[str],
) -> str:
    """
    Bir alanın başlangıcından sonraki alan başlığına kadar olan metni alır.
    """

    next_fields_pattern = "|".join(
        re.escape(field)
        for field in next_fields
    )

    pattern = (
        rf"(?ims)^{re.escape(start_field)}\s*\|\s*"
        rf"(.*?)"
        rf"(?=^(?:{next_fields_pattern})\s*\||\Z)"
    )

    match = re.search(pattern, text)

    if not match:
        return ""

    value = match.group(1).strip()

    # Aynı hücre metninin Word tablosunda tekrar etmesini azaltır.
    repeated_parts = [
        part.strip()
        for part in value.split(" | ")
        if part.strip()
    ]

    if repeated_parts:
        value = repeated_parts[0]

    return value.strip()


def extract_request_data(text: str) -> RequestModel:
    """
    Okunan doküman metninden talep bilgilerini çıkarır.
    """

    request_title = _get_multiline_field(
        text=text,
        start_field="Talep",
        next_fields=[
            "Talebin Tanımlanması",
            "İsteğin ayrıntılı açıklaması",
        ],
    )

    description = _get_multiline_field(
        text=text,
        start_field="Talebin Tanımlanması",
        next_fields=[
            "İsteğin ayrıntılı açıklaması",
            "Gereksinimler",
        ],
    )

    requirements = _get_multiline_field(
        text=text,
        start_field="İsteğin ayrıntılı açıklaması",
        next_fields=[
            "Beklenen Sonuç",
            "Ek Bilgiler",
            "Kategori",
        ],
    )

    return RequestModel(
        itsm_no=_get_field_value(text, "ITSM NO"),
        request_form_no=_get_field_value(text, "Talep Form Numarası"),
        request_date=_get_field_value(text, "Talep Tarihi"),
        customer_name=_get_field_value(text, "Talepte Bulunan Müşteri"),
        country=_get_field_value(
            text,
            "Talep Hangi Ülkede Kullanılacak?",
        ),
        category=_get_field_value(text, "İstek Kategorisi"),
        request_title=request_title,
        description=description,
        requirements=requirements,
    )