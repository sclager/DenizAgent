from __future__ import annotations

from datetime import datetime


SUPPORTED_DATE_FORMATS = (
    "%d.%m.%Y",
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%m/%d/%Y",
)


def normalize_meeting_date(value: str) -> str:
    raw_value = value.strip()

    if not raw_value:
        raise ValueError("Toplantı tarihi boş bırakılamaz.")

    for date_format in SUPPORTED_DATE_FORMATS:
        try:
            parsed_date = datetime.strptime(
                raw_value,
                date_format,
            )

            return parsed_date.strftime("%d.%m.%Y")

        except ValueError:
            continue

    raise ValueError(
        "Toplantı tarihi desteklenmeyen biçimde. "
        "Örnek: 15.07.2026"
    )


def get_meeting_input() -> dict[str, str]:
    print()
    print("=" * 70)
    print("DENİZ AGENT - TOPLANTI KAYDI")
    print("=" * 70)

    customer_name = input(
        "Müşteri adını girin: "
    ).strip()

    if not customer_name:
        raise ValueError(
            "Müşteri adı boş bırakılamaz."
        )

    meeting_subject = input(
        "Toplantı konusunu girin: "
    ).strip()

    if not meeting_subject:
        raise ValueError(
            "Toplantı konusu boş bırakılamaz."
        )

    meeting_date = normalize_meeting_date(
        input(
            "Toplantı tarihini girin "
            "[Örnek: 15.07.2026]: "
        )
    )

    return {
        "customer_name": customer_name,
        "meeting_subject": meeting_subject,
        "meeting_date": meeting_date,
    }