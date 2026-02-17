import sys
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path):
    """Extract text from the given PDF file."""
    doc = fitz.open(pdf_path)
    text = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text.append(page.get_text())
    return text


def save_text_to_file(text, output_path):
    """Save extracted text to a file."""
    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(text))


def main():
    if len(sys.argv) != 2:
        print("Usage: python step1_extract_text.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = "output/step1/extracted_text.txt"

    print(f"Extracting text from {pdf_path}...")

    # Extract and save text
    text = extract_text_from_pdf(pdf_path)
    save_text_to_file(text, output_path)

    print(f"Text saved to {output_path}")


if __name__ == "__main__":
    main()
