"""Retrieval measurement: is the keyed article among the first 1, 3, or 5 articles that the tool would send as evidence?

Articles are ranked exactly as aquinas.core.retrieve_context ranks them (explicit ST references first, then the search
ranking of respondeo passages, de-duplicated by article). This measures retrieval only, not answer accuracy.

  python scripts/evaluate_retrieval.py [--dataset holdout|confirmation] [--out results/retrieval.json]
"""
import argparse, json, re, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aquinas.core import read_jsonl, rank_articles  # noqa: E402

DATA = {'holdout': 'data/evaluation/holdout.jsonl', 'confirmation': 'data/evaluation/confirmation.jsonl'}


def measure(root, rows):
    items = []
    for r in rows:
        ranked = rank_articles(root, r['question'], 5)
        keyed = set(r['source_refs'])
        pos = next((i + 1 for i, a in enumerate(ranked) if a in keyed), None)
        items.append({'id': r['id'], 'expected': r['source_refs'], 'ranked': ranked, 'position': pos})
    rate = lambda k: round(statistics.mean(1.0 if i['position'] and i['position'] <= k else 0.0 for i in items), 3)
    return {'questions': len(items), 'top1': rate(1), 'top3': rate(3), 'top5': rate(5), 'items': items}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', choices=sorted(DATA), default='holdout')
    ap.add_argument('--out')
    a = ap.parse_args()
    rep = measure('.', read_jsonl(DATA[a.dataset]))
    rep = dict({'metric': 'keyed article among the first k articles sent as evidence; retrieval only, not answer accuracy',
                'dataset': a.dataset}, **rep)
    if a.out:
        Path(a.out).write_text(json.dumps(rep, indent=1) + '\n')
    print(json.dumps({k: v for k, v in rep.items() if k != 'items'}))
