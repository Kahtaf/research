from pathlib import Path
import os,json,subprocess as s,hashlib,shutil,tarfile,io
R=Path('/srv/android/asus-odsign-startup-20261106');P=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');R.mkdir(exist_ok=True);
for n in ['source','inputs','evidence','tmp']: (R/n).mkdir(exist_ok=True)
os.environ['TMPDIR']=str(R/'tmp')
for n in ['root-enabled-admission.json','runtime-bin-preserved.json','final-seal.json']:
 shutil.copyfile(P/'evidence'/n,R/'evidence'/n)
debug=Path('/srv/android/asus-full-system-observer-preparation-20261106/immutable/bin/debugfs');env=os.environ.copy();env['LD_LIBRARY_PATH']=str(debug.parents[1]/'lib64');raw=json.loads((R/'evidence/root-enabled-admission.json').read_text())['raw_identity']['path'];receipts=[]
for path in ['system/etc/init/odsign.rc','system/bin/odsign']:
 dest=R/'inputs'/Path(path).name;p=s.run([str(debug),'-R','dump /'+path+' '+str(dest),raw],env=env,capture_output=True,text=True,timeout=20);receipts.append(dict(path=path,rc=p.returncode,stdout=p.stdout,stderr=p.stderr))
 if dest.is_file():receipts[-1]['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest()
git='/srv/android/lineage24/.repo/projects/system/security.git';rev=s.check_output(['git','--git-dir='+git,'rev-parse','HEAD'],text=True).strip();b=s.check_output(['git','--git-dir='+git,'archive',rev,'ondevice-signing']);(R/'inputs/art-odsign.tar').write_bytes(b)
with tarfile.open(fileobj=io.BytesIO(b)) as t:t.extractall(R/'inputs/art-source',filter='data')
sgit='/srv/android/lineage24/.repo/projects/system/sepolicy.git';policy=[]
for path in ['private/odsign.te','public/odsign.te']:
 p=s.run(['git','--git-dir='+sgit,'show','d61fd80832f558d52de026097d30d695634e8b0f:'+path],capture_output=True)
 if p.returncode==0:(R/'inputs'/Path(path).name.replace('.te','-'+path.split('/')[0]+'.te')).write_bytes(p.stdout)
receipt=dict(actual_raw_reads=receipts,art_immutable_git_object=rev,archive_sha256=hashlib.sha256(b).hexdigest(),active_working_source_or_out_read=False,r3_visibility='serial odsign pid651 started89.821s; prior observer process filter excluded odsign, logcat filter excluded odsign/odrefresh; no internal cause observable')
(R/'evidence/input-inspection.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2));print((R/'inputs/odsign.rc').read_text())
for f in (R/'inputs/art-source/ondevice-signing').glob('*.cc'):
 lines=f.read_text().splitlines();selected=[str(i+1)+': '+x for i,x in enumerate(lines) if any(w in x for w in ['key.done','LOG_TAG','LOG(','WaitFor','waitFor','wait_for','sleep','main(', 'Parse','KeyMint','Keymaster'])];print(f.name);print('\n'.join(selected)[:13000])
