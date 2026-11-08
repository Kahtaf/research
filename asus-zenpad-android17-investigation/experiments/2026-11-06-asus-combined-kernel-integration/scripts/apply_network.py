from pathlib import Path
import hashlib,json,shutil,subprocess,fcntl,datetime
R=Path('/srv/android/asus-build-continuation');K=R/'kernel';H=Path('/srv/android/asus-network-runtime/handoff-r1');E=R/'integration-r5';E.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,j): (E/n).write_text(json.dumps(j,indent=2)+'\n')
with (R/'logs/kernel.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert (R/'logs/kernel-r4.exit-code').read_text().strip()=='0'
 assert (R/'logs/kernel-r4.complete').exists()
 assert not (R/'logs/kernel-r5.started').exists()
 assert sha(R/'build/arch/arm64/boot/Image.gz-dtb')=='34a2032db2173b2937fa1862160647b612e813a66e37cf998e1fa74c7119ec94'
 assert sha(R/'build/.config')=='067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f'
 archive=E/'preserved-r4';archive.mkdir(exist_ok=True)
 for rel in ['arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image','arch/arm64/boot/dts/mediatek/asus-p00a.dtb','.config','System.map','vmlinux']:
  src=R/'build'/rel;dst=archive/src.name;shutil.copy2(src,dst);assert sha(src)==sha(dst)
 for f in (R/'logs').glob('kernel-r4.*'):shutil.copy2(f,archive/f.name)
 for rel in ['combined-source-receipt.json','combined-from-active-soc.patch','firstboot-cgroups-applied.json','network-staging.json']:
  p=R/'evidence'/rel
  if p.exists():shutil.copy2(p,archive/rel)
 assert sha(H/'manifest.json')=='d6790e2efde8ddb11102f561b5c58129660be09d41f1bbfb66402f3865ef13dd'
 m=json.loads((H/'manifest.json').read_text())
 assert len(m['sha256'])==60
 for p,h in m['sha256'].items():assert sha(H/p)==h,p
 first=json.loads((R/'evidence/firstboot-cgroups-applied.json').read_text())
 for row in first['files']:assert sha(K/row['path'])==row['after_sha256'],row
 for p,row in m['kernel_changed_files'].items():assert (sha(K/p) if (K/p).exists() else None)==row['baseline_sha256'],p
 config=(R/'build/.config').read_text()
 for opt in ['FILE_LOCKING','BLK_CGROUP']:assert f'CONFIG_{opt}=y\n' in config
 for opt in ['DUMMY','VETH','NAMESPACES','NET_NS']:assert f'CONFIG_{opt}=y\n' not in config
 patchdir=E/'patches';patchdir.mkdir()
 results=[]
 for n in m['kernel_patch_order']:
  q=patchdir/n;shutil.copy2(H/'patches'/n,q)
  result=subprocess.run(['patch','--batch','--forward','--fuzz=0','-p1','-i',str(q)],cwd=K,text=True,capture_output=True)
  results.append(dict(patch=n,sha256=sha(q),returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
  save('network-apply-in-progress.json',results)
  assert result.returncode==0 and 'fuzz' not in result.stdout and 'offset' not in result.stdout,result
 for p,row in m['kernel_changed_files'].items():assert sha(K/p)==row['tested_sha256'],p
 for row in first['files']:assert sha(K/row['path'])==row['after_sha256'],row
 for p,row in m['connectivity_changed_files'].items():
  assert sha(R/'platform-connectivity'/p)==row['tested_sha256'],p
  assert sha(Path('/srv/android/lineage24/packages/modules/Connectivity')/p)==row['baseline_sha256'],p
 save('network-applied.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),manifest=sha(H/'manifest.json'),files=m['kernel_changed_files'],patches=results,firstboot_preserved=first['files'],connectivity=m['connectivity_changed_files'],active_aosp_modified=False,virtual_config_copied=False,patch12_applied=False))
print('Archived r4; all60 handoff hashes verified; four patches applied with fuzz0 and exact postimages; firstboot and staged Connectivity11 preserved.')
log=(R/'logs/kernel-r5.log').open('xb');p=subprocess.Popen(['bash',str(R/'build_combined.sh'),'r5'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(R/'logs/kernel-r5.pid').write_text(str(p.pid)+'\n');print('Launched isolated combined kernel r5 maxj4 PID',p.pid)
