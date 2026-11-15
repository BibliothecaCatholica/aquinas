# Aquinas 0.1.2 — citation rendering and grounding diagnostic

The 450-response Bazzite run completed but is not a model-promotion result. It includes 61/150 length-limited baseline answers, 5/150 prompt answers, and 1/150 RAG answer. Keyed articles appear in 27/50 actual supplied RAG contexts; the three priority law cases all lack q.96 a.4. A close, provisional assistant review of 41 responses identifies both retrieval and source-interpretation failures. No full-suite scholarly accuracy score is established.

This update removes parser offsets from model-facing citation headers, retaining only canonical article IDs and the complete-respondeo label. Internal IDs remain in saved metadata. Runtime generation accepts an explicit diagnostic context override and generation allowance; default production modes and their 768-token allowance remain unchanged. All generated artifacts record pipeline 0.1.2.

`scripts.grounding_diagnostic` compares normal retrieval with an explicitly oracle-assisted keyed-source condition. It uses only source IDs from the answer-key dataset, not answer text, for the oracle arm. It must not be represented as blind evaluation or deployed retrieval quality. Three existing scenarios × three seeds × two arms yield 18 responses with identical 1536-token budgets. This diagnoses source selection versus interpretation; it does not improve source discovery or prove a trained model is reliable. New generation has not been executed in the development environment.

Run from the project directory with the active existing venv:

```bash
python -m scripts.grounding_diagnostic --out results/grounding-012-v1.jsonl
```

The command prints progress after each answer, saves raw responses and a model/control manifest, and refuses to overwrite a result file. On failure, retain the error record; do not treat it as a philosophical failure. No model, primary source, training record or prior experiment is changed by this diagnostic.

The RTX 3070 / 8 GB VRAM and approximately 47 GiB RAM support investigating a short-sequence rank-8 BF16 LoRA pilot. Full-checkpoint training compatibility and peak memory remain to be measured. Read the training guide and check the hardware-compatible torch installation before that separate experiment. No trained candidate is promoted.
