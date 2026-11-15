# Reproduce source pilot v2.1

The released adapter is already trained; installation and inference do not require training. Its original source-conditioned data are `data/training/source-conditioned-v2.jsonl` (40 records); the old `train.jsonl` (28) is preserved only for historical compatibility. Do not mistake the old default training script for the v2.1 experiment.

The standalone experiment runner is `scripts/source_pilot_v21.py`. It embeds the exact 40-record dataset and worker, requires an existing `.train-venv` with the pinned stack, defaults to cached model assets, writes a fresh checkpoint and results directory, and never replaces Ollama models. Run from the project root:

```bash
python3 scripts/source_pilot_v21.py --root "$PWD" --unload-base
```

On a fresh machine, populate the pinned base cache by running the adapter inference command in README first, or explicitly pass `--allow-download`. The runner requires native BF16 CUDA, enough free VRAM, at least 2 GiB free artifact storage, and the original source/data manifests. It tests cached decoding, then a complete optimizer step on the longest example. It restores the fresh LoRA parameters after that probe and proceeds only if the gate passes. An out-of-memory failure stops and preserves diagnostics. The full run may still have a higher peak than the single-example gate.

Settings: rank 8, alpha 16, dropout 0.05, learning rate 1e-4, batch 1, accumulation 4, 3 epochs, training seed 22, evaluation seed 11; SDPA and non-reentrant gradient checkpointing; assistant-token loss with an exact token-prefix check; no truncation of training examples. Full sources stay in input messages. Optional Triton wide convolution and automatic generation compilation are disabled.

The evaluation contains 50 philosophical and 10 ordinary questions without retrieval, three exact-source law applications, and 50 article-keyed source comparisons, each under base-disabled-adapter and adapter-enabled conditions. Evidence comes from full source sections, never answer-key wording. The questions are development material; scores remain null pending review. This is not evidence of reliable philosophical accuracy or grounds for automatic promotion.

Model revision, dataset and adapter hashes, original training losses, package versions and generation outputs accompany the release. Follow `AGENTS.md`: keep article IDs disjoint, preserve originals, and do not train on evaluation answers. Never merge a synthetic smoke adapter or label a prompt-only Ollama tag as learned specialization.
