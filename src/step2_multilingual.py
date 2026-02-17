import sys
import json
import os
import spacy
from langdetect import detect
from presidio_analyzer import AnalyzerEngine
from concurrent.futures import ThreadPoolExecutor

# Initialize Presidio analyzer
analyzer = AnalyzerEngine()

# Increase spaCy max_length to handle larger texts
spacy.util.fix_random_seed(42)


def load_spacy_model(language):
    """Load spaCy model based on the detected language."""
    if language == 'en':
        return spacy.load("en_core_web_trf")
    elif language == 'bg':
        return spacy.load("bg_news_trf")
    elif language == 'ru':
        return spacy.load("ru_core_news_lg")
    else:
        raise ValueError(f"Unsupported language: {language}")


def analyze_text_for_pii(text, nlp_model):
    """Analyze text for PII using Presidio."""
    results = analyzer.analyze(text=text, language="en")
    pii_data = [{"text_row_number": res.start, "column_number": res.end, "pii_type": res.entity_type,
                 "value": text[res.start:res.end]} for res in results]
    return pii_data


def process_page(page_data, nlp_model, output_dir):
    """Process each page, analyze for PII, and save to a separate file."""
    page_number = page_data["page_number"]
    page_text = page_data['content']

    # PII analysis
    pii_data = analyze_text_for_pii(page_text, nlp_model)

    # Save the PII results to a file
    output_file = f"{output_dir}/page_{page_number}_pii.json"
    save_pii_to_file(pii_data, output_file)

    return output_file


def read_json_file(input_file):
    """Read the JSON file containing extracted text."""
    with open(input_file, "r", encoding="utf-8") as file:
        return json.load(file)


def save_pii_to_file(pii_data, output_file):
    """Save PII analysis results to a file."""
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(pii_data, file, ensure_ascii=False, indent=4)


def merge_json_files(file_paths, output_file):
    """Merge multiple JSON files into a single JSON file."""
    merged_data = []
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as file:
            merged_data.extend(json.load(file))

    with open(output_file, "w", encoding="utf-8") as output_file:
        json.dump(merged_data, output_file, ensure_ascii=False, indent=4)


def main():
    if len(sys.argv) != 4:
        print("Usage: python step2_analyze_pii.py <extracted_text_file> <output_dir> <final_output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    final_output_file = sys.argv[3]

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Read the extracted text JSON file
    pages = read_json_file(input_file)

    # Detect language from the first page's text (in the main thread)
    first_page_text = pages[0]['content']
    sys.stdout.flush()

    detected_language = None
    for page in pages:
        text = page['content'].strip()
        if len(text) > 50:
            detected_language = detect(text)
            print(f"Detected language '{detected_language}' from page {page['page_number']}")
            break

    if not detected_language:
        print("Error: No pages with sufficient text found")
        sys.exit(1)
    # Print detected language (before parallel processing starts)
    print(f"Detected language for the document: {detected_language}")
    sys.stdout.flush()  # Ensure the print statement is flushed immediately to the console

    # Load spaCy model based on detected language
    try:
        nlp_model = load_spacy_model(detected_language)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Use ThreadPoolExecutor for parallel processing of pages
    with ThreadPoolExecutor() as executor:
        # Process each page concurrently
        futures = [executor.submit(process_page, page_data, nlp_model, output_dir) for page_data in pages]
        result_files = [future.result() for future in futures]

    # After processing all pages, merge the results into one file
    merge_json_files(result_files, final_output_file)

    print(f"PII analysis results saved to {final_output_file}")


if __name__ == "__main__":
    main()
