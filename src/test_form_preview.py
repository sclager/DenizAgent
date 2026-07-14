import json
from pathlib import Path
from typing import Any

from src.parser.document_loader import load_document
from src.parser.rule_based_extractor import extract_request_data


DEFAULT_FIELD_NAMES = {
    "application_type": "Uygulama Türü",
    "status": "Durum",
    "status_category": "Durum Kategorisi",
    "category": "Kategori",
    "priority": "Öncelik",
    "difficulty": "Zorluk derecesi",
    "planned_duration": "Planlanan Çalışma Süresi",
    "impact_level": "Etki seviyesi",
    "assigned_to": "Atanan",
    "mdh_specialist": "İlişkili MDH Uzmanı",
}


def load_json_file(file_path: str | Path) -> dict[str, Any]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Yapılandırma dosyası bulunamadı: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    documents_folder = Path("documents")
    docx_files = list(documents_folder.glob("*.docx"))

    if not docx_files:
        raise FileNotFoundError(
            "documents klasöründe .docx dosyası bulunamadı."
        )

    document_file = docx_files[0]

    document_text = load_document(document_file)
    request_data = extract_request_data(document_text)
    request_dict = request_data.model_dump()

    mapping = load_json_file("src/config/mapping.json")
    defaults = load_json_file("src/config/defaults.json")

    form_values: dict[str, Any] = {}

    print()
    print("=" * 90)
    print("DENİZ AGENT - SHAREPOINT FORM ÖNİZLEMESİ")
    print("=" * 90)
    print(f"Kaynak doküman: {document_file.name}")
    print()

    print("DOKÜMANDAN ÇIKARILAN ALANLAR")
    print("-" * 90)

    for source_field, sharepoint_field in mapping.items():
        value = request_dict.get(source_field, "")
        form_values[sharepoint_field] = value

        status = "DOLU" if str(value).strip() else "EKSİK"

        print(f"{sharepoint_field}:")
        print(f"  Durum : {status}")
        print(f"  Değer : {value}")
        print()

    print("VARSAYILAN ALANLAR")
    print("-" * 90)

    for source_field, value in defaults.items():
        sharepoint_field = DEFAULT_FIELD_NAMES.get(
            source_field,
            source_field,
        )

        form_values[sharepoint_field] = value

        status = "DOLU" if str(value).strip() else "EKSİK"

        print(f"{sharepoint_field}:")
        print(f"  Durum : {status}")
        print(f"  Değer : {value}")
        print()
    related_problem = request_dict.get("request_title", "")
    form_values["İlgili sorun"] = related_problem

    print("İlgili sorun:")
    print(f"  Durum : " f"{'DOLU' if str(related_problem).strip() else 'EKSİK'}"
        )
    print(f"  Değer : {related_problem}")
    print()
    missing_fields = [
        field_name
        for field_name, value in form_values.items()
        if value is None or str(value).strip() == ""
    ]

    print("=" * 90)
    print("SONUÇ")
    print("=" * 90)

    if missing_fields:
        print("Eksik alanlar:")

        for field_name in missing_fields:
            print(f"- {field_name}")
    else:
        print("Tanımlanan bütün form alanları dolu.")

    output_file = Path("output/form_preview.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            form_values,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(f"Önizleme dosyası: {output_file.resolve()}")


if __name__ == "__main__":
    main()