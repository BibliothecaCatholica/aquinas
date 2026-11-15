import json
import re
import statistics
from pathlib import Path
from .core import read_jsonl, digest
from .runtime import ask, post

DIMENSIONS=['accuracy','premise_fidelity','logical_consistency','source_fidelity','instruction_following']

def citation_audit(text,valid,supplied):
    # Only explicit canonical ST references are mechanically checked. A valid ID does NOT prove support.
    refs=re.findall(r'ST\s+(I-II|II-II|III|I)\s+q\.\s*(\d+)\s+a\.\s*(\d+)',text)
    ids=[f'ST {p} q.{q} a.{a}' for p,q,a in refs]
    return {'detected':ids,'missing_from_corpus':[r for r in ids if r not in valid],'not_supplied':[r for r in ids if r not in supplied],'semantic_verdict':'requires_human_review'}

def benchmark(root,out,modes,models,seeds,host,limit=None,dataset="holdout"):
    root=Path(root);out=Path(out)
    if out.exists():raise ValueError('Output exists; use a fresh run filename')
    items=read_jsonl(root/f'data/evaluation/{dataset}.jsonl')[:limit]
    valid={r['id'] for r in read_jsonl(root/'data/corpus/articles.jsonl')}
    frozen={'dataset_sha256':digest((root/f'data/evaluation/{dataset}.jsonl').read_bytes()),'models':{}}
    for model in set(models):
        frozen['models'][model]=post(host+'/api/show',{'model':model})
    out.parent.mkdir(parents=True,exist_ok=True)
    Path(str(out)+'.manifest.json').write_text(json.dumps(frozen,indent=2))
    with out.open('x') as f:
        for mode,model in zip(modes,models,strict=True):
            for item in items:
                for seed in seeds:
                    try:
                        r=ask(root,item['question'],mode,model,seed,host)
                        supplied={p['id'].split('::')[0] for p in r['retrieved']}
                        r.update({'item_id':item['id'],'category':item.get('category','ordinary'),'words':len(r['response'].split()),'citation_audit':citation_audit(r['response'],valid,supplied),'human_scores':None})
                    except Exception as e:r={'item_id':item['id'],'mode':mode,'model':model,'seed':seed,'error':str(e)}
                    f.write(json.dumps(r)+'\n');f.flush()

def summarize(path):
    rows=read_jsonl(path);groups={}
    for r in rows:groups.setdefault(r['mode'],[]).append(r)
    summary={}
    for mode,rs in groups.items():
        good=[r for r in rs if 'error' not in r];graded=[r for r in good if r.get('human_scores')]
        s={'runs':len(rs),'errors':len(rs)-len(good),'graded':len(graded),'accuracy':None,'mean_words':statistics.mean([r['words'] for r in good]) if good else None,'mean_wall_seconds':statistics.mean([r['wall_seconds'] for r in good]) if good else None,'mean_tokens_per_second':statistics.mean([r['tokens_per_second'] for r in good if r.get('tokens_per_second')]) if any(r.get('tokens_per_second') for r in good) else None}
        if graded:s['dimension_means']={d:statistics.mean(r['human_scores'][d] for r in graded) for d in DIMENSIONS};s['accuracy']=s['dimension_means']['accuracy']
        byitem={}
        for r in graded:byitem.setdefault(r['item_id'],[]).append(r['human_scores']['accuracy'])
        s['accuracy_score_spread_by_item']={k:max(v)-min(v) for k,v in byitem.items() if len(v)>1}
        s['promotion']='UNREVIEWED' if len(graded)!=len(rs) else 'REVIEW_REQUIRED'
        summary[mode]=s
    return summary

def apply_grades(run,grades,out):
    rows=read_jsonl(run);gs=read_jsonl(grades)
    lookup={ (g['item_id'],g['mode'],g['seed']):g for g in gs}
    if len(lookup)!=len(gs):raise ValueError('Duplicate grades')
    runkeys={(r['item_id'],r['mode'],r['seed']) for r in rows}
    if set(lookup)-runkeys:raise ValueError('Grades contain unknown run identifiers')
    for r in rows:
        g=lookup.get((r['item_id'],r['mode'],r['seed']))
        if not g:continue
        if any(type(g['scores'].get(d)) is not int or not 0<=g['scores'][d]<=2 for d in DIMENSIONS):raise ValueError('Scores must be integers 0..2')
        if not g.get('reviewer') or not g.get('rationale'):raise ValueError('Reviewer and rationale required')
        r['human_scores']=g['scores'];r['reviewer']=g['reviewer'];r['rationale']=g['rationale'];r['failure_flags']=g.get('failure_flags',[])
    from .core import write_jsonl
    if Path(out).exists():raise ValueError('Output exists')
    write_jsonl(out,rows)
