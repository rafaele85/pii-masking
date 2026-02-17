import json
import sys
import fitz


def extract_text_from_pdf(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)
    pages = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        pages.append({
            "page_number": page_num,
            "text": text,
            "char_count": len(text),
        })

    doc.close()

    return {
        "filename": pdf_path,
        "total_pages": len(pages),
        "pages": pages,
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = extract_text_from_pdf(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Please provide a PDF path")

