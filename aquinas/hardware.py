import importlib.util
import json
import platform
import shutil
import subprocess
from pathlib import Path

def command(args):
    if not shutil.which(args[0]):return {'available':False}
    try:
        r=subprocess.run(args,capture_output=True,text=True,timeout=15)
        return {'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    except Exception as e:return {'error':str(e)}

def diagnose(root):
    r={'platform':platform.platform(),'machine':platform.machine(),'disk':dict(zip(['total','used','free'],shutil.disk_usage(root))), 'cpu':command(['lscpu']), 'ram':command(['free','-b']), 'nvidia':command(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv']), 'amd':command(['rocminfo']), 'apple':command(['system_profiler','SPHardwareDataType','SPDisplaysDataType']), 'ollama':command(['ollama','list']), 'packages':{n:importlib.util.find_spec(n) is not None for n in ['torch','transformers','peft']}}
    if r['packages']['torch']:
        import torch
        r['torch']={'version':torch.__version__,'cuda':torch.cuda.is_available(),'hip':torch.version.hip,'mps':bool(hasattr(torch.backends,'mps') and torch.backends.mps.is_available())}
    return r
