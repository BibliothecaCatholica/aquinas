import gc
import json
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch
from aquinas.core import retrieve,retrieve_context,index,read_jsonl
from aquinas.runtime import ask
ROOT=Path(__file__).resolve().parents[1]

class ContextRegressionTests(unittest.TestCase):
    def test_opposing_view_and_rejection_stay_together(self):
        c=retrieve_context(ROOT,'ST I-II q.19 a.5 erring conscience')
        p=next(p for p in c['passages'] if p['article_id']=='ST I-II q.19 a.5')
        self.assertIn('They say,',p['text'])
        self.assertIn('But this is unreasonable.',p['text'])
        self.assertIn('every will at variance with reason',p['text'])
        self.assertTrue(p['complete_section'])
    def test_complete_source_equality_and_no_unpaired_objections(self):
        a={r['id']:r for r in read_jsonl(ROOT/'data/corpus/articles.jsonl')}
        for p in retrieve_context(ROOT,'When does an unjust law bind in conscience?')['passages']:
            self.assertEqual(p['kind'],'respondeo')
            self.assertTrue(any(p['text']==s['text'] for s in a[p['article_id']]['sections'] if s['kind']=='respondeo'))
    def test_tiny_budget_omits_instead_of_cutting(self):
        c=retrieve_context(ROOT,'ST I-II q.19 a.5',max_chars=100)
        self.assertEqual(c['passages'],[])
        self.assertTrue(c['omitted'])
    def test_primary_source_survives(self):
        c=retrieve_context(ROOT,'When does an unjust law bind in conscience?')
        self.assertEqual(c['passages'][0]['article_id'],'ST I-II q.96 a.4')
        self.assertIn('must\r\nnowise be observed',c['passages'][0]['text'])
    def test_sqlite_connections_closed(self):
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter('always',ResourceWarning)
            retrieve(ROOT,'law conscience')
            with tempfile.TemporaryDirectory() as d:
                from aquinas.core import write_jsonl
                p=Path(d)/'data/corpus';p.mkdir(parents=True)
                write_jsonl(p/'articles.jsonl',read_jsonl(ROOT/'data/corpus/articles.jsonl')[:1])
                index(d)
            gc.collect()
        self.assertFalse([w for w in ws if issubclass(w.category,ResourceWarning)])
    def test_ask_sends_full_sections(self):
        with patch('aquinas.runtime.post',return_value={'message':{'content':'Test'},'eval_count':1,'eval_duration':1000}),patch('aquinas.runtime.urllib.request.urlopen',side_effect=OSError('No server')):
            r=ask(ROOT,'ST I-II q.19 a.5 erring conscience')
        self.assertEqual(r['pipeline_version'],'0.1.2')
        self.assertIn('But this is unreasonable.',r['request']['messages'][1]['content'])
        self.assertEqual(r['context_policy']['policy'],'complete_respondeo_v1')

if __name__=='__main__':unittest.main()
