"""Diagnostic ablation: normal retrieval vs exact keyed reference, not a blind test.
Keyed-reference selection uses only source IDs, never answer text. This is openly
oracle-assisted diagnosis; do not report it as production retrieval performance.
"""
import argparse
import datetime
import json
from pathlib import Path
from aquinas.core import read_jsonl,digest
from aquinas.runtime import ask,post
ITEMS=['natural_law-08','natural_law-09','natural_law-10']

def keyed_context(articles,refs):
    passages=[]
    for ref in refs:
        row=articles[ref]
        for n,s in enumerate(row['sections']):
            if s['kind']=='respondeo':passages.append({'id':f'{ref}::{n}:full','article_id':ref,'source_id':row['source_id'],'kind':'respondeo','text':s['text'],'complete_section':True,'rank':None})
    return {'passages':passages,'omitted':[],'policy':'ORACLE_KEYED_SOURCE_DIAGNOSTIC_ONLY','answer_key_text_supplied':False,'blind_evaluation':False}

def run(root,out,model,seeds,host,num_predict):
    root=Path(root);out=Path(out)
    if out.exists():raise ValueError('Output exists; choose a fresh path')
    keys={r['id']:r for r in read_jsonl(root/'data/evaluation/holdout.jsonl')}
    articles={r['id']:r for r in read_jsonl(root/'data/corpus/articles.jsonl')}
    out.parent.mkdir(parents=True,exist_ok=True)
    show=post(host.rstrip('/')+'/api/show',{'model':model})
    manifest={'purpose':'Retrieval vs source-interpretation diagnostic; oracle arm is not blind/production evaluation','items':ITEMS,'seeds':seeds,'num_predict':num_predict,'model':model,'model_show':show,'dataset_sha256':digest((root/'data/evaluation/holdout.jsonl').read_bytes()),'answer_key_text_sent_to_model':False,'pipeline_version':'0.1.2'}
    with Path(str(out)+'.manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
    with out.open('x') as f:
        for item in ITEMS:
            row=keys[item]
            for seed in seeds:
                for condition in ['normal_retrieval','oracle_keyed_source']:
                    override=keyed_context(articles,row['source_refs']) if condition=='oracle_keyed_source' else None
                    try:
                        result=ask(root,row['question'],'rag',model,seed,host,context_override=override,num_predict=num_predict)
                        result.update({'item_id':item,'condition':condition,'oracle_assisted':override is not None,'words':len(result['response'].split()),'grading_status':'UNREVIEWED'})
                        done=result['raw'].get('done_reason')
                    except Exception as e:
                        result={'item_id':item,'seed':seed,'condition':condition,'error':str(e)};done='ERROR'
                    f.write(json.dumps(result,ensure_ascii=False)+'\n');f.flush()
                    print(item,seed,condition,done,flush=True)
    print('Saved:',out)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default='.');p.add_argument('--out');p.add_argument('--model',default='lfm3-official:1.7b');p.add_argument('--host',default='http://127.0.0.1:11434');p.add_argument('--seeds',nargs='+',type=int,default=[11,22,33]);p.add_argument('--max-tokens',type=int,default=1536);a=p.parse_args()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run(a.root,a.out or f'results/grounding-012-{stamp}.jsonl',a.model,a.seeds,a.host,a.max_tokens)
if __name__=='__main__':main()
