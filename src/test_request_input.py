import json
import os

from src.document.document_generator import generate_request_document
from src.input.request_input import get_request_input
from src.input.request_text_parser import parse_request_text


def main() -> None:
    input_data = get_request_input()

    request_data = parse_request_text(
        raw_text=input_data["raw_request_text"],
        customer_name=input_data["customer_name"],
        itsm_no=input_data["itsm_no"],
        country=input_data["country"],
        priority=input_data["priority"],
    )

    print()
    print("=" * 70)
    print("AYRIŞTIRILAN TALEP VERİSİ")
    print("=" * 70)

    print(
        json.dumps(
            request_data,
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print("Word dokümanı hazırlanıyor...")

    output_file = generate_request_document(
        request_data=request_data,
    )

    print()
    print("=" * 70)
    print("DOKÜMAN OLUŞTURULDU")
    print("=" * 70)
    print(output_file.resolve())

    open_document = input(
        "\nOluşturulan Word dokümanı açılsın mı? (E/H): "
    ).strip().casefold()

    if open_document == "e":
        os.startfile(output_file)


if __name__ == "__main__":
    main()