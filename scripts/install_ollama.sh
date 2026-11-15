#!/usr/bin/env bash
# One-line install of the experimental Aquinas Neuron model for Ollama (Linux and macOS). No clone needed:
#
#   curl -fsSL https://raw.githubusercontent.com/BibliothecaCatholica/aquinas/v0.2.0-alpha.3/scripts/install_ollama.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/BibliothecaCatholica/aquinas/v0.2.0-alpha.3/scripts/install_ollama.sh | bash -s -- --with-tool
#
# What you get: one file that is LiquidAI's LFM3-1.7B with the Bibliotheca Catholica adapter already merged into it.
# You do not download LFM3 separately: Ollama cannot apply an adapter to a model at run time, so the two are combined
# before release (scripts/build_gguf.sh) and published as one verified file.
#
# Options:  --q8         the Q8_0 file (about 1.85 GB) instead of Q4_K_M (about 1.1 GB)
#           --with-tool  also set up the Aquinas tool (Summa texts and retrieval) in ~/aquinas, or AQUINAS_DIR
#           --force      replace an existing aquinas-neuron model
# It adds one Ollama model, aquinas-neuron, and changes nothing else. Experimental alpha: answer quality has not been
# reviewed; not a teaching authority. Check the primary text.
set -euo pipefail

VERSION="v0.2.0-alpha.3"  # the release this script belongs to: model files and tool come from the same tag
RELEASE="https://github.com/BibliothecaCatholica/aquinas/releases/download/$VERSION"
TAG="aquinas-neuron"
# Pinned checksums of the release files (models/aquinas-neuron/README.md).
SHA_Q4_K_M="76749668eda353685ff3563202172092af4bebe45ee817e40e01133e94a7a164"
SHA_Q8_0="f59ecf6f7043bead9f0e4908fa985c3bc277390bc168e538e56771e4cc3011fe"
SHA_MODELFILE="724ba2692ec762b00f6027cb7ab4d02b1ba19ab4fb017a2aa0c3e660c0004d78"

BASE="LiquidAI/LFM3-1.7B, revision 1da06bec6a819da10b54c67e5c90972b46d81871"
ADAPTER="source-pilot-v21, SHA-256 3f9f9eb50257bb734f054f810e7604c11fd1638094a6ce6d1f32807f17b7eca4"

usage() { cat <<'USAGE'
Install the experimental Aquinas Neuron model into Ollama.
  --q8         use the Q8_0 file (about 1.85 GB) instead of Q4_K_M (about 1.1 GB)
  --with-tool  also set up the Aquinas tool (Summa texts and retrieval) in ~/aquinas, or AQUINAS_DIR
  --force      replace an existing aquinas-neuron model
USAGE
}
QUANT="Q4_K_M"; FORCE=0; TOOL=0
for arg in "$@"; do
  case "$arg" in
    --q8) QUANT="Q8_0" ;;
    --force) FORCE=1 ;;
    --with-tool) TOOL=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $arg"; usage; exit 2 ;;
  esac
done
FILE="aquinas-neuron-$QUANT.gguf"
if [ "$QUANT" = "Q8_0" ]; then WANT="$SHA_Q8_0"; else WANT="$SHA_Q4_K_M"; fi

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not installed. Install it from https://ollama.com/download (Linux: curl -fsSL https://ollama.com/install.sh | sh), start it, then run this again."
  exit 1
fi
if ! ollama list >/dev/null 2>&1; then
  echo "Ollama is installed but not running. Start it (open the Ollama app, or run: ollama serve) and run this again."
  exit 1
fi
if ollama list | awk 'NR>1 {print $1}' | grep -qx "$TAG:latest"; then
  if [ "$FORCE" -ne 1 ]; then
    echo "An Ollama model named $TAG already exists. Nothing was changed. Re-run with --force to replace it."
    exit 1
  fi
  echo "Replacing the existing $TAG tag (--force)."
fi

sha() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }
DIR="${AQUINAS_NEURON_DIR:-$HOME/.cache/aquinas-neuron}"
mkdir -p "$DIR"
fetch() {  # fetch NAME EXPECTED_SHA256: download (resuming) and verify, or stop
  local name="$1" want="$2"
  if [ ! -f "$DIR/$name" ] || [ "$(sha "$DIR/$name")" != "$want" ]; then
    echo "Downloading $name ..."
    curl -fL --retry 3 -C - -o "$DIR/$name" "$RELEASE/$name" || curl -fL --retry 3 -o "$DIR/$name" "$RELEASE/$name"
  fi
  local got; got="$(sha "$DIR/$name")"
  if [ "$got" != "$want" ]; then
    echo "SHA-256 mismatch for $name: expected $want, got $got. Stopping; nothing was installed."
    rm -f "$DIR/$name"
    exit 1
  fi
  echo "$name: SHA-256 OK ($got)"
}
echo "Aquinas Neuron = LFM3-1.7B base + Aquinas adapter, already combined in one file:"
echo "  1. base model:  $BASE (included in the file)"
echo "  2. adapter:     $ADAPTER (merged into the file)"
echo "  3. this step:   download $FILE, verify it, and add it to Ollama as $TAG"
fetch "$FILE" "$WANT"
fetch Modelfile "$SHA_MODELFILE"

sed "s#^FROM .*#FROM $DIR/$FILE#" "$DIR/Modelfile" > "$DIR/Modelfile.$QUANT"
ollama create "$TAG" -f "$DIR/Modelfile.$QUANT"

ASK="python -m aquinas.cli ask 'When does an unjust law bind in conscience?' --model $TAG --mode rag"
if [ "$TOOL" -eq 1 ]; then
  HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
  if [ -n "$HERE" ] && [ -f "$HERE/bootstrap.sh" ] && [ -f "$HERE/../pyproject.toml" ]; then
    DEST="$(cd "$HERE/.." && pwd)"   # run from a clone: use it
  else
    DEST="${AQUINAS_DIR:-$HOME/aquinas}"
    command -v git >/dev/null 2>&1 || { echo "--with-tool needs git. Install git and run this again."; exit 1; }
    if [ ! -d "$DEST/.git" ]; then git clone --depth 1 --branch "$VERSION" https://github.com/BibliothecaCatholica/aquinas.git "$DEST"; fi
  fi
  python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null \
    || { echo "The Aquinas tool needs Python 3.11 or newer. The model is installed; set up the tool later with: bash $DEST/scripts/bootstrap.sh"; exit 1; }
  echo "Setting up the Aquinas tool in $DEST (Summa texts, search index, tests) ..."
  mkdir -p "$DEST/results"
  if ! bash "$DEST/scripts/bootstrap.sh" > "$DEST/results/install-tool.log" 2>&1; then
    tail -20 "$DEST/results/install-tool.log"
    echo "Setting up the tool failed (log: $DEST/results/install-tool.log). The model is installed and works with ollama run."
    exit 1
  fi
  ASK="cd $DEST && .venv/bin/python -m aquinas.cli ask 'When does an unjust law bind in conscience?' --model $TAG --mode rag"
fi

cat <<MSG

Installed the experimental Ollama model "$TAG" ($QUANT).

Chat with the model alone (it has no access to the Summa text):
  ollama run $TAG

Answers grounded in the Summa text, through the Aquinas tool$( [ "$TOOL" -eq 1 ] || echo " (set it up with --with-tool, or see the README)" ):
  $ASK

Experimental alpha: answer quality has not been reviewed; not a teaching authority. Check the primary text.
MSG
