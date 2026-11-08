from pathlib import Path
import subprocess,os,json,hashlib,datetime,shutil,resource,time,signal,traceback
R=Path('/srv/android/asus-gpio28-lifecycle-full-kernel-20261107-r1');K=R/'kernel';O=R/'out';E=R/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def cfg(p):
 d={}
 for l in p.read_text().splitlines():
  if l.startswith('CONFIG_'):k,v=l.split('=',1);d[k]=v
  elif l.startswith('# CONFIG_') and l.endswith(' is not set'):d[l.split()[1]]='n'
 return d
assert (E/'preparation.json').is_file() and not (E/'build-status.json').exists()
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
assert resource.getrlimit(resource.RLIMIT_AS)==(-1,-1),'native AS must remain unlimited'
os.environ['TMPDIR']=str(R/'tmp')
for name in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE']:os.environ.pop(name,None)
record=dict(started=now(),pid=os.getpid(),status='running',affinity=sorted(os.sched_getaffinity(0)),max_jobs=1,native_as=resource.getrlimit(resource.RLIMIT_AS),window_seconds=3600,commands=[])
def save():(E/'build-status.json').write_text(json.dumps(record,indent=2)+'\n')
save(); deadline=time.monotonic()+3600
source_bytes=json.loads((E/'source-copy.json').read_text())['allocated_file_bytes']
# Account directory/receipt overhead conservatively without rescanning the full copied source.
output_limit=3*1024**3-source_bytes-96*1024**2
base=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j1']
try:
 tool={}
 expected=json.loads((E/'baseline-toolchains.json').read_text())
 for n in ['aarch64-linux-gnu-gcc','aarch64-linux-gnu-ld','gcc','make']:
  p=Path(shutil.which(n)).resolve();tool[n]=dict(path=str(p),sha256=sha(p),version=subprocess.check_output([n,'--version'],text=True).splitlines()[0]);assert tool[n]==expected[n]
 (E/'toolchains.json').write_text(json.dumps(tool,indent=2)+'\n')
 # Explicit whole translation-unit objects first, then actual DTBs, then full fresh Image link.
 for label,targets in [('olddefconfig',['olddefconfig']),('audio-objects',['sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.o','sound/soc/mediatek/mt_soc_audio_8163/AudDrv_Gpio.o']),('dtbs',['dtbs']),('Image.gz-dtb',['Image.gz-dtb'])]:
  cmd=base+targets;row=dict(command=cmd,started=now());record['commands'].append(row);save()
  with (E/(label+'.log')).open('x') as f:
   p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
   while True:
    remaining=deadline-time.monotonic()
    if remaining<=0:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=5)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
     raise RuntimeError('60-minute compile window expired; owned make group stopped')
    try:code=p.wait(timeout=min(45,remaining));break
    except subprocess.TimeoutExpired:
     # Only this new owned out/tmp/evidence is inspected, never any product path/process/cache.
     allocated=sum(int(subprocess.check_output(['du','-s','-B1',str(R/n)],text=True).split()[0]) for n in ['out','tmp','evidence'])
     record['owned_output_allocated_bytes']=allocated;save()
     if allocated>output_limit:
      os.killpg(p.pid,signal.SIGTERM)
      try:p.wait(timeout=5)
      except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
      raise RuntimeError('owned allocation budget exceeded; make group stopped')
  row.update(exit=code,finished=now());save()
  if code:raise RuntimeError(f'{label} exit {code}')
  if label=='olddefconfig':
   old=cfg(E/'baseline.config');new=cfg(O/'.config');delta={k:{'before':old.get(k),'after':new.get(k)} for k in old.keys()|new.keys() if old.get(k)!=new.get(k)}
   assert delta=={'CONFIG_AMP_AW8737S':{'before':'y','after':'n'},'CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE':{'before':None,'after':'y'}},delta
   (E/'config-delta.json').write_text(json.dumps(delta,sort_keys=True,indent=2)+'\n')
   record['resolved_config_sha256']=sha(O/'.config');save()
 record.update(status='complete',exit=0)
except Exception as e:
 record.update(status='failed',exit=1,error=repr(e));traceback.print_exc()
finally:
 record['finished']=now();save()
raise SystemExit(record['exit'])
