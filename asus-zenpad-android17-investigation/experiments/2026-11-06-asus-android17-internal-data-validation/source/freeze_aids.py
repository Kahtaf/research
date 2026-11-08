from pathlib import Path
import subprocess,json,hashlib,re
R=Path('/srv/android/asus-internal-data-validation');base=Path('/srv/android/asus-android17-runtime-prereqs/handoff-r1/evidence/input-manifest.json')
pins=json.loads(base.read_text());record=next(x for x in pins if x.get('source')=='system/core');print(record)
repo=Path('/srv/android/lineage24/system/core');commit=record['commit'];pins=[]
for name,path in [('android_filesystem_config.h','libcutils/include/private/android_filesystem_config.h'),('committed-android-init.rc','rootdir/init.rc')]:
 cmd=['git','-C',str(repo),'show',commit+':'+path];b=subprocess.check_output(cmd);q=R/'inputs'/name
 with q.open('xb') as f:f.write(b)
 pins.append(dict(repository=str(repo),commit=commit,path=path,copy=str(q),sha256=hashlib.sha256(b).hexdigest(),command=cmd))
aids={m[0].lower():int(m[1]) for m in re.findall(rb'#define\s+AID_(ROOT|SYSTEM|KEYSTORE|MEDIA_RW|MISC)\s+(\d+)\b',(R/'inputs/android_filesystem_config.h').read_bytes())}
aids={k.decode():v for k,v in aids.items()};assert aids==dict(root=0,system=1000,keystore=1017,media_rw=1023,misc=9998)
assert (R/'inputs/committed-android-init.rc').read_bytes()==(R/'inputs/android-init.rc').read_bytes()
(R/'evidence/android-init-pins.json').write_text(json.dumps(dict(pins=pins,aids=aids,captured_init_matches_committed_source=True),indent=2)+'\n')
print(json.dumps(aids))
