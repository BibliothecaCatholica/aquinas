import json,statistics
from pathlib import Path
from aquinas.core import read_jsonl,retrieve
rows=read_jsonl('data/evaluation/holdout.jsonl');results=[]
for r in rows:
    hits=retrieve('.',r['question'],6);ids=[h['id'].split('::')[0] for h in hits]
    results.append({'id':r['id'],'expected':r['source_refs'],'retrieved':ids,'hit_at_6':bool(set(ids)&set(r['source_refs']))})
report={'metric':'Any keyed article retrieved among six passages, not answer accuracy','questions':len(results),'hit_at_6':statistics.mean(r['hit_at_6'] for r in results),'items':results,'caveat':'Retrieval development metric uses held-out source labels. This evaluates source coverage, not philosophical correctness. Future confirmatory benchmark should be newly sealed.'}
Path('results/retrieval.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='items'},indent=2))
