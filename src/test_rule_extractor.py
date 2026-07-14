from pathlib import Path

from src.parser.document_loader import load_document
from src.parser.rule_based_extractor import extract_request_data


def main() -> None:
    documents_folder = Path("documents")
    docx_files = list(documents_folder.glob("*.docx"))

    if not docx_files:
        raise FileNotFoundError(
            "documents klasöründe .docx dosyası bulunamadı."
        )

    test_file = docx_files[0]

    text = load_document(str(test_file))
    request_data = extract_request_data(text)

    print(f"Okunan dosya: {test_file.name}")
    print("-" * 80)
    print(request_data.model_dump_json(indent=2))


if __name__ == "__main__":
    main()