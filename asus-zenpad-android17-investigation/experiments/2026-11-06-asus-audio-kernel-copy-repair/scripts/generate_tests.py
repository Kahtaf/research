from pathlib import Path
import re,hashlib,json
p=Path(__file__).resolve().parents[1];a=Path('sound/soc/mediatek/mt_soc_audio_8163');records=[]
def fn(path,name,newname=None):
 s=path.read_text();m=re.search(r'^(?:static )?[^;{}#\n]+\b'+name+r'\([^;{}]*\)\n\{',s,re.M)
 assert m,(path,name)
 text=s[m.start():s.index('\n}',m.end())+2]
 records.append({'source':str(path.relative_to(p)),'function':name,'body_sha256':hashlib.sha256(text.encode()).hexdigest()})
 return text.replace(name,newname) if newname else text
out=['#include "shim.h"']
h=p/'source/current'/a/'mt_soc_pcm_transfer.h';text=h.read_text();records.append({'source':str(h.relative_to(p)),'sha256':hashlib.sha256(text.encode()).hexdigest(),'substitution':'remove Linux includes only; shim supplies boundary types/functions'})
out.append(re.sub(r'^#include <linux/[^>]+>\n','',text,flags=re.M))
for cap,file in [(False,'mt_soc_pcm_dl1.c'),(True,'mt_soc_pcm_capture.c')]:
 for name in (['mtk_pcm_pointer','mtk_pcm_copy','mtk_pcm_dl1_stop'] if not cap else ['mtk_capture_pcm_pointer','mtk_capture_pcm_copy','mtk_capture_alsa_stop']):out.append(fn(p/'source/current'/a/file,name))
for name in ['audio_frame_to_bytes','audio_bytes_to_frame']:out.append(fn(p/'source/original'/a/'mt_soc_pcm_common.c',name))
for name in ['copy_to_user_fromio','copy_from_user_toio']:out.append(fn(p/'source/original/sound/core/memory.c',name))
for file,name in [('mt_soc_pcm_dl1.c','mtk_pcm_copy'),('mt_soc_pcm_capture.c','mtk_capture_pcm_copy')]:out.append(fn(p/'source/original'/a/file,name,'original_'+name))
for name in ['Auddrv_DL1_Interrupt_Handler','Auddrv_UL1_Interrupt_Handler']:out.append(fn(p/'source/original'/a/'mt_soc_afe_control.c',name))
for name in ['snd_pcm_lib_write_transfer','snd_pcm_lib_read_transfer']:out.append(fn(p/'source/original/sound/core/pcm_lib.c',name))
out.append('#include "cases.c"')
(p/'tests/generated.c').write_text('\n\n'.join(out)+'\n');(p/'evidence/test-production-bodies.json').write_text(json.dumps(records,indent=2)+'\n')
