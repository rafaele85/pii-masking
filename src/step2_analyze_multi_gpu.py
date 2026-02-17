import json
import sys
from pathlib import Path
from multiprocessing import Pool, set_start_method


# Import after setting CUDA visible devices in main
from pii_detector.text_analyzer import init_worker, analyze_text_worker


def analyze_extracted_text_multi_gpu(step1_file: Path, output_dir: Path, num_gpus: int = 3) -> Path:
    """Step 2: Analyze extracted text using multiple GPUs."""
    with open(step1_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    pages_data = [(p["page_number"], p["text"]) for p in data["pages"]]
    total_pages = len(pages_data)

    print(f"Processing {total_pages} pages across {num_gpus} GPUs...")

    # Create pool with one worker per GPU
    # Each worker gets assigned to a specific GPU
    gpu_ids = list(range(num_gpus))

    # Use spawn to avoid CUDA fork issues
    set_start_method("spawn", force=True)

    with Pool(processes=num_gpus, initializer=init_worker, initargs=(0,)) as pool:
        # Map pages to GPUs round-robin
        results = pool.map(analyze_text_worker, pages_data)

    # Update data with results
    for page, result in zip(data["pages"], results):
        page["detections"] = result["detections"]
        del page["text"]

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{step1_file.stem.replace('_text', '')}_detections.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return output_file


if __name__ == "__main__":
    if len(sys.argv) > 1:
        step1_file = Path(sys.argv[1])
        step2_file = analyze_extracted_text_multi_gpu(step1_file, Path("output/step2"), num_gpus=3)
        print(f"Step 2 saved: {step2_file}")
    else:
        print("Usage: python step2_analyze_multi_gpu.py <step1_json_path>")