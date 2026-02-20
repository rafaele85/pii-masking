import sys
import json
import os

import requests
from langdetect import detect
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

configuration = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "en", "model_name": "en_core_web_sm"},
        {"lang_code": "bg", "model_name": "bg_news_trf"},
        {"lang_code": "ru", "model_name": "ru_core_news_sm"},
    ],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()


ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IBAN_CODE", "IP_ADDRESS"]


def analyze_with_presidio(text, analyzer, language):
    lang = language if language in ["en", "de", "es", "fr", "it", "ru", "bg"] else "en"
    print(f"  Presidio language: {lang}")
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

def load_system_prompt():
    with open("prompts/system-prompt.txt", "r", encoding="utf-8") as f:
        return f.read()

def call_ollama(page_text, system_prompt, model="qwen3:14b-no-think"):
    user_prompt = f"Text:\n{page_text} Scan the text for any PII."

    response = requests.post("http://localhost:11434/api/chat", json={
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }, timeout=100)
    result = response.json()
    print(f"  LLM response: {result}")
    if "message" not in result:
        print(f"  Ollama error: {result}")
        return "[]"
    return result["message"]["content"]


def create_analyzer(language):
    models = {
        "en": "en_core_web_lg",
        "bg": "bg_news_trf",
        "ru": "ru_core_news_lg",
    }

    model_list = [{"lang_code": "en", "model_name": "en_core_web_lg"}]
    if language != "en" and language in models:
        model_list.append({"lang_code": language, "model_name": models[language]})

    configuration = {
        "nlp_engine_name": "spacy",
        "models": model_list,
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()

    supported = ["en"]
    if language != "en":
        supported.append(language)

    return AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=supported)

def main():
    if len(sys.argv) != 3:
        print("Usage: python step2_analyze_pii.py <extracted_text.json> <output_dir>")
        sys.exit(1)

    system_prompt = load_system_prompt()

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    pages = read_json_file(input_file)
    language = detect_language(pages)
    print(f"Language: {language}")

    output_file = sys.argv[2]
    with open(output_file, "w", encoding="utf-8") as f:
        for page in pages:
            text = page["content"].strip()
            if len(text) < 2:
                print(f"Page {page['page_number']}: empty, skipping")
                continue

            llm_response = call_ollama(text, system_prompt)
            print(f"  LLM response: {llm_response[:100]}...")

            try:
                page_pii = json.loads(llm_response)
            except json.JSONDecodeError:
                print(f"  Warning: failed to parse LLM response")
                page_pii = []

            result = {"page_number": page["page_number"], "pii_found": page_pii}
            f.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            f.flush()

    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()