# Merged GGUF paired run (November 15, 2026)

`paired-20-adapter-vs-merged-q4.jsonl`: the first 20 items of `data/evaluation/holdout.jsonl` (development questions,
already used during development; not a sealed benchmark). Each line holds the question and both responses with time and
word count: the unmerged adapter (Transformers 5.20.2, CPU, float32) and the merged Q4_K_M model in Ollama 0.40.16. Both
received the identical request built by `aquinas.adapter.build_messages(..., rag=True)`. Not scored, not reviewed; no
answer-quality claim. Summary: models/aquinas-neuron/README.md (an earlier build of the same weights).
