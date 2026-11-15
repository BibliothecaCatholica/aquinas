"""Restore only manifest-listed source editions, checking hashes before installing bytes."""
import hashlib,json,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for src in json.loads((root/'data/sources.json').read_text()):
 path=root/src['path']
 if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==src['sha256']:
  print(src['id'],'already verified');continue
 raw=urllib.request.urlopen(src['url'],timeout=90).read()
 if hashlib.sha256(raw).hexdigest()!=src['sha256']:raise SystemExit('Upstream changed: '+src['id']+'. Review a new edition explicitly; existing file untouched.')
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);print(src['id'],'restored')
