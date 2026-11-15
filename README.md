# Aquinas

A local Thomistic study and research tool from Bibliotheca Catholica. Aquinas combines searchable primary texts with local language-model inference and an experimental LFM3 adapter.

**Experimental alpha — v0.2.0a1.** The adapter trained successfully on an RTX 3070 and completed 226 development responses. Philosophical accuracy and source fidelity have not been independently approved. Answers can still contain mistakes and unsupported citations; check the primary text. This is not an official Catholic teaching authority or a demonstrated improvement over the base model.

## One-command install

On Linux with Python 3.11+, from the repository folder:

```bash
bash scripts/install.sh
```

It runs the bootstrap below (core tool, index, tests), creates the separate inference environment, downloads the pinned LiquidAI/LFM3-1.7B base (about 3.5 GB), verifies the adapter checksum, and answers one question with the experimental adapter and retrieved evidence. It uses your GPU if PyTorch sees one, otherwise the CPU (`AQUINAS_DEVICE=cpu` forces it; on a 4-core CPU one answer took under a minute and about 11 GB of memory, see [results/cpu-load-test](results/cpu-load-test/README.md)). It does not install, remove, or overwrite any Ollama model. The adapter is experimental and unpromoted; answer quality has not been reviewed.

The sections below do the same steps one at a time.

## Download and search the texts

Choose **Code → Download ZIP**, extract it, and open a terminal inside the extracted `aquinas` folder. Alternatively:

```bash
git clone --depth 1 https://github.com/BibliothecaCatholica/aquinas.git
cd aquinas
```

Python 3.11+ and SQLite FTS5 are required for the core. Linux/Bazzite is the tested platform. Bootstrap installs the core, builds the index from the bundled source files, and runs its tests:

```bash
bash scripts/bootstrap.sh
source .venv/bin/activate
python -m aquinas.cli search 'human law conscience scandal disturbance'
```

The corpus covers **Summa Theologiae I and I-II: 1,203 articles**, in the Fathers of the English Dominican Province translation transcribed by Project Gutenberg. Original text bytes and notices are preserved. The other parts of the Summa and other authors are not included.

## Use an existing Ollama model

With Ollama running and `lfm3-official:1.7b` already installed:

```bash
python -m aquinas.cli ask 'When does an unjust law bind in conscience?' --mode rag --plain
```

This uses the unchanged Ollama model with retrieved evidence. It does not load the adapter below. Use `--model YOUR_LOCAL_TAG` if your installed model has another name. These commands do not install, delete, or overwrite any Ollama model.

## Use the experimental trained adapter

The ~31 MiB LoRA adapter is included at `models/source-pilot-v21/`. It requires the separate LiquidAI/LFM3-1.7B base; it is not a standalone GGUF or an Ollama tag. First download of the pinned base requires Internet access and several GB of storage. Questions are generated locally; they are not sent to a hosted chat API.

Create a separate inference environment. Install a PyTorch build appropriate for your GPU before installing the remaining dependencies. On the validated Bazzite/NVIDIA setup, an existing `.train-venv` with CUDA PyTorch can be reused. Otherwise:

```bash
python3 -m venv .train-venv
source .train-venv/bin/activate
python -m pip install torch==2.14.1
python -m pip install -r requirements-training.txt
python -m pip install -e .
python -c 'import torch; print("CUDA available:", torch.cuda.is_available())'
```

The CUDA result must be `True` for `--device cuda`; if it is false, install the GPU-specific build using the [official PyTorch installer](https://pytorch.org/get-started/locally/). The executed training stack used PyTorch 2.14.1+cu130, Transformers 5.20.2, PEFT 0.21.2, Accelerate 1.15.0 and safetensors 0.8.0. Full-size CPU inference is available with `--device cpu`, but has not been measured here; expect substantially more RAM and time.

From the repository root, try an explicitly identified source article first:

```bash
python -m aquinas.adapter \
  'Using ST I-II q.96 a.4, when does an unjust law bind in conscience?' \
  --device cuda --rag
```

For subsequent disconnected use, add `--offline` after the pinned base and its custom Python have been cached. Without `--rag`, the adapter answers without retrieved evidence. `--base-only` disables the adapter under the same prompt, tokenizer and inference backend for a comparison. `--save results/local-answer.json` preserves the request and response and refuses to overwrite an existing result.

The base uses upstream custom Python; the loader pins revision `1da06bec6a819da10b54c67e5c90972b46d81871` and enables that code explicitly. It verifies the adapter checksum and tokenizer mapping/template, uses SDPA attention and the model's native Torch convolution, and disables automatic compilation. No GPU Triton compiler or system Python development headers are required by this inference path. Evidence is supplied as complete respondeo sections; oversized context is refused rather than silently truncated. Retrieval relevance still needs judgment.

## What actually ran

| Item | Observed result |
|---|---|
| Source-conditioned training | 40 examples, 3 epochs, 120 microbatches, 30 optimizer updates |
| Hardware | NVIDIA RTX 3070, 8 GB |
| Longest training example | 1,178 tokens; complete forward/backward/update memory check passed |
| Training memory peak | 5.16 GiB allocated; 6.63 GiB reserved |
| Matched development generation | 226/226 responses, zero generation errors, zero output-limit stops |
| Independent answer-quality approval | Pending; no accuracy percentage or promotion claimed |

Development results are under `results/source-pilot-v21/`. Completion is not correctness. These questions have already been used during development and are not a sealed final benchmark. See [the model card](models/source-pilot-v21/README.md), [status](docs/STATUS.md), [training instructions](docs/TRAINING.md), and [source provenance](docs/SOURCES.md).

## Reproduce and contribute

```bash
python -m aquinas.cli ingest
python -m aquinas.cli index
python -m aquinas.cli validate
python -m unittest discover -s tests -v
```

Original draft code/data are MIT licensed. Model-derived adapter and tokenizer assets remain subject to the bundled **LFM Open License v1.0**. Upstream model Python retains Apache 2.0 notices; Gutenberg source files retain their own notices. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No base model weights are bundled. Contributions should preserve source wording and distinguish technical checks from scholarly review.
