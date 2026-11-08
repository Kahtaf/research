import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REL=Path('sound/soc/mediatek/mt_soc_audio_8163')
def funcs(s):
 out=[]
 for m in re.finditer(r'(?m)^((?:(?:static|inline|unsigned|int|void|bool|uint16|uint32|struct \w+|__init|__exit)\s+)+\**)(\w+)\(([^;]*?)\)\s*(?:/\*[^\n]*?\*/\s*)?\n\{',s):
  p=m.end();d=1
  while d:d+=(s[p]=='{')-(s[p]=='}');p+=1
  out.append({'name':m[2],'prefix':m[1],'params':m[3],'start':m.start(),'brace':m.end()-1,'end':p,'text':s[m.start():p],'body':s[m.end()-1:p]})
 return out
def fn(s,n):return next(f['text']+'\n' for f in funcs(s) if f['name']==n)
def edit_fn(s,n,change):
 f=next(f for f in funcs(s) if f['name']==n);return s[:f['start']]+change(f['text'])+s[f['end']:]
def private_graph(s):
 fs=funcs(s);names={f['name'] for f in fs};calls={n:set() for n in names};direct=set()
 for f in fs:
  calls[f['name']]|=set(re.findall(r'\b(\w+)\s*\(',f['body']))&names
  if 'mCodec_data' in f['body']:direct.add(f['name'])
 reach=set(direct)
 while True:
  add={n for n,c in calls.items() if c&reach};before=len(reach);reach|=add
  if before==len(reach):break
 return fs,calls,direct,reach
