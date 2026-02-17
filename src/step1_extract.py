import json
import sys
from pathlib import Path
import fitz


def extract_pdf_text(pdf_path: str, output_dir: Path) -> Path:
    """Step 1: Extract text from PDF and save to output/step1/."""
    doc = fitz.open(pdf_path)
    pages_data = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        pages_data.append({
            "page_number": page_num + 1,
            "text": text,
            "char_count": len(text)
        })

    doc.close()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{Path(pdf_path).stem}_text.json"

    result = {
        "filename": Path(pdf_path).name,
        "total_pages": len(pages_data),
        "pages": pages_data
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return output_file


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        step1_file = extract_pdf_text(pdf_path, Path("output/step1"))
        print(f"Step 1 saved: {step1_file}")
    else:
        print("Usage: python step1_extract.py <pdf_path>")