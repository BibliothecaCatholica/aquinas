# Aquinas Neuron (experimental), v0.2.0-alpha.2

**Experimental alpha. Answer quality has not been reviewed. Not a teaching authority and not a demonstrated improvement
over the base model. Check the primary text.** The model alone has no access to the Summa; use it through the Aquinas
tool (`--mode rag`) for answers grounded in the text.

The Aquinas Neuron is LiquidAI/LFM3-1.7B (revision `1da06bec6a819da10b54c67e5c90972b46d81871`) with Bibliotheca
Catholica's `source-pilot-v21` adapter merged into its weights, quantized for Ollama and llama.cpp. Thinking is off in
the embedded chat template, so `ollama run aquinas-neuron` answers directly.

## Files

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `aquinas-neuron-Q4_K_M.gguf` (default) | 1,099,627,008 | `030bd4086674da99974a6e73c9a7388c050d7beb658bf471268a9e8e0c391c45` |
| `aquinas-neuron-Q8_0.gguf` (higher quality) | 1,846,237,696 | `f59ecf6f7043bead9f0e4908fa985c3bc277390bc168e538e56771e4cc3011fe` |
| `Modelfile` | text | the tool's system prompt and sampling settings |
| `SHA256SUMS` | text | checksums of the attachments |
| `LICENSE-LFM-Open-License-v1.0.txt` | text | the base model's licence |
| `NOTICE` | text | base model, revision, and the changes made |

## Install

```bash
bash scripts/install_ollama.sh     # from a clone of the repository; --q8 for the Q8_0 file
ollama run aquinas-neuron
python -m aquinas.cli ask 'When does an unjust law bind in conscience?' --model aquinas-neuron --mode rag
```

Manual steps for Windows and macOS are in the README.

## Honest status

- Both files load and answer in Ollama 0.40.16 and llama.cpp on CPU (`results/aquinas-neuron-test/`).
- Paired comparison on 20 development questions, same request to the unmerged adapter and the merged Q4_K_M
  (`results/gguf-experimental/`): median answer length 26.5 and 32 words; the same set of articles cited in 10 of 20.
  Observation from review: with retrieval on, 8 of 20 unmerged and 7 of 20 merged answers cited the article the question
  is keyed to. No answer has been scored.
- Not run: GPU inference, a sealed or fresh evaluation, independent scholarly review.

The files were built from the repository's `scripts/build_gguf.sh` by the release workflow, which refuses to publish
unless the checksums match the ones above. Licence: LFM Open License v1.0; see `NOTICE`.
