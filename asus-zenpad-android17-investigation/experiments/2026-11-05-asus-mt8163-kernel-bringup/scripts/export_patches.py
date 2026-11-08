#!/usr/bin/env python3
import difflib,hashlib,json,subprocess,tarfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];source=root/'sources/kernel';archive=root/'downloads/mt8163-4.9-dc63af1.tar.gz'
baseline={
 'sound/soc/mediatek/mt_soc_audio_8163/mt_soc_pcm_dl1_bt.c',
 'drivers/misc/mediatek/base/power/mt8163/mt_cpufreq.c',
 'drivers/misc/mediatek/boot/mtk_boot_common.c',
 'drivers/misc/mediatek/boot/mtk_boot.c',
 'drivers/misc/mediatek/sensors-1.0/alsps/alsps.c',
 'drivers/misc/mediatek/usb20/musb_gadget_ep0.c',
 'drivers/misc/mediatek/video/mt8163/videox/debug.h',
 'sound/soc/codecs/rt551x.c',
}
paths=set(str(p.relative_to(root/'sources/original-files')) for p in (root/'sources/original-files').rglob('*') if p.is_file())
paths|={r['target'] for r in json.loads((root/'evidence/asus-import-provenance.json').read_text())}
paths.add('arch/arm64/configs/asus_p00a_defconfig')
groups={'0001-build-compatibility.patch':[],'0002-asus-board-panel-touch.patch':[]};rows=[]
check=root/'evidence/patch-replay';check.mkdir(exist_ok=True)
with tarfile.open(archive) as tf:
 members={m.name:m for m in tf.getmembers()};prefix=next(iter(members)).split('/')[0]+'/'
 for path in sorted(paths):
  member=members.get(prefix+path);old=tf.extractfile(member).read() if member else b'';new=(source/path).read_bytes()
  if old==new:continue
  if member:
   dest=check/path;dest.parent.mkdir(exist_ok=True,parents=True);dest.write_bytes(old)
  diff='diff --git a/'+path+' b/'+path+'\n'
  if not member:diff+='new file mode 100644\n'
  diff+=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='a/'+path if member else '/dev/null',tofile='b/'+path))
  group='0001-build-compatibility.patch' if path in baseline else '0002-asus-board-panel-touch.patch'
  groups[group].append(diff);rows.append(dict(path=path,patch=group,new_file=not bool(member),sha256=hashlib.sha256(new).hexdigest()))
for name,parts in groups.items():
 patch=root/'patches'/name;patch.write_text('\n'.join(parts));assert parts
 # Apply actual exported patches against pristine base files; verify final bytes.
 subprocess.run(['git','apply','--check',str(patch)],cwd=check,check=True)
 subprocess.run(['git','apply',str(patch)],cwd=check,check=True)
for row in rows:assert hashlib.sha256((check/row['path']).read_bytes()).hexdigest()==row['sha256']
(root/'evidence/patch-manifest.json').write_text(json.dumps(dict(status='replay-passed',files=rows),indent=2)+'\n')
print('Exported and replayed patches:',len(rows),'changed/imported source files')
