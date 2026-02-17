import sys
import json
from presidio_analyzer import AnalyzerEngine
import spacy

# Initialize Presidio analyzer and spaCy model
analyzer = AnalyzerEngine()
nlp = spacy.load("en_core_web_trf")

# Increase spaCy max_length to handle larger texts, but still mindful of memory usage
nlp.max_length = 1500000  # Allow longer texts, up to ~1.5 million characters


def analyze_text_for_pii(text):
    """Analyze text for PII using Presidio and spaCy."""
    results = analyzer.analyze(text=text, language="en")

    pii_data = []
    for res in results:
        pii_data.append({
            "text_row_number": res.start,  # This is a simple placeholder
            "column_number": res.end,  # Placeholder for column position
            "pii_type": res.entity_type,
            "value": text[res.start:res.end]
        })
    return pii_data


def read_json_file(input_file):
    """Read the JSON file containing extracted text."""
    with open(input_file, "r", encoding="utf-8") as file:
        return json.load(file)


def save_pii_to_file(pii_data, output_file):
    """Save PII analysis results to a file."""
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(pii_data, file, ensure_ascii=False, indent=4)


def analyze_page_for_pii(page_data):
    """Analyze a single page's text for PII."""
    page_text = page_data['content']
    return analyze_text_for_pii(page_text)


def main():
    if len(sys.argv) != 3:
        print("Usage: python step2_analyze_pii.py <extracted_text_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    print(f"Reading text from {input_file} and analyzing for PII...")

    # Read the JSON file containing extracted text
    pages = read_json_file(input_file)

    pii_data = []

    # Analyze each page one at a time
    for page_data in pages:
        print(f"Analyzing page {page_data['page_number']}...")
        page_pii = analyze_page_for_pii(page_data)
        pii_data.extend(page_pii)

    # Save results to file
    save_pii_to_file(pii_data, output_file)

    print(f"PII results saved to {output_file}")


if __name__ == "__main__":
    main()
