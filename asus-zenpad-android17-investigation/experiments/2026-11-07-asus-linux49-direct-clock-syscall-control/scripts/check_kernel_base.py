"""Offline exact public assembly-base check; no candidate/static-ELF claim."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent;B=W/'2026-11-07-asus-linux49-runnable-timer-format-fix'
sys.path.insert(0,str(R/'source'));import bootformat as b,fdt
image=(B/'artifacts/candidate.img').read_bytes();full=(B/'artifacts/candidate.p10.raw').read_bytes()
assert len(image)==7974912 and b.sha(image)=='13033865fe5c88952efe2d5e429246a76a08689be604fb89a4776afa990c4ab8'
assert full==image+bytes(b.PARTITION_SIZE-len(image)) and b.sha(full)=='88f79cc02d71bfe0708d6be77d66d06d3107befcee3d5d0225ecc8134942f617'
h,k,ram,tail=b.parse_image(image);assert not tail
compiled=(B/'artifacts/Image.gz-dtb').read_bytes();config=(B/'artifacts/resolved.config').read_bytes()
assert b.sha(compiled)=='97b7e1199d607f852bf52ff7766e8aa079fee92986cd3d473b765a45adbf45fb'
assert b.sha(config)=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
raw,dt=b.ungzip(k[512:]);cr,cd=b.ungzip(compiled);stream=k[512:-len(dt)]
assert raw==cr and stream==compiled[:-len(cd)]
assert b.sha(raw)=='60755a9910450cb0303157017ddb4f6ff08874fca32bf70298bb5a91d5450381'
assert b.sha(stream)=='29437894a38cba034db136aa5ea3f1c930edf6ff6abcfc14a4dd652ceeebc491'
_,nodes,_=fdt.parse(dt);_,cn,_=fdt.parse(cd);ch=nodes['/chosen']
assert {p:v for p,v in nodes.items() if p!='/chosen'}=={p:v for p,v in cn.items() if p!='/chosen'}
assert ch['linux,initrd-start']==bytes.fromhex('44000000') and ch['linux,initrd-end']==bytes.fromhex('4403e975')
args=ch['bootargs'].rstrip(b'\0');assert args==h[64:576].rstrip(b'\0')
assert args==b'bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1 printk.devkmsg=on nohlt'
assert len(ram)-512==256373 and ram[512:]==(B/'artifacts/initramfs.cpio.gz').read_bytes()
rec=dict(status='EXACT_PUBLIC_BASE_VERIFIED_NO_NEW_CANDIDATE',image_sha256=b.sha(image),full_p10_sha256=b.sha(full),compiled_kernel_sha256=b.sha(compiled),config_sha256=b.sha(config),runtime_gzip_sha256=b.sha(stream),raw_Image_sha256=b.sha(raw),cmdline=args.decode(),chosen_initrd_end='0x4403e975',existing_guard='0x44000000..0x4403f007',compressed_limit_bytes=258055,candidate_static_ELF_check='NOT_RUN_NO_COMPILED_HELPER',hardware_properties_match_compiled_DTB=True)
(R/'evidence/kernel-base-receipt.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec,indent=2))
