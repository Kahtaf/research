import gzip,hashlib,json,shutil,struct,zlib,resource
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; W=ROOT.parent
resource.setrlimit(resource.RLIMIT_CPU,(40,40))
try: resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
except (ValueError,OSError): pass
H=lambda b:hashlib.sha256(b).hexdigest()
a=W/'2026-11-06-asus-minimal-audio-hal'
b=W/'2026-11-06-asus-bmc156-full-kernel'
k=W/'2026-11-05-asus-p00a-power-port/sources/kernel'
manifest=json.loads(gzip.decompress((b/'evidence/r5-source-manifest.json.gz').read_bytes()))
rows=[]
def copy(p,dst,expect=None):
 data=p.read_bytes(); h=H(data)
 if expect: assert h==expect,(p,h,expect)
 dest=ROOT/'inputs'/dst; dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 rows.append({'path':str(p.relative_to(W)),'copy':str(dest.relative_to(ROOT)),'bytes':len(data),'sha256':h,'expected_sha256':expect})
 return data
for x in json.loads((a/'evidence/source-pins.json').read_text()):
 c=x['copy']
 if c.startswith('source/kernel/') and ('mt_soc_pcm_' not in c) and ('sdk37' not in c):
  rel=c.removeprefix('source/kernel/');copy(a/c,'combined/'+rel,x['sha256']);assert manifest[rel]==x['sha256'],rel
 if c.startswith('source/oem/asus-original/') or c.startswith('source/stock/'):
  # Exclude unrelated PCM files and public calibration audit entirely.
  if 'mt_soc_pcm_' not in c:copy(a/c,c.removeprefix('source/'),x['sha256'])
for rel in ['Kconfig','sound/Kconfig','sound/soc/Kconfig','sound/soc/mediatek/Kconfig','sound/soc/mediatek/Makefile','sound/soc/mediatek/mt_soc_audio_8163/Makefile','arch/arm64/boot/dts/mediatek/mt8163.dtsi','arch/arm64/boot/dts/mediatek/mt8163-pinfunc.h']:
 copy(k/rel,'combined/'+rel,manifest[rel])
copy(b/'artifacts/resolved.config','bmc/resolved.config','10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2')
copy(b/'source/arch/arm64/configs/asus_p00a_defconfig','bmc/asus_p00a_defconfig')
copy(b/'artifacts/asus-p00a.dtb','bmc/asus-p00a.dtb','a099d0538b270e23ec0d034b507eef9248252a3c459a11aa70edb6520bfd2b77')
image=copy(b/'artifacts/Image.gz-dtb','bmc/Image.gz-dtb','e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1')
z=zlib.decompressobj(31); raw=z.decompress(image,64*1024**2);raw+=z.flush();assert len(raw)<64*1024**2
(ROOT/'inputs/bmc/Image').write_bytes(raw);assert z.unused_data==(ROOT/'inputs/bmc/asus-p00a.dtb').read_bytes()
stock=W/'2026-11-05-asus-latest-android-feasibility/sources/stock-firmware'
boot=copy(stock/'boot.img','stock-public/boot.img','a175ed39c9e9642756dd28f1d006b39937d17f290da6af69dda6d4b52d6f910d')
assert boot[:8]==b'ANDROID!';n=struct.unpack_from('<I',boot,8)[0];page=struct.unpack_from('<I',boot,36)[0];payload=boot[page:page+n];assert payload[:4]==bytes.fromhex('88168858')
z=zlib.decompressobj(31);raw=z.decompress(payload[512:],64*1024**2)+z.flush();assert len(raw)<64*1024**2
(ROOT/'inputs/stock-public/Image').write_bytes(raw);(ROOT/'inputs/stock-public/appended.dtb').write_bytes(z.unused_data)
assert raw==(stock/'unpacked/Image').read_bytes();assert z.unused_data==(stock/'unpacked/appended-0.dtb').read_bytes()
for name in ['stock-selected-mixer-queries.json','stock-idle-mixer-baseline.json','root-selected-mixer-queries.json']:
 copy(W/'2026-11-06-asus-stock-audio-topology/evidence'/name,'observations/'+name)
(ROOT/'evidence/input-pins.json').write_text(json.dumps(rows,indent=2)+'\n')
(ROOT/'evidence/image-extraction.json').write_text(json.dumps({'stock_Image_sha256':H(raw),'stock_Image_bytes':len(raw),'stock_embedded_config':b'IKCFG_ST' in raw,'combined_Image_sha256':H((ROOT/'inputs/bmc/Image').read_bytes()),'combined_embedded_config':b'IKCFG_ST' in (ROOT/'inputs/bmc/Image').read_bytes(),'stock_boot_extraction_matches_existing_public_copy':True,'combined_appended_dtb_matches_pinned_separate_artifact':True},indent=2)+'\n')
print('Copied and verified',len(rows),'public inputs; actual boot and combined images extracted')
