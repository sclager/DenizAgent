from __future__ import annotations


def read_multiline_input() -> str:
    """
    Windows terminalinde çok satırlı metin alır.

    Metin yapıştırıldıktan sonra:
    Ctrl+Z
    Enter
    tuşlarına basılarak giriş tamamlanır.
    """

    print()
    print("7 başlıklı talep metnini yapıştırın.")
    print("Metin bitince Ctrl+Z ardından Enter tuşuna basın.")
    print("-" * 70)

    lines: list[str] = []

    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    return "\n".join(lines).strip()


def get_request_input() -> dict[str, str]:
    print()
    print("=" * 70)
    print("DENİZ AGENT - TALEP DOKÜMANI OLUŞTURMA")
    print("=" * 70)

    customer_name = input("Müşteri adını girin: ").strip()

    if not customer_name:
        raise ValueError("Müşteri adı boş bırakılamaz.")

    itsm_no = input(
        "ITSM numarasını girin, yoksa Enter'a basın: "
    ).strip()

    country = input(
        "Ülke [Türkiye]: "
    ).strip() or "Türkiye"

    priority = input(
        "Öncelik [Standart / Normal / Acil] [Standart]: "
    ).strip() or "Standart"

    valid_priorities = {
        "standart": "Standart",
        "normal": "Normal",
        "acil": "Acil",
    }

    normalized_priority = priority.casefold()

    if normalized_priority not in valid_priorities:
        raise ValueError(
            "Öncelik yalnızca Standart, Normal veya Acil olabilir."
        )

    request_text = read_multiline_input()

    if not request_text:
        raise ValueError("Talep metni boş bırakılamaz.")

    return {
        "customer_name": customer_name,
        "itsm_no": itsm_no,
        "country": country,
        "priority": valid_priorities[normalized_priority],
        "raw_request_text": request_text,
    }