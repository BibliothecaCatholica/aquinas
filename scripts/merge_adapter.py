import argparse,json
from pathlib import Path

def exact_merge(path, output, manifest):
 """Merge without PEFT, reproducibly: W + (alpha/r) * sum_k outer(B[:,k], A[k,:]), with the rank-8 sum taken in float64
 in a fixed order using element-wise operations only, then rounded once to float32. Element-wise IEEE arithmetic rounds the
 same on every x86 CPU, so two machines produce identical bytes (needed by the release workflow's checksum check)."""
 import shutil, torch
 from huggingface_hub import snapshot_download
 from safetensors import safe_open
 from safetensors.torch import save_file
 cfg=json.loads((path/'adapter_config.json').read_text())
 assert not cfg.get('use_dora') and not cfg.get('use_rslora') and not cfg.get('fan_in_fan_out') and cfg.get('bias','none')=='none'
 scale=cfg['lora_alpha']/cfg['r']
 snap=Path(snapshot_download(manifest['base'],revision=manifest['revision']))
 lora={}
 with safe_open(path/'adapter_model.safetensors','pt') as f:
  for k in f.keys():
   name,ab=k.replace('base_model.model.','',1).rsplit('.lora_',1)
   lora.setdefault(name+'.weight',{})[ab.split('.')[0]]=f.get_tensor(k).to(torch.float64)
 out,used={},set()
 with safe_open(snap/'model.safetensors','pt') as f:
  for k in f.keys():
   w=f.get_tensor(k).to(torch.float64)
   if k in lora:
    A,B=lora[k]['A'],lora[k]['B'];delta=torch.zeros_like(w)
    for i in range(A.shape[0]):delta=delta+B[:,i:i+1]*A[i:i+1,:]
    w=w+scale*delta;used.add(k)
   out[k]=w.to(torch.float32).contiguous()
 assert used==set(lora),'adapter tensors without a base weight: %r'%sorted(set(lora)-used)
 Path(output).mkdir(parents=True)
 save_file(out,str(Path(output)/'model.safetensors'),metadata={'format':'pt'})
 for name in ('config.json','generation_config.json','configuration_lfm3.py','modeling_lfm3.py','lfm3_conv.py'):
  if (snap/name).exists():shutil.copy2(snap/name,Path(output)/name)
 for name in ('tokenizer.json','tokenizer_config.json','chat_template.jinja','special_tokens_map.json'):
  if (path/name).exists():shutil.copy2(path/name,Path(output)/name)
 Path(output,'aquinas-origin.json').write_text(json.dumps(manifest,indent=2))

def main():
 p=argparse.ArgumentParser();p.add_argument('adapter');p.add_argument('output');p.add_argument('--exact',action='store_true',help='reproducible float64 merge without PEFT (used by scripts/build_gguf.sh)');a=p.parse_args()
 import torch
 from transformers import AutoModelForCausalLM,AutoTokenizer
 from peft import PeftModel
 path=Path(a.adapter);manifest=json.loads((path/'training-manifest.json').read_text())
 if manifest['smoke_only']:p.error('Synthetic smoke checkpoint cannot be deployed')
 if Path(a.output).exists():p.error('Output exists')
 if a.exact:return exact_merge(path,a.output,manifest)
 base=AutoModelForCausalLM.from_pretrained(manifest['base'],revision=manifest['revision'],trust_remote_code=True,dtype=torch.float32)
 model=PeftModel.from_pretrained(base,path).merge_and_unload();model.save_pretrained(a.output,safe_serialization=True)
 AutoTokenizer.from_pretrained(path).save_pretrained(a.output)
 # Preserve custom model code required by converters where available.
 import shutil,inspect
 for f in Path(inspect.getfile(base.__class__)).parent.glob('*.py'):shutil.copy2(f,Path(a.output)/f.name)
 Path(a.output,'aquinas-origin.json').write_text(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
