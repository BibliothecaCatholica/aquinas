import argparse
import json
from pathlib import Path
from .core import ingest,index,retrieve,validate_dataset
from .hardware import diagnose
from .runtime import ask
from .evaluation import benchmark,summarize,apply_grades

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default='.')
    sub=p.add_subparsers(dest='cmd',required=True)
    for c in ['ingest','index','validate','diagnose']:sub.add_parser(c)
    for c in ['search','ask']:
        s=sub.add_parser(c);s.add_argument('question')
        if c=='ask':
            s.add_argument('--mode',choices=['baseline','prompt','rag','trained'],default='rag');s.add_argument('--model',default='lfm3-official:1.7b');s.add_argument('--host',default='http://127.0.0.1:11434');s.add_argument('--seed',type=int,default=11);s.add_argument('--plain',action='store_true');s.add_argument('--save')
    s=sub.add_parser('benchmark');s.add_argument('--out',required=True);s.add_argument('--modes',nargs='+',default=['baseline','prompt','rag']);s.add_argument('--models',nargs='+',default=['lfm3-official:1.7b']*3);s.add_argument('--seeds',nargs='+',type=int,default=[11,22,33]);s.add_argument('--host',default='http://127.0.0.1:11434');s.add_argument('--limit',type=int);s.add_argument('--dataset',choices=['holdout','ordinary'],default='holdout')
    s=sub.add_parser('report');s.add_argument('run');s.add_argument('--out',required=True)
    s=sub.add_parser('grade');s.add_argument('run');s.add_argument('grades');s.add_argument('--out',required=True)
    a=p.parse_args()
    if a.cmd=='ingest':r={'articles':len(ingest(a.root))}
    elif a.cmd=='index':r={'articles':index(a.root)}
    elif a.cmd=='validate':r=validate_dataset(a.root)
    elif a.cmd=='diagnose':r=diagnose(a.root)
    elif a.cmd=='search':r=retrieve(a.root,a.question)
    elif a.cmd=='ask':
        if a.save and Path(a.save).exists():p.error('Save path already exists; choose a new filename')
        r=ask(a.root,a.question,a.mode,a.model,a.seed,a.host)
        if a.save:
            Path(a.save).parent.mkdir(parents=True,exist_ok=True)
            with Path(a.save).open('x',encoding='utf-8') as f:json.dump(r,f,indent=2,ensure_ascii=False)
        if a.plain:
            print(r['response']);return
    elif a.cmd=='benchmark':
        if len(a.modes)!=len(a.models):p.error('one model per mode required')
        benchmark(a.root,a.out,a.modes,a.models,a.seeds,a.host,a.limit,a.dataset);r={'saved':a.out}
    elif a.cmd=='grade':apply_grades(a.run,a.grades,a.out);r={'saved':a.out}
    elif a.cmd=='report':
        r=summarize(a.run);Path(a.out+'.json').write_text(json.dumps(r,indent=2));Path(a.out+'.md').write_text('# Aquinas comparison\n\nHuman scores are 0–2; null means ungraded, not zero.\n\n'+ '\n\n'.join('## '+m+'\n\n```json\n'+json.dumps(s,indent=2)+'\n```' for m,s in r.items()))
    print(json.dumps(r,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
