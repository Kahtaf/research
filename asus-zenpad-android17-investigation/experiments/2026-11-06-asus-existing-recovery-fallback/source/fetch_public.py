#!/usr/bin/env python3
"""Finite public fetches; no auth/cookies, 2 MiB/page and 64 MiB spike cap."""
import concurrent.futures, hashlib, json, pathlib, sys, time, urllib.request, urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[1]
CAP=2*1024*1024

def fetch(item):
    label,url,*limits=item
    cap=limits[0] if limits else CAP
    if cap>32*1024*1024: raise ValueError('max ZIP bound')
    rec={'label':label,'url':url,'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'limit_bytes':cap}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'public-device-research/1.0','Accept':'*/*'})
        with urllib.request.urlopen(req,timeout=25) as r:
            rec.update(status=r.status,final_url=r.url,headers=dict(r.headers))
            body=r.read(cap+1)
            if len(body)>cap: raise ValueError('page exceeds bound')
    except urllib.error.HTTPError as e:
        rec.update(status=e.code,error=str(e)); body=e.read(cap+1)[:cap]
    except Exception as e:
        rec['error']=str(e); body=b''
    if body:
        path=ROOT/'research'/(label+'.body');path.write_bytes(body)
        rec.update(path=str(path.relative_to(ROOT)),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
    (ROOT/'research'/(label+'.json')).write_text(json.dumps(rec,indent=2)+'\n')
    return rec
if __name__=='__main__':
    pairs=json.loads(sys.argv[1])
    if len(pairs)>8: raise SystemExit('max 8 requests per invocation')
    if sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())+sum(i[2] if len(i)>2 else CAP for i in pairs)>64*1024*1024: raise SystemExit('spike budget')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for rec in ex.map(fetch,pairs): print(json.dumps(rec))
