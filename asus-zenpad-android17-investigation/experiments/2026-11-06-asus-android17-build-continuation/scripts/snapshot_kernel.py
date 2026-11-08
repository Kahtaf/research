#!/usr/bin/env python3
import pathlib,subprocess,hashlib,json,tarfile,datetime
R=pathlib.Path('/srv/android/asus-build-continuation'); R.mkdir(exist_ok=False)
for d in ('evidence','logs','inputs','artifacts'): (R/d).mkdir()
K=pathlib.Path('/srv/android/asus-android17/kernel-bpf-fd'); D=R/'kernel'
def run(*cmd): return subprocess.check_output(cmd)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
head=run('git','-C',str(K),'rev-parse','HEAD').decode().strip();assert head=='717bb3c9e13ce573cfdd2dda856debd27a0fa17f'
paths=sorted(set(run('git','-C',str(K),'ls-files','-z','--cached','--others','--exclude-standard').decode().strip('\0').split('\0')))
before={p:sha(K/p) for p in paths if (K/p).is_file()}
subprocess.run(['git','clone','--no-hardlinks','--no-checkout',str(K),str(D)],check=True)
archive=R/'inputs/active-soc-source.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in paths:t.add(K/p,arcname=p,recursive=False)
with tarfile.open(archive) as t:t.extractall(D,filter='data')
subprocess.run(['git','-C',str(D),'reset','--mixed',head],check=True,stdout=subprocess.DEVNULL)
after={p:sha(K/p) for p in before}; copied={p:sha(D/p) for p in before};assert before==after==copied
config=pathlib.Path('/srv/android/asus-android17/build-main-battery-soc-r1/.config')
(R/'inputs/soc.config').write_bytes(config.read_bytes())
(R/'evidence/active-soc.patch').write_bytes(run('git','-C',str(K),'diff','--binary','HEAD'))
(R/'evidence/snapshot.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),head=head,source=str(K),fixture=str(D),files=before,archive_sha256=sha(archive),config_sha256=sha(config),active_unchanged=True),indent=2)+'\n')
print('Pinned',len(before),'source files; active source unchanged')
