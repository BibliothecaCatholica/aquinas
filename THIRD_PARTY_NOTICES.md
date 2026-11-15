# Attribution and licensing

Original Aquinas code, documentation, and authored draft examples: MIT, copyright 2026 Bibliotheca Catholica. This grant does not replace third-party terms for included evidence or model-derived assets.

- `data/raw/`: Project Gutenberg ebooks 17611 and 17897, Thomas Aquinas, Summa Theologiae I and I-II, Fathers of the English Dominican Province translation. Source bytes, credits and full embedded Gutenberg notices are unchanged. Source metadata are in `data/sources.json`; see `docs/SOURCES.md` for exact editions and editorial boundaries. Embedded evidence in datasets is attributable to the same sources.
- `models/source-pilot-v21/`: LoRA derivative trained by Bibliotheca Catholica from LiquidAI/LFM3-1.7B. Adapter and tokenizer are distributed subject to LFM Open License v1.0; copies are `models/source-pilot-v21/LICENSE` and `research/model-license.txt`. The model license includes commercial-use conditions; the root MIT grant does not supersede them. The base weights are downloaded separately.
- `research/configuration_lfm3.py`, `modeling_lfm3.py`, `lfm3_conv.py`: unchanged pinned upstream model source; original Apache 2.0 notices retained, complete text at `research/APACHE-2.0.txt`, origin/revision at `research/model-revision.json`.
- `research/tokenizer/` and model-folder tokenizer/template: upstream LiquidAI tokenizer assets with the model-license reference. No project authorship is claimed over their contents.

The upstream cookbook notebook, personal hardware dumps, raw process logs, temporary checkpoints and historical user-chat exports are not part of this public source distribution. Historical initial-build notes are labeled as history. Generated philosophical responses are research outputs, not authoritative quotations.
