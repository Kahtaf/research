from pathlib import Path
import os,resource,subprocess,json,hashlib,shlex
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
r=Path('/srv/android/asus-camera-arm32-route');old=Path('/srv/android/asus-camera-source-abi-route');out=r/'compat-out';out.mkdir(exist_ok=True)
argv=json.loads((r/'abi-out/compile.json').read_text())[2]['argv'];assert '-c' in argv;flags=argv[1:argv.index('-c')];clang=argv[0];pins=[];rows=[]
for label,base in [('oem',old/'oem-kernel'),('kernel49',old/'sdk37/kernel/asus/p00a-fd')]:
 # Prior report froze these exact public headers. No calibration payloads.
 for n in ['cam_cal_define.h','cam_cal.h']:
  p=out/(label+'_'+n);d=p.read_bytes();pins.append({'source':str(p),'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)})
 typ='stCAM_CAL_INFO_STRUCT' if label=='oem' else 'struct stCAM_CAL_INFO_STRUCT'
 src=out/(label+'.c');src.write_text('#include <stddef.h>\n#include <stdint.h>\ntypedef uint32_t u32; typedef uint8_t u8;\n#include "'+label+'_cam_cal_define.h"\n#include "'+label+'_cam_cal.h"\nconst uint32_t '+label+'_layout[]={sizeof('+typ+'),offsetof('+typ+',pu1Params),CAM_CALIOC_G_READ};\n')
 b=Path('/srv/android/lineage24')
 scan=subprocess.run([clang,*flags,'-M',str(src)],cwd=b,text=True,capture_output=True,check=True,timeout=30)
 for n in shlex.split(scan.stdout.replace('\\\n',' ').split(':',1)[1]):
  q=Path(n);q=q if q.is_absolute() else b/q
  if not q.is_relative_to(b):continue
  rel=q.relative_to(b);dst=r/'sdk37'/rel;dst.parent.mkdir(parents=True,exist_ok=True);data=q.read_bytes();dst.write_bytes(data);pins.append({'source':str(q),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
 a=[clang,*flags,'-c',str(src),'-o',str(out/(label+'.o'))];p=subprocess.run(a,cwd=r/'sdk37',capture_output=True,text=True,timeout=30);rows.append({'argv':a,'rc':p.returncode,'stderr':p.stderr});print(p.stderr)
 if p.returncode:raise SystemExit(1)
 print(label,subprocess.run([str(Path(clang).parent/'llvm-readelf'),'-x','.rodata.'+label+'_layout',str(out/(label+'.o'))],capture_output=True,text=True,check=True).stdout)
print('INPUT_PINS',json.dumps(pins));print('COMMANDS',json.dumps(rows))
