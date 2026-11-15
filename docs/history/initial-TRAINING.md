# Training, export, and reproducibility

The original trainable checkpoint is LiquidAI/LFM3-1.7B, pinned in research/model-revision.json. It is a custom tri-hybrid model, not an ordinary Llama checkpoint. Upstream describes 1.73B parameters and provides a supervised fine-tuning notebook. Its notebook uses LoRA on q_proj, k_proj, v_proj, o_proj, in_proj, out_proj, w1, w2, w3. The implementation uses these explicit targets, verifies their existence, and performs assistant-only next-token supervision through PyTorch and PEFT. It does not change convolution parameters directly.

Official sources checked 2026-11-14:

- https://huggingface.co/LiquidAI/LFM3-1.7B
- https://huggingface.co/LiquidAI/LFM3-1.7B/blob/main/LICENSE
- https://github.com/Liquid4All/cookbook/blob/main/finetuning/notebooks/lfm3_sft_with_trl.ipynb
- https://huggingface.co/docs/peft/en/developer_guides/custom_models
- https://docs.ollama.com/import

The exact upstream notebook and pinned model code/config are included in research. Code is loaded with trust_remote_code=True from the pinned checkpoint; review that code. This is required for this checkpoint's custom implementation. Model license is LFM Open License v1.0; read its commercial-use limitations, attribution and redistribution terms. It is not the project code's license. No weights are bundled.

The original Ollama GGUF has not been proven byte-equivalent to this trainable checkpoint. `scripts/freeze_baseline.py` captures local Ollama metadata; compare architecture, template, tokenizer, and upstream identity on Bazzite before interpreting differences as pure effects of training. Never fine-tune the original GGUF directly.

## Installation and execution

Use a separate environment with a matching PyTorch GPU installation for your driver. On CPU for the small compatibility test:

```bash
python3 -m venv .train-venv
source .train-venv/bin/activate
python -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-training.txt
python -m pip install -e .
python -m scripts.train --device cpu --smoke-test --out checkpoints/smoke-v1
```

A smoke test initializes a tiny random three-layer LFM3 (convolution, sliding attention, full attention), uses synthetic tokens, checks nonzero finite adapter gradients, and saves an adapter. It does not specialize or benchmark the released 1.7B model. It must never be merged or deployed as a useful model.

For actual training, install a torch build matching CUDA/ROCm rather than the CPU command above, read the model license, and review the draft examples. The explicit draft flag permits private experiments before independent scholarly review; it is not release approval.

```bash
python -m scripts.train --device cuda --epochs 3 --out checkpoints/aquinas-lora-v0.1.0 --accept-model-license --allow-draft-data
```

Use `--max-steps 1` in a fresh output directory for a full-checkpoint backward compatibility/memory test before an epoch run. It still downloads and loads the actual weights. Trainable checkpoint weights need about 3.46 GB in BF16 before activations, adapters, gradients, optimizer, temporary buffers and framework overhead. This implementation falls back to FP32 if BF16 is unavailable, approximately doubling base-weight storage. Budget an estimated 8–16 GB VRAM for conservative short-context BF16 adapter experiments; this is an engineering estimate, not a measured requirement. 16 GB is a more comfortable starting point. CPU execution is explicit and likely slow; Apple MPS support is unvalidated. QLoRA is not implemented or claimed; AMD support depends on a functioning ROCm torch build and checkpoint operators. Use external GPU compute if the local one-step test is impractical.

Defaults: seed 22, rank 8, alpha 16, dropout .05, learning rate .0001, AdamW, batch size one, accumulation four, max length 1024, three epochs. Oversize examples are rejected instead of silently truncated. Prompt tokens are masked; assistant tokens including the final end token are trained. Template prefix alignment is checked. A dataset hash, pinned revision, package versions, loss history, gradient verification and GPU peak allocation are recorded. No held-out evaluation questions are loaded into the training loop. There is no hyperparameter-validation split yet; these 28 records are only a pilot, not sufficient for a general competence claim. Before larger training, add an article-disjoint development set and measure forgetting.

The recorded manifest and lock file make a completed run reconstructible, subject to hardware nondeterminism. A saved adapter is a final training artifact; interrupted optimizer-state resumption is not implemented. Restart into a fresh versioned directory. Download/cache model and tokenizer while online before using training or inference offline (`HF_HUB_OFFLINE=1` with cached files).

## Merge and convert

```bash
python -m scripts.merge_adapter checkpoints/aquinas-lora-v0.1.0 merged/aquinas-v0.1.0
# In a separately installed, current llama.cpp checkout supporting LFM3:
python /path/to/llama.cpp/convert_hf_to_gguf.py merged/aquinas-v0.1.0 --outfile merged/aquinas-f16.gguf --outtype f16
/path/to/llama.cpp/build/bin/llama-quantize merged/aquinas-f16.gguf merged/aquinas-q4_k_m.gguf Q4_K_M
```

Conversion of this particular merged checkpoint is **unexecuted**. Verify architecture recognition in your llama.cpp revision and test tokenizer/template equivalence and a held-out sample before quantizing. Do not substitute Llama metadata or promise that arbitrary Safetensors adapters can be imported directly by Ollama. If unsupported, keep the trained checkpoint for Transformers inference and retain the original Ollama base with retrieval.

For a successfully converted and evaluated GGUF, create a Modelfile with an absolute `FROM /path/to/aquinas-q4_k_m.gguf`, preserve the verified chat template, then create a new `aquinas-trained:0.1.0` tag. Ollama does not itself apply this Python retriever; use `aquinas ask --mode rag --model ...` for retrieval. Never use `ollama rm lfm3-official:1.7b`. Roll back by asking with `--model lfm3-official:1.7b` or running that original tag. No trained model has been promoted.

## Transformers fallback

Before GGUF export, an actual adapter can be tested locally with:

```bash
python -m scripts.ask_transformers checkpoints/aquinas-lora-v0.1.0 'Explain the distinction between permission and obligation.' --device cuda
python -m scripts.ask_transformers checkpoints/aquinas-lora-v0.1.0 'What does Aquinas say about unjust laws?' --device cuda --rag
```

These fallback commands are implemented, but full-weight inference has not run in this workspace. The synthetic checkpoint is explicitly rejected.
