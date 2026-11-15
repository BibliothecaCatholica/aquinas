"""The fresh confirmation set: 50 articles from one seeded draw, none in training or holdout."""
import glob, json, random, re, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = r'ST (?:I-II|II-II|III|I) q\.\d+ a\.\d+'


class ConfirmationSet(unittest.TestCase):
    def test_fifty_items_from_one_seeded_draw(self):
        rows = [json.loads(l) for l in (ROOT / 'data/evaluation/confirmation.jsonl').read_text().splitlines() if l.strip()]
        self.assertEqual([r['id'] for r in rows], ['confirmation-%02d' % i for i in range(1, 51)])
        refs = [r['source_refs'][0] for r in rows]
        corpus = ROOT / 'data/corpus/articles.jsonl'
        if not corpus.exists():
            self.skipTest('corpus not ingested')
        ids = [json.loads(l)['id'] for l in corpus.read_text().splitlines()]
        used = set()
        for f in glob.glob(str(ROOT / 'data/training/*.jsonl')) + [str(ROOT / 'data/evaluation/holdout.jsonl')]:
            used |= set(re.findall(REF, Path(f).read_text()))
        self.assertFalse(set(refs) & used)
        draw = random.Random(20261115).sample(sorted(i for i in ids if i not in used), 50)
        self.assertEqual(sorted(refs[:20]), sorted(draw[:20]))
        self.assertEqual(sorted(refs), sorted(draw))
        self.assertEqual(len(set(r['question'].lower() for r in rows)), 50)


if __name__ == '__main__':
    unittest.main()
