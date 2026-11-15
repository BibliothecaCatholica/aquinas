"""Assistant-only SFT on a pinned trainable checkpoint, never a GGUF.
--smoke-test runs synthetic tokens on a tiny randomly initialized LFM3; it is NOT fine-tuning the released model.
"""
import argparse
import importlib.metadata
import json
import math
import random
import subprocess
from pathlib import Path
from aquinas.core import read_jsonl,validate_dataset,digest

TARGETS=['q_proj','k_proj','v_proj','o_proj','in_proj','out_proj','w1','w2','w3']

def encode_example(tokenizer,row,max_length):
    messages=row['messages']
    prompt=tokenizer.apply_chat_template(messages[:-1],tokenize=False,add_generation_prompt=True)
    full=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=False)
    # Reject template/tokenization boundary drift instead of training on user text.
    pids=tokenizer(prompt,add_special_tokens=False)['input_ids']
    ids=tokenizer(full,add_special_tokens=False)['input_ids']
    if ids[:len(pids)]!=pids:raise ValueError('Chat template prompt is not an exact token prefix')
    if len(ids)>max_length:raise ValueError('Example exceeds max length; edit/chunk explicitly')
    labels=[-100]*len(pids)+ids[len(pids):]
    if not any(x!=-100 for x in labels):raise ValueError('No assistant tokens')
    return ids,labels

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--out',required=True);p.add_argument('--device',default='cuda',choices=['cpu','cuda','mps']);p.add_argument('--epochs',type=int,default=3);p.add_argument('--max-steps',type=int);p.add_argument('--max-length',type=int,default=1024);p.add_argument('--accumulation',type=int,default=4);p.add_argument('--lr',type=float,default=0.0001);p.add_argument('--seed',type=int,default=22);p.add_argument('--smoke-test',action='store_true');p.add_argument('--allow-draft-data',action='store_true');p.add_argument('--accept-model-license',action='store_true');a=p.parse_args()
    if min(a.epochs,a.max_length,a.accumulation)<=0:p.error('epochs, length and accumulation must be positive')
    root=Path(a.root);out=Path(a.out)
    if out.exists():p.error('output exists; choose a versioned new directory')
    if not a.smoke_test and not a.accept_model_license:p.error('Read research/model-license.txt, then pass --accept-model-license')
    rows=read_jsonl(root/'data/training/train.jsonl');validate_dataset(root)
    if not a.smoke_test and not a.allow_draft_data and any(r['review_status']=='draft_pending_scholarly_review' for r in rows):p.error('Scholarly review pending; review records or explicitly pass --allow-draft-data for private experimentation')
    import torch
    from transformers import AutoConfig,AutoModelForCausalLM,AutoTokenizer
    from peft import LoraConfig,get_peft_model
    random.seed(a.seed);torch.manual_seed(a.seed)
    if a.device=='cuda' and not torch.cuda.is_available():p.error('CUDA/ROCm unavailable; install matching torch wheel or choose external compute')
    pin=json.loads((root/'research/model-revision.json').read_text());model_id=pin['model'];rev=pin['revision']
    config=AutoConfig.from_pretrained(str(root/'research') if a.smoke_test else model_id,revision=rev,trust_remote_code=True)
    if a.smoke_test:
        config.hidden_size=64;config.intermediate_size=128;config.num_hidden_layers=3;config.layer_types=['conv','sliding_attention','full_attention'];config.num_attention_heads=4;config.num_key_value_heads=2;config.head_dim=16;config.vocab_size=128;config.bos_token_id=1;config.eos_token_id=2;config.pad_token_id=0;config.max_position_embeddings=128;config.sliding_window=32
        model=AutoModelForCausalLM.from_config(config,trust_remote_code=True)
        encoded=[(list(range(3,35)),[-100]*16+list(range(19,35)))]
        tokenizer=None
    else:
        tokenizer=AutoTokenizer.from_pretrained(model_id,revision=rev,trust_remote_code=True)
        dtype=torch.bfloat16 if a.device=='cuda' and torch.cuda.is_bf16_supported() else torch.float32
        model=AutoModelForCausalLM.from_pretrained(model_id,revision=rev,trust_remote_code=True,dtype=dtype,attn_implementation='eager')
        encoded=[encode_example(tokenizer,r,a.max_length) for r in rows]
    present={n.split('.')[-1] for n,m in model.named_modules() if isinstance(m,torch.nn.Linear)}
    missing=set(TARGETS)-present
    if missing:raise ValueError('Expected target modules absent: '+str(missing))
    model.config.use_cache=False
    model=get_peft_model(model,LoraConfig(r=8,lora_alpha=16,lora_dropout=0.05,target_modules=TARGETS,task_type='CAUSAL_LM'))
    model.to(a.device);model.train()
    optimizer=torch.optim.AdamW([v for v in model.parameters() if v.requires_grad],lr=a.lr)
    out.mkdir(parents=True)
    steps=0;losses=[];gradient_verified=False
    count=1 if a.smoke_test else a.epochs
    for epoch in range(count):
        order=list(range(len(encoded)));random.shuffle(order);optimizer.zero_grad()
        for pos,i in enumerate(order):
            ids,labels=encoded[i]
            x=torch.tensor([ids],device=a.device);y=torch.tensor([labels],device=a.device)
            group_start=(pos//a.accumulation)*a.accumulation
            group_size=min(a.accumulation,len(order)-group_start)
            loss=model(input_ids=x,attention_mask=torch.ones_like(x),labels=y).loss
            if not torch.isfinite(loss):raise RuntimeError('Non-finite loss')
            (loss/group_size).backward();losses.append(float(loss.detach().cpu()))
            if (pos+1)%a.accumulation==0 or pos+1==len(order):
                norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
                if not math.isfinite(float(norm)) or float(norm)<=0:raise RuntimeError('Invalid or zero adapter gradients')
                gradient_verified=True;optimizer.step();optimizer.zero_grad();steps+=1
                print(json.dumps({'step':steps,'loss':losses[-1]}),flush=True)
                if a.max_steps and steps>=a.max_steps:break
        if a.max_steps and steps>=a.max_steps:break
    model.save_pretrained(out)
    if tokenizer:tokenizer.save_pretrained(out)
    packages={n:importlib.metadata.version(n) for n in ['torch','transformers','peft','accelerate']}
    (out/'training-manifest.json').write_text(json.dumps({'base':model_id,'revision':rev,'smoke_only':a.smoke_test,'args':vars(a),'steps':steps,'losses':losses,'gradient_verified':gradient_verified,'packages':packages,'data_sha256':digest((root/'data/training/train.jsonl').read_bytes()),'max_gpu_bytes':torch.cuda.max_memory_allocated() if a.device=='cuda' else None},indent=2))
    with (out/'requirements.lock.txt').open('w') as f:subprocess.run(['python','-m','pip','freeze'],stdout=f,check=True)
if __name__=='__main__':main()
