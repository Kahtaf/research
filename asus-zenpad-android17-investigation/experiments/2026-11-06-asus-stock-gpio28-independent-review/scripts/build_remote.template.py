from pathlib import Path
import os,resource,subprocess,json,time,hashlib,signal,base64
R=Path('/srv/android/asus-stock-gpio28-review-20261106-r1');K=R/'kernel';O=R/'out';E=R/'evidence'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(180,180))
signal.alarm(480)
os.nice(10)
assert (E/'initialization.json').exists()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def storage():
    n=sum(p.stat().st_size for p in R.rglob('*') if p.is_file())
    assert n<=4*1024**3,n
    return n
def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(90,90))
    resource.setrlimit(resource.RLIMIT_FSIZE,(128*1024**2,128*1024**2))
    os.setsid()
def run(cmd,name,wall=120):
    assert not (E/(name+'.json')).exists()
    before=storage();start=time.time()
    with (E/(name+'.log')).open('wb') as out:
        p=subprocess.Popen([str(x) for x in cmd],stdout=out,stderr=subprocess.STDOUT,cwd=R,preexec_fn=limits)
        try:code=p.wait(timeout=wall)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);p.wait();code='WALL_TIMEOUT'
    rec=dict(command=[str(x) for x in cmd],exit=code,wall_seconds=time.time()-start,per_process_cpu_seconds=90,wall_limit_seconds=wall,address_space_bytes=resource.getrlimit(resource.RLIMIT_AS),affinity=sorted(os.sched_getaffinity(0)),storage_before=before,storage_after=storage(),log_sha256=sha(E/(name+'.log')))
    (E/(name+'.json')).write_text(json.dumps(rec,indent=2)+'\n')
    print(name,code,flush=True)
    assert code==0,(name,(E/(name+'.log')).read_text()[-5000:])
(R/'inputs/tests/adversarial.c').write_bytes(base64.b64decode(ADVERSARIAL))
run(['gcc','-std=gnu89','-O0','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-Wno-declaration-after-statement','-fsanitize=undefined','-fno-sanitize-recover=all','-pthread',R/'inputs/tests/contract.c','-o',R/'tmp/contract-host'],'original-host-compile',45)
run([R/'tmp/contract-host'],'original-host-run',45)
run(['gcc','-std=gnu89','-O0','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-Wno-declaration-after-statement','-fsanitize=undefined','-fno-sanitize-recover=all','-pthread',R/'inputs/tests/adversarial.c','-o',R/'tmp/adversarial-host'],'adversarial-host-compile',45)
run([R/'tmp/adversarial-host'],'adversarial-host-run',45)
base=['make','-C',K,'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j1','V=1']
run(base+['olddefconfig'],'olddefconfig')
def cfg(p):
    d={}
    for l in p.read_text().splitlines():
        if l.startswith('CONFIG_'):k,v=l.split('=',1);d[k]=v
        elif l.startswith('# CONFIG_') and l.endswith(' is not set'):d[l.split()[1]]='n'
    return d
old=cfg(R/'inputs/preimage/resolved.config');new=cfg(O/'.config')
delta={k:[old.get(k,'n'),new.get(k,'n')] for k in old.keys()|new.keys() if old.get(k,'n')!=new.get(k,'n')}
expected={'CONFIG_AMP_AW8737S':['y','n'],'CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE':['n','y']}
(E/'resolved-config-check.json').write_text(json.dumps(dict(delta=delta,expected=expected,all_other_symbols_preserved=delta==expected,manual_candidate_sha256=sha(R/'config-replay/.config'),actual_resolved_sha256=sha(O/'.config')),indent=2)+'\n')
assert delta==expected,delta
for target,name in [('sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.o','arm64-codec'),('sound/soc/mediatek/mt_soc_audio_8163/AudDrv_Gpio.o','arm64-gpio'),('sound/soc/mediatek/mt_soc_audio_8163/AudDrv_Afe.o','arm64-afe'),('mediatek/asus-p00a.dtb','board-dtb')]:
    run(base+[target],name)
print('AFFECTED_OBJECTS_AND_DTB_COMPLETE',flush=True)
