import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('adapter');p.add_argument('output');a=p.parse_args()
 import torch
 from transformers import AutoModelForCausalLM,AutoTokenizer
 from peft import PeftModel
 path=Path(a.adapter);manifest=json.loads((path/'training-manifest.json').read_text())
 if manifest['smoke_only']:p.error('Synthetic smoke checkpoint cannot be deployed')
 if Path(a.output).exists():p.error('Output exists')
 base=AutoModelForCausalLM.from_pretrained(manifest['base'],revision=manifest['revision'],trust_remote_code=True,dtype=torch.float32)
 model=PeftModel.from_pretrained(base,path).merge_and_unload();model.save_pretrained(a.output,safe_serialization=True)
 AutoTokenizer.from_pretrained(path).save_pretrained(a.output)
 # Preserve custom model code required by converters where available.
 import shutil,inspect
 for f in Path(inspect.getfile(base.__class__)).parent.glob('*.py'):shutil.copy2(f,Path(a.output)/f.name)
 Path(a.output,'aquinas-origin.json').write_text(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
