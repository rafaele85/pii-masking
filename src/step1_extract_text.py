import sys
import fitz  # PyMuPDF
import json
import os


def extract_text_from_pdf(pdf_path):
    """Extract text from the given PDF file."""
    doc = fitz.open(pdf_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = page.get_text()
        pages.append({
            "page_number": page_num + 1,  # Page numbers in the output are 1-based
            "content": page_text
        })
    return pages


def save_text_to_json(pages, output_path):
    """Save extracted text to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(pages, file, ensure_ascii=False, indent=4)


def main():
    if len(sys.argv) != 2:
        print("Usage: python step1_extract_text.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = "output/step1"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "extracted_text.json")

    print(f"Extracting text from {pdf_path}...")

    # Extract and save text as JSON
    pages = extract_text_from_pdf(pdf_path)
    save_text_to_json(pages, output_path)

    print(f"Text saved to {output_path}")


if __name__ == "__main__":
    main()
