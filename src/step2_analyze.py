import json
import sys
from pathlib import Path
from pii_detector.text_analyzer import analyze_text


def analyze_extracted_text(step1_file: Path, output_dir: Path) -> Path:
    """Step 2: Analyze extracted text for PII and save to output/step2/."""
    with open(step1_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for page in data["pages"]:
        page["detections"] = analyze_text(page["text"]) if page["text"].strip() else []
        del page["text"]

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{step1_file.stem.replace('_text', '')}_detections.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return output_file


if __name__ == "__main__":
    if len(sys.argv) > 1:
        step1_file = Path(sys.argv[1])
        step2_file = analyze_extracted_text(step1_file, Path("output/step2"))
        print(f"Step 2 saved: {step2_file}")
    else:
        print("Usage: python step2_analyze.py <step1_json_path>")