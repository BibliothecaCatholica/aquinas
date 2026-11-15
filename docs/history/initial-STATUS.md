# Aquinas status — 2026-11-14

**Implemented portable development system. No new trained 1.7B model, Bazzite deployment, or model promotion is claimed.**

## Completed and executed

- Read the supplied assignment and recovered all nine historical response JSONs and the prior benchmark review. Kept originals and recomputed performance statistics. Historical measurements remain evidence for one scenario only.
- Researched LiquidAI checkpoint, license, configuration, custom code and official SFT notebook; pinned trainable model revision `1da06bec6a819da10b54c67e5c90972b46d81871`. Verified original tokenizer compatibility for every starter training example.
- Downloaded the exact Gutenberg Summa I and I-II digital editions with raw notices intact and SHA-256 provenance. Parsed 584 + 619 articles, preserving source wording, character offsets, objections, replies, sed contra and respondeo. Disclosed numbering anomalies and three implicit article headings.
- Built a working offline FTS5 index containing 10,386 passage chunks. No third-party runtime dependencies or downloaded embedding model required.
- Authored 50 evaluation items, exactly ten per requested category, with answer keys, exact evidence, rubrics and failure criteria; ten additional ordinary-task checks; 28 pilot SFT examples. Training and philosophical evaluation use disjoint article IDs. Evidence strings and reference existence verified mechanically. Independent scholarly approval remains pending.
- Implemented CLI ingestion, search, asking, diagnostics, three/four-condition seeded benchmarking, citation audits, human grading, JSON/Markdown reporting and raw artifact retention. Verified request handling against a fake Ollama response in unit tests; no live Ollama was available here.
- Implemented assistant-token-only PEFT training, gradient checks, reproducible manifests/locks, merge, fallback Transformers inference, export instructions, versioned prompt Modelfile, and rollback procedure.
- Executed 20 passing core tests. Ran one adapter training step on a tiny randomly initialized three-layer LFM3 using synthetic tokens and CPU; finite loss 4.869815349578857, nonzero finite gradients, saved adapter. This is a compatibility check, not released-model training. Exact stack: torch 2.14.1+cpu, transformers 5.20.2, peft 0.21.2, accelerate 1.15.0.
- Real tokenizer validation: 28/28 examples have exact prompt-token prefix alignment; maximum sequence 105 tokens with the bundled starter dataset.

## Measurements actually available

| Experiment | Result | Limit |
|---|---|---|
| Core tests | 20/20 pass | Ollama calls mocked; no live local server |
| Corpus integrity | 1,203 article IDs, hashes and original section substrings validated | Digital edition verified; no full print collation |
| Retrieval coverage | 28/50 questions retrieve a keyed article among top six passages (56%) | Not answer accuracy; measured on development questions |
| Tiny LFM3 LoRA | One successful CPU backward/update/save step | Random tiny model; not 1.7B specialization |
| Original LFM3 historical speed | 162.8 mean tokens/s | Prior Bazzite run, one scenario, three seeds |
| Historical Aquinas / Lite speed | 162.3 / 162.7 mean tokens/s | Prompt variants only, not trained models |

Raw results and scripts are under results/ and scripts/. The current retrieval coverage is inadequate to assume robust source grounding; 22/50 fail the keyed-article retrieval criterion. No claim that RAG improves answers is justified yet.

## Remaining blockers and next executable steps

1. **Bazzite hardware and model access:** run `bash scripts/bootstrap.sh`, review results/local-hardware.json, and `python -m scripts.freeze_baseline`. Match the actual Ollama checkpoint/template to the trainable upstream checkpoint before attributing differences purely to fine-tuning.
2. **New generation comparison:** with existing Ollama, run `python -m aquinas.cli benchmark --out results/local-comparison-v1.jsonl`. This collects 450 new responses. Review using docs/GRADING.md; the ordinary task command is in README.md. No philosophical answers or speed figures for the new RAG/trained conditions were fabricated.
3. **Scholarship:** independently review the draft keys and 28 SFT records before public release. Review specific source editions and interpretations. Add a separate training-development set and fresh sealed confirmatory questions after retrieval tuning. The current 50-question set is already used for retrieval development, not an untouched final test.
4. **Full 1.7B LoRA:** install the hardware-matching torch stack, follow docs/TRAINING.md, run a full-checkpoint one-step test into a fresh directory, then an experiment if feasible. No full weights were downloaded and no released 1.7B checkpoint trained here.
5. **Conversion/deployment:** merge only an actual trained adapter; verify LFM3 support in the local llama.cpp converter, quantize and test under a new Ollama tag. This whole path is unexecuted. Fallback Transformers adapter inference is implemented but unexecuted on full weights. Never overwrite the original model.
6. **Corpus expansion:** SCG, De ente, De veritate, Aristotle and Augustine are not imported. Exact edition/translation rights and structure remain to verify (docs/SOURCES.md).
7. **Repository hosting:** connected GitHub tools do not expose repository creation; local gh is not authenticated. A local committed repository and complete source ZIP are the deliverable. No existing Bibliotheca Catholica repository was changed.

No model is promoted. The supported present deployment path is the original local LFM3 plus this offline retrieval client, subject to the measured retrieval limitations and local live testing.
