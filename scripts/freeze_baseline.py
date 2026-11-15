import json,subprocess,datetime
from pathlib import Path
from aquinas.runtime import post
out=Path('results/baseline-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));out.mkdir(parents=True,exist_ok=False)
r=post('http://127.0.0.1:11434/api/show',{'model':'lfm3-official:1.7b'})
(out/'show.json').write_text(json.dumps(r,indent=2));(out/'Modelfile').write_text(r.get('modelfile',''))
try:
 (out/'ollama-version.txt').write_text(subprocess.check_output(['ollama','--version'],text=True))
except FileNotFoundError:pass
print(out)
