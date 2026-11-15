"""Optional meaning-based reranking: word search stays the default and the fallback; no Ollama is needed to run these."""
import os, unittest
from pathlib import Path
from unittest import mock

from aquinas import core, rerank as R

ROOT = Path(__file__).resolve().parents[1]
Q = 'When does an unjust law bind in conscience?'


class Rerank(unittest.TestCase):
    def setUp(self):
        if not (ROOT / 'data/corpus/index.sqlite3').exists():
            self.skipTest('index not built')
        self.articles = {r['id']: r for r in core.read_jsonl(ROOT / 'data/corpus/articles.jsonl')}
        self.word = core.ordered_articles(ROOT, Q, self.articles)[0]

    def test_word_search_is_the_default(self):
        self.assertEqual(core.rank_articles(ROOT, Q, 5), self.word[:5])
        ctx = core.retrieve_context(ROOT, Q)
        self.assertEqual(ctx['ranking'], 'word search')
        self.assertNotIn('ranking_note', ctx)

    def test_missing_vectors_fall_back_to_word_search(self):
        with mock.patch.object(R, 'load', return_value={}):
            order, _, note = core.ordered_articles(ROOT, Q, self.articles, 'no-such-model')
        self.assertEqual(order, self.word)
        self.assertIn('aquinas embed --model no-such-model', note)
        with mock.patch.object(R, 'load', return_value={}):
            ctx = core.retrieve_context(ROOT, Q, rerank='no-such-model')
        self.assertEqual(ctx['ranking'], 'word search')
        self.assertIn('word search only', ctx['ranking_note'])

    def test_unreachable_ollama_falls_back_to_word_search(self):
        fake = {a: [1.0, 0.0] for a in self.word}
        with mock.patch.object(R, 'load', return_value=fake), mock.patch.dict(os.environ, {'OLLAMA_HOST': '127.0.0.1:9'}):
            order, _, note = core.ordered_articles(ROOT, Q, self.articles, 'nomic-embed-text')
        self.assertEqual(order, self.word)
        self.assertIn('not reachable', note)

    def test_reranks_only_the_candidates_by_meaning(self):
        head = self.word[:R.CANDIDATES]
        target = head[-1]
        fake = {a: ([0.0, 1.0] if a == target else [1.0, 0.0]) for a in head}
        with mock.patch.object(R, 'load', side_effect=lambda root, m, ids: {i: fake[i] for i in ids}), \
                mock.patch.object(R, 'embed', return_value=[[0.0, 1.0]]):
            order, _, note = core.ordered_articles(ROOT, Q, self.articles, 'm')
        self.assertIsNone(note)
        self.assertEqual(order[0], target)
        self.assertEqual(sorted(order[:R.CANDIDATES]), sorted(head))
        self.assertEqual(order[R.CANDIDATES:], self.word[R.CANDIDATES:])

    def test_named_articles_keep_their_place(self):
        q = 'Explain ST I-II q.96 a.4 on unjust laws'
        word = core.ordered_articles(ROOT, q, self.articles)[0]
        self.assertEqual(word[0], 'ST I-II q.96 a.4')
        with mock.patch.object(R, 'load', side_effect=lambda root, m, ids: {i: [1.0, 0.0] for i in ids}), \
                mock.patch.object(R, 'embed', return_value=[[0.0, 1.0]]):
            order = core.ordered_articles(ROOT, q, self.articles, 'm')[0]
        self.assertEqual(order[0], 'ST I-II q.96 a.4')

    def test_document_text_and_prefixes(self):
        doc = R.document(self.articles['ST I-II q.96 a.4'])
        self.assertTrue(doc.startswith('Whether'))
        self.assertLessEqual(len(doc), R.DOC_CHARS)
        self.assertEqual(R.PREFIXES['nomic-embed-text'][0], 'search_query: ')
        self.assertEqual(R._unit([3.0, 4.0]), [0.6, 0.8])


if __name__ == '__main__':
    unittest.main()
