from src.parser.document_loader import load_document

file_path = "C:\Users\can.deniz\Desktop\Deniz Agent v0.1\DenizAgent\documents\DEVCR_XXX_QR_ODEME_HATASI.docx"

text = load_document(file_path)

print(text[:1000])