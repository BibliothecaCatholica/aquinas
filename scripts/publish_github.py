"""Publish this prepared alpha to the separate BibliothecaCatholica/aquinas repo.

Requires Git and the official GitHub CLI. Existing repositories are refused.
No website repository is changed. GitHub sign-in runs locally if needed.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

REPO='BibliothecaCatholica/aquinas'
TAG='v0.2.0-alpha.1'
ROOT=Path(__file__).resolve().parents[1]

def run(*args,capture=False):
    return subprocess.run(list(args),cwd=ROOT,check=True,text=True,stdout=subprocess.PIPE if capture else None).stdout

def archive_files():
    for f in sorted(ROOT.rglob('*')):
        if not f.is_file():continue
        parts=f.relative_to(ROOT).parts
        if any(part in {'.git','.venv','.train-venv','__pycache__','dist','build','checkpoints','merged'} or part.endswith('.egg-info') for part in parts):continue
        if parts[:2]==('data','corpus') or f.suffix=='.pyc':continue
        if parts[0]=='results' and len(parts)>1 and parts[1]!='source-pilot-v21' and parts[1]!='.gitkeep':continue
        yield f

def main():
    for cmd in ['git','gh']:
        if not shutil.which(cmd):raise SystemExit('Install '+cmd+' (official GitHub CLI for gh), then rerun this script.')
    auth=subprocess.run(['gh','auth','status','--hostname','github.com'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if auth.returncode:run('gh','auth','login','--hostname','github.com','--git-protocol','https','--web')
    user=json.loads(run('gh','api','user',capture=True))
    if user['login']!='BibliothecaCatholica':raise SystemExit('Sign in to the BibliothecaCatholica GitHub account before publishing; no repository was created.')
    # Refuse an existing target rather than overwrite unrelated history.
    exists=subprocess.run(['gh','repo','view',REPO,'--json','nameWithOwner'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if exists.returncode==0:raise SystemExit(REPO+' already exists. Nothing was overwritten; use a reviewed update instead.')
    sys.path.insert(0,str(ROOT))
    from aquinas.adapter import verify_adapter
    verify_adapter(ROOT/'models/source-pilot-v21')
    run(sys.executable,'-m','aquinas.cli','ingest')
    run(sys.executable,'-m','aquinas.cli','index')
    run(sys.executable,'-m','unittest','discover','-s','tests','-v')
    if not (ROOT/'.git').exists():run('git','init','-b','main')
    else:
        top=Path(run('git','rev-parse','--show-toplevel',capture=True).strip()).resolve()
        if top!=ROOT:raise SystemExit('Refusing to publish a different working tree')
        if run('git','remote',capture=True).strip():raise SystemExit('Working tree already has a remote; refusing to replace it')
    run('git','config','user.name','Bibliotheca Catholica')
    run('git','config','user.email',str(user['id'])+'+'+user['login']+'@users.noreply.github.com')
    run('git','add','.')
    if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:
        run('git','commit','-m','Release Aquinas experimental source-conditioned alpha')
    run('gh','auth','setup-git','--hostname','github.com')
    run('gh','repo','create',REPO,'--public','--source',str(ROOT),'--remote','origin','--push','--description','Local Thomistic retrieval and an experimental LFM3 LoRA adapter, with source provenance and reproducible evaluations.')
    dist=ROOT/'dist';dist.mkdir(exist_ok=True);asset=dist/'Aquinas-v0.2.0-alpha.1.zip'
    with zipfile.ZipFile(asset,'w',zipfile.ZIP_DEFLATED) as z:
        for f in archive_files():z.write(f,Path('aquinas')/f.relative_to(ROOT))
    checksum=dist/'SHA256SUMS';checksum.write_text(hashlib.sha256(asset.read_bytes()).hexdigest()+'  '+asset.name+'\n')
    run('gh','release','create',TAG,str(asset),str(checksum),'--repo',REPO,'--target','main','--prerelease','--title','Aquinas v0.2.0 alpha 1 — experimental local study tool','--notes-file',str(ROOT/'docs/RELEASE.md'))
    run('gh','repo','view',REPO,'--json','url','--jq','.url')
    run('gh','release','view',TAG,'--repo',REPO,'--json','url','--jq','.url')
    return 0

if __name__=='__main__':sys.exit(main())
