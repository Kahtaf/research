from pathlib import Path
import os,json,subprocess as s,stat,hashlib,datetime
R=Path('/srv/android/asus-final-image-startup-20261107');I=R/'inputs';E=R/'evidence';status=json.loads((R/'run-runtime/status.json').read_text());assert status['finished_utc']
p=s.run(['/usr/sbin/debugfs','-R','dump /local/tmp/actual-runtime-report.txt '+str(E/'public-report-raw.txt'),str(I/'data.ext4')],capture_output=True,text=True,timeout=15);(E/'report-extraction.json').write_text(json.dumps(dict(rc=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0
text=(E/'public-report-raw.txt').read_text(errors='replace');seen=set();out=[]
for line in text.splitlines():
 if line not in seen:out.append(line);seen.add(line)
(E/'public-report-compact.txt').write_text('\n'.join(out)+'\n')
serial=(R/'run-runtime/serial.log').read_text(errors='replace');need=['odsign','odrefresh','NetBpfLoad','bpf.progs_loaded','zygote','aconfig','linkerconfig','apexd.status','keystore.module','all packages','Activated','keymaster','shared secret','earlyBootEnded','avc: denied','panic']
highlights=[]
for i,line in enumerate(serial.splitlines(),1):
 if any(n in line for n in need):highlights.append(f'{i}: {line}')
(E/'serial-highlights.txt').write_text('\n'.join(highlights)+'\n')
for p in [I/'data.ext4',I/'runtime-initramfs.cpio.gz',I/'system.qcow2']:os.chmod(p,0o400)
def identity(p):
 x=p.stat();return dict(path=str(p),dev=x.st_dev,inode=x.st_ino,bytes=x.st_size,mtime_ns=x.st_mtime_ns,ctime_ns=x.st_ctime_ns,mode=oct(stat.S_IMODE(x.st_mode)))
a=json.loads((E/'admission.json').read_text());base=Path(a['system']['path']);boot=Path(a['boot']['path']);assert identity(base)==a['system'] and identity(boot)==a['boot']
files=[p for p in R.rglob('*') if p.is_file() and not p.is_symlink()]
d=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),system_identity_before=a['system'],system_identity_after=identity(base),boot_identity_before=a['boot'],boot_identity_after=identity(boot),base_unchanged=True,boot_unchanged=True,published_system_sha256=a['published_system_sha256'],published_report_sha256=a['published_report_sha256'],no_fullraw_hash_or_materialization=True,cow=dict(bytes=(I/'system.qcow2').stat().st_size,allocated_bytes=(I/'system.qcow2').stat().st_blocks*512,sha256=hashlib.sha256((I/'system.qcow2').read_bytes()).hexdigest()),owned_logical_bytes=sum(p.stat().st_size for p in files),owned_allocated_bytes=sum(p.stat().st_blocks*512 for p in files),runtime=status,retained_remote=['DATA','fresh entropy inside private runtime initramfs','COW','serial','full public report'],export_scope='Serial, compact public observer report, scripts and summary/receipts only; no DATA or entropy input')
(E/'base-unchanged-receipt.json').write_text(json.dumps(d,indent=2));print(json.dumps({'serial_bytes':len(serial),'public_raw_bytes':len(text),'public_compact_bytes':(E/'public-report-compact.txt').stat().st_size,'system_unchanged':True,'boot_unchanged':True,'finished_utc':status['finished_utc']},indent=2))
print('ODSIGN_AND_NEXT');print('\n'.join(x for x in out if any(n in x.lower() for n in ['odsign','odrefresh','dex2oat','netbpfload','bpf.progs_loaded','zygote','public_process','selinux/enforce']))[-22000:])
