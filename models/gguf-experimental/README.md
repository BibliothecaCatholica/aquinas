# Aquinas experimental merged model (GGUF): model card

**Experimental, unpromoted, answer quality not reviewed.** This is LiquidAI/LFM3-1.7B (revision
`1da06bec6a819da10b54c67e5c90972b46d81871`) with the `source-pilot-v21` LoRA adapter merged into its weights, converted
to GGUF for llama.cpp and Ollama. It is not an improvement over the base model, not a teaching authority, and not
reviewed for accuracy. Check every answer against the primary text.

## Files (built November 15, 2026; not published)

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `aquinas-experimental-Q4_K_M.gguf` | 1,099,627,040 | `3bbe907b286aa1788148cca1045a904975bc7c324b816d3db4708159086d45c2` |
| `aquinas-experimental-Q8_0.gguf` | 1,846,237,728 | `1994779b37a3d72ba936cbe6868bfd5d9153b547b4d752608111dfdb5589676b` |
| `Modelfile` (this folder) | text | uses the tool's existing system prompt (`aquinas/runtime.py` `SYSTEM`) |

Rebuild them with `bash scripts/build_gguf.sh` (merge with `scripts/merge_adapter.py`, convert with llama.cpp at commit
`e574a17b062be51b98e239ccd3d3743e3d902333`, quantize). The files above are not committed and have not been uploaded
anywhere; creating a Hugging Face page or a release is the owner's decision.

## Retrieval lives in the Python tool

The model alone has no access to the Summa. Retrieved evidence comes from the Aquinas tool, which sends it with the
question. With the tag created (`ollama create aquinas-experimental:q4_k_m -f Modelfile`, which adds one new tag and
changes no existing model):

```bash
python -m aquinas.cli ask 'When does an unjust law bind in conscience?' --model aquinas-experimental:q4_k_m --mode rag
```

The CLI turns thinking off. `ollama run` directly shows the chat template's thinking section first, because the
upstream template enables thinking by default.

## What was tested

- Merge, GGUF conversion, and Q4_K_M/Q8_0 quantization: completed on CPU.
- llama.cpp (`llama-completion`): the Q4_K_M file loads and generates.
- Ollama 0.40.16: `ollama create` from the Q4_K_M file and a chat request both work; the CLI command above answered.
- Adapter-only route (base GGUF plus a GGUF LoRA with `ADAPTER` in the Modelfile): the LoRA converts (16 MB, 284
  tensors) and llama.cpp applies it with `--lora`, but **Ollama 0.40.16 refuses it**: "LoRA adapters are no longer
  supported". A merged file is therefore the only Ollama route that worked.
- Paired comparison on 20 development questions (`results/gguf-experimental/`): the same request (system prompt,
  complete respondeo evidence, question; temperature 0.35, seed 11) went to the unmerged adapter in Transformers on CPU
  and to the merged Q4_K_M in Ollama. Median answer length 26.5 words (unmerged) and 32 words (merged); median time 18.4 s
  and 7.8 s on a 4-core CPU; the two cite the same set of ST articles in 10 of 20 answers. Sampling and quantization
  both differ, so the outputs are not expected to match. **No answer has been scored or reviewed**; this shows the files
  run, not that they are correct.

## Licence (LFM Open License v1.0)

The merged weights are a Derivative Work of LiquidAI/LFM3-1.7B. The bundled `models/source-pilot-v21/LICENSE` is
byte-identical to the licence at the pinned revision (SHA-256 `4d28ca14dedc0b3d0fcc2b3339f0e79931faa33874f3d24f522183a8fc70068c`);
the base repository has no NOTICE file. Redistributing these files requires, under section 4:

- a copy of the LFM Open License v1.0 with them;
- a prominent notice that the files were changed (merged with the Aquinas adapter and quantized; this card serves);
- the retained copyright, trademark, and attribution notices of the source form;
- the commercial-use threshold of section 5 ($10 million annual revenue) applies to the recipient's use.
