#!/usr/bin/env bash
# One-command install for the Aquinas alpha: core tool, inference environment, pinned base, adapter check, one answer.
#
#   bash scripts/install.sh            # GPU if PyTorch sees one, otherwise CPU
#   AQUINAS_DEVICE=cpu bash scripts/install.sh
#
# What it does, in order:
#   1. scripts/bootstrap.sh: core environment (.venv), ingest, index, validate, unit tests.
#   2. A separate inference environment (.train-venv) with torch==2.14.1 and requirements-training.txt, unless one
#      already exists (an existing CUDA .train-venv is reused as is).
#   3. Downloads the pinned LiquidAI/LFM3-1.7B base revision (about 3.5 GB) into the Hugging Face cache.
#   4. Verifies the adapter's SHA-256 against models/source-pilot-v21/release-manifest.json.
#   5. Answers one README question with the experimental adapter and retrieved evidence.
# It never installs, removes, or overwrites an Ollama model, and it does not train anything.
# The adapter is experimental and unpromoted; answer quality has not been reviewed. Check the primary text.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1/5 core tool (scripts/bootstrap.sh)"
bash scripts/bootstrap.sh

echo "== 2/5 inference environment (.train-venv)"
if [ ! -x .train-venv/bin/python ]; then
  python3 -m venv .train-venv
  .train-venv/bin/python -m pip install --upgrade pip >/dev/null
  .train-venv/bin/python -m pip install torch==2.14.1
fi
.train-venv/bin/python -m pip install -r requirements-training.txt
.train-venv/bin/python -m pip install -e .

DEVICE="${AQUINAS_DEVICE:-$(.train-venv/bin/python -c 'import torch; print("cuda" if torch.cuda.is_available() else "cpu")')}"
echo "   device: $DEVICE"

echo "== 3/5 pinned base model"
.train-venv/bin/python - <<'PY'
import json
from huggingface_hub import snapshot_download
m = json.load(open('models/source-pilot-v21/release-manifest.json'))
path = snapshot_download(m['base'], revision=m['revision'])
print('   base %s at %s: %s' % (m['base'], m['revision'], path))
PY

echo "== 4/5 adapter checksum"
.train-venv/bin/python - <<'PY'
import hashlib, json, sys
m = json.load(open('models/source-pilot-v21/release-manifest.json'))
got = hashlib.sha256(open('models/source-pilot-v21/adapter_model.safetensors', 'rb').read()).hexdigest()
if got != m['adapter_sha256']:
    sys.exit('adapter checksum differs: %s != %s' % (got, m['adapter_sha256']))
print('   adapter sha256 OK: ' + got)
PY

echo "== 5/5 one answer (experimental adapter, with retrieved evidence)"
.train-venv/bin/python -m aquinas.adapter \
  'Using ST I-II q.96 a.4, when does an unjust law bind in conscience?' \
  --device "$DEVICE" --rag --offline

printf '\nAquinas installed. Core: source .venv/bin/activate. Adapter: .train-venv/bin/python -m aquinas.adapter QUESTION --device %s --rag --offline\n' "$DEVICE"
printf 'Experimental and unpromoted: answer quality has not been reviewed. Check the primary text.\n'
