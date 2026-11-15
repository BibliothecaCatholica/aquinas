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
