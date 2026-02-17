from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerRegistry
import spacy

nlp = spacy.load("en_core_web_trf")

cc_pattern = Pattern(name="credit_card", regex=r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", score=0.9)
phone_pattern = Pattern(name="phone", regex=r"\b\d{3}[-.]?\d{4}\b", score=0.8)

cc_recognizer = PatternRecognizer(supported_entity="CREDIT_CARD", patterns=[cc_pattern])
phone_recognizer = PatternRecognizer(supported_entity="PHONE_NUMBER", patterns=[phone_pattern])

registry = RecognizerRegistry()
registry.load_predefined_recognizers()
registry.recognizers = [r for r in registry.recognizers if r.name not in ["DateTimeRecognizer", "UrlRecognizer"]]

analyzer = AnalyzerEngine(registry=registry)
analyzer.registry.add_recognizer(cc_recognizer)
analyzer.registry.add_recognizer(phone_recognizer)


def analyze_text(text: str) -> list:
    detections = []

    # Presidio
    for r in analyzer.analyze(text=text, language="en"):
        detections.append({
            "type": r.entity_type,
            "text": text[r.start:r.end],
            "start": r.start,
            "end": r.end,
            "score": round(r.score, 3),
            "source": "presidio"
        })

    # spaCy NER
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "LOC"]:
            detections.append({
                "type": ent.label_,
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "score": 0.85,
                "source": "spacy"
            })

    # Deduplicate: keep highest score per position
    seen = {}  # key: (start, end) -> detection
    for d in detections:
        key = (d["start"], d["end"])
        if key not in seen or d["score"] > seen[key]["score"]:
            seen[key] = d

    return list(seen.values())


# Test
text = "John Smith from Microsoft visited London. Contact him at john.smith@email.com or 555-1234. CC: 4532-1234-5678-9012"
results = analyze_text(text)
for r in results:
    print(f"{r['type']}: {r['text']} (score: {r['score']}, source: {r['source']})")