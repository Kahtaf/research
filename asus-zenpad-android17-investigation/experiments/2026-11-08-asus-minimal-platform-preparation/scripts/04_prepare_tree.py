from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess
B=Path('/srv/android/asus-linux49-calibrated-entry-build-20261107');K=B/'kernel';O=B/'out';R=Path('/srv/android/asus-minimal-platform-preparation-20261108')
assert not R.exists()
usage=shutil.disk_usage('/srv/android')
size=int(subprocess.check_output(['du','-sb',str(K)],text=True).split()[0]);assert usage.free>size+1024**3
R.mkdir();(R/'out').mkdir();(R/'evidence').mkdir()
subprocess.run(['cp','-a',str(K),str(R/'kernel')],check=True)
checks={}
for n in ['arch/arm64/kernel/head.S','arch/arm64/kernel/asus_retained_trace.c','drivers/misc/mediatek/power/mt8163/asus_p00a/control.h','arch/arm64/boot/dts/mediatek/asus-p00a.dts']:
 a=K/n;b=R/'kernel'/n
 checks[n]=dict(sha256=hashlib.sha256(b.read_bytes()).hexdigest(),independent_inode=a.stat().st_ino!=b.stat().st_ino)
 assert checks[n]['independent_inode'] and a.read_bytes()==b.read_bytes()
shutil.copyfile(O/'.config',R/'out/.config')
conf=O/'scripts/kconfig/conf';assert conf.is_file()
files={}
for n in ['init/main.c','arch/arm64/kernel/setup.c']:
 b=(K/n).read_bytes();files['source/baseline/'+n]=dict(data=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest())
# Existing linked artifact only; no compilation or relinking.
v=O/'vmlinux'
names=['BAT_thread','bat_thread_kthread','mt_cpufreq_thermal_protect','mt_gpufreq_thermal_protect','tscpu_set_power_consumption_state','tscpu_set_cur_state','mtktsbattery_get_temp','mtktspmic_get_temp','p00a_apply','p00a_monitor','p00a_hw_init','devkmsg_write']
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-n',str(v)],text=True)
selected=[l for l in nm.splitlines() if len(l.split())==3 and (l.split()[2] in names or any(x in l.split()[2] for x in ['sysrst','kshutdown','thermal_protect','is_usb_rdy']))]
for n in names:
 data=subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--disassemble='+n,str(v)],text=True).encode()
 if len(data)<100000:files['evidence/baseline-linked-'+n+'.txt']=dict(data=base64.b64encode(data).decode(),sha256=hashlib.sha256(data).hexdigest())
receipt=dict(remote_owned_root=str(R),baseline=str(B),free_before=usage.free,source_tree_bytes=size,copy='ordinary independent cp -a; no hardlinks/reflink or out copy',checks=checks,conf_sha256=hashlib.sha256(conf.read_bytes()).hexdigest(),existing_vmlinux_sha256=hashlib.sha256(v.read_bytes()).hexdigest(),selected_symbols=selected,production_files_this_read=['init/main.c','arch/arm64/kernel/setup.c'])
(R/'evidence/copy-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(files=files,**receipt)))
