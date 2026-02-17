from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerRegistry
import spacy
import torch

# Global variables set per process
nlp = None
analyzer = None
device_id = None


def init_worker(gpu_id):
    """Initialize worker with specific GPU."""
    global nlp, analyzer, device_id
    device_id = gpu_id

    # Set CUDA device for this process
    torch.cuda.set_device(gpu_id)

    # Load spaCy model on this GPU
    nlp = spacy.load("en_core_web_trf")

    # Initialize Presidio
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

    print(f"Worker initialized on GPU {gpu_id}")


def analyze_text_worker(args):
    """Analyze text on assigned GPU."""
    page_num, text = args
    if not text or len(text.strip()) == 0:
        return {"page_number": page_num, "detections": []}

    detections = []

    # Presidio (CPU)
    for r in analyzer.analyze(text=text, language="en"):
        detections.append({
            "type": r.entity_type,
            "text": text[r.start:r.end],
            "start": r.start,
            "end": r.end,
            "score": round(r.score, 3),
            "source": "presidio"
        })

    # spaCy NER (GPU)
    doc = nlp(text[:50000])
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