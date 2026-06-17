# RAGAS Benchmark Instructions

These steps run the SEP RAG system on the Vectara Open RAG Benchmark with
Ollama and RAGAS.

## 1. Setup

From the `code/` directory:

```bash
python3 --version  # must be 3.10 or newer
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Verify imports:

```bash
python -c "import ragas, datasets, sentence_transformers; print('ok')"
```

## 2. Download Benchmark

Start with a smaller subset to verify everything works:

```bash
python scripts/download_benchmark.py --subset 50
```

Check how much data was prepared before starting a long run:

```bash
find datasets/open_rag_bench/prepared/corpus -type f | wc -l
wc -l datasets/open_rag_bench/prepared/qa.jsonl
```

For the full benchmark:

```bash
python scripts/download_benchmark.py --subset all
```

This prepares files under:

```text
datasets/open_rag_bench/prepared/
```

## 3. Quick Loader Check

Before running RAGAS, check that the full suite loads:

```bash
python -m eval.run \
  --suite full \
  --config configs/ci-smoke.yaml \
  --tag loader-check
```

This creates a normal eval report under:

```text
reports/runs/<timestamp>_full/
```

## 4. Start Ollama

Install Ollama if needed:

```text
https://ollama.com/download
```

Pull the required models:

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

Start Ollama:

```bash
ollama serve
```

Keep this terminal open.

## 5. Run RAGAS

Open a second terminal, go to `code/`, and activate the environment:

```bash
source .venv/bin/activate
```

Set Ollama variables:

```bash
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=llama3.1:8b
```

Run RAGAS:

```bash
python -m eval.ragas_run \
  --suite full \
  --config configs/ollama-full.yaml \
  --judge-model llama3.1:8b \
  --embedding-model nomic-embed-text \
  --batch-size 1 \
  --tag full-open-ragbench-ollama
```

## 6. Send Back Results

Please send back the generated folder:

```text
reports/ragas/<timestamp>_full/
```

It should contain:

```text
ragas_report.json
ragas_scores.csv
ragas_inputs.jsonl
```

If the full benchmark is too slow, rerun with:

```bash
python scripts/download_benchmark.py --subset 50
```

Then run the same RAGAS command again.
