import hashlib
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

HEADER = re.compile(r'^([A-Z -]+) ARTICLE \[((?:I(?:-II)?[,.] )?)Q[.,] (\d+), (?:[Aa]rt\.?|A\.) (\d+)\][ \t\r]*$', re.M)
SECTION = re.compile(r'(?m)^((?:_?Objection|Obj\.) \d+|_?On the contrary|_?I answer that|(?:_?Reply to Objection|Reply Obj\.) \d+)[,:._ ]*')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]

def write_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows))

def parse_summa(raw, source_id):
    """Slice exact decoded strings; byte-original source is retained separately."""
    text = raw.decode('utf-8-sig')
    end = text.find('*** END OF THE PROJECT GUTENBERG')
    if end < 0:
        raise ValueError('Missing Gutenberg end marker; refuse uncertain source boundary')
    text = text[:end]
    heads = list(HEADER.finditer(text))
    if not heads:
        raise ValueError('No supported Summa article headings')
    records = []
    ordinals = {v:i+1 for i,v in enumerate(['FIRST','SECOND','THIRD','FOURTH','FIFTH','SIXTH','SEVENTH','EIGHTH','NINTH','TENTH','ELEVENTH','TWELFTH','THIRTEENTH','FOURTEENTH','FIFTEENTH','SIXTEENTH','SEVENTEENTH','EIGHTEENTH','NINETEENTH','TWENTIETH'])}
    for i, h in enumerate(heads):
        stop = heads[i+1].start() if i+1 < len(heads) else len(text)
        body = text[h.end():stop]
        # A following question's preamble is not part of this article.
        nextq = re.search(r'(?m)^QUESTION \d+\s*$', body)
        if nextq:
            stop = h.end()+nextq.start()
            body = text[h.end():stop]
        part = 'I-II' if source_id=='pg17897' else 'I'
        article = ordinals[h[1]]
        question = 42 if source_id=='pg17611' and h[3]=='4' and article==4 and 'Whether the Son Is Equal' in body else int(h[3])
        pid = f'ST {part} q.{question} a.{article}'
        marks = list(SECTION.finditer(body))
        sections = [{'kind':'heading','start':h.start(),'end':h.end(),'text':h[0]}]
        first = marks[0].start() if marks else len(body)
        sections.append({'kind':'preamble','start':h.end(),'end':h.end()+first,'text':body[:first]})
        for j,m in enumerate(marks):
            e=marks[j+1].start() if j+1<len(marks) else len(body)
            label=m[1].strip('_')
            kind=('objection' if label.startswith(('Objection','Obj.')) else 'sed_contra' if label=='On the contrary' else 'respondeo' if label=='I answer that' else 'reply')
            sections.append({'kind':kind,'label':label,'start':h.end()+m.start(),'end':h.end()+e,'text':body[m.start():e]})
        records.append({'id':pid,'source_id':source_id,'part':part,'question':question,'printed_question':int(h[3]),'article':article,'printed_article':int(h[4]),'metadata_note':('Ordinal heading and bracket disagree; ordinal used for index only, raw preserved' if article!=int(h[4]) or question!=int(h[3]) else None),'start':h.start(),'end':stop,'text':text[h.start():stop],'sha256':digest(text[h.start():stop].encode()),'sections':sections})
    # Three articles lack an ARTICLE heading in these specific transcriptions.
    missing = [71,72] if source_id=='pg17611' else [23]
    part = 'I' if source_id=='pg17611' else 'I-II'
    for question in missing:
        m = re.search(r'(?m)^QUESTION '+str(question)+r'[ \t\r]*$', text)
        if not m: raise ValueError('Missing supported implicit article heading')
        ends = [h.start() for h in heads if h.start()>m.start()]
        qnext=re.search(r'(?m)^QUESTION \d+[ \t\r]*$',text[m.end():])
        if qnext: ends.append(m.end()+qnext.start())
        stop=min(ends) if ends else len(text)
        body=text[m.end():stop];marks=list(SECTION.finditer(body));sections=[]
        for j,mark in enumerate(marks):
            e=marks[j+1].start() if j+1<len(marks) else len(body)
            label=mark[1].strip('_')
            kind='reply' if label.startswith('Reply') else 'objection' if label.startswith(('Obj.','Objection')) else 'respondeo' if label=='I answer that' else 'sed_contra'
            sections.append({'kind':kind,'label':label,'start':m.end()+mark.start(),'end':m.end()+e,'text':body[mark.start():e]})
        records.append({'id':f'ST {part} q.{question} a.1','source_id':source_id,'part':part,'question':question,'article':1,'printed_article':None,'metadata_note':'No ARTICLE heading; article 1 inferred from one-article question or position before SECOND ARTICLE; raw preserved','start':m.start(),'end':stop,'text':text[m.start():stop],'sha256':digest(text[m.start():stop].encode()),'sections':sections})
    return sorted(records,key=lambda r:(r['question'],r['article']))

def ingest(root):
    root=Path(root)
    manifest=json.loads((root/'data/sources.json').read_text())
    allrows=[]
    for src in manifest:
        raw=(root/src['path']).read_bytes()
        if digest(raw)!=src['sha256']:
            raise ValueError('Source hash changed: '+src['id'])
        rows=parse_summa(raw,src['id'])
        if len(rows)!=src['expected_articles']:
            raise ValueError(f"Article count mismatch: {src['id']}: {len(rows)}")
        allrows.extend(rows)
    ids=[r['id'] for r in allrows]
    if len(ids)!=len(set(ids)):
        raise ValueError('Duplicate article IDs')
    write_jsonl(root/'data/corpus/articles.jsonl',allrows)
    return allrows

def index(root):
    root=Path(root); rows=read_jsonl(root/'data/corpus/articles.jsonl')
    path=root/'data/corpus/index.sqlite3'
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('DROP TABLE IF EXISTS passages')
        # Each passage also carries its article's title (the "Whether ...?" preamble) in a separate, searchable column,
        # so a question can match the article it asks about even when the respondeo words differ. Returned text is unchanged.
        db.execute('CREATE VIRTUAL TABLE passages USING fts5(id UNINDEXED, source_id UNINDEXED, kind UNINDEXED, text, title, tokenize="porter unicode61")')
        for r in rows:
            title=' '.join(s['text'].strip() for s in r['sections'] if s['kind']=='preamble')
            for n,s in enumerate(r['sections']):
                if s['kind'] in ('heading','preamble'): continue
                # Split only at paragraph boundaries; preserve text in each returned chunk.
                paragraphs=re.split(r'(?<=\n)\r?\n',s['text'])
                chunk=''; chunks=[]
                for paragraph in paragraphs:
                    if chunk and len(chunk)+len(paragraph)>2400:
                        chunks.append(chunk);chunk=''
                    chunk+=paragraph
                if chunk:chunks.append(chunk)
                for c,t in enumerate(chunks):
                    db.execute('INSERT INTO passages VALUES(?,?,?,?,?)',(f"{r['id']}::{n}:{c}",r['source_id'],s['kind'],t,title))
    return len(rows)

TITLE_WEIGHT=2.0

def retrieve(root, query, k=6, kind=None):
    tokens=re.findall(r'[A-Za-z0-9]+',query.lower())
    stop={'the','a','an','is','are','of','to','in','and','or','does','what','whether','that','for','it','can','be','do',
          # question wording that names the author or asks for a form of answer, not the topic
          'aquinas','his','according','give','rather','than','conclusion','objection','objections','view','thomas','for'}
    terms=list(dict.fromkeys(t for t in tokens if t not in stop and len(t)>2))[:32]
    if not terms:return []
    expr=' OR '.join('"'+t+'"' for t in terms)
    path=Path(root)/'data/corpus/index.sqlite3'
    if not path.exists():raise ValueError('Run aquinas ingest and aquinas index first')
    with closing(sqlite3.connect(f'file:{path}?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row
        predicate=' AND kind = ?' if kind else ''
        params=(expr,kind,k) if kind else (expr,k)
        # bm25 column weights: id, source_id, kind (unindexed), text 1.0, title TITLE_WEIGHT
        return [dict(r) for r in db.execute('SELECT id,source_id,kind,text,bm25(passages,0,0,0,1.0,'+str(TITLE_WEIGHT)+') AS rank FROM passages WHERE passages MATCH ?'+predicate+' ORDER BY rank LIMIT ?', params)]

def validate_dataset(root):
    root=Path(root)
    articles={r['id']:r for r in read_jsonl(root/'data/corpus/articles.jsonl')}
    train=read_jsonl(root/'data/training/train.jsonl'); hold=read_jsonl(root/'data/evaluation/holdout.jsonl')
    trainrefs={ref for r in train for ref in r['source_refs']}
    evalrefs={ref for r in hold for ref in r['source_refs']}
    if trainrefs & evalrefs:raise ValueError('Training/holdout article overlap')
    questions=[r['question'].strip().lower() for r in train+hold]
    if len(questions)!=len(set(questions)):raise ValueError('Duplicate questions')
    for row in train+hold:
        for ref in row['source_refs']:
            if ref not in articles:raise ValueError('Missing source '+ref)
        for ev in row.get('evidence',[]):
            if ev['text'] not in articles[ev['ref']]['text']:raise ValueError('Unverifiable evidence')
    return {'train':len(train),'holdout':len(hold),'article_disjoint':True,'exact_evidence_verified':True,'scholarly_approval':False}


def article_candidates(root, query, articles):
    """(article id, rank) in the order retrieve_context considers them."""
    candidates=[]
    # Explicit article references are evidence requests, not inferred answer keys.
    for part,q,a in re.findall(r'ST\s+(I-II|II-II|III|I)\s+q\.\s*(\d+)\s+a\.\s*(\d+)',query):
        ref=f'ST {part} q.{q} a.{a}'
        if ref in articles:candidates.append((ref,None))
    candidates.extend((h['id'].split('::')[0],h['rank']) for h in retrieve(root,query,64,kind='respondeo'))
    return candidates


def rank_articles(root, query, n=5):
    """The first n distinct articles retrieve_context would consider (for scripts/evaluate_retrieval.py)."""
    articles={r['id']:r for r in read_jsonl(Path(root)/'data/corpus/articles.jsonl')}
    out=[]
    for ref,rank in article_candidates(root,query,articles):
        if ref not in out:out.append(ref)
        if len(out)>=n:break
    return out


def retrieve_context(root, query, max_articles=3, max_chars=18000):
    """Retrieve complete authorial sections; never cut an argument at a chunk boundary.

    Search chunks remain the relevance units, but are expanded to their entire
    respondeo before delivery. Unpaired objections are excluded from this path.
    Whole sections that exceed the budget are reported as omitted, not truncated.
    """
    articles={r['id']:r for r in read_jsonl(Path(root)/'data/corpus/articles.jsonl')}
    candidates=article_candidates(root,query,articles)
    seen=set();passages=[];omitted=[];used=0
    for ref,rank in candidates:
        if ref in seen:continue
        seen.add(ref)
        r=articles[ref]
        for n,section in enumerate(r['sections']):
            if section['kind']!='respondeo':continue
            # Include label overhead in the conservative character budget.
            cost=len(section['text'])+len(ref)+100
            if len(passages)>=max_articles:break
            if used+cost>max_chars:
                omitted.append({'article':ref,'reason':'Complete respondeo exceeds remaining character budget','characters':len(section['text'])})
                continue
            passages.append({'id':f'{ref}::{n}:full','article_id':ref,'source_id':r['source_id'],'kind':'respondeo','text':section['text'],'rank':rank,'complete_section':True})
            used+=cost
        if len(passages)>=max_articles:break
    return {'passages':passages,'omitted':omitted,'characters_with_labels':used,'budget_characters':max_chars,'policy':'complete_respondeo_v1','token_budget_verified':False}
