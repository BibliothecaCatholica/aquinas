#!/usr/bin/env bash
# Build the experimental merged GGUF files (Q4_K_M and Q8_0) from the released adapter and the pinned base.
# Nothing is published or installed into an existing Ollama library. Output: dist/gguf/ (git-ignored).
#
#   bash scripts/build_gguf.sh            # needs .train-venv (scripts/install.sh), git, cmake, a C++ compiler, ~15 GB free
#
# Steps, as executed on November 15, 2026 (results in models/aquinas-neuron/README.md):
#   1. scripts/merge_adapter.py --exact: base + adapter merged reproducibly (float64 sum, one rounding to float32; 6.9 GB)
#   2. llama.cpp convert_hf_to_gguf.py: merged model to GGUF F16 (about 3.5 GB)
#   3. llama-quantize: Q4_K_M (about 1.1 GB) and Q8_0 (about 1.8 GB)
#   4. gguf_new_metadata.py: the embedded chat template with thinking off (plain `ollama run` gives a clean answer)
set -euo pipefail
cd "$(dirname "$0")/.."
LLAMA_CPP_COMMIT="${LLAMA_CPP_COMMIT:-e574a17b062be51b98e239ccd3d3743e3d902333}"  # the commit that was tested
WORK="${WORK:-$(pwd)/dist/gguf}"; mkdir -p "$WORK"
PY=.train-venv/bin/python
[ -x "$PY" ] || { echo 'Run scripts/install.sh first (it creates .train-venv).'; exit 1; }

if [ ! -d "$WORK/llama.cpp" ]; then
  git clone https://github.com/ggml-org/llama.cpp "$WORK/llama.cpp"
  git -C "$WORK/llama.cpp" checkout "$LLAMA_CPP_COMMIT"
fi
cmake -S "$WORK/llama.cpp" -B "$WORK/llama.cpp/build" -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF -DGGML_NATIVE=OFF  # portable: same bytes on any x86-64
cmake --build "$WORK/llama.cpp/build" -j"$(nproc)" --target llama-quantize llama-completion
"$PY" -m pip install --target "$WORK/pyextra" sentencepiece protobuf

rm -f "$WORK"/aquinas-neuron-*.gguf
[ -e "$WORK/merged" ] || "$PY" scripts/merge_adapter.py --exact models/source-pilot-v21 "$WORK/merged"
PYTHONPATH="$WORK/llama.cpp/gguf-py:$WORK/pyextra" "$PY" "$WORK/llama.cpp/convert_hf_to_gguf.py" "$WORK/merged" \
  --outtype f16 --outfile "$WORK/aquinas-neuron-f16.gguf"
rm -rf "$WORK/merged"  # free about 6.9 GB before quantizing
# The embedded chat template decides the prompt in Ollama (a Modelfile TEMPLATE is not used for this model). The
# upstream template thinks by default and Ollama passes enable_thinking=true, so a plain `ollama run` printed a thinking
# section. Thinking is switched off in the embedded template (one line; nothing else changes, weights untouched).
PYTHONPATH="$WORK/llama.cpp/gguf-py" "$PY" - "$WORK/aquinas-neuron-f16.gguf" "$WORK/chat_template-nothink.jinja" <<'PYEOF'
import sys
from gguf import GGUFReader
f = GGUFReader(sys.argv[1]).fields['tokenizer.chat_template']
t = bytes(f.parts[f.data[0]]).decode('utf-8')
old = '{%- set enable_thinking = enable_thinking | default(true) -%}'
assert t.count(old) == 1, 'upstream template changed; review the thinking switch'
open(sys.argv[2], 'w').write(t.replace(old, '{%- set enable_thinking = false -%}'))
PYEOF
for q in Q4_K_M Q8_0; do
  "$WORK/llama.cpp/build/bin/llama-quantize" "$WORK/aquinas-neuron-f16.gguf" "$WORK/quant-$q.gguf" "$q"
  PYTHONPATH="$WORK/llama.cpp/gguf-py" "$PY" "$WORK/llama.cpp/gguf-py/gguf/scripts/gguf_new_metadata.py" \
    --chat-template-file "$WORK/chat_template-nothink.jinja" "$WORK/quant-$q.gguf" "$WORK/aquinas-neuron-$q.gguf"
  rm -f "$WORK/quant-$q.gguf"
done
rm -rf "$WORK/merged" "$WORK/aquinas-neuron-f16.gguf"
cp models/aquinas-neuron/Modelfile models/source-pilot-v21/LICENSE "$WORK/"
( cd "$WORK" && sha256sum aquinas-neuron-*.gguf | tee SHA256SUMS )
echo "Done. To try it with your own Ollama (it adds one new tag and changes no existing model):"
echo "  cd $WORK && ollama create aquinas-neuron -f Modelfile"
