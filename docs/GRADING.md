# Grading and promotion

The 50 questions have answer keys, exact source evidence, and item-specific failures. These are author-written draft scholarly instruments, not independently approved scholarship. Reference existence and an exact evidence substring are mechanically verified; this does not prove every interpretation is correct. Review keys alongside the whole article, especially objections and replies.

Each response receives five human scores, 0, 1, or 2:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Accuracy | Wrong conclusion or item failure | Partially correct; important distinction omitted | Correct conclusion and relevant distinctions |
| Premise fidelity | Changes a stipulated fact | Ambiguous handling of a fact | Preserves all material supplied facts |
| Logical consistency | Contradictory or conclusion lacks required premises | Gaps or equivocation | Consistent argument, limited to what premises support |
| Source fidelity | Fabricated citation/quote, reverses source | Citation exists but support unclear or attribution incomplete | Claims supported, quotation exact if used, attribution and limitations clear |
| Instruction following | Fails requested task or format | Partial compliance or unnecessary verbosity | Follows task and length/format requirements |

Hard-failure flags: fabricated_quote, fabricated_reference, forbidden_obedience, permission_obligation_confusion, premise_mutation, internal_contradiction, objection_as_conclusion. Record flags and rationale even if the overall answer sounds persuasive. Absence of a citation where none was required is not automatically a failure. A nonexistent source outside the present corpus must be researched, rather than automatically pronounced fictitious.

Canonical automatic citation checking recognizes `ST I q.2 a.3` format only. It checks local existence and presence in retrieved context; it neither proves entailment nor detects every citation style. Machine output leaves substantive grades null until a reviewer supplies them.

Grade JSONL row example (one row for every item/mode/seed):

```json
{"item_id":"natural_law-08","mode":"rag","seed":11,"reviewer":"YOUR_NAME","scores":{"accuracy":2,"premise_fidelity":2,"logical_consistency":2,"source_fidelity":2,"instruction_following":2},"failure_flags":[],"rationale":"Preserves shared benefit, distinguishes nonbinding payment from forbidden conduct, cites the correct respondeo."}
```

Blind reviewers to model/mode when feasible. Keep keys out of inference requests. Use the same seeds 11,22,33; temperature .35, context 8192, output limit 768, think=false. Measure whole request latency and Ollama decoding speed separately. Preserve model show metadata, requests, responses, finish reason, retrieval passages, dataset hash, and memory snapshots. Compare trained against prompt-only to isolate training; compare RAG against prompt-only to isolate retrieval. `trained` uses the same system prompt as `prompt` without retrieval. To test trained+RAG, run a separate fresh RAG experiment with that model and label it distinctly.

`report` aggregates dimension means and per-item accuracy-score spreads across seeds. It does not infer philosophical consistency merely from matching words. Evaluate the ten ordinary questions separately with `--dataset ordinary`.

Promotion policy: every required paired item/seed must have reviewed grades; no missing/error runs; improved accuracy on an independently sealed holdout; no increase in critical failures; no material ordinary-task or source-fidelity regression; review latency and memory costs. The software never promotes a candidate automatically. Record the human decision and evidence before deployment. The current 50-question suite also serves as a development instrument; after inspecting retrieval outcomes, create a fresh sealed confirmatory set before making public generalization claims. Source-disjointness reduces article memorization leakage, but does not remove shared concepts or baseline pretraining exposure.
