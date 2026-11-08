"""Package the once-compiled helper; preserve stock kernel and installer mechanics."""
from pathlib import Path
import ast,difflib,gzip,hashlib,json,shutil,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent;PREV=W/'2026-11-07-asus-stock-kernel-sd-control'
sys.path.insert(0,str(R/'source'));import bootformat as b
record=lambda data:dict(bytes=len(data),sha256=b.sha(data))
working=(PREV/'artifacts/candidate.img').read_bytes();assert b.sha(working)=='eccfc87f28169bee14d0675f6ad31335f832ab25db46b013b03a06109b0df13d'
h,k,r,tail=b.parse_image(working);assert not tail
assert b.sha(k)=='b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
oldcp,extra=b.ungzip(r[512:]);entries=b.parse_cpio(oldcp);assert not extra and set(entries)=={'init','dev','proc','sys','sd'}
init=(R/'artifacts/init').read_bytes();elf=b.elf_static(init)
assert record(init)==json.loads((R/'evidence/helper-compile.json').read_text())['init']
entries['init']=(0o100755,0,0,init);cp=b.make_cpio(entries);gz=gzip.compress(cp,compresslevel=9,mtime=0);nr=b.wrap(r,gz)
im=b.make_image(h,k,nr);full=im+bytes(b.PARTITION_SIZE-len(im))
(R/'artifacts/candidate.img').write_bytes(im);(R/'artifacts/candidate.p10.raw').write_bytes(full)
h2,k2,r2,t2=b.parse_image((R/'artifacts/candidate.img').read_bytes());cp2,ex=b.ungzip(r2[512:])
assert not t2 and not ex and cp2==cp and b.parse_cpio(cp2)==entries and k2==k
assert r[:4]==r2[:4] and r[8:512]==r2[8:512]
assert h2[:16]==h[:16] and h2[20:576]==h[20:576] and h2[608:]==h[608:]
raw,dt=b.ungzip(k2[512:]);staged=im[2560:];gzlen=len(k2)-512-len(dt)
assert staged.rfind(bytes.fromhex('d00dfeed'),1,len(k2)+4)==gzlen
assert b.sha(dt)=='77e2d8fbeced5a827ede6c0b8589140e9211d8dc3ca77aaa31a1dd1787a9c455'
# Focused behavioral preservation: every original function except setup/make_report is exact.
oldsrc=(W/'2026-11-07-asus-sd-media-flag-probe/source/init.c').read_text();src=(R/'source/init.c').read_text()
names=['arm_watchdog','bounded_read','text','equals','dev_number','bind_card','same_card','earlier','discover','sd_root','marker','write_report','lifecycle','watchdog_signal','main']
def fn(s,name):
 import re
 m=list(re.finditer(r'^(?:static )?[^\n;]+\b'+name+r'\([^\n;]*\)\{',s,re.M));assert len(m)==1,name
 start=m[0].start();pos=s.index('{',start);depth=1;i=pos+1
 while depth:
  depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return s[start:i]
for name in names:assert fn(src,name)==fn(oldsrc,name),name
marker=b'ASUS-stock-retained-control-20261107-v1 1fd4c968-c0b4-49ab-851a-b0ea4c50c01d'
msg=b'<0>'+marker+b' pid1 /dev/kmsg\n';assert msg in init
assert src.index('retained_marker();')<src.index('if(discover(&b)')
assert fn(src,'retained_marker').count('write(fd,msg,sizeof(msg)-1)')==1
# Worst-case bounded uname and decimal diagnostic values fit report without truncation.
report_max=1024;estimated_max=4*64+len(marker)+len('run_id=dbbb6afb-dd70-4c35-961e-9c977d7164a8\npid1=1\nsysname=\nrelease=\nversion=\nmachine=\nstatus=pid1_uname_observed\nretained_marker=\n')+9*len('kmsg_close_errno=-2147483648\n')
assert estimated_max<report_max
original=(PREV/'source/install.py').read_text();installer=original
edits={"IMAGE_SHA='eccfc87f28169bee14d0675f6ad31335f832ab25db46b013b03a06109b0df13d'":f"IMAGE_SHA='{b.sha(im)}'", "FULL_SHA='4b564d404bc13b20ba44790733a37010fe0677bfced235de2b334c3bff08fa19'":f"FULL_SHA='{b.sha(full)}'",'len(image)==7798784':f'len(image)=={len(im)}',"profile='exact-linux49-microsd-probe'":"profile='stock-retained-report-control'"}
for old,new in edits.items():assert installer.count(old)==1;installer=installer.replace(old,new)
def segment(s,typ,name):return ast.get_source_segment(s,next(n for n in ast.parse(s).body if isinstance(n,typ) and n.name==name))
for typ,name in [(ast.FunctionDef,'execute'),(ast.ClassDef,'Transport')]:assert segment(original,typ,name)==segment(installer,typ,name)
(R/'source/install.py').write_text(installer)
(R/'source/install.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),installer.splitlines(True),fromfile='working-stock/install.py',tofile='retained-control/install.py')))
for name in ['adb','legacy_adb.py']:shutil.copy2(PREV/'source'/name,R/'source'/name)
receipt=dict(status='COMPILED_PACKAGED_PLAN_ONLY_NO_PHYSICAL_TRIAL',working=record(working),image=record(im),full_p10=record(full),init={**record(init),**elf},wrapped_kernel=record(k2),stock_raw_image=record(raw),fdt=record(dt),wrapped_ramdisk=record(nr),cpio=record(cp),kernel_android_offset=2048,ramdisk_android_offset=2048+b.align(len(k2)),header_fields=list(struct.unpack_from('<10I',h2,8)),cmdline=h2[64:576].split(b'\0')[0].decode(),android_id=h2[576:608].hex(),marker=marker.decode(),kmsg_record=msg.decode(),kmsg_record_bytes=len(msg),sd_run_id='dbbb6afb-dd70-4c35-961e-9c977d7164a8',report='PROBE.TXT',lifecycle_seconds=60,preservation=dict(stock_kernel_and_dt_byte_exact=True,header_addresses_page_bootargs_exact=True,ramdisk_entries_only_init_changed=True,mtk_ramdisk_wrapper_only_length_changed=True,unchanged_helper_functions=names,installer_execute_Transport_exact=True,installer_preimages_exact=True,lk_fdt_selection_exact=True),focused_checks=dict(report_bound=estimated_max,report_capacity=report_max,static_AArch64=True,one_kmsg_write=True,kmsg_before_sd_discovery=True),physical_retention_proven=False,device_contacted=False)
(R/'evidence/packaging-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
