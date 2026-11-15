"""Optional meaning-based reranking with a small embedding model served by Ollama.

Word search (SQLite FTS5) stays the default. When reranking is asked for, the first CANDIDATES distinct articles from
word search are reordered by cosine similarity between the question and each article (its title and the opening of its
respondeo), using vectors computed once with `aquinas embed`. If Ollama is not reachable, the model is not installed, or
the vectors have not been built for that model, ranking falls back to word search and says why. Standard library only.
"""
import array
import json
import math
import os
import sqlite3
import urllib.error
import urllib.request
from contextlib import closing
from pathlib import Path

DEFAULT_MODEL = 'nomic-embed-text'
CANDIDATES = 20
DOC_CHARS = 1500
# Some embedding models are trained with task prefixes; others take plain text.
PREFIXES = {'nomic-embed-text': ('search_query: ', 'search_document: ')}


def host():
    h = os.environ.get('OLLAMA_HOST', '127.0.0.1:11434')
    return h if h.startswith('http') else 'http://' + h


def store_path(root):
    return Path(root) / 'data/corpus/embeddings.sqlite3'


def _base(model):
    return model.split(':')[0]


def embed(texts, model, timeout=120):
    """Vectors for texts from Ollama's /api/embed, unit-normalized. Raises OSError when Ollama cannot serve them."""
    body = json.dumps({'model': model, 'input': texts, 'truncate': True}).encode()
    req = urllib.request.Request(host() + '/api/embed', body, {'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.load(r)['embeddings']
    except urllib.error.HTTPError as e:
        raise OSError(f'Ollama could not embed with {model}: HTTP {e.code} {e.read().decode(errors="replace")[:200]}')
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise OSError(f'Ollama is not reachable at {host()}: {e}')
    return [_unit(v) for v in out]


def _unit(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def document(article):
    title = ' '.join(s['text'].strip() for s in article['sections'] if s['kind'] == 'preamble')
    resp = ' '.join(s['text'].strip() for s in article['sections'] if s['kind'] == 'respondeo')
    return (title + '\n' + resp)[:DOC_CHARS]


def build(root, model=DEFAULT_MODEL, batch=32, progress=None):
    """Embed every article once and store the vectors for this model. Returns the number of articles embedded."""
    from .core import read_jsonl
    rows = read_jsonl(Path(root) / 'data/corpus/articles.jsonl')
    doc_prefix = PREFIXES.get(_base(model), ('', ''))[1]
    with closing(sqlite3.connect(store_path(root))) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS vectors (model TEXT, article TEXT, dims INTEGER, vec BLOB, PRIMARY KEY (model, article))')
        db.execute('DELETE FROM vectors WHERE model = ?', (model,))
        for i in range(0, len(rows), batch):
            part = rows[i:i + batch]
            vecs = embed([doc_prefix + document(r) for r in part], model)
            db.executemany('INSERT INTO vectors VALUES (?,?,?,?)',
                           [(model, r['id'], len(v), array.array('f', v).tobytes()) for r, v in zip(part, vecs)])
            if progress:
                progress(min(i + batch, len(rows)), len(rows))
    return len(rows)


def load(root, model, ids):
    path = store_path(root)
    if not path.exists():
        return {}
    with closing(sqlite3.connect(f'file:{path}?mode=ro', uri=True)) as db:
        marks = ','.join('?' * len(ids))
        rows = db.execute(f'SELECT article, vec FROM vectors WHERE model = ? AND article IN ({marks})', [model, *ids])
        return {a: array.array('f', v).tolist() for a, v in rows}


def rerank(root, query, ranked, model=DEFAULT_MODEL):
    """Reorder word-search article ids by meaning. Returns (ids, note); note is None when reranking ran.

    Articles named explicitly in the question keep their place at the front, as in word search."""
    import re
    pinned = []
    for part, q, a in re.findall(r'ST\s+(I-II|II-II|III|I)\s+q\.\s*(\d+)\s+a\.\s*(\d+)', query):
        ref = f'ST {part} q.{q} a.{a}'
        if ref in ranked and ref not in pinned:
            pinned.append(ref)
    rest = [r for r in ranked if r not in pinned]
    vecs = load(root, model, rest)
    if not rest:
        return ranked, None
    if len(vecs) < len(rest):
        return ranked, f'word search only: article vectors for {model} are missing; run `aquinas embed --model {model}`'
    try:
        q = embed([PREFIXES.get(_base(model), ('', ''))[0] + query], model)[0]
    except OSError as e:
        return ranked, 'word search only: ' + str(e)
    score = {r: sum(a * b for a, b in zip(q, vecs[r])) for r in rest}
    return pinned + sorted(rest, key=lambda r: -score[r]), None
