# Aquinas Neuron (experimental): model card

**Experimental alpha. Answer quality has not been reviewed. Not a teaching authority and not a demonstrated improvement
over the base model. Check every answer against the primary text.** The model alone has no access to the Summa: it
answers from its weights. For answers grounded in the text, use it through the Aquinas tool (`--mode rag`), which
retrieves the relevant articles and sends them with the question.

## What it is

LiquidAI/LFM3-1.7B (revision `1da06bec6a819da10b54c67e5c90972b46d81871`) with Bibliotheca Catholica's `source-pilot-v21`
LoRA adapter merged into its weights, converted to GGUF, and quantized. The adapter was trained on 40 source-conditioned
examples (3 epochs, 30 optimizer updates); see [the adapter card](../source-pilot-v21/README.md) and
[status](../../docs/STATUS.md). One line of the embedded chat template is changed so that thinking is off, which lets a
plain `ollama run` answer without a thinking section. Built by `scripts/build_gguf.sh`.

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `aquinas-neuron-Q4_K_M.gguf` (default) | 1,099,627,008 | `030bd4086674da99974a6e73c9a7388c050d7beb658bf471268a9e8e0c391c45` |
| `aquinas-neuron-Q8_0.gguf` (higher quality) | 1,846,237,696 | `f59ecf6f7043bead9f0e4908fa985c3bc277390bc168e538e56771e4cc3011fe` |
| `Modelfile` | text | the tool's existing system prompt and sampling settings |

These replace the checksums of the first build of November 15 (`3bbe907b…` and `1994779b…`, upstream template with
thinking on, PEFT merge). The release build uses `scripts/merge_adapter.py --exact` (the rank-8 update summed in float64,
rounded once to float32; it matches the PEFT merge to within one float32 rounding step) and a portable llama.cpp build,
so the same bytes come out on any x86-64 machine; the release workflow refuses to publish unless they match.

## Use

```bash
bash scripts/install_ollama.sh          # downloads and verifies the Q4_K_M file, then: ollama create aquinas-neuron
ollama run aquinas-neuron               # the model alone (no access to the Summa)
python -m aquinas.cli ask 'When does an unjust law bind in conscience?' --model aquinas-neuron --mode rag
```

## What was tested (November 15, 2026, 4-core CPU, no GPU)

- Both files load in Ollama 0.40.16 and in llama.cpp. The README question was answered with plain `ollama run`
  (no retrieval, no thinking section) and through the tool with `--mode rag`, for each file.
- Paired comparison on 20 development questions (`results/gguf-experimental/`): the identical request (system prompt,
  complete respondeo evidence, question; temperature 0.35, seed 11) went to the unmerged adapter in Transformers on CPU
  and to the merged Q4_K_M in Ollama (thinking off through the API). Median answer length 26.5 and 32 words; median time
  18.4 s and 7.8 s; the same set of ST articles cited in 10 of 20 answers. Observation from review: with retrieval on,
  8 of 20 unmerged and 7 of 20 merged answers cited the article the question is keyed to. Sampling and quantization
  both differ, so outputs are not expected to match. No answer has been scored; this shows that the files run and
  behave broadly like the unmerged adapter, not that they are correct.
- Not run: GPU inference, any machine other than this cloud container, any sealed or fresh evaluation.

## Licence

LFM Open License v1.0 (the bundled copy is byte-identical to the licence at the pinned revision). The files are a
Derivative Work: see `NOTICE` for the base model, revision, and the changes made. Redistribution requires the licence
copy, the change notice, and the retained upstream notices; the commercial-use conditions of section 5 apply.
