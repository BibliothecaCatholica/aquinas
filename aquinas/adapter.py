"""Run the released experimental LoRA adapter with its pinned LFM3 base."""
import argparse
import hashlib
import json
from pathlib import Path
from .runtime import SYSTEM

BASE = 'LiquidAI/LFM3-1.7B'
REVISION = '1da06bec6a819da10b54c67e5c90972b46d81871'
ADAPTER_SHA256 = '3f9f9eb50257bb734f054f810e7604c11fd1638094a6ce6d1f32807f17b7eca4'

def verify_adapter(path):
    path = Path(path)
    manifest = json.loads((path/'training-manifest.json').read_text())
    if manifest.get('smoke_only', True):raise ValueError('Synthetic or unidentified checkpoint cannot be used')
    if (manifest.get('base'), manifest.get('revision')) != (BASE, REVISION):raise ValueError('Adapter base/revision differs from the released experiment')
    digest = hashlib.sha256()
    with (path/'adapter_model.safetensors').open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):digest.update(block)
    if digest.hexdigest() != ADAPTER_SHA256:raise ValueError('Adapter checksum mismatch; restore the release file')
    return manifest

def build_messages(root, question, rag=False):
    messages = [{'role':'system','content':SYSTEM}]
    if rag:
        from .core import retrieve_context
        context = retrieve_context(root, question)
        if context['passages']:
            evidence = '\n\n'.join('['+p['article_id']+'; complete respondeo]\n'+p['text'] for p in context['passages'])
            messages.append({'role':'user','content':'Reference evidence:\n'+evidence})
    messages.append({'role':'user','content':question})
    return messages

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('question');p.add_argument('--root',default='.')
    p.add_argument('--adapter',help='Defaults to models/source-pilot-v21 under root')
    p.add_argument('--device',choices=['cpu','cuda'],default='cuda')
    p.add_argument('--rag',action='store_true');p.add_argument('--base-only',action='store_true')
    p.add_argument('--offline',action='store_true',help='Require the base to be cached; make no Hub download')
    p.add_argument('--seed',type=int,default=11);p.add_argument('--max-new-tokens',type=int,default=768)
    p.add_argument('--save',help='Optional new JSON result path')
    a=p.parse_args();root=Path(a.root).expanduser().resolve()
    adapter=Path(a.adapter).expanduser().resolve() if a.adapter else root/'models/source-pilot-v21'
    if not 1<=a.max_new_tokens<=1536:p.error('Use 1–1536 output tokens')
    if a.save and Path(a.save).exists():p.error('Save path exists; choose a new path')
    verify_adapter(adapter)
    import torch
    from transformers import AutoModelForCausalLM,AutoTokenizer,set_seed
    from peft import PeftModel
    from .transformers_backend import disable_optional_wide_conv,generation
    if a.device=='cuda' and not torch.cuda.is_available():p.error('CUDA unavailable; select --device cpu or install a matching PyTorch build')
    set_seed(a.seed)
    dtype=torch.bfloat16 if a.device=='cuda' and torch.cuda.is_bf16_supported(including_emulation=False) else torch.float32
    tokenizer=AutoTokenizer.from_pretrained(adapter,local_files_only=True,trust_remote_code=False)
    reference=AutoTokenizer.from_pretrained(root/'research/tokenizer',local_files_only=True,trust_remote_code=False)
    if tokenizer.get_vocab()!=reference.get_vocab() or tokenizer.chat_template!=reference.chat_template:raise ValueError('Released tokenizer differs from the pinned reference')
    messages=build_messages(root,a.question,a.rag)
    ids=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False)
    if len(ids)+a.max_new_tokens>8192:p.error('Complete evidence and output exceed context budget; use an explicit article or omit --rag')
    base=AutoModelForCausalLM.from_pretrained(BASE,revision=REVISION,trust_remote_code=True,dtype=dtype,attn_implementation='sdpa',local_files_only=a.offline)
    if len(tokenizer)>base.get_input_embeddings().num_embeddings:raise ValueError('Tokenizer exceeds embedding capacity')
    model=PeftModel.from_pretrained(base,adapter).to(a.device).eval()
    backend=disable_optional_wide_conv(model);model.config.use_cache=True
    if a.base_only:
        with model.disable_adapter():result=generation(model,tokenizer,messages,torch,a.seed,a.max_new_tokens)
    else:result=generation(model,tokenizer,messages,torch,a.seed,a.max_new_tokens)
    result.update({'question':a.question,'condition':'hf_base' if a.base_only else 'hf_adapter','rag':a.rag,'base':BASE,'revision':REVISION,'backend':backend,'release_status':'experimental_unpromoted'})
    if a.save:
        target=Path(a.save);target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False)
    print(result['response'])

if __name__=='__main__':main()
