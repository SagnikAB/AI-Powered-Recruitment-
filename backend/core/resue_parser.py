import PyPDF2


def extract_text(file_path):
    text = ""

    try:
        if file_path.endswith(".pdf"):
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""

    except Exception as e:
        print("Parsing error:", e)

    return text.strip()