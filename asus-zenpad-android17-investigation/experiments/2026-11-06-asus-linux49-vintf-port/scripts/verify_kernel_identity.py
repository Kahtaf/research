from pathlib import Path
import hashlib,json,zlib,re
root=Path(__file__).resolve().parents[1]
a=root.parent/'2026-11-06-asus-bmc156-full-kernel/artifacts'
k=(a/'Image.gz-dtb').read_bytes();c=(a/'resolved.config').read_bytes();h=lambda b:hashlib.sha256(b).hexdigest()
assert h(k)=='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'
z=zlib.decompressobj(31);raw=z.decompress(k,32*1024*1024);assert z.eof and not z.unconsumed_tail
start=raw.index(b'IKCFG_ST')+8;end=raw.index(b'IKCFG_ED',start);embedded=zlib.decompress(raw[start:end],31)
assert embedded==c and h(c)=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
banner=re.search(rb'Linux version [^\x00\n]+',raw).group().decode(errors='replace')
receipt={'input_kernel':str(a/'Image.gz-dtb'),'kernel_sha256':h(k),'kernel_bytes':len(k),'raw_image_bytes':len(raw),'embedded_config_sha256':h(embedded),'resolved_config_sha256':h(c),'embedded_config_matches_resolved':True,'banner':banner,'max_decompressed_bytes':32*1024*1024,'physical_or_runtime_validation':False}
(root/'evidence/kernel-identity.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
