from pathlib import Path

from src.parser.document_loader import load_document
from src.parser.rule_based_extractor import extract_request_data
from src.utils.json_exporter import export_request_to_json


def main() -> None:
    documents_folder = Path("documents")
    docx_files = list(documents_folder.glob("*.docx"))

    if not docx_files:
        raise FileNotFoundError(
            "documents klasöründe .docx dosyası bulunamadı."
        )

    input_file = docx_files[0]

    text = load_document(str(input_file))
    request_data = extract_request_data(text)

    output_file = Path("output") / f"{input_file.stem}.json"

    created_file = export_request_to_json(
        request_data=request_data,
        output_file=output_file,
    )

    print(f"JSON oluşturuldu: {created_file.resolve()}")


if __name__ == "__main__":
    main()