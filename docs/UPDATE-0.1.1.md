# Aquinas 0.1.1 — correction after first Bazzite live test

The user supplied an actual successful install and Ollama RAG response. Corpus validation and 20 existing tests passed on Bazzite Python 3.14. Ollama reported lfm3-official:1.7b, Q8_0, 8192 context, 1,999,152,085 bytes of loaded-model VRAM; 469 generated tokens, 157.9738 generated tokens/s and 4.7819 seconds request wall time. GPU make/model and full training feasibility remain unknown.

The generated philosophical answer fails review. It adds an unsupported 1 John 5:40 reference; quotes an opponent's position recounted inside I-II q.19 a.5 as Aquinas's own; contradicts itself about when unjust laws do not bind; and blurs the difference between yielding rights to avoid scandal or disturbance and obeying an intrinsically wrongful command. The actual I-II q.96 a.4 was retrieved first. Source availability alone did not make the answer reliable.

A concrete implementation defect amplified this failure: the retriever exposed only the first chunk of I-II q.19 a.5. It stopped immediately before Aquinas rejects the view just recounted. Merely tagging a chunk 'respondeo' is not enough to establish its speaker's final position.

Changes:

- Keep lexical chunk search for discovery, but expand hits into COMPLETE respondeo sections before building model context. Select up to three distinct articles, excluding unpaired objections in the default RAG generation path.
- Never shorten a selected respondeo at the character-budget boundary: omit it and disclose the omission instead. The 18,000-character cap is a conservative engineering limit, not an exact tokenizer guarantee.
- Support explicit `ST I-II q.19 a.5` article requests in the context builder. No evaluation answer keys are used in retrieval.
- Explain opponent-reporting within a respondeo in the prompt; request faithful paraphrases and supplied ST references rather than additional remembered Bible/secondary citations. This is an instruction, not a guarantee of compliance.
- Explicitly close SQLite connections. SQLite's connection context manager only commits/rolls back transactions; it does not close the connection. Python 3.14 made the leak visible in the user's tests.
- Add `ask --plain` for concise terminal output and `--save FILE` for complete JSON retention. Existing save paths are refused.
- Record pipeline_version 0.1.1 and context-selection metadata in results. Old 56% retrieval numbers describe the original chunk-discovery measurement, not a newly measured answer-quality improvement for this revision.
- Add six regression tests: both sides of the q.19 a.5 argument retained, exact complete source equality, omission rather than truncation, correct law article retained, connection closure, and request payload completeness. All 26 tests pass in the development workspace. Live Bazzite generation with this revision remains pending.

Correct source distinction for reviewing the next answer: laws unjust through defects of end, authority or disproportionate burden do not ordinarily bind in conscience; avoiding scandal or disturbance can require yielding one's rights. Laws commanding conduct contrary to divine good must not be obeyed. The duty to avoid harm does not license the stipulated wrongdoing. Read q.19 a.5 alongside q.19 a.6 when discussing erroneous conscience; do not generalize it into a blanket excuse or permission for evil.

The updater backs up only files it changes and refuses unrecognized code edits. It changes no original model, source texts, training examples, historical benchmark results or checkpoints. Its test run uses mocked generation only. After applying it, save a fresh live response before running a large comparison. The original README/status describe initial v0.1.0 measurements; read this update note for revised context behavior and current live-test limits.
