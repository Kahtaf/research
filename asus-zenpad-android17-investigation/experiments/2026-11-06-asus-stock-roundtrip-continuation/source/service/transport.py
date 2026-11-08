"""Fixed reviewed I/O. Instantiated only behind the controller's execute gate."""
from __future__ import annotations
import io,json,re,secrets,shlex,subprocess,tarfile,threading,time
from pathlib import Path
import fixed as F
import observer as O
E=F.E

class HostIO:
 def __init__(self,directory):
  self.directory=directory;directory.mkdir(mode=0o700,exist_ok=False);self.sequence=0;self.lock=threading.Lock()
 def command(self,argv,*,script=None,timeout=12,text=False):
  with self.lock:self.sequence+=1;n=self.sequence
  path=self.directory/f'{n:04}.json'
  F.durable(path,dict(argv=argv,stdin=script,status='dispatched'),exclusive=True)
  try:p=subprocess.run(argv,input=script,capture_output=True,text=text,timeout=timeout)
  except (subprocess.TimeoutExpired,OSError) as exc:
   try:F.durable(self.directory/f'{n:04}-result.json',dict(status='uncertain',error=str(exc)),exclusive=True)
   except OSError:pass
   raise O.Unavailable(f'Uncertain command {n}; never retry a mutating command') from exc
  def output(s):return s if isinstance(s,str) else s.decode('utf-8',errors='replace')
  try:F.durable(self.directory/f'{n:04}-result.json',dict(status='returned',exit_status=p.returncode,stdout=output(p.stdout),stderr=output(p.stderr)),exclusive=True)
  except OSError as exc:raise O.Unavailable('Completion could not be made durable; no mutating retry') from exc
  return p
 def inventory(self,timeout=8):
  p=self.command(['adb','devices','-l'],timeout=timeout)
  if p.returncode:raise O.Unavailable('ADB inventory failed')
  return O.inventory(p.stdout.decode('utf-8'))
 def stock_snapshot(self,row,timeout=8):
  F.require(all(row.get(k)==v for k,v in F.STOCK_ROW.items()),'Stock snapshot requires exact stock enumeration')
  tid=row['transport_id'];F.require(re.fullmatch('[0-9]+',tid),'Invalid enumeration ID')
  token=secrets.token_hex(16)
  pairs=[(k,'getprop '+k) for k in F.STOCK_PROPS]
  pairs += [('enforce','getenforce'),('uid','id -u'),('context','cat /proc/self/attr/current'),
            ('kernel','cat /proc/version'),('boot_id','cat /proc/sys/kernel/random/boot_id'),('flash_recovery','getprop init.svc.flash_recovery')]
  lines=['set -eu',f"printf 'ASUS_STOCK_BEGIN_{token}\\n'"]
  for label,cmd in pairs:lines.append("printf '%s\\t%s\\n' "+shlex.quote(label)+' "$('+cmd+')"')
  lines.append(f"printf 'ASUS_STOCK_END_{token}\\n'")
  p=self.command(['adb','-t',tid,'shell','\n'.join(lines)],timeout=timeout)
  if p.returncode:raise O.Unavailable('Stock snapshot command did not complete')
  data=p.stdout.decode('utf-8').replace('\r\n','\n').splitlines()
  if len(data)!=len(pairs)+2 or data[0]!=f'ASUS_STOCK_BEGIN_{token}' or data[-1]!=f'ASUS_STOCK_END_{token}':raise O.Unavailable('Incomplete stock snapshot')
  result={}
  for line,(key,_) in zip(data[1:-1],pairs):
   F.require(line.startswith(key+'\t'),'Misordered stock snapshot');result[key]=line[len(key)+1:]
  return result
 def report(self,row,timeout=12):
  F.require(all(row.get(k)==v for k,v in F.DIAG_ROW.items()),'Report requires exact diagnostic enumeration')
  F.require(re.fullmatch('[0-9]+',row['transport_id']),'Invalid report transport')
  return self.command(['adb','-t',row['transport_id'],'shell','report'],timeout=timeout)
 def entry(self,pin):
  # Exactly one service request. The audited adbd implementation sends a volatile
  # property and waits; EOF/status/timeout alone never proves reboot or failure.
  argv=['adb','-t',pin['initial_transport_id'],'reboot','recovery']
  try:p=self.command(argv,timeout=15)
  except O.Unavailable as exc:return dict(delivery='unknown',error=str(exc),requests=1)
  out=p.stdout.decode('utf-8',errors='replace').replace('\r\n','\n').strip()
  known_failure=out=='reboot failed: -1' and p.returncode in (0,1) and not p.stderr
  return dict(delivery='explicit_service_failure' if known_failure else 'completion_unconfirmed',
              exit_status=p.returncode,stdout=out,requests=1)
 def ensure_tcp(self,pin,returned):
  F.require(returned['snapshot']['boot_id']!=pin['stock_boot_id'] and O.stock_ready(returned['snapshot']),
            'TCP reenable requires an actual new healthy stock boot')
  row=O.usb_row(self.inventory(),pin)
  F.require(row is not None and row['serial']==F.SERIAL,'Normal USB unavailable for stock cleanup')
  s=self.stock_snapshot(row)
  F.require(O.stock_ready(s) and s['boot_id']==returned['snapshot']['boot_id'],'Stock cleanup boot identity changed')
  matches=[r for r in self.inventory() if r['serial']==F.ENDPOINT]
  F.require(len(matches)<=1,'Ambiguous pinned TCP endpoint')
  if matches and matches[0]['state']=='device':return
  # Re-enable only the already-authorized secure TCP service. No key, listener
  # port, host ADB server, firewall, or authentication configuration changes.
  p=self.command(['adb','-t',row['transport_id'],'tcpip','5555'],timeout=8)
  if p.returncode or p.stdout.decode().strip()!='restarting in TCP mode port: 5555':
   raise F.Unknown('TCP re-enable completion uncertain; no retry')
  p=self.command(['adb','connect',F.ENDPOINT],timeout=8)
  if p.returncode or p.stdout.decode().strip() not in ('connected to '+F.ENDPOINT,'already connected to '+F.ENDPOINT):
   raise F.Unknown('Fixed TCP connection unavailable; no retry')

class Transport(E.AdbRootTransport):
 """Inherited writer methods/guards unchanged; fresh sessions and stricter health."""
 def __init__(self,directory,journal,action,run_id,phase,boot_id,io):
  super().__init__(directory,journal,action)
  F.valid_run(run_id);F.require(phase in ('preflight','install','entry-guard','restore','restore-guard','restore-verification'),'Invalid phase')
  F.require(O.UUID.fullmatch(boot_id),'Invalid expected boot ID')
  self.session=E.BASE+'/stockv2-'+run_id+'-'+phase
  self.vault=self.session+'/vault';self.inbox=self.session+'/inbox';self.boot_id=boot_id;self.io=io;self.extra=set()
 def command(self,argv,*,script=None,timeout=90):
  self.sequence+=1
  try:return self.io.command(argv,script=script,timeout=timeout,text=True)
  except O.Unavailable as exc:raise E.UncertainTransport(str(exc)) from exc
 def healthy(self):
  super().healthy()
  F.require(self.adb(['shell','cat','/proc/sys/kernel/random/boot_id'])==self.boot_id,'Stock boot ID changed during operation')
  F.require(self.adb(['shell','cat','/proc/version'])==F.KERNEL_BANNER,'Current stock kernel banner mismatch')
  F.require(self.adb(['shell','getprop','init.svc.flash_recovery'])=='stopped','Stock recovery autorepair still running')
 def root(self,body,label):
  fixed=f'''[ "$(cat /proc/sys/kernel/random/boot_id)" = '{self.boot_id}' ]
[ "$(getprop init.svc.flash_recovery)" = stopped ]
[ "$(cat /proc/version)" = '{F.KERNEL_BANNER}' ]'''
  return super().root(fixed+'\n'+body,label)
 def blob(self,source,name,limit):
  self.extra.add(name)
  self.root(f'''{self.stage_guard()}
[ ! -L {source} ]
[ -f {source} ]
[ "$(wc -c < {source})" -le {limit} ]
[ ! -e {self.vault}/{name} ]
[ ! -L {self.vault}/{name} ]
cp {source} {self.vault}/{name}
{self.export(self.vault+'/'+name)}''','read_'+name)
  return self.pull_blob(name,limit)
 def pull_blob(self,name,limit):
  p=self.directory/f'{self.sequence:03}-{name}'
  self.adb(['pull',self.inbox+'/readback.bin',str(p)])
  data=F.read(p,limit);self.journal.event('guard_readback',name=name,bytes=len(data),sha256=F.sha(data),path=str(p))
  return data
 def safety_snapshot(self,expected_p10,rc_manifest):
  self.healthy();self.setup();self.extra.add('para.bin')
  self.root(f'''{self.stage_guard()}
{METADATA_GUARDS}
[ ! -e {self.vault}/para.bin ]
[ ! -L {self.vault}/para.bin ]
dd if=/dev/block/mmcblk0p12 of={self.vault}/para.bin bs=512 count=1024
[ "$(wc -c < {self.vault}/para.bin)" -eq 524288 ]
{self.export(self.vault+'/para.bin')}''','read_para_and_guard_cache')
  para=self.pull_blob('para.bin',F.PARA_SIZE)
  F.require(len(para)==F.PARA_SIZE and F.sha(para)==F.PARA_SHA,'Current entire para differs from known-good normal preimage; never clear it')
  F.require(F.sha(self.blob('/init','init.bin',2*1024*1024))==F.INIT_SHA,'Current init is not the audited stock binary')
  F.require(F.sha(self.blob('/sbin/adbd','adbd.bin',2*1024*1024))==F.ADBD_SHA,'Current adbd is not the audited stock binary')
  self.extra.add('rc.tar')
  self.root(f'''{self.stage_guard()}
set --
asus_rc_bytes=0
for asus_rc in /*.rc /system/etc/init/*.rc /system/vendor/etc/init/*.rc /system/odm/etc/init/*.rc; do
    if [ ! -e "$asus_rc" ] && [ ! -L "$asus_rc" ]; then continue; fi
    [ ! -L "$asus_rc" ]
    [ -f "$asus_rc" ]
    asus_rc_bytes=$((asus_rc_bytes + $(wc -c < "$asus_rc")))
    [ "$asus_rc_bytes" -le 1048576 ]
    set -- "$@" "$asus_rc"
    [ "$#" -le 128 ]
done
[ "$#" -gt 0 ]
[ ! -e {self.vault}/rc.tar ]
[ ! -L {self.vault}/rc.tar ]
tar -cf {self.vault}/rc.tar "$@"
{self.export(self.vault+'/rc.tar')}''','read_exact_init_rc_set')
  raw=self.pull_blob('rc.tar',2*1024*1024)
  actual={}
  with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as t:
   for m in t:
    F.require(m.isfile() and m.size<=1048576 and '..' not in m.name.split('/'),'Unexpected RC archive member')
    name='/'+m.name.lstrip('/');F.require(name not in actual,'Duplicate RC file')
    f=t.extractfile(m);data=f.read(1048577);F.require(len(data)==m.size,'Incomplete RC archive')
    actual[name]=F.sha(data)
  F.require(actual=={p:r['sha256'] for p,r in rc_manifest.items()},'Current RC set differs from exact audited stock boot/system')
  before=self.read();allowed=(expected_p10,) if isinstance(expected_p10,str) else expected_p10
  actual_p10=F.sha(before)
  F.require(len(before)==F.SIZE and actual_p10 in allowed,'Fresh full p10 readback mismatch')
  self.root(METADATA_GUARDS,'recheck_cache_without_mutation')
  self.healthy()
  self.journal.event('fresh_stock_safety_snapshot',p10_sha256=actual_p10,para_sha256=F.PARA_SHA,
                     init_sha256=F.INIT_SHA,adbd_sha256=F.ADBD_SHA,rc_set_verified=True,cache_command_absent=True)
  self.cleanup();self.healthy()
 def cleanup(self):
  if self.stage_created and self.extra:
   F.require(self.extra<=set(('para.bin','init.bin','adbd.bin','rc.tar')),'Unexpected cleanup file')
   self.root(self.stage_guard()+'\nrm -f '+' '.join(self.vault+'/'+p for p in sorted(self.extra)),'cleanup_guard_files')
   self.extra.clear()
  return super().cleanup()

METADATA_GUARDS='''[ -b /dev/block/mmcblk0p12 ]
[ "$(readlink -f /dev/block/mmcblk0p12)" = /dev/block/mmcblk0p12 ]
[ "$(readlink -f /dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para)" = /dev/block/mmcblk0p12 ]
[ "$(cat /sys/class/block/mmcblk0p12/partition)" = 12 ]
[ "$(cat /sys/class/block/mmcblk0p12/start)" = 225576 ]
[ "$(cat /sys/class/block/mmcblk0p12/size)" = 1024 ]
[ "$(cat /sys/class/block/mmcblk0p12/dev)" = 179:12 ]
asus_para_node=$(ls -ln /dev/block/mmcblk0p12)
set -- $asus_para_node
[ "$#" -eq 9 ] && [ "$5" = 179, ] && [ "$6" = 12 ] && [ "$9" = /dev/block/mmcblk0p12 ]
[ -b /dev/block/mmcblk0p24 ]
[ "$(readlink -f /dev/block/mmcblk0p24)" = /dev/block/mmcblk0p24 ]
[ "$(readlink -f /dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/cache)" = /dev/block/mmcblk0p24 ]
[ "$(cat /sys/class/block/mmcblk0p24/partition)" = 24 ]
[ "$(cat /sys/class/block/mmcblk0p24/start)" = 662824 ]
[ "$(cat /sys/class/block/mmcblk0p24/size)" = 409600 ]
[ "$(cat /sys/class/block/mmcblk0p24/dev)" = 179:24 ]
asus_cache_node=$(ls -ln /dev/block/mmcblk0p24)
set -- $asus_cache_node
[ "$#" -eq 9 ] && [ "$5" = 179, ] && [ "$6" = 24 ] && [ "$9" = /dev/block/mmcblk0p24 ]
[ ! -L /cache ] && [ -d /cache ]
[ "$(awk '$2 == "/cache" {n++} END {print n+0}' /proc/mounts)" = 1 ]
asus_cache_source=$(awk '$2 == "/cache" {print $1}' /proc/mounts)
[ "$(readlink -f "$asus_cache_source")" = /dev/block/mmcblk0p24 ]
[ "$(awk '$2 == "/cache" {print $3}' /proc/mounts)" = ext4 ]
[ ! -L /cache/recovery ]
if [ -e /cache/recovery ]; then [ -d /cache/recovery ]; fi
[ ! -L /cache/recovery/command ]
[ ! -e /cache/recovery/command ]
# Exact MTK battery uevent names/units are captured in root-hardware-baseline.txt.
asus_battery_mv=$(awk -F= '$1 == "POWER_SUPPLY_BATT_VOL" {print $2}' /sys/class/power_supply/battery/uevent)
[ "$asus_battery_mv" -ge 3700 ] && [ "$asus_battery_mv" -le 4500 ]
[ "$(awk -F= '$1 == "POWER_SUPPLY_PRESENT" {print $2}' /sys/class/power_supply/battery/uevent)" = 1 ]
[ "$(awk -F= '$1 == "POWER_SUPPLY_HEALTH" {print $2}' /sys/class/power_supply/battery/uevent)" = Good ]
[ "$(awk -F= '$1 == "POWER_SUPPLY_CAPACITY" {print $2}' /sys/class/power_supply/battery/uevent)" -ge 50 ]
asus_battery_temp=$(awk -F= '$1 == "POWER_SUPPLY_BATT_TEMP" {print $2}' /sys/class/power_supply/battery/uevent)
[ "$asus_battery_temp" -ge 100 ] && [ "$asus_battery_temp" -le 450 ]
[ "$(awk -F= '$1 == "POWER_SUPPLY_ONLINE" {print $2}' /sys/class/power_supply/usb/uevent)" = 1 ]
printf 'ASUS_STOCK_BATTERY_MV=%s\\n' "$asus_battery_mv"'''
