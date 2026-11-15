# Current limitations

- This is an experimental 1.7B adapter, not an independently approved philosophical or doctrinal authority. Technical completion is established; complete v2.1 answer-quality review and sealed confirmation are pending. Draft dataset keys and answers require scholarly review.
- The corpus includes only Summa I and I-II. Exact digital source bytes are preserved, but no complete independent print collation is claimed. Metadata reconciliation is disclosed in SOURCES.md.
- Retrieval uses lexical SQLite FTS5, not a semantic reranker. Its relevance can fail, and supplying the right source does not guarantee a faithful answer. Canonical article references in a query are recognized. Full respondeo sections are kept intact; unpaired objections are excluded from answer context.
- Forty training examples are a small experimental set, not broad philosophical coverage. Article IDs are disjoint from evaluation keys; related concepts and base pretraining exposure remain possible. Published development questions are no longer a sealed test.
- The full training run was executed on one RTX 3070. Other GPUs and full-size CPU inference are not measured. The public convenience CLI uses the exercised inference backend, but has only local integration checks here. There is no merged GGUF, Ollama import of this adapter, Mac/mobile package, or network service.
- Core tests use mock Ollama calls. Full adapter development responses came from the uploaded real GPU run. Unit tests passing do not establish answer correctness.
- After model assets are cached, offline local inference is available. First installation and base download need Internet. The pinned upstream model executes custom Python explicitly. Keep the original Ollama baseline for comparisons.
- Source, model-derived assets and original code have different license terms and notices; root MIT does not relicense the whole bundle.
