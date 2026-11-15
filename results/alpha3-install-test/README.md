# v0.2.0-alpha.3 clean-machine install test

November 15, 2026, after the v0.2.0-alpha.3 release was published.

- Machine: Linux x86-64, 4-core Intel Xeon (2.1 GHz), CPU only. Fresh empty `HOME`, a separate Ollama 0.40.16 server
  with an empty model directory, and a minimal environment (`env -i`, with only `PATH`, `HOME`, `OLLAMA_HOST`, and the
  network proxy settings this test machine needs).
- Command, exactly as in the README:
  `curl -fsSL https://raw.githubusercontent.com/BibliothecaCatholica/aquinas/v0.2.0-alpha.3/scripts/install_ollama.sh | bash -s -- --with-tool`
- Result: exit 0 in 51 seconds. `aquinas-neuron-Q4_K_M.gguf` and `Modelfile` were downloaded from the v0.2.0-alpha.3
  release and passed their pinned SHA-256 checks (`install-head.log`). The tool was cloned at tag `v0.2.0-alpha.3`
  (commit `f821b32ae7091b202229379a20bbeb5eb1f8088b`), set up, and its tests passed. `ollama list` showed only
  `aquinas-neuron:latest` (1.1 GB).
- The command the script prints, `.venv/bin/python -m aquinas.cli ask 'When does an unjust law bind in conscience?'
  --model aquinas-neuron --mode rag`, returned an answer citing ST I-II q.96 a.4 in 16 seconds. The answer has not
  been reviewed; this records that the install works, not answer quality.
- Release assets: GitHub's digests for both GGUF files equal the pinned checksums
  (`76749668…a7a164` and `f59ecf6f…3011fe`), unchanged from v0.2.0-alpha.2.
- Not tested: macOS, Windows, GPU, and the `--q8` option on this release.
- Cosmetic: `git clone --branch <tag>` prints Git's "detached HEAD" advice during `--with-tool`; harmless.
