from pathlib import Path
import re,shlex
VAR=re.compile(r'\$\{([^}]+)\}|\$([A-Za-z0-9_.-]+)')
def logical(s):return s.replace('$\n','')
def parse(s):
 lines=logical(s).splitlines();glob={};rules={};edges=[];current=None;variant=''
 for line in lines:
  if line.startswith('# Variant:'):variant=line.split(':',1)[1].strip()
  if line.startswith('rule '):current=('rule',line[5:].strip());rules[current[1]]={}
  elif line.startswith('build '):
   body=line[6:];m=re.search(r'(?<!\$): ',body);assert m,line[:200];outs=body[:m.start()].split();tokens=body[m.end():].split();edge={'out':outs,'rule':tokens[0],'inputs':[],'implicit':[],'orderonly':[],'vars':{},'variant':variant};mode='inputs'
   for v in tokens[1:]:
    if v=='|':mode='implicit'
    elif v=='||':mode='orderonly'
    else:edge[mode].append(v)
   edges.append(edge);current=('edge',edge)
  elif line.startswith(' ') and '=' in line and current:
   k,v=line.strip().split('=',1);target=rules[current[1]] if current[0]=='rule' else current[1]['vars'];target[k.strip()]=v.strip()
  elif line and not line.startswith((' ','#')) and '=' in line:
   k,v=line.split('=',1);glob[k.strip()]=v.strip();current=None
 return glob,rules,edges
def expand(s,variables):
 def sub(m):
  key=m[1] or m[2]
  if key not in variables:raise KeyError(key)
  return expand(variables[key],variables)
 return VAR.sub(sub,s.replace('$$','\x00')).replace('\x00','$').replace('$:',':').replace('$ ',' ')
