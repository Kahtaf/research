from pathlib import Path
import os,json
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');exec((R/'source/ninja_leaf.py').read_text());g,r,e=parse((R/'inputs/leaf/main-prelude.ninja').read_text());d={'global_keys':len(g),'rules':{k:v for k,v in r.items() if k in ['g.cc.cc','g.cc.ld','g.cc.ar','g.cc.partialLd','g.cc.archive','g.cc.strip']},'selected':{}}
for module in ['linkerconfig','linkerconfig_contents','linkerconfig_contents_fulltest']:
 mg,mr,edges=parse((R/'inputs/leaf'/(module+'.ninja')).read_text());selected=[]
 for edge in edges:
  if any(x.endswith('systemdefault.cc') for x in edge['inputs']) or any('/unstripped/linkerconfig' in x or x.endswith('/linkerconfig_contents.a') or x.endswith('/linkerconfig_contents_fulltest') for x in edge['out']):
   v={**g,**mg,**edge['vars'],'in':' '.join(edge['inputs']),'out':' '.join(edge['out'])}
   values={}
   for k in ['ccCmd','cFlags','ldCmd','ldFlags','arCmd','arFlags','libFlags','rspfile','rspfile_content','crtBegin','crtEnd']:
    if k in v:
     try:values[k]=expand(v[k],v)
     except KeyError as ex:values[k]='MISSING:'+str(ex)
   edge['expanded']=values;selected.append(edge)
 d['selected'][module]=selected
(R/'evidence/leaf-summary.json').write_text(json.dumps(d,indent=2));print(json.dumps({'rules':d['rules'],'selected':{k:[{'out':x['out'],'rule':x['rule'],'variant':x['variant'],'vars':list(x['vars']),'expanded_summary':{k:(v[:300]+'...' if len(v)>300 else v) for k,v in x['expanded'].items()}} for x in rows] for k,rows in d['selected'].items()}},indent=2))
