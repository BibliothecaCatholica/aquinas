#!/usr/bin/env bash
# Install the experimental Aquinas Neuron model into your own Ollama, in one command (Linux and macOS):
#
#   bash scripts/install_ollama.sh            # Q4_K_M, about 1.1 GB (default)
#   bash scripts/install_ollama.sh --q8       # Q8_0, about 1.85 GB (higher quality)
#   bash scripts/install_ollama.sh --force    # replace an existing aquinas-neuron tag
#
# It downloads one GGUF file and the Modelfile from the GitHub release, refuses to continue unless their SHA-256 match
# the values pinned below, and runs `ollama create aquinas-neuron`. That adds one new tag and changes nothing else; an
# existing aquinas-neuron tag is never overwritten without --force. No other Ollama model is touched.
# Experimental alpha: answer quality has not been reviewed; not a teaching authority. Check the primary text.
set -euo pipefail

RELEASE="https://github.com/BibliothecaCatholica/aquinas/releases/download/v0.2.0-alpha.2"
TAG="aquinas-neuron"
# Pinned checksums of the release files (models/aquinas-neuron/README.md).
SHA_Q4_K_M="030bd4086674da99974a6e73c9a7388c050d7beb658bf471268a9e8e0c391c45"
SHA_Q8_0="f59ecf6f7043bead9f0e4908fa985c3bc277390bc168e538e56771e4cc3011fe"
SHA_MODELFILE="724ba2692ec762b00f6027cb7ab4d02b1ba19ab4fb017a2aa0c3e660c0004d78"

QUANT="Q4_K_M"; FORCE=0
for arg in "$@"; do
  case "$arg" in
    --q8) QUANT="Q8_0" ;;
    --force) FORCE=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Unknown option: $arg (use --q8, --force, or --help)"; exit 2 ;;
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
fetch "$FILE" "$WANT"
fetch Modelfile "$SHA_MODELFILE"

sed "s#^FROM .*#FROM $DIR/$FILE#" "$DIR/Modelfile" > "$DIR/Modelfile.$QUANT"
ollama create "$TAG" -f "$DIR/Modelfile.$QUANT"

cat <<MSG

Installed the experimental Ollama model "$TAG" ($QUANT).

Chat with the model alone (it has no access to the Summa text):
  ollama run $TAG

Answers grounded in the Summa text, through the Aquinas tool (recommended; see README):
  python -m aquinas.cli ask 'When does an unjust law bind in conscience?' --model $TAG --mode rag

Experimental alpha: answer quality has not been reviewed; not a teaching authority. Check the primary text.
MSG
