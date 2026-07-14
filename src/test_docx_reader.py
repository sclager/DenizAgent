from pathlib import Path

from src.parser.document_loader import load_document

documents_folder = Path("documents")

docx_files = list(documents_folder.glob("*.docx"))

if not docx_files:
    raise FileNotFoundError("documents klasöründe .docx bulunamadı.")

test_file = docx_files[0]

print(f"Okunan dosya : {test_file.name}")
print("-" * 80)

text = load_document(str(test_file))

print(text[:3000])