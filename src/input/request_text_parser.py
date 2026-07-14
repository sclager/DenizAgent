from __future__ import annotations

import re
from typing import Any


SECTION_KEYS = {
    1: "request",
    2: "request_description",
    3: "detailed_description",
    4: "cash_register_work",
    5: "service_work",
    6: "database_information",
    7: "success_failure_scenarios",
}


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = text.replace("\xa0", " ")

    return text.strip()

def extract_request_title(text: str) -> str:
    """
    1. bölümdeki yalnızca 'Talep Konusu:' değerini alır.

    Talep Konusu satırı yoksa mevcut metni olduğu gibi döndürür.
    """

    match = re.search(
        r"(?im)^\s*Talep\s+Konusu\s*:\s*(.+?)\s*$",
        text,
    )

    if match:
        return match.group(1).strip()

    return text.strip()

def clean_section_content(content: str) -> str:
    """
    Başlığın sonunda kalabilecek Markdown ve başlık metnini temizler.
    """

    content = content.strip()

    # Başlığın ilk satırını kaldırır.
    lines = content.splitlines()

    if lines:
        lines = lines[1:]

    cleaned = "\n".join(lines).strip()

    # Markdown kalıntılarını temizler.
    cleaned = re.sub(r"^\*+\s*", "", cleaned)
    cleaned = re.sub(r"\s*\*+$", "", cleaned)

    return cleaned.strip()


def find_numbered_sections(
    text: str,
) -> list[tuple[int, int, int]]:
    """
    Satır başında bulunan 1–7 numaralı başlıkları tespit eder.

    Desteklenen örnekler:
    1. Talep ve Genel Bilgiler
    1) Talep ve Genel Bilgiler
    **1. Talep ve Genel Bilgiler**
    ### 1. Talep ve Genel Bilgiler
    """

    pattern = re.compile(
        r"(?im)^"
        r"\s*"
        r"(?:#{1,6}\s*)?"
        r"(?:\*{1,2}\s*)?"
        r"([1-7])"
        r"\s*[\.\-\):]?\s*"
        r".+?"
        r"(?:\*{1,2})?"
        r"\s*$"
    )

    sections: list[tuple[int, int, int]] = []

    for match in pattern.finditer(text):
        section_number = int(match.group(1))

        sections.append(
            (
                section_number,
                match.start(),
                match.end(),
            )
        )

    return sections


def parse_request_text(
    raw_text: str,
    customer_name: str,
    itsm_no: str = "",
    country: str = "Türkiye",
    priority: str = "Standart",
) -> dict[str, Any]:
    text = normalize_text(raw_text)
    sections = find_numbered_sections(text)

    detected_numbers = {
        section_number
        for section_number, _, _ in sections
    }

    missing_numbers = [
        number
        for number in range(1, 8)
        if number not in detected_numbers
    ]

    if missing_numbers:
        missing_text = ", ".join(
            str(number)
            for number in missing_numbers
        )

        raise ValueError(
            "7 bölümün tamamı bulunamadı. "
            f"Eksik bölüm numaraları: {missing_text}"
        )

    # Aynı numaradan birden fazla bulunmuşsa ilkini kullanır.
    unique_sections: list[tuple[int, int, int]] = []
    used_numbers: set[int] = set()

    for section in sections:
        section_number = section[0]

        if section_number in used_numbers:
            continue

        used_numbers.add(section_number)
        unique_sections.append(section)

    unique_sections.sort(
        key=lambda item: item[1]
    )

    parsed_values: dict[str, str] = {}

    for index, section in enumerate(unique_sections):
        section_number, section_start, _ = section

        if index + 1 < len(unique_sections):
            content_end = unique_sections[index + 1][1]
        else:
            content_end = len(text)

        full_section = text[section_start:content_end]
        content = clean_section_content(full_section)

        section_key = SECTION_KEYS[section_number]
        if section_number == 1:
            parsed_values[section_key] = extract_request_title(content)
        else:
            parsed_values[section_key] = content

    empty_sections = [
        SECTION_KEYS[number]
        for number in range(1, 8)
        if not parsed_values.get(
            SECTION_KEYS[number],
            "",
        ).strip()
    ]

    if empty_sections:
        raise ValueError(
            "Bazı bölümlerin içeriği boş: "
            + ", ".join(empty_sections)
        )

    return {
        "itsm_no": itsm_no,
        "request_date": "",
        "customer_name": customer_name,
        "country": country,
        "priority": priority,
        **parsed_values,
    }