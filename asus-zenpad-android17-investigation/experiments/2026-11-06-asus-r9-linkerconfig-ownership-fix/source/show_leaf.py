from pathlib import Path
import re,json,os
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');D=R/'inputs/leaf';out={}
for n in ['linkerconfig','linkerconfig_contents','linkerconfig_contents_fulltest']:
 text=(D/(n+'.ninja')).read_text();rows=text.splitlines();kept=[]
 for i,row in enumerate(rows):
  if row.startswith('# Module:') or row.startswith('# Variant:'):kept.append(row)
  elif row.startswith('build ') and (('systemdefault.o' in row) or ('p00a_legacy_graphics_test.o' in row) or (': ' in row and ('/unstripped/linkerconfig:' in row or 'linkerconfig.a:' in row or '/linkerconfig_contents.a:' in row or '/linkerconfig_contents_fulltest:' in row))):kept+=rows[max(0,i-2):i+15]
 out[n]='\n'.join(kept)
print(json.dumps(out,indent=2))
