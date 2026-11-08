#!/usr/bin/env python3
"""Read-only bounded source capture; no remote writes or build commands."""
import subprocess,tarfile,io,pathlib,json,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
paths=['include/linux/fs.h','fs/read_write.c','drivers/watchdog/mtk_wdt.c','net/wireless/nl80211.c','include/linux/inetdevice.h','include/net/if_inet6.h','include/linux/mmc/core.h','drivers/misc/mediatek/chip/mt8163/mt_chip.c','COPYING','Makefile','drivers/misc/mediatek/connectivity','drivers/misc/mediatek/btif','drivers/misc/mediatek/include/mt-plat','drivers/soc/mediatek/mtk-scpsys-mt8163.c','drivers/reset','drivers/clk/mediatek/clk-mt8163.c','drivers/misc/mediatek/pmic/mt6323','drivers/misc/mediatek/emi_mpu','include/net/cfg80211.h','include/linux/netdevice.h','include/linux/timer.h','include/linux/sched.h','include/uapi/linux/nl80211.h','include/net/genetlink.h','arch/arm64/boot/dts/mediatek/mt8163.dtsi','arch/arm64/boot/dts/mediatek/asus-p00a.dts']
ssh=['ssh','-i',str(pathlib.Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(pathlib.Path.home()/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
code='import pathlib,tarfile,sys; r=pathlib.Path("/srv/android/asus-android17/kernel-bpf-fd"); t=tarfile.open(fileobj=sys.stdout.buffer,mode="w|"); '+ '; '.join('t.add(str(r/'+repr(p)+'),arcname='+repr(p)+') if (r/'+repr(p)+').exists() else None' for p in paths)+'; t.close()'
import shlex
p=subprocess.run(ssh+['python3 -c '+shlex.quote(code)],check=True,stdout=subprocess.PIPE)
assert len(p.stdout)<25*1024*1024,len(p.stdout)
dest=root/'sourceinputs/kernel-4.9';dest.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(p.stdout)) as t:
 for m in t:
  assert not pathlib.PurePosixPath(m.name).is_absolute() and '..' not in pathlib.PurePosixPath(m.name).parts
  if m.isfile():
   f=dest/m.name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(t.extractfile(m).read())
print('captured bytes',len(p.stdout))
