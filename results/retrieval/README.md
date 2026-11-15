# Retrieval measurement (November 15, 2026)

Is the keyed article among the first 1, 3, or 5 articles the tool would send as evidence? Articles are ranked exactly as
`retrieve_context` ranks them (`aquinas.core.rank_articles`); the tool sends the first three. This measures retrieval
only, not answer accuracy. Reproduce with `python scripts/evaluate_retrieval.py --dataset holdout|confirmation` after
`python -m aquinas.cli index`.

| Index | Dataset | Questions | Top-1 | Top-3 | Top-5 |
|---|---|---|---|---|---|
| Before | holdout | 50 | 0.42 | 0.54 | 0.56 |
| After | holdout | 50 | 0.50 | 0.62 | 0.68 |
| Before | confirmation | 20 | 0.30 | 0.50 | 0.75 |
| After | confirmation | 20 | 0.50 | 0.65 | 0.80 |

**Fixes (no new dependencies):** each passage also indexes its article's title (the "Whether ...?" preamble) in a
separate FTS5 column, weighted 2.0 against the passage text; and question wording that names the author or the form of
answer ("Aquinas", "his", "give ... conclusion rather than an objection") is no longer searched. Separately on the
holdout set: titles alone gave 0.48 / 0.60 / 0.66, the stopwords alone 0.44 / 0.56 / 0.60. Title weights 1.0 and 4.0 gave
0.46 / 0.60 / 0.64 and 0.50 / 0.64 / 0.66; 2.0 was kept rather than tuned further on the holdout.

**Caveats.** The 50 holdout items are development questions, already used while developing; the fixes were chosen on
them. The 20 confirmation items (`data/evaluation/confirmation.jsonl`) are fresh: articles drawn at random (seed
20261115) from those in neither training nor holdout, questions written by Claude without the article title's wording,
keyed articles not scholarly reviewed. With 20 questions one item is 5 points. The search output text is unchanged; the
index must be rebuilt (`aquinas index`) after updating.

## Optional meaning-based reranking (separate PR, for review)

`aquinas/rerank.py` reorders the first 20 articles from word search by cosine similarity between the question and each
article (its title and the first 1,500 characters of its respondeo), with a small embedding model served by Ollama
(`/api/embed`; standard library only, no Python ML packages). Word search remains the default; with `--rerank` the tool
falls back to word search, and says why, when Ollama is not reachable, the model is not installed, or the article
vectors have not been built (`aquinas embed --model …`, once). The 20-candidate pool, the 1,500-character article text,
and both models were fixed before measuring; nothing was tuned on either dataset.

The confirmation set now has 50 fresh items. Items 21–50 were drawn from the same seeded sample as 01–20 (the 50 first
articles of `random.Random(20261115).sample(sorted(eligible), 50)`, whose first 20 are the original items) and written
before any search was run on them. They avoid the article titles' vocabulary more strictly than 01–20, and word search
finds them much less often, so the 50-item numbers are not comparable with the earlier 20-item figures.

| Ranking | Dataset | Questions | Top-1 | Top-3 | Top-5 |
|---|---|---|---|---|---|
| Word search (current) | holdout | 50 | 0.50 | 0.62 | 0.68 |
| Reranked, all-minilm | holdout | 50 | 0.62 | 0.74 | 0.80 |
| Reranked, nomic-embed-text | holdout | 50 | 0.70 | 0.82 | 0.82 |
| Word search (current) | confirmation 01–20 | 20 | 0.50 | 0.65 | 0.80 |
| Reranked, all-minilm | confirmation 01–20 | 20 | 0.85 | 1.00 | 1.00 |
| Reranked, nomic-embed-text | confirmation 01–20 | 20 | 0.85 | 1.00 | 1.00 |
| Word search (current) | confirmation 21–50 | 30 | 0.07 | 0.20 | 0.33 |
| Reranked, all-minilm | confirmation 21–50 | 30 | 0.30 | 0.43 | 0.47 |
| Reranked, nomic-embed-text | confirmation 21–50 | 30 | 0.33 | 0.47 | 0.53 |
| Word search (current) | confirmation, all | 50 | 0.24 | 0.38 | 0.52 |
| Reranked, all-minilm | confirmation, all | 50 | 0.52 | 0.66 | 0.68 |
| Reranked, nomic-embed-text | confirmation, all | 50 | 0.54 | 0.68 | 0.72 |

Reranking can only reorder the 20 word-search candidates: the keyed article is among them for 0.88 of holdout and 0.76
of confirmation questions, which caps top-5.

**Cost** (4-core Intel Xeon 2.1 GHz, CPU only, Ollama 0.40.16):

| Model | Download | Article vectors (once) | Median time per question | Added over word search | First question, model not loaded |
|---|---|---|---|---|---|
| Word search | none | none | 0.063 s | — | — |
| all-minilm | 45 MB | 41 s | 0.083 s | +0.02 s | 0.37 s |
| nomic-embed-text | 274 MB | 420 s | 0.12 s | +0.06 s | 0.67 s |

Both models' vectors together take 7.5 MB in `data/corpus/embeddings.sqlite3` (not committed; built locally). Files:
`word-*.json`, `rerank-<model>-*.json` (per-question rankings and times). Reproduce:
`python scripts/evaluate_retrieval.py --dataset holdout|confirmation [--rerank all-minilm|nomic-embed-text]`.
