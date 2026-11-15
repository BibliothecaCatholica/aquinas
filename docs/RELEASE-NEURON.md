# Aquinas Neuron (experimental), v0.2.0-alpha.3

## What changed since v0.2.0-alpha.2

- The model files are the same: both GGUF files are re-attached from v0.2.0-alpha.2 with unchanged checksums.
- Retrieval fixes in the tool: article titles are indexed and weighted, common question words are ignored, and results
  are ranked by article (`results/retrieval/`).
- The one-line install command now fetches `install_ollama.sh` from this release tag instead of `main`, so the script,
  the model files, and the tool it clones (`--with-tool`) always come from the same release.

**Experimental alpha. Answer quality has not been reviewed. Not a teaching authority and not a demonstrated improvement
over the base model. Check the primary text.** The model alone has no access to the Summa; use it through the Aquinas
tool (`--mode rag`) for answers grounded in the text.

The Aquinas Neuron is LiquidAI/LFM3-1.7B (revision `1da06bec6a819da10b54c67e5c90972b46d81871`) with Bibliotheca
Catholica's `source-pilot-v21` adapter merged into its weights, quantized for Ollama and llama.cpp. Thinking is off in
the embedded chat template, so `ollama run aquinas-neuron` answers directly.

## Files

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `aquinas-neuron-Q4_K_M.gguf` (default) | 1,099,627,008 | `76749668eda353685ff3563202172092af4bebe45ee817e40e01133e94a7a164` |
| `aquinas-neuron-Q8_0.gguf` (higher quality) | 1,846,237,696 | `f59ecf6f7043bead9f0e4908fa985c3bc277390bc168e538e56771e4cc3011fe` |
| `Modelfile` | text | the tool's system prompt and sampling settings |
| `SHA256SUMS` | text | checksums of the attachments |
| `LICENSE-LFM-Open-License-v1.0.txt` | text | the base model's licence |
| `NOTICE` | text | base model, revision, and the changes made |

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/BibliothecaCatholica/aquinas/v0.2.0-alpha.3/scripts/install_ollama.sh | bash
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

The GGUF files were built for v0.2.0-alpha.2 from the repository's `scripts/build_gguf.sh` by the release workflow,
which refused to publish unless the checksums matched the ones above; the v0.2.0-alpha.3 workflow downloads them from
that release and again refuses to publish unless they match. The Q8_0 file is bit-identical to the one tested in development; Q4_K_M
quantization differs slightly between CPU types, so the Q4_K_M file was tested again after publication. Licence: LFM Open License v1.0; see `NOTICE`.
