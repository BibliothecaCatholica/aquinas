#!/usr/bin/env bash
# Build the experimental merged GGUF files (Q4_K_M and Q8_0) from the released adapter and the pinned base.
# Nothing is published or installed into an existing Ollama library. Output: dist/gguf/ (git-ignored).
#
#   bash scripts/build_gguf.sh            # needs .train-venv (scripts/install.sh), git, cmake, a C++ compiler, ~15 GB free
#
# Steps, as executed on November 15, 2026 (results in models/gguf-experimental/README.md):
#   1. scripts/merge_adapter.py: base + adapter merged in float32 (about 6.9 GB)
#   2. llama.cpp convert_hf_to_gguf.py: merged model to GGUF F16 (about 3.5 GB)
#   3. llama-quantize: Q4_K_M (about 1.1 GB) and Q8_0 (about 1.8 GB)
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
cmake -S "$WORK/llama.cpp" -B "$WORK/llama.cpp/build" -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF
cmake --build "$WORK/llama.cpp/build" -j"$(nproc)" --target llama-quantize llama-completion
"$PY" -m pip install --target "$WORK/pyextra" sentencepiece protobuf

[ -e "$WORK/merged" ] || "$PY" scripts/merge_adapter.py models/source-pilot-v21 "$WORK/merged"
PYTHONPATH="$WORK/llama.cpp/gguf-py:$WORK/pyextra" "$PY" "$WORK/llama.cpp/convert_hf_to_gguf.py" "$WORK/merged" \
  --outtype f16 --outfile "$WORK/aquinas-experimental-f16.gguf"
for q in Q4_K_M Q8_0; do
  "$WORK/llama.cpp/build/bin/llama-quantize" "$WORK/aquinas-experimental-f16.gguf" "$WORK/aquinas-experimental-$q.gguf" "$q"
done
rm -rf "$WORK/merged" "$WORK/aquinas-experimental-f16.gguf"
cp models/gguf-experimental/Modelfile models/source-pilot-v21/LICENSE "$WORK/"
( cd "$WORK" && sha256sum aquinas-experimental-*.gguf | tee SHA256SUMS )
echo "Done. To try it with your own Ollama (it adds one new tag and changes no existing model):"
echo "  cd $WORK && ollama create aquinas-experimental:q4_k_m -f Modelfile"
