# CPU load test of the v0.2.0a1 adapter (November 15, 2026)

Run by Claude (Claude Code) in a cloud container, as a stranger following the README. **No GPU.** Not a quality evaluation:
completion is not correctness, and neither answer has been reviewed.

| Item | Value |
|---|---|
| Machine | 4 vCPU (Intel Xeon @ 2.30GHz), 15 GiB RAM, no GPU |
| Software | Python 3.13.18, torch 2.14.1 (PyPI wheel, CUDA unavailable), transformers 5.20.2, peft 0.21.2, accelerate 1.15.0, safetensors 0.8.0 |
| Base | LiquidAI/LFM3-1.7B at `1da06bec6a819da10b54c67e5c90972b46d81871` (downloaded during the first run) |
| Adapter | `models/source-pilot-v21`, SHA-256 verified by the loader |
| Question | `Using ST I-II q.96 a.4, when does an unjust law bind in conscience?` (the README example) |
| Dtype | float32 (the loader's CPU choice) |

| Run | Command | Whole process | Generation | Input / output tokens | Peak resident memory |
|---|---|---|---|---|---|
| Adapter with retrieval | `python -m aquinas.adapter QUESTION --device cpu --rag` | 50.8 s (includes the first download of the base) | 24.6 s | 2216 / 39 | 10.90 GiB |
| Base only, same prompt and retrieval | `python -m aquinas.adapter QUESTION --device cpu --base-only --rag` | 54.7 s | 45.4 s | 2216 / 143 | 10.87 GiB |

Peak memory is the process high-water mark (`ru_maxrss`) measured by a wrapper around each command.
`--base-only` was run with `--rag` so that both runs share the same prompt and evidence.

## Answers (verbatim, unreviewed)

**Adapter, with retrieval:**

> An unjust law does not bind in conscience. It binds only if it is just. Distinguish the law's justification from its application. [ST I-II q.96 a.4]

**Base only, same prompt and retrieval:**

> According to ST I-II q.96 a.4, an unjust law does **not** bind in conscience, except in cases where it is employed merely to avoid scandal or disturbance. The author states that such unjust laws—whether contrary to human good, exceeding the lawgiver's power, or imposing burdens unequally on the community—"do not bind in conscience, except perhaps in order to avoid scandal or disturbance, for which cause a man should even yield his right" (citing Matthew 5:40–41). Thus, only when an unjust law serves to prevent social disturbance or scandal might it have a tenuous binding effect, but even then it is not genuine binding in conscience.

The full records, with the request and token ids, are `rag.json` and `base-only.json` in this folder (written by `--save`).

## Notes for a fresh machine
- The README's `python -m pip install torch==2.14.1` installs the default PyPI wheel (CUDA build, several GB) even on a CPU-only machine. It works on CPU but is a large download.
- The first run downloads the base (about 3.5 GB). In this container the Hugging Face Xet CDN host had to be allowed before the download worked; on an ordinary connection this needs nothing.
