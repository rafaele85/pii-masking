import sys
import json
import os
from langdetect import detect
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

configuration = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "en", "model_name": "en_core_web_trf"},
        {"lang_code": "bg", "model_name": "bg_news_trf"},
        {"lang_code": "ru", "model_name": "ru_core_news_lg"},
    ],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

analyzer = AnalyzerEngine(
    nlp_engine=nlp_engine,
    supported_languages=["en", "bg", "ru"]
)

ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IBAN_CODE", "IP_ADDRESS"]


def analyze_with_presidio(text, language):
    lang = language if language in ["en", "de", "es", "fr", "it"] else "en"
    results = analyzer.analyze(text=text, language=lang, entities=ENTITIES, score_threshold=0.7)
    return [{"value": text[r.start:r.end], "type": r.entity_type, "score": r.score} for r in results]



def read_json_file(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_language(pages):
    for page in pages:
        text = page["content"].strip()
        if len(text) > 50:
            lang = detect(text)
            print(f"Detected language '{lang}' from page {page['page_number']}")
            return lang
    print("Error: No pages with sufficient text")
    sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print("Usage: python step2_analyze_pii.py <extracted_text.json> <output_dir>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    pages = read_json_file(input_file)
    language = detect_language(pages)
    print(f"Language: {language}")

    for page in pages:
        candidates = analyze_with_presidio(page["content"], language)
        print(f"Page {page['page_number']}: {len(candidates)} candidates")
        for c in candidates:
            print(f"  {c['type']}: {c['value']} ({c['score']})")


if __name__ == "__main__":
    main()