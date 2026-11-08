"""Freeze authentic per-invocation logs before Soong rotation; never execute them."""
from pathlib import Path
import re
import shutil
import sys
from integrate import need, read, write, sha

def capture(root,phase,code):
    plan=read(root/'inputs/plan.json');need(re.fullmatch('[A-Za-z0-9_.-]+',phase),'Unsafe phase')
    out=root/'attempt/native-evidence'/phase;out.mkdir(parents=True)
    a=Path(plan['aosp']);files={}
    for name in ['verbose.log.gz','.ninja_log','siso_metrics.json','siso_metadata.json','siso_localexec','siso_output','siso_failed_commands.sh']:
        p=a/'out'/name
        if p.is_file():
            dst=out/name
            with p.open('rb') as src,dst.open('xb') as f:shutil.copyfileobj(src,f,1048576)
            need(sha(dst)==sha(p),'Native log changed while capturing: '+name)
            files[name]=dict(sha256=sha(dst),bytes=dst.stat().st_size)
    need({'verbose.log.gz','.ninja_log'}<=set(files),'Actual native evidence channel missing')
    write(out/'receipt.json',dict(phase=phase,exit_code=code,files=files,attempt_started_sha256=sha(root/'attempt/started.json'),integration_sha256=sha(root/'attempt/integration.json')))

if __name__=='__main__':capture(Path(sys.argv[1]),sys.argv[2],int(sys.argv[3]))
