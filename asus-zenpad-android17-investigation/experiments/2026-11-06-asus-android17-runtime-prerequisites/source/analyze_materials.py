"""Associate hash output with exact guest begin/end markers, tolerating diagnostic lines."""
import re

def analyze_materials(text,payloads):
    observed={};active=None;hashes=[]
    for line in text.splitlines():
        m=re.fullmatch(r'MATERIAL name=(\S+) level=(\S+) file=(.+)',line)
        if m:
            active=tuple(m.groups());hashes=[];continue
        if active:
            m=re.fullmatch(r'([0-9a-f]{64})  /mnt/(.+)',line)
            if m and m[2]==active[2]:hashes.append(m[1])
            m=re.fullmatch(r'MATERIAL_EXIT (\S+) (\S+) (.+) (\d+)',line)
            if m:
                key=tuple(m.groups()[:3])
                if key==active and m[4]=='0' and len(hashes)==1 and key not in observed:observed[key]=hashes[0]
                else:observed[key]=None
                active=None;hashes=[]
    result=[]
    for p in payloads:
        for level in ['bare','verity']:
            for f in p['files']:
                actual=observed.get((p['name'],level,f['path']))
                result.append(dict(payload=p['name'],level=level,path=f['path'],expected=f['sha256'],actual=actual,passed=actual==f['sha256']))
    return result
