from pathlib import Path
import json,hashlib,re
R=Path(__file__).resolve().parents[1]
selected=['/data/vendor','/data/vendor/hardware','/data/misc','/data/misc/keystore','/data/property','/data/apex','/data/apex/active','/data/apex/backup','/data/apex/decompressed','/data/apex/images','/data/system','/data/media','/data/misc_ce','/data/misc_de','/data/system_ce','/data/system_de','/data/user','/data/user_de','/data/vendor_ce','/data/vendor_de']
aids={'root':0,'system':1000,'keystore':1017,'media_rw':1023,'misc':9998}
s=R/'inputs/android-init.rc';rows=[]
for n,line in enumerate(s.read_text().splitlines(),1):
 a=line.split()
 if len(a)>=5 and a[0]=='mkdir' and a[1] in selected:
  rows.append(dict(path=a[1],mode=a[2],uid=aids[a[3]],gid=aids[a[4]],source_line=n,source=line.strip(),encryption_options_not_executed=a[5:]))
assert set(r['path'] for r in rows)==set(selected)
(R/'evidence/data-requirements.json').write_text(json.dumps(dict(source=str(s),sha256=hashlib.sha256(s.read_bytes()).hexdigest(),root_changes=['chown system system /data','chmod 0771 /data'],directories=rows,scope='Filesystem ownership/modes only; actual init, encryption policy and SELinux not executed'),indent=2)+'\n')
(R/'source/requirements.h').write_text('struct requirement {const char *path; unsigned mode,uid,gid;};\nstatic struct requirement requirements[]={\n'+''.join('{"%s",0%s,%d,%d},\n'%(r['path'],r['mode'],r['uid'],r['gid']) for r in rows)+'};\n')
