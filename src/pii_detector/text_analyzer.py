from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerRegistry
import spacy
import torch
import os

# Worker globals
_nlp = None
_analyzer = None
_initialized = False
_worker_id = None


def init_on_gpu(gpu_id):
    """Initialize on specific GPU."""
    global _nlp, _analyzer, _initialized, _worker_id

    if _initialized:
        return

    _worker_id = gpu_id
    torch.cuda.set_device(gpu_id)
    _nlp = spacy.load("en_core_web_trf")

    cc_pattern = Pattern(name="credit_card", regex=r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", score=0.9)
    phone_pattern = Pattern(name="phone", regex=r"\b\d{3}[-.]?\d{4}\b", score=0.8)

    cc_recognizer = PatternRecognizer(supported_entity="CREDIT_CARD", patterns=[cc_pattern])
    phone_recognizer = PatternRecognizer(supported_entity="PHONE_NUMBER", patterns=[phone_pattern])

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers()
    registry.recognizers = [r for r in registry.recognizers if r.name not in ["DateTimeRecognizer", "UrlRecognizer"]]

    _analyzer = AnalyzerEngine(registry=registry)
    _analyzer.registry.add_recognizer(cc_recognizer)
    _analyzer.registry.add_recognizer(phone_recognizer)

    _initialized = True
    print(f"Worker initialized on GPU {gpu_id}")


def analyze_text(args):
    """Analyze text. args = (page_num, text, gpu_id)."""
    page_num, text, gpu_id = args

    # Initialize on first call
    init_on_gpu(gpu_id)

    # Progress log every 10 pages
    if page_num % 10 == 0:
        print(f"  GPU {gpu_id} processing page {page_num}")

    if not text or len(text.strip()) == 0:
        return {"page_number": page_num, "detections": []}

    detections = []

    # Presidio
    for r in _analyzer.analyze(text=text, language="en"):
        detections.append({
            "type": r.entity_type,
            "text": text[r.start:r.end],
            "start": r.start,
            "end": r.end,
            "score": round(r.score, 3),
            "source": "presidio"
        })

    # spaCy NER
    doc = _nlp(text[:50000])
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

    # Deduplicate
    seen = {}
    for d in detections:
        key = (d["start"], d["end"])
        if key not in seen or d["score"] > seen[key]["score"]:
            seen[key] = d

    return {"page_number": page_num, "detections": list(seen.values())}