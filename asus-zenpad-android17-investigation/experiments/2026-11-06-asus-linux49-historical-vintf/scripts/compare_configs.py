from pathlib import Path
import re,json,xml.etree.ElementTree as E,hashlib
R=Path(__file__).resolve().parents[1];cfg=R.parent/'2026-11-06-asus-bmc156-full-kernel/artifacts/resolved.config'
def parse(p):
 out={}
 for line in p.read_text().splitlines():
  m=re.fullmatch(r'(CONFIG_\w+)=(.*)',line)
  if m:out[m[1]]=m[2]
  m=re.fullmatch(r'# (CONFIG_\w+) is not set',line)
  if m:out[m[1]]='n'
 return out
actual=parse(cfg)
def entry(e):return {'key':e.findtext('key'),'value':e.findtext('value'),'type':e.find('value').get('type')}
def matches(e):
 a=actual.get(e['key'],'n')
 if e['type']=='string':a=a.strip('"')
 if e['type']=='range':
  lo,hi=map(int,e['value'].split('-'));return lo<=int(a,0)<=hi
 return a==e['value']
res={}
for profile in ['p','q']:
 D=R/'upstream/s'/profile/'android-4.9';base=parse(D/'android-base.config.decoded');pred=[{'key':k,'value':v,'type':'tristate','origin':str((D/'android-base.config.decoded').relative_to(R))} for k,v in base.items()]
 active=[];skipped=[]
 if profile=='p':
  for arch in ['arm','arm64']:
   f=D/('android-base-'+arch+'.config.decoded')
   terms=[{'key':k,'value':v,'type':'tristate','origin':str(f.relative_to(R))} for k,v in parse(f).items()]
   if actual.get('CONFIG_'+arch.upper())=='y':pred+=terms;active.append('architecture '+arch)
   else:skipped.append('architecture '+arch)
 text=(D/'android-base-conditional.xml.decoded').read_text();root=E.fromstring('<root>'+text+'</root>')
 for i,g in enumerate(root.findall('group')):
  cond=[entry(x) for x in g.findall('conditions/config')];terms=[entry(x) for x in g.findall('config')]
  if all(matches(x) for x in cond):
   active.append({'group':i,'conditions':cond})
   for e in terms:e['origin']=str((D/'android-base-conditional.xml.decoded').relative_to(R))+f':group[{i}]'
   pred+=terms
  else:skipped.append({'group':i,'conditions':cond})
 gaps=[dict(e,actual=actual.get(e['key'],'n')) for e in pred if not matches(e)]
 res[profile]={'minlts':root.find('kernel').get('minlts'),'active_predicate_count':len(pred),'gaps':gaps,'active_groups':active,'inactive_groups':skipped,'predicates':pred}
result={'config_sha256':hashlib.sha256(cfg.read_bytes()).hexdigest(),'profiles':res}
(R/'evidence/config-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
for p,r in res.items():
 print(p,'minlts',r['minlts'],'predicates',r['active_predicate_count'],'gaps',len(r['gaps']))
 for e in r['gaps']:print(e['key'],'actual='+e['actual'],'required='+e['value'])
