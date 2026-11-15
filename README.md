# Aquinas

A local Thomistic study and research tool from Bibliotheca Catholica: searchable primary texts of the Summa, and the
**Aquinas Neuron**, an experimental LFM3-1.7B model with a Bibliotheca Catholica adapter merged in, for local use with
Ollama.

> **Experimental alpha (v0.2.0-alpha.2).** Answer quality has not been reviewed. Aquinas is not a teaching authority
> and not a demonstrated improvement over the base model; answers can contain mistakes and unsupported citations, so
> check the primary text. **The model alone has no access to the Summa.** It answers from its weights unless you use
> it through the Aquinas tool below, which retrieves the relevant articles and sends them with your question.

## 1. Install (one line)

You need [Ollama](https://ollama.com/download) installed and running. Then, on Linux or macOS, paste this into a
terminal. It installs the model and the Summa tool together:

```bash
curl -fsSL https://raw.githubusercontent.com/BibliothecaCatholica/aquinas/main/scripts/install_ollama.sh | bash -s -- --with-tool
```

**What this downloads.** One file, the Aquinas Neuron: LiquidAI's **LFM3-1.7B** (revision `1da06bec…`) with the
Bibliotheca Catholica **adapter already merged into it**. You do not download LFM3 separately. Ollama cannot apply an
adapter to a model at run time, so the two are combined before release (`scripts/build_gguf.sh`) and published as one
file, which the installer checks against a pinned SHA-256 before using it. In order, the installer:

1. downloads the combined file (Q4_K_M, about 1.1 GB; add `--q8` for the 1.85 GB Q8_0) and its Modelfile from the
   [v0.2.0-alpha.2 release](https://github.com/BibliothecaCatholica/aquinas/releases/tag/v0.2.0-alpha.2), and stops if
   either checksum differs;
2. adds it to Ollama as `aquinas-neuron` (one new model; nothing else changes; an existing `aquinas-neuron` is replaced
   only with `--force`);
3. with `--with-tool`, downloads this repository to `~/aquinas` and sets up the tool (needs git and Python 3.11+).

It ends by printing the two commands to use. Leave out `--with-tool` to install the model only.

**Windows and macOS by hand:** download `aquinas-neuron-Q4_K_M.gguf` and `Modelfile` from the release into one folder;
check the file's SHA-256 against `SHA256SUMS` in the release (Windows PowerShell: `Get-FileHash aquinas-neuron-Q4_K_M.gguf`;
macOS: `shasum -a 256 aquinas-neuron-Q4_K_M.gguf`); then, in that folder, run `ollama create aquinas-neuron -f Modelfile`.

## 2. Ask

```bash
ollama run aquinas-neuron
```

That is the model alone: it answers from its weights and **has no access to the Summa**. For answers grounded in the
text (recommended), ask through the tool, which searches the bundled Summa Theologiae I and I-II (1,203 articles,
Fathers of the English Dominican Province translation, transcribed by Project Gutenberg) and sends the complete
*respondeo* of the relevant articles with your question:

```bash
cd ~/aquinas && .venv/bin/python -m aquinas.cli ask 'When does an unjust law bind in conscience?' --model aquinas-neuron --mode rag
```

Retrieved evidence still needs judgment: check the cited articles. `.venv/bin/python -m aquinas.cli search 'TERMS'`
searches the texts without any model. Without `--with-tool`, set the tool up from a clone with `bash scripts/bootstrap.sh`.

## 3. Developer path

The rest of this README covers the Python adapter (the unmerged LoRA, for research and comparison), the one-command
developer install, and how the model files are built (`scripts/build_gguf.sh`; [model card](models/aquinas-neuron/README.md)).

### One-command developer install

On Linux with Python 3.11+, from the repository folder:

```bash
bash scripts/install.sh
```

It runs the bootstrap below (core tool, index, tests), creates the separate inference environment, downloads the pinned LiquidAI/LFM3-1.7B base (about 3.5 GB), verifies the adapter checksum, and answers one question with the experimental adapter and retrieved evidence. It uses your GPU if PyTorch sees one, otherwise the CPU (`AQUINAS_DEVICE=cpu` forces it; on a 4-core CPU one answer took under a minute and about 11 GB of memory, see [results/cpu-load-test](results/cpu-load-test/README.md)). It does not install, remove, or overwrite any Ollama model. The adapter is experimental and unpromoted; answer quality has not been reviewed.

The sections below do the same steps one at a time.

### Download and search the texts

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

### Use an existing Ollama model

With Ollama running and `lfm3-official:1.7b` already installed:

```bash
python -m aquinas.cli ask 'When does an unjust law bind in conscience?' --mode rag --plain
```

This uses the unchanged Ollama model with retrieved evidence. It does not load the adapter below. Use `--model YOUR_LOCAL_TAG` if your installed model has another name. These commands do not install, delete, or overwrite any Ollama model.

### Use the experimental trained adapter

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

### What actually ran

| Item | Observed result |
|---|---|
| Source-conditioned training | 40 examples, 3 epochs, 120 microbatches, 30 optimizer updates |
| Hardware | NVIDIA RTX 3070, 8 GB |
| Longest training example | 1,178 tokens; complete forward/backward/update memory check passed |
| Training memory peak | 5.16 GiB allocated; 6.63 GiB reserved |
| Matched development generation | 226/226 responses, zero generation errors, zero output-limit stops |
| Independent answer-quality approval | Pending; no accuracy percentage or promotion claimed |

Development results are under `results/source-pilot-v21/`. Completion is not correctness. These questions have already been used during development and are not a sealed final benchmark. See [the model card](models/source-pilot-v21/README.md), [status](docs/STATUS.md), [training instructions](docs/TRAINING.md), and [source provenance](docs/SOURCES.md).

### Reproduce and contribute

```bash
python -m aquinas.cli ingest
python -m aquinas.cli index
python -m aquinas.cli validate
python -m unittest discover -s tests -v
```

Original draft code/data are MIT licensed. Model-derived adapter and tokenizer assets remain subject to the bundled **LFM Open License v1.0**. Upstream model Python retains Apache 2.0 notices; Gutenberg source files retain their own notices. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No base model weights are bundled. Contributions should preserve source wording and distinguish technical checks from scholarly review.
