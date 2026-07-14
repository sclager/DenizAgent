from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.parser.document_loader import load_document
from src.parser.rule_based_extractor import extract_request_data


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MAPPING_FILE = (
    PROJECT_ROOT
    / "src"
    / "config"
    / "mapping.json"
)

DEFAULTS_FILE = (
    PROJECT_ROOT
    / "src"
    / "config"
    / "defaults.json"
)


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


def load_json_file(
    file_path: Path,
) -> dict[str, Any]:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Yapılandırma dosyası bulunamadı:\n{file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def build_form_data_from_document(
    document_path: str | Path,
) -> dict[str, Any]:
    path = Path(document_path).resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"Word dokümanı bulunamadı:\n{path}"
        )

    document_text = load_document(str(path))
    request_model = extract_request_data(document_text)
    request_dict = request_model.model_dump()

    mapping = load_json_file(MAPPING_FILE)
    defaults = load_json_file(DEFAULTS_FILE)

    form_data: dict[str, Any] = {}

    for source_field, sharepoint_field in mapping.items():
        form_data[sharepoint_field] = request_dict.get(
            source_field,
            "",
        )

    # İlgili sorun alanına Sorun ile aynı metin hazırlanır.
    # Lookup eşleşmesi yoksa SharePointWriter alanı boş bırakacaktır.
    form_data["İlgili sorun"] = request_dict.get(
        "request_title",
        "",
    )

    for default_key, default_value in defaults.items():
        sharepoint_field = DEFAULT_FIELD_NAMES.get(
            default_key,
            default_key,
        )

        form_data[sharepoint_field] = default_value

    return form_data