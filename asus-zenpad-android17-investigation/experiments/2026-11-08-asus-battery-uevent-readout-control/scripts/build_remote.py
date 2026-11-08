from pathlib import Path
import datetime,hashlib,json,os,resource,shutil,subprocess,sys,traceback,zlib
R=Path(__file__).resolve().parents[1];I=json.loads((R/'evidence/identity.json').read_text());B=Path(I['base_remote']);K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+'\n')
def run(cmd,log):
 with (E/log).open('w') as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 assert q.returncode==0,(cmd,q.returncode,log)
assert not (E/'build-status.json').exists()
assert (E/'CALLER-INVENTORY.md').is_file() and (E/'production-check.json').is_file()
s=dict(status='running',kernel_builds=0,helper_compiles=0);save('build-status.json',s)
try:
 assert resource.getrlimit(resource.RLIMIT_AS)==(-1,-1)
 pins=json.loads((E/'prepost.json').read_text())
 preserved=['arch/arm64/boot/dts/mediatek/mt8163.dtsi','drivers/watchdog/mtk_wdt.c','kernel/sched/core.c','kernel/sched/rt.c','kernel/time/timekeeping.c','drivers/clocksource/arm_arch_timer.c','arch/arm64/lib/delay.c','drivers/misc/mediatek/Makefile','drivers/base/regmap/regmap.c','drivers/misc/mediatek/power/mt8163/asus_p00a/pmic_battery.inc','drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.c','drivers/soc/mediatek/mtk-pmic-wrap.c','drivers/power/supply/mediatek/battery/battery_common.c','kernel/printk/printk.c']
 for n,v in pins.items():assert sha(B/'kernel'/n)==v['before']
 selected=['out/.config','out/arch/arm64/boot/Image.gz-dtb','out/System.map','out/vmlinux']+['kernel/'+n for n in list(pins)+preserved]
 frozen={n:dict(sha256=sha(B/n),inode=(B/n).stat().st_ino,mtime_ns=(B/n).stat().st_mtime_ns) for n in selected}
 assert frozen['out/.config']['sha256']=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
 # Metadata-only space and sharing checks, before ordinary independent full copies.
 metadata={}
 for tree in ['kernel','out']:
  for p in (B/tree).rglob('*'):
   if p.is_file() and not p.is_symlink():
    st=p.stat();metadata[str(p.relative_to(B))]=dict(bytes=st.st_size,inode=st.st_ino,device=st.st_dev)
 needed=sum(v['bytes'] for v in metadata.values());free=shutil.disk_usage(B).free
 save('space-receipt.json',dict(required_logical_bytes=needed,free_bytes=free,reserve_bytes=2*1024**3,adequate=free>needed+2*1024**3,source='filesystem stat metadata only'))
 assert free>needed+2*1024**3
 assert not K.exists() and not O.exists()
 for tree in ['kernel','out']:run(['cp','-a','--reflink=never',str(B/tree),str(R/tree)],'copy-'+tree+'.log')
 for n,v in metadata.items():
  st=(R/n).stat();assert (st.st_dev,st.st_ino)!=(v['device'],v['inode']) and st.st_size==v['bytes'],n
 save('base-freeze.json',frozen)
 relocated=[]
 for p in O.rglob('*'):
  if p.is_file() and not p.is_symlink() and (p.name.endswith('.cmd') or p==O/'Makefile'):
   d=p.read_bytes();z=d.replace(str(B).encode(),str(R).encode())
   if d!=z:p.write_bytes(z);relocated.append(str(p.relative_to(O)))
 if (O/'source').is_symlink():(O/'source').unlink()
 (O/'source').symlink_to(K)
 save('copy-receipt.json',dict(method='cp -a --reflink=never; ordinary full copies authorized; no shared mutable inodes',regular_files_checked=len(metadata),dependency_paths_relocated=relocated,nested_repositories_preserved=True))
 for n,v in pins.items():shutil.copyfile(R/'source'/n,K/n);assert sha(K/n)==v['after']
 before={str(p.relative_to(O)):(p.stat().st_mtime_ns,p.stat().st_size) for p in O.rglob('*.o')};config=(O/'.config').read_bytes()
 for n in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(n,None)
 os.environ.update(TMPDIR=str(R/'tmp'),KBUILD_BUILD_TIMESTAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %H:%M:%S UTC %Y'),KBUILD_BUILD_VERSION='1')
 cmd=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j8','Image.gz-dtb']
 s.update(kernel_builds=1,kernel_command=cmd);save('build-status.json',s);run(cmd,'compile-1.log')
 assert (O/'.config').read_bytes()==config==(B/'out/.config').read_bytes()
 for n,v in frozen.items():
  p=B/n;assert sha(p)==v['sha256'] and p.stat().st_ino==v['inode'] and p.stat().st_mtime_ns==v['mtime_ns'],n
 for n in preserved:assert (B/'kernel'/n).read_bytes()==(K/n).read_bytes()
 for n,v in pins.items():assert sha(K/n)==v['after']
 def unzip(p):
  d=zlib.decompressobj(31);raw=d.decompress(p.read_bytes());assert d.eof;return raw,d.unused_data
 raw,dt=unzip(O/'arch/arm64/boot/Image.gz-dtb');_,bdt=unzip(B/'out/arch/arm64/boot/Image.gz-dtb');assert dt==bdt
 assert I['mode'].encode() in raw and ('ASUS49-ENTRY run='+I['kernel_uuid']).encode() in raw
 assert not any((x+' uuid=').encode() in raw for x in ['A49CAP1','A49SW2','A49WD1','A49PS1','A49PM1','A49DL1'])
 names=['arch/arm64/boot/Image.gz-dtb','.config','System.map','vmlinux']
 save('build-receipt.json',dict(artifacts={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n)) for n in names},config_byte_identical=True,compiled_DT_byte_identical=True,base_scoped_freeze_unchanged=True,preserved_sources=preserved,changed_objects=[str(p.relative_to(O)) for p in O.rglob('*.o') if before.get(str(p.relative_to(O)))!=(p.stat().st_mtime_ns,p.stat().st_size)],helper_compiles=0,kernel_builds=1,hot_header_tags_absent=True))
 for sym in ['power_supply_uevent','power_supply_changed_work','asus_battery_uevent_begin','battery_uevent_omitted','asus_battery_uevent_publish','power_supply_show_property','battery_get_property','asus_pwrap_backstop_publish','asus_retained_trace_write','sparse_admit','devkmsg_write','asus_devkmsg_boundary','power_supply_read_temp','BAT_thread','asus_p00a_soc_update','asus_p00a_battery_read_sample']:
  (E/('linked-'+sym+'.disasm')).write_bytes(subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--disassemble='+sym,str(O/'vmlinux')]))
 nm=subprocess.check_output(['aarch64-linux-gnu-nm','-n','-S',str(O/'vmlinux')],text=True)
 (E/'selected-symbols.txt').write_text('\n'.join(l for l in nm.splitlines() if any(x in l for x in ['pwrap','battery_get_property','pmic_adc','pmic_prepare','sched_clock','opp_tbl_e1','plls','get_cur_phy_freq','set_cur_freq']))+'\n')
 s.update(status='complete')
except BaseException as exc:s.update(status='failed',error=repr(exc));traceback.print_exc()
finally:save('build-status.json',s)
print(json.dumps(s));sys.exit(0 if s['status']=='complete' else 1)
