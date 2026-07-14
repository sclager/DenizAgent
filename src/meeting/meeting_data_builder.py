from __future__ import annotations

from datetime import date
from typing import Any


def build_meeting_form_data(
    meeting_input: dict[str, str],
) -> dict[str, Any]:
    customer_name = meeting_input[
        "customer_name"
    ].strip()

    meeting_subject = meeting_input[
        "meeting_subject"
    ].strip()

    meeting_date = meeting_input[
        "meeting_date"
    ].strip()

    first_arrival_date = date.today().strftime(
        "%d.%m.%Y"
    )

    problem_description = (
        f"Toplantı Konusu:\n"
        f"{meeting_subject}\n\n"
        f"Toplantı Tarihi:\n"
        f"{meeting_date}\n\n"
        f"Amaç:\n"
        f"Toplantı yapılacak."
    )

    return {
        "Müşteri/Firma Ünvanı": customer_name,
        "Uygulama Türü": "GeniusOpen",
        "Sorun": meeting_subject,
        "Sorun açıklaması": problem_description,
        "İlgili sorun": "",
        "İlk Geliş Tarihi": first_arrival_date,
        "ITSM Kayıt No": "",
        "Öncelik": "3",
        "Zorluk derecesi": "Saat",
        "Gereksinimler": "Toplantı yapılacak.",
        "Planlanan Çalışma Süresi": 1.0,
        "Durum": "Yeni",
        "Atanan": "Can Deniz",
        "İlişkili MDH Uzmanı": "Can Deniz",
        "Durum Kategorisi": (
            "Müşteri test sonucu bekleniyor"
        ),
        "Kategori": "Müşteri Toplantı",
        "Etki seviyesi": "Genel",
    }