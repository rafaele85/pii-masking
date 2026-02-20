# PII Detection POC — Setup Guide (Windows 11)

## 1. Python 3.11

1. Download Python 3.11 from https://www.python.org/downloads/release/python-3110/
2. Run the installer — **check "Add Python to PATH"**
3. Verify:
   ```
   python --version
   ```

## 2. CUDA Toolkit

1. Download CUDA 12.4 from https://developer.nvidia.com/cuda-12-4-0-download-archive
2. Select: Windows > x86_64 > 11 > exe (local)
3. Run installer with default settings
4. Verify:
   ```
   nvcc --version
   ```

## 3. PyTorch with CUDA

```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

Verify GPU access:
```
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.device_count())"
```
Expected: `True` and `3`

## 4. Core Python Packages

```
pip install pymupdf spacy presidio-analyzer presidio-anonymizer langdetect requests
```

## 5. spaCy Models

```
python -m spacy download en_core_web_trf
python -m spacy download ru_core_news_lg
```

For Bulgarian (`bg_news_trf`), check availability:
```
pip install https://huggingface.co/spacy/bg_news_trf/resolve/main/bg_news_trf-any-py3-none-any.whl
```

If that URL doesn't work, search for the latest version at https://huggingface.co/spacy/bg_news_trf

## 6. Ollama

1. Download from https://ollama.com/download/windows
2. Run the installer
3. Verify:
   ```
   ollama --version
   ```

### Pull the model

```
ollama pull qwen3:14b
```

### Create no-think variant

Create a file called `Modelfile` with this content:

```
FROM qwen3:14b
PARAMETER num_ctx 8192
TEMPLATE """{{- range .Messages }}<|im_start|>{{ .Role }}
{{ .Content }}<|im_end|>
{{ end }}<|im_start|>assistant
<think>
</think>
"""
```

Then run:
```
ollama create qwen3:14b-no-think -f Modelfile
```

Verify:
```
ollama run qwen3:14b-no-think "Reply with just the word OK"
```

## 7. Project Structure

```
pii-poc/
├── step1_extract_text.py      # PDF text extraction (PyMuPDF)
├── step2_analyze_pii.py       # PII detection (Presidio + spaCy + Ollama)
├── input/                     # Place test PDFs here
├── output/
│   ├── step1/                 # Extracted text JSON files
│   └── step2/                 # PII analysis results
└── Modelfile                  # Ollama model config
```

## 8. Verification Checklist

| Component | Command | Expected |
|-----------|---------|----------|
| Python | `python --version` | 3.11.x |
| CUDA | `nvcc --version` | 12.4 |
| PyTorch GPU | `python -c "import torch; print(torch.cuda.is_available())"` | True |
| PyMuPDF | `python -c "import fitz; print(fitz.version)"` | No error |
| spaCy EN | `python -c "import spacy; spacy.load('en_core_web_trf')"` | No error |
| spaCy RU | `python -c "import spacy; spacy.load('ru_core_news_lg')"` | No error |
| spaCy BG | `python -c "import spacy; spacy.load('bg_news_trf')"` | No error |
| Presidio | `python -c "from presidio_analyzer import AnalyzerEngine"` | No error |
| Ollama | `ollama run qwen3:14b-no-think "say OK"` | OK |

