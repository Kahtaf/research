from pathlib import Path
import json,re,hashlib
R=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24');D=R/'inputs/missing-api-rules-r1';D.mkdir();wanted={'framework-ondeviceintelligence-platform.stubs.source.module_lib','service-configinfrastructure.stubs.source.system_server','service-healthfitness.stubs.source.system_server','service-media-s.stubs.source.system_server'};modules=[]
for f in (T/'out/soong').glob('build.lineage_p00a.*.ninja'):
 lines=[];name=''
 def save():
  if name not in wanted or not lines:return
  text=''.join(lines);out=D/(name+'.ninja');assert not out.exists();out.write_text(text);logical=text.replace('$\n','');manifests=[]
  for line in logical.splitlines():
   tok=line.split()
   if len(tok)>3 and tok[0]=='build' and 'sbox.textproto:' in tok[1] and tok[2]=='g.android.rawFileCopy':
    raw=T/tok[3];b=raw.read_bytes();dst=D/(name+'-'+Path(tok[1][:-1]).name);dst.write_bytes(b);txt=b.decode();paths=re.findall(r'copy_before: \{\s*from: "([^"]+)"',txt);manifests.append(dict(target=tok[1][:-1],raw_source=str(raw),raw_sha256=hashlib.sha256(b).hexdigest(),captured_manifest=str(dst),inputs=len(paths),missing=[p for p in paths if not(T/p).exists()]))
  modules.append(dict(module=name,ninja=str(f),ninja_capture=str(out),manifests=manifests))
 for line in f.open():
  if line.startswith('# Module:'):save();name=line.split(':',1)[1].strip();lines=[line] if name in wanted else []
  elif name in wanted:lines.append(line)
 save()
(D/'inventory.json').write_text(json.dumps(modules,indent=2));print(json.dumps(modules,indent=2))
