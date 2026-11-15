#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p results
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m aquinas.cli ingest
python -m aquinas.cli index
python -m aquinas.cli validate
python -m unittest discover -s tests -v
python -m aquinas.cli diagnose > results/local-hardware.json
printf '\nAquinas ready. Activate with: source .venv/bin/activate\n'
