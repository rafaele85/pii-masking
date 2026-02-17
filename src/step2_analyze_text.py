import sys
import json
from presidio_analyzer import AnalyzerEngine
import spacy

# Initialize Presidio analyzer and spaCy model
analyzer = AnalyzerEngine()
nlp = spacy.load("en_core_web_trf")


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


def read_text_file(input_file):
    """Read the text from a file."""
    with open(input_file, "r", encoding="utf-8") as file:
        return file.read()


def save_pii_to_file(pii_data, output_file):
    """Save PII analysis results to a file."""
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(pii_data, file, ensure_ascii=False, indent=4)


def main():
    if len(sys.argv) != 2:
        print("Usage: python step2_analyze_pii.py <extracted_text_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = "output/step2/pii_results.json"

    print(f"Reading text from {input_file} and analyzing for PII...")

    # Read the extracted text file
    text = read_text_file(input_file)

    # Analyze for PII
    pii_data = analyze_text_for_pii(text)

    # Save results to file
    save_pii_to_file(pii_data, output_file)

    print(f"PII results saved to {output_file}")


if __name__ == "__main__":
    main()
