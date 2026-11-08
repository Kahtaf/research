from pathlib import Path
import hashlib,subprocess,json,gzip,sys,struct
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'source'))
from bootformat import make_cpio
name=sys.argv[1];block_test='blocks' in name;assert name.startswith('qemu-') and '/' not in name
out=R/'evidence'/name;out.mkdir()
candidate=Path(sys.argv[2]) if len(sys.argv)>2 else R/'artifacts/candidate-data-r1'
tools=Path(sys.argv[3]) if len(sys.argv)>3 else R/'artifacts'
kernel=R/'inputs/fixture-Image'
assert hashlib.sha256(kernel.read_bytes()).hexdigest()=='113c4f19c736b949626c62bbf68cf23c9e3c5a821ec6ab031a5684cdcba14431'
files={'init':tools/'guest-init','guest-helper':tools/'guest-init','target-probe':tools/'target-probe','sbin/os-rescue':tools/'os-rescue','system/bin/sh':tools/'rescue-proxy','sepolicy':candidate/'rescue-sepolicy'}
entries={n:(0o40755,0,0,b'') for n in ['dev','proc','sys','tmp','sbin','system','system/bin']}
for n,p in files.items():entries[n]=(0o100755 if n!='sepolicy' else 0o100644,0,0,p.read_bytes())
entries['rescue.manifest']=(0o100444,0,0,b'ASUSR002'+struct.pack('<II',2,0)+bytes(96))
if block_test:
 entries['require-block-probe']=(0o100444,0,0,b'1')
 entries['ueventd']=(0o100755,0,0,(R/'inputs/stock-init').read_bytes())
 contexts=(candidate/'file_contexts').read_text()+'\n/dev/block/vda u:object_r:rescue_system_device:s0\n/dev/block/vdb u:object_r:rescue_recovery_device:s0\n'
 (out/'file_contexts').write_text(contexts)
 subprocess.run([str(tools/'sefcontext_compile'),str(out/'file_contexts')],check=True)
 entries['file_contexts.bin']=(0o100644,0,0,(out/'file_contexts.bin').read_bytes())
 entries['ueventd.rc']=(0o100644,0,0,b'/dev/block/vda 0600 root root\n/dev/block/vdb 0600 root root\n')
 for n in ['a','b']:
  with (out/('disk-'+n+'.raw')).open('xb') as f:f.truncate(16777216)
initrd=out/'guest.cpio.gz';initrd.write_bytes(gzip.compress(make_cpio(entries),mtime=0))
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-cpu','cortex-a53','-smp','2','-m','1536','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(kernel),'-initrd',str(initrd),'-append','console=ttyAMA0 rdinit=/init panic=-1 loglevel=8 audit=1'+(' selinux=0' if 'missing' in name else ' selinux=1 enforcing=1')]
if block_test:
 for n in ['a','b']:cmd+=['-drive',f'file={out}/disk-{n}.raw,format=raw,if=none,id=disk{n}','-device',f'virtio-blk-device,drive=disk{n}']
(out/'command.json').write_text(json.dumps(cmd,indent=2))
with (out/'serial.log').open('w') as f:
 try:p=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,timeout=60);rc=p.returncode
 except subprocess.TimeoutExpired:rc=124
text=(out/'serial.log').read_text();passed=rc==0 and 'QEMU_RESCUE_RESULT failures=0' in text
(out/'result.json').write_text(json.dumps(dict(passed=passed,returncode=rc,kernel_sha256=hashlib.sha256(kernel.read_bytes()).hexdigest(),policy_sha256=hashlib.sha256(files['sepolicy'].read_bytes()).hexdigest(),daemon_sha256=hashlib.sha256(files['sbin/os-rescue'].read_bytes()).hexdigest(),proxy_sha256=hashlib.sha256(files['system/bin/sh'].read_bytes()).hexdigest(),physical=False),indent=2))
print(text[-12000:]);sys.exit(0 if passed else 1)
