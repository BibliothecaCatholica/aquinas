# Aquinas Neuron load test (November 15, 2026)

Final release files (Q4_K_M `030bd408…`, Q8_0 `f59ecf6f…`). Ollama 0.40.16 in a private model directory (no existing
model or tag touched), 4-core CPU, no GPU. Question: the README example, "Using ST I-II q.96 a.4, when does an unjust
law bind in conscience?". Answers are verbatim and **unreviewed**; completion is not correctness.

```
create Q4_K_M exit 0
Q4_K_M plain run: 5 s, words 16, 'think' mentions 0
Q4_K_M tool --mode rag: exit 0, 14 s, words 37
create Q8_0 exit 0
Q8_0 plain run: 9 s, words 57, 'think' mentions 0
Q8_0 tool --mode rag: exit 0, 12 s, words 29
```

## Q4_K_M, plain `ollama run aquinas-neuron` (no retrieval; the model alone)

> The question requires a specific doctrinal source that is not supplied. I cannot answer from it.

## Q4_K_M, `python -m aquinas.cli ask ... --model aquinas-neuron --mode rag` (retrieved evidence)

> An unjust law binds only if it is just on its own terms—consistent with human good, the author's power, and proportionate burdens for the common good. Otherwise it does not bind in conscience. [ST I-II q.96 a.4]

## Q8_0, plain `ollama run` (no retrieval)

> An unjust law cannot be obeyed while it violates justice and moral order; obedience requires rejecting the injustice itself rather than complying with the letter of the law. This distinction is essential to distinguishing permissible action from obligation. The relevant principle depends on whether the law is imposed by legitimate authority and conforms to a just order.

## Q8_0, tool with `--mode rag`

> It binds only when it is just—ordained to the common good, within its author's power, and proportionate to the community. Otherwise it does not bind. [ST I-II q.96 a.4]
