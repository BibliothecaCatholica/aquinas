import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from aquinas.core import read_jsonl
from aquinas.runtime import ask
from scripts.grounding_diagnostic import run,keyed_context
ROOT=Path(__file__).resolve().parents[1]
class GroundingDiagnosticTests(unittest.TestCase):
    def test_prompt_has_canonical_refs_without_internal_offsets(self):
        with patch('aquinas.runtime.post',return_value={'message':{'content':'Mock answer'}}),patch('aquinas.runtime.urllib.request.urlopen',side_effect=OSError('No live server')):
            r=ask(ROOT,'When does an unjust law bind in conscience?')
        evidence=r['request']['messages'][1]['content']
        self.assertIn('[ST I-II q.96 a.4; complete respondeo]',evidence)
        self.assertNotIn('::',evidence)
    def test_oracle_supplies_only_exact_requested_article(self):
        a={r['id']:r for r in read_jsonl(ROOT/'data/corpus/articles.jsonl')}
        c=keyed_context(a,['ST I-II q.96 a.4'])
        self.assertEqual({p['article_id'] for p in c['passages']},{'ST I-II q.96 a.4'})
        self.assertFalse(c['answer_key_text_supplied']);self.assertFalse(c['blind_evaluation'])
    def test_diagnostic_separates_conditions_and_preserves_budget(self):
        def fake(url,payload):return {'message':{'content':'Mock answer'},'done_reason':'stop','eval_count':2,'eval_duration':1000}
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'test.jsonl'
            with patch('scripts.grounding_diagnostic.post',return_value={'model':'mock'}),patch('aquinas.runtime.post',side_effect=fake),patch('aquinas.runtime.urllib.request.urlopen',side_effect=OSError('No live server')):
                run(ROOT,path,'mock',[11],'http://fake',1536)
            rows=read_jsonl(path);self.assertEqual(len(rows),6)
            self.assertEqual({r['condition'] for r in rows},{'normal_retrieval','oracle_keyed_source'})
            self.assertTrue(all(r['request']['options']['num_predict']==1536 for r in rows))
            self.assertTrue(all('answer_key' not in json.dumps(r['request']) for r in rows))
            with self.assertRaisesRegex(ValueError,'exists'):run(ROOT,path,'mock',[11],'http://fake',1536)
if __name__=='__main__':unittest.main()
