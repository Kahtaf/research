"""Only completed Soong action records, joined to actual Ninja output entries."""
import gzip
from pathlib import Path
import re
import shlex
from integrate import need,read,sha

def commands_for(root,targets,entries=None):
    commands={};receipts=[]
    folders=sorted((root/'attempt/native-evidence').glob('*'))
    need(folders,'Missing frozen native invocation logs')
    for folder in folders:
        r=read(folder/'receipt.json')
        need(r['attempt_started_sha256']==sha(root/'attempt/started.json') and r['integration_sha256']==sha(root/'attempt/integration.json'),'Native evidence attempt binding drift')
        for name,row in r['files'].items():
            p=folder/name
            need(p.is_file() and sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],'Frozen native evidence changed')
        path=folder/'verbose.log.gz';finished=[]
        with gzip.open(path,'rt',errors='strict') as f:
            for line in f:
                match=re.match(r'^\[\d+/\d+\] (.+)\n?$',line)
                if match:
                    finished.append(match.group(1).rstrip('\n'))
                elif line.startswith('FAILED: ') and finished:
                    finished.pop()
        from verify_product_r3 import log_entries
        phase_entries=log_entries(folder/'.ninja_log',targets) if entries is not None else {}
        for command in finished:
            if not any(t in command for t in ('clang','rustc','ld.lld')):continue
            words=shlex.split(command)
            # The command must produce this exact output, rather than merely use
            # it as a linker dependency or print it in a pending-work summary.
            outputs={words[i+1] for i,w in enumerate(words[:-1]) if w=='-o'}
            for target in outputs & targets:
                if entries is not None:
                    if target not in phase_entries or phase_entries[target]!=entries.get(target):continue
                commands.setdefault(target,[]).append(command)
        receipts.append(dict(path=str(folder/'receipt.json'),sha256=sha(folder/'receipt.json')))
    return commands,receipts
