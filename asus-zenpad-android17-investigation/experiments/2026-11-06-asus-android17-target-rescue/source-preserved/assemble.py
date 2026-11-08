"""Offline assembly with exact stock kernel/init/adbd and a reviewed manifest or unarmed default.
No ADB/device operations. Never overwrites an output directory."""
import argparse,base64,gzip,hashlib,json,stat,struct,subprocess
from pathlib import Path
from bootformat import *
from file_contexts import derive,extract
from client import parse
S=Path(__file__).resolve().parent
def regular(p,limit):
 st=p.lstat()
 if not stat.S_ISREG(st.st_mode) or st.st_size>limit:raise ValueError('bounded ordinary file required: '+str(p))
 return p.read_bytes()
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--stock',type=Path,required=True);a.add_argument('--stock-verify',type=Path,required=True);a.add_argument('--public-key',type=Path,required=True);a.add_argument('--tools',type=Path,required=True);a.add_argument('--manifest',type=Path);a.add_argument('--manifest-sha256');a.add_argument('--out',type=Path,required=True);v=a.parse_args()
 stock=regular(v.stock,PARTITION_SIZE);assert len(stock)==PARTITION_SIZE and sha(stock)==RECOVERY_SHA and regular(v.stock_verify,PARTITION_SIZE)==stock
 h,k,r,trailer=parse_image(stock);old=parse_cpio(ungzip(r[512:])[0])
 cmd=h[64:576].split(b'\0')[0];assert cmd.count(b'androidboot.selinux=permissive')==1
 cmd=cmd.replace(b'androidboot.selinux=permissive',b'androidboot.selinux=enforcing');h=h[:64]+cmd+bytes(512-len(cmd))+h[576:]
 assert v.public_key.name.endswith('.pub')
 public=regular(v.public_key,2048).decode('ascii').split()[0];key=base64.b64decode(public,validate=True)
 assert len(key)==524 and struct.unpack_from('<I',key)[0]==64 and struct.unpack_from('<I',key,520)[0]==65537
 manifest=b'ASUSR001'+struct.pack('<II',1,0)+bytes(96)
 if v.manifest:
  manifest=regular(v.manifest,1024*1024)
  if sha(manifest)!=v.manifest_sha256:raise ValueError('explicit reviewed manifest hash required')
  if not parse(manifest):raise ValueError('armed build requires image records')
 v.out.mkdir(parents=True,exist_ok=False)
 (v.out/'stock-sepolicy').write_bytes(old['sepolicy'][3])
 userdata=len(parse(manifest))==5
 result=subprocess.run([str(v.tools/'policy_build'),str(v.out/'stock-sepolicy'),str(v.out/'rescue-sepolicy')]+(['--userdata'] if userdata else []),capture_output=True,text=True,check=True)
 (v.out/'policy-delta.txt').write_text(result.stdout)
 entries={n:(0o40755,0,0,b'') for n in ['dev','proc','sys','tmp','sbin','system','system/bin','data']}
 for name in ['init','sbin/adbd','property_contexts','seapp_contexts','service_contexts']:entries[name]=old[name]
 entries['sbin/ueventd']=(0o120777,0,0,b'../init')
 for n,tool,mode in [('sbin/os-rescue','os-rescue',0o100700),('sbin/rescue-proxy','rescue-proxy',0o100755),('system/bin/sh','rescue-proxy',0o100755)]:
  data=regular(v.tools/tool,2*1024*1024);elf_static(data);entries[n]=(mode,0,0,data)
 entries['sepolicy']=(0o100644,0,0,(v.out/'rescue-sepolicy').read_bytes())
 contexts=derive(old['file_contexts.bin'][3]);(v.out/'file_contexts').write_bytes(contexts)
 subprocess.run([str(v.tools/'sefcontext_compile'),str(v.out/'file_contexts')],check=True)
 compiled=(v.out/'file_contexts.bin').read_bytes()
 from collections import Counter
 expected=[]
 for line in contexts.decode().splitlines():
  fields=line.split();expected.append((fields[0],fields[1] if len(fields)==3 else '',fields[-1]))
 assert Counter(extract(compiled))==Counter(expected)
 entries['file_contexts.bin']=(0o100644,0,0,compiled)
 entries['adb_keys']=(0o100444,0,0,public.encode()+b'\n')
 entries['rescue.manifest']=(0o100444,0,0,manifest)
 for name in ['init.rc','default.prop','ueventd.rc']:entries[name]=(0o100644,0,0,(S/name).read_bytes())
 cpio=make_cpio(entries);assert parse_cpio(cpio)==entries
 gz=bytearray(gzip.compress(cpio,compresslevel=9,mtime=0));gz[9]=255
 image=make_image(h,k,wrap(r,gz));padded=image+bytes(PARTITION_SIZE-len(image))
 (v.out/'UNTESTED-target-rescue.img').write_bytes(image);(v.out/'UNTESTED-target-rescue.p10.raw').write_bytes(padded);(v.out/'rescue.cpio.gz').write_bytes(gz)
 contract=dict(mode='PARENT_REVIEW_REQUIRED',manifest_sha256=sha(manifest),p10_full_sha256=sha(padded),p10_bytes=len(padded),kernel_wrapped_sha256=sha(k),original_recovery_sha256=RECOVERY_SHA,armed=bool(v.manifest),userdata_enabled=userdata,physical_validation=False)
 (v.out/'session-contract.UNAPPROVED.json').write_text(json.dumps(contract,indent=2)+'\n')
 report=dict(contract=contract,image_bytes=len(image),image_sha256=sha(image),headroom=PARTITION_SIZE-len(image),policy_sha256=sha(entries['sepolicy'][3]),public_key_rsa_sha256=sha(key),private_key_included=False,stock_preserved={n:sha(old[n][3]) for n in ['init','sbin/adbd']},file_contexts_stock_rows=len(extract(old['file_contexts.bin'][3])),entries={n:dict(mode=oct(m),uid=u,gid=g,bytes=len(b),sha256=sha(b)) for n,(m,u,g,b) in sorted(entries.items())},elfs={n:elf_static(entries[n][3]) for n in ['init','sbin/adbd','sbin/os-rescue','system/bin/sh']},sources={p.name:sha(p.read_bytes()) for p in sorted(S.glob('*')) if p.is_file()})
 (v.out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(contract,indent=2))
if __name__=='__main__':main()
