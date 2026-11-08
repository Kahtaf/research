from pathlib import Path
import base64,hashlib,json,re
R=Path('/srv/android/asus-minimal-platform-build-20261108');E=R/'evidence';O=R/'out'
status=json.loads((E/'kernel-status.json').read_text());assert status['exit']!=0
log=E/'kernel-compile.log';lines=log.read_text().splitlines();hits=[i for i,l in enumerate(lines) if re.search(r'error:|fatal error:|undefined reference|Error [0-9]',l)]
contexts=[dict(line=i+1,text='\n'.join(lines[max(0,i-6):min(len(lines),i+8)])) for i in hits]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=dict(status='SUBSTANTIVE_KERNEL_COMPILE_FAILURE_STOP_NO_RETRY_NO_PACKAGE',kernel_attempts=1,helper_compile_attempts=1,compiler_errors=contexts,config_sha256_after_make=sha(O/'.config'),config_matches_parent=sha(O/'.config')=='add8f8e85e0fe007364da835f2d45d91663551876387ba4a695e410d4c1cc7bb',image_exists=(O/'arch/arm64/boot/Image.gz-dtb').exists(),vmlinux_exists=(O/'vmlinux').exists(),candidate_exists=(R/'artifacts/candidate.img').exists(),preserved_remote_out=str(O),device_contact=False,packaged=False)
(E/'failure-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
paths={'evidence/kernel-compile.log':log,'evidence/failure-receipt.json':E/'failure-receipt.json','artifacts/resolved-after-make.config':O/'.config'}
for n in ['include/generated/utsrelease.h','include/generated/compile.h','arch/arm64/boot/dts/mediatek/asus-p00a.dtb']:
 if (O/n).is_file():paths['evidence/partial-'+Path(n).name]=O/n
files={}
for n,p in paths.items():d=p.read_bytes();files[n]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
print(json.dumps(dict(files=files,**result)))
