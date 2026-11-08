import difflib,hashlib,json,re,shutil,sys
from pathlib import Path
from bounded import ROOT,run
H=lambda b:hashlib.sha256(b).hexdigest();rows=[];chunks=[]
for dest in sorted((ROOT/'candidate').rglob('*')):
 if not dest.is_file():continue
 rel=dest.relative_to(ROOT/'candidate');src=ROOT/'preimage'/rel
 a=src.read_text() if src.exists() else '';b=dest.read_text()
 if a==b:continue
 row={'path':str(rel),'pre_sha256':H(src.read_bytes()) if src.exists() else None,'post_sha256':H(dest.read_bytes()),'pre_bytes':src.stat().st_size if src.exists() else None,'post_bytes':dest.stat().st_size,'destination_must_be_absent':not src.exists()};rows.append(row)
 diff=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+str(rel) if src.exists() else '/dev/null',tofile='b/'+str(rel),n=3))
 if str(rel)=='resolved.config':
  diff=diff.replace('a/resolved.config','a/.config').replace('b/resolved.config','b/.config');(ROOT/'patches/resolved-config.patch').write_text(diff)
 else:chunks.append(diff)
(ROOT/'patches/kernel-source.patch').write_text(''.join(chunks))
assert len(rows)==7,len(rows)
replay=ROOT/'evidence'/(sys.argv[1] if len(sys.argv)>1 else 'patch-replay');assert not replay.exists(),'Do not overwrite a previous patch replay; use fresh evidence destination'
replay.mkdir()
for p in (ROOT/'preimage').rglob('*'):
 if p.is_file():
  rel=p.relative_to(ROOT/'preimage');rel=Path('.config') if str(rel)=='resolved.config' else rel;out=replay/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(p.read_bytes())
for patch in ['kernel-source.patch','resolved-config.patch']:
 # cwd is deliberately fixed to this spike by bounded.run; patch supports -d.
 run(['/usr/bin/patch','--batch','-d',replay,'-p1','-i',ROOT/'patches'/patch],output='evidence/apply-'+patch+'.txt',timeout=30)
for row in rows:
 rel=Path('.config') if row['path']=='resolved.config' else Path(row['path']);assert H((replay/rel).read_bytes())==row['post_sha256']
(ROOT/'evidence/pre-post-pins.json').write_text(json.dumps(rows,indent=2)+'\n')
(ROOT/'evidence/patch-replay.json').write_text(json.dumps({'status':'PASS','scope':'fresh owned seven-path preimage copies only','paths':len(rows),'target_source_or_out_touched':False,'patches':{p.name:H(p.read_bytes()) for p in (ROOT/'patches').glob('*.patch')}},indent=2)+'\n')
# Exact API semantics with original source line receipts for reviewers.
queries=[('include/linux/gpio.h','int devm_gpio_request_one'),('drivers/gpio/devres.c','int devm_gpio_request_one'),('drivers/gpio/gpiolib-legacy.c','int gpio_request_one'),('include/asm-generic/gpio.h','static inline int gpio_direction_output'),('drivers/gpio/gpiolib-of.c','int of_get_named_gpio_flags'),('drivers/gpio/gpiolib-of.c','struct gpio_desc *of_find_gpio'),('include/linux/of.h','static inline int of_property_count_u32_elems'),('include/linux/device.h','static inline int devm_add_action_or_reset'),('drivers/base/dd.c','devres_release_all(dev);'),('drivers/pinctrl/mediatek/pinctrl-mtk-common.c','static int mtk_pmx_gpio_request_enable'),('drivers/pinctrl/mediatek/pinctrl-mtk-common.c','pctl->chip->base = -1;'),('drivers/pinctrl/pinmux.c','if (ops->strict && desc->mux_usecount'),('sound/soc/soc-core.c','int snd_soc_register_codec')]
api=[]
for rel,q in queries:
 p=ROOT/'inputs/api'/rel;lines=p.read_text().splitlines();line=next(i for i,l in enumerate(lines,1) if q in l);api.append({'copy':'inputs/api/'+rel,'sha256':H(p.read_bytes()),'line':line,'match':q})
(ROOT/'evidence/api-line-receipts.json').write_text(json.dumps(api,indent=2)+'\n')
print('PASS: seven-path minimal candidate patch replays exactly; API/pre/post pins sealed')
