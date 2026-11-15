import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from aquinas.core import digest,read_jsonl,ingest,index,retrieve,validate_dataset,parse_summa
from aquinas.runtime import ask
from aquinas.evaluation import citation_audit,benchmark,summarize,apply_grades
ROOT=Path(__file__).resolve().parents[1]

class CorpusTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=read_jsonl(ROOT/'data/corpus/articles.jsonl');cls.byid={r['id']:r for r in cls.rows}
 def test_complete_article_counts(self):
  self.assertEqual(sum(r['part']=='I' for r in self.rows),584);self.assertEqual(sum(r['part']=='I-II' for r in self.rows),619)
 def test_unique_ids(self):self.assertEqual(len(self.rows),len(self.byid))
 def test_source_bytes_and_offsets(self):
  manifest=json.loads((ROOT/'data/sources.json').read_text())
  for src in manifest:
   raw=(ROOT/src['path']).read_bytes();self.assertEqual(digest(raw),src['sha256']);text=raw.decode('utf-8-sig')
   for r in self.rows:
    if r['source_id']!=src['id']:continue
    self.assertEqual(r['text'],text[r['start']:r['end']])
    for s in r['sections']:self.assertEqual(s['text'],text[s['start']:s['end']])
 def test_objection_answer_and_replies_separate(self):
  kinds=[s['kind'] for s in self.byid['ST I-II q.96 a.4']['sections']]
  self.assertEqual(kinds.count('objection'),3);self.assertEqual(kinds.count('reply'),3);self.assertEqual(kinds.count('respondeo'),1);self.assertEqual(kinds.count('sed_contra'),1)
 def test_recorded_numbering_discrepancy(self):
  r=self.byid['ST I q.42 a.4'];self.assertEqual(r['printed_question'],4);self.assertTrue(r['metadata_note']);self.assertIn('Q. 4, Art. 4',r['text'])
 def test_implicit_articles(self):
  for ref in ['ST I q.71 a.1','ST I q.72 a.1','ST I-II q.23 a.1']:self.assertIsNone(self.byid[ref]['printed_article'])
 def test_source_integrity_guard(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'data').mkdir();(p/'data/raw').mkdir();(p/'data/raw/source.txt').write_text('tamper')
   (p/'data/sources.json').write_text(json.dumps([{'path':'data/raw/source.txt','sha256':'wrong','id':'test'}]))
   with self.assertRaisesRegex(ValueError,'hash changed'):ingest(p)
 def test_license_not_in_final_article(self):self.assertNotIn('END OF THE PROJECT GUTENBERG',self.rows[-1]['text'])
 def test_dataset_disjoint_and_evidence_valid(self):
  r=validate_dataset(ROOT);self.assertEqual(r['holdout'],50);self.assertTrue(r['article_disjoint'])
 def test_five_balanced_categories(self):
  from collections import Counter
  c=Counter(r['category'] for r in read_jsonl(ROOT/'data/evaluation/holdout.jsonl'));self.assertEqual(len(c),5);self.assertEqual(set(c.values()),{10})
 def test_search_excludes_query_syntax(self):
  hits=retrieve(ROOT,'" OR NOT *');self.assertIsInstance(hits,list)
  self.assertEqual(retrieve(ROOT,'" * ()'),[])
 def test_source_search(self):
  hits=retrieve(ROOT,'human law binds conscience unjust scandal disturbance',6)
  self.assertTrue(any(h['id'].startswith('ST I-II q.96 a.4::') for h in hits))
 def test_returns_original_chunk(self):
  for h in retrieve(ROOT,'faith reason revelation',6):self.assertIn(h['text'],self.byid[h['id'].split('::')[0]]['text'])

class RuntimeTests(unittest.TestCase):
 def fake(self,url,payload):return {'message':{'content':'Test answer'},'eval_count':20,'eval_duration':1000000000}
 def test_baseline_has_no_system_or_retrieval(self):
  with patch('aquinas.runtime.post',side_effect=self.fake):r=ask(ROOT,'hello','baseline')
  self.assertEqual(len(r['request']['messages']),1);self.assertEqual(r['retrieved'],[]);self.assertEqual(r['tokens_per_second'],20)
 def test_prompt_controls_consistent(self):
  with patch('aquinas.runtime.post',side_effect=self.fake):r=ask(ROOT,'hello','prompt',seed=33)
  self.assertEqual(r['request']['options']['seed'],33);self.assertFalse(r['request']['think']);self.assertEqual(r['request']['messages'][0]['role'],'system')
 def test_rag_sends_evidence(self):
  with patch('aquinas.runtime.post',side_effect=self.fake):r=ask(ROOT,'human law conscience','rag')
  self.assertTrue(r['retrieved']);self.assertIn('Reference excerpts',r['request']['messages'][1]['content'])
 def test_citation_audit_is_not_semantic_grading(self):
  a=citation_audit('ST I q.2 a.3 and ST I q.999 a.1',{'ST I q.2 a.3'},set());self.assertEqual(a['missing_from_corpus'],['ST I q.999 a.1']);self.assertEqual(a['semantic_verdict'],'requires_human_review')
 def test_benchmark_persists_without_answer_keys(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'run.jsonl'
   with patch('aquinas.evaluation.post',return_value={'details':{}}),patch('aquinas.runtime.post',side_effect=self.fake):benchmark(ROOT,out,['baseline'],['test'],[11],'http://fake',1)
   r=read_jsonl(out)[0];self.assertNotIn('answer_key',json.dumps(r['request']));self.assertIsNone(r['human_scores']);self.assertIsNone(summarize(out)['baseline']['accuracy'])
 def test_grading_requires_rationale(self):
  from aquinas.core import write_jsonl
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);write_jsonl(p/'r',[{'item_id':'x','mode':'rag','seed':11}]);write_jsonl(p/'g',[{'item_id':'x','mode':'rag','seed':11,'scores':{k:2 for k in ['accuracy','premise_fidelity','logical_consistency','source_fidelity','instruction_following']}}])
   with self.assertRaisesRegex(ValueError,'Reviewer'):apply_grades(p/'r',p/'g',p/'out')
 def test_training_mask(self):
  from scripts.train import encode_example
  class Tokenizer:
   def apply_chat_template(self,messages,tokenize,add_generation_prompt):return 'P' if add_generation_prompt else 'Panswer'
   def __call__(self,text,add_special_tokens):return {'input_ids':list(text.encode())}
  ids,labels=encode_example(Tokenizer(),{'messages':[{'role':'user','content':'Q'},{'role':'assistant','content':'A'}]},20)
  self.assertEqual(labels[0],-100);self.assertEqual(labels[1:],ids[1:])

if __name__=='__main__':unittest.main()
