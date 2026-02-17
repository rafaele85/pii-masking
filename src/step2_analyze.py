import json
import sys
from pathlib import Path
from pii_detector.text_analyzer import analyze_single_text
from concurrent.futures import ProcessPoolExecutor
import multiprocessing


def analyze_page(page_data: dict) -> dict:
    """Analyze a single page (for multiprocessing)."""
    page_num, text = page_data
    detections = analyze_single_text(text) if text.strip() else []
    return {
        "page_number": page_num,
        "detections": detections
    }


def analyze_extracted_text(step1_file: Path, output_dir: Path) -> Path:
    """Step 2: Analyze extracted text for PII using multiprocessing."""
    with open(step1_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Prepare page data for parallel processing
    pages_data = [(p["page_number"], p["text"]) for p in data["pages"]]

    # Use multiprocessing - one process per CPU core
    cpu_count = max(1, multiprocessing.cpu_count() - 1)  # Leave one core free
    print(f"Processing {len(pages_data)} pages using {cpu_count} workers...")

    with ProcessPoolExecutor(max_workers=cpu_count) as executor:
        results = list(executor.map(analyze_page, pages_data))

    # Sort by page number and update data
    results.sort(key=lambda x: x["page_number"])
    for i, page in enumerate(data["pages"]):
        page["detections"] = results[i]["detections"]
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