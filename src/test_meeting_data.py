import json
from pathlib import Path

from src.meeting.meeting_data_builder import (
    build_meeting_form_data,
)
from src.meeting.meeting_input import (
    get_meeting_input,
)


def main() -> None:
    meeting_input = get_meeting_input()

    form_data = build_meeting_form_data(
        meeting_input
    )

    output_file = Path(
        "output/meeting_form_preview.json"
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            form_data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 70)
    print("TOPLANTI KAYDI ÖNİZLEMESİ")
    print("=" * 70)

    print(
        json.dumps(
            form_data,
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print(
        f"Önizleme dosyası oluşturuldu:\n"
        f"{output_file.resolve()}"
    )


if __name__ == "__main__":
    main()