import json
import unittest
from pathlib import Path
from unittest.mock import patch
from aquinas.adapter import verify_adapter,build_messages,ADAPTER_SHA256

ROOT=Path(__file__).resolve().parents[1]
class ReleaseTests(unittest.TestCase):
    def test_uploaded_adapter_and_manifest(self):
        m=verify_adapter(ROOT/'models/source-pilot-v21')
        self.assertEqual(m['steps'],30);self.assertFalse(m['promoted'])
        self.assertEqual(json.loads((ROOT/'models/source-pilot-v21/release-manifest.json').read_text())['adapter_sha256'],ADAPTER_SHA256)
    def test_corrupt_adapter_is_refused(self):
        with patch('aquinas.adapter.ADAPTER_SHA256','0'*64):
            with self.assertRaisesRegex(ValueError,'checksum'):verify_adapter(ROOT/'models/source-pilot-v21')
    def test_rag_preserves_full_section_and_canonical_reference(self):
        section='They say X. But this is unreasonable. Aquinas concludes Y.'
        with patch('aquinas.core.retrieve_context',return_value={'passages':[{'article_id':'ST I-II q.19 a.5','text':section}]}):messages=build_messages(ROOT,'Question?',True)
        self.assertIn(section,messages[1]['content']);self.assertIn('[ST I-II q.19 a.5;',messages[1]['content'])
        self.assertEqual(messages[-1]['content'],'Question?')
    def test_source_conditioned_articles_do_not_overlap_keys(self):
        load=lambda p:[json.loads(l) for l in (ROOT/p).read_text().splitlines()]
        train=load('data/training/source-conditioned-v2.jsonl');keys=load('data/evaluation/holdout.jsonl')
        self.assertEqual(len(train),40)
        self.assertFalse({a for r in train for a in r['source_refs']}&{a for r in keys for a in r['source_refs']})
        for row in train:
            for e in row['evidence']:self.assertIn(e['text'],row['messages'][1]['content'])
if __name__=='__main__':unittest.main()
