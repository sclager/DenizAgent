from pathlib import Path

from src.parser.docx_reader import read_docx


def load_document(file_path: str) -> str:
    """
    Desteklenen belgeyi okuyup metin döndürür.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: {path}")

    extension = path.suffix.lower()

    if extension == ".docx":
        return read_docx(path)

    raise ValueError(f"Desteklenmeyen dosya türü: {extension}")