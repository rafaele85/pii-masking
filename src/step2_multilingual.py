import sys
import json
import os
import logging
from concurrent.futures import ProcessPoolExecutor
from langdetect import detect
from presidio_analyzer import AnalyzerEngine
import spacy

# Initialize Presidio analyzer
analyzer = AnalyzerEngine()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[
    logging.FileHandler("language_detection.log"),
    logging.StreamHandler()
])

# Increase spaCy max_length to handle larger texts
spacy.util.fix_random_seed(42)


def load_spacy_model(language):
    """Load appropriate spaCy model based on the detected language."""
    if language == 'en':
        return spacy.load("en_core_web_trf")
    elif language == 'bg':
        return spacy.load("bg_news_trf")
    elif language == 'ru':
        return spacy.load("ru_core_news_lg")
    else:
        raise ValueError(f"Unsupported language: {language}")


def analyze_text_for_pii(text, nlp_model):
    """Analyze text for PII using Presidio and spaCy."""
    results = analyzer.analyze(text=text, language="en")
    pii_data = []
    for res in results:
        pii_data.append({
            "text_row_number": res.start,
            "column_number": res.end,
            "pii_type": res.entity_type,
            "value": text[res.start:res.end]
        })
    return pii_data


def analyze_page_for_pii(page_data):
    """Analyze a single page's text for PII, auto-detect language."""
    page_text = page_data['content']

    # Auto-detect language using langdetect
    language = detect(page_text)

    # Log the detected language
    logging.info(f"Detected language for page {page_data['page_number']}: {language}")

    # Load appropriate spaCy model based on the detected language
    nlp_model = load_spacy_model(language)

    # Run PII analysis
    return analyze_text_for_pii(page_text, nlp_model)


def read_json_file(input_file):
    """Read the JSON file containing extracted text."""
    with open(input_file, "r", encoding="utf-8") as file:
        return json.load(file)


def save_pii_to_file(pii_data, output_file):
    """Save PII analysis results to a file."""
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(pii_data, file, ensure_ascii=False, indent=4)


def process_page(page_data, output_dir):
    """Process each page, analyze for PII, and save to a separate file."""
    page_number = page_data["page_number"]
    pii_data = analyze_page_for_pii(page_data)

    # Create a separate JSON file for each page's results
    output_file = os.path.join(output_dir, f"page_{page_number}_pii.json")
    save_pii_to_file(pii_data, output_file)

    return output_file


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

    # Use ProcessPoolExecutor for parallel processing
    with ProcessPoolExecutor() as executor:
        # Process each page concurrently
        futures = [executor.submit(process_page, page_data, output_dir) for page_data in pages]
        result_files = [future.result() for future in futures]

    # After processing all pages, merge the results into one file
    merge_json_files(result_files, final_output_file)

    print(f"PII analysis results saved to {final_output_file}")


if __name__ == "__main__":
    main()
