"""Pinned LFM3 inference helpers, exercised in the v2.1 GPU run."""
import inspect,time
def generation(model,tokenizer,messages,torch,seed,max_new_tokens):
    from transformers import set_seed
    set_seed(seed)
    device=next(model.parameters()).device
    inputs=tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,enable_thinking=False,return_tensors='pt',return_dict=True).to(device)
    size=inputs['input_ids'].shape[1]
    if size+max_new_tokens>8192:raise ValueError('Input and output allowance exceed 8192-token project budget')
    if device.type=='cuda':torch.cuda.synchronize()
    start=time.perf_counter()
    with torch.inference_mode():
        output=model.generate(**inputs,max_new_tokens=max_new_tokens,do_sample=True,temperature=.35,top_p=.9,top_k=40,repetition_penalty=1.,eos_token_id=tokenizer.eos_token_id,pad_token_id=tokenizer.pad_token_id)
    if device.type=='cuda':torch.cuda.synchronize()
    elapsed=time.perf_counter()-start
    ids=output[0,size:].detach().cpu().tolist()
    reason='length' if len(ids)>=max_new_tokens and (not ids or ids[-1]!=tokenizer.eos_token_id) else 'stop'
    return {'response':tokenizer.decode(ids,skip_special_tokens=True),'generated_token_ids':ids,'input_tokens':size,'eval_tokens':len(ids),'wall_seconds':elapsed,'tokens_per_second':len(ids)/elapsed if elapsed else None,'done_reason':reason,'request':{'messages':messages,'enable_thinking':False,'seed':seed,'temperature':.35,'top_p':.9,'top_k':40,'max_new_tokens':max_new_tokens,'engine':'Transformers','dtype':str(next(model.parameters()).dtype)}}


def disable_optional_wide_conv(model):
    base=model.get_base_model() if hasattr(model,'get_base_model') else model
    if getattr(base.config,'model_type',None)!='lfm3' or getattr(base.config,'conv_L_cache',None)!=7:
        raise RuntimeError('This fallback is verified for the pinned LFM3 width-7 model only')
    namespaces={};blocks=[]
    for layer in base.modules():
        if layer.__class__.__name__=='Lfm3ShortConv':
            forward=inspect.unwrap(type(layer).forward)
            namespace=getattr(forward,'__globals__',{})
            if 'can_use_lfm3_conv' not in namespace:raise RuntimeError('Unsupported LFM3 forward implementation; refusing an unverified patch')
            namespaces[id(namespace)]=namespace;blocks.append(layer)
    if not blocks:raise RuntimeError('LFM3 short-convolution blocks not found')
    def use_builtin_torch(*args,**kwargs):return False
    for namespace in namespaces.values():namespace['can_use_lfm3_conv']=use_builtin_torch
    if not hasattr(base.generation_config,'disable_compile'):raise RuntimeError('Pinned Transformers generation compile control is unavailable')
    base.generation_config.disable_compile=True
    model.generation_config.disable_compile=True
    if not all(inspect.unwrap(type(b).forward).__globals__['can_use_lfm3_conv'] is use_builtin_torch for b in blocks):
        raise RuntimeError('Could not enforce the same torch fallback in every conv block')
    return {'backend':'Built-in LFM3 PyTorch width-7 convolution fallback','optional_wide_triton_conv_enabled':False,'blocks':len(blocks),'patched_namespaces':len(namespaces),'patch_scope':'Current Python process only; no source/cache files changed','attention':'sdpa in both conditions','automatic_torch_compile_enabled':False}


