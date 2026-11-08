"""Execute exact saved stock init in a disposable QEMU guest.
A guest-only adbd-domain test service reports success through init's exit log.
The deliverable ramdisk is never edited."""
from pathlib import Path
import gzip,json,subprocess,sys,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'))
from bootformat import parse_cpio,ungzip,make_cpio
name=sys.argv[1];candidate=Path(sys.argv[2]) if len(sys.argv)>2 else R/'artifacts/candidate-r3';out=R/'evidence'/name;out.mkdir()
entries=parse_cpio(ungzip((candidate/'rescue.cpio.gz').read_bytes())[0])
entries['guest-helper']=(0o100755,0,0,(Path(sys.argv[4]) if len(sys.argv)>4 else R/'artifacts/guest-init').read_bytes())
m,u,g,b=entries['init.rc']
b+=b'\non boot\n    start rescue-test\n\nservice rescue-test /guest-helper stock-client\n    seclabel u:r:adbd:s0\n    user root\n    group root\n    disabled\n    oneshot\n'
# The minimal recovery init has no late-init boot trigger; trigger the test at init.
b=b.replace(b'on early-init\n',b'on early-init\n    write /dev/.coldboot_done 1\n')
b=b.replace(b'    start adbd\n',b'    start adbd\n    start rescue-test\n')
b=b.replace(b'rescue-test',b'rescue_test')
# Only the disposable observer restarts, so stock init logs its exit code.
# The delivered os-rescue service remains oneshot (never auto-restarted).
head,observer=b.split(b'service rescue_test ',1);b=head+b'service rescue_test '+observer.replace(b'    oneshot\n',b'')
entries['init.rc']=(m,u,g,b)
initrd=out/'guest.cpio.gz';initrd.write_bytes(gzip.compress(make_cpio(entries),mtime=0))
kernel=Path(sys.argv[3]) if len(sys.argv)>3 else R/'inputs/fixture-Image'
if len(sys.argv)<=3:assert hashlib.sha256(kernel.read_bytes()).hexdigest()=='113c4f19c736b949626c62bbf68cf23c9e3c5a821ec6ab031a5684cdcba14431'
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-cpu','cortex-a53','-smp','2','-m','1536','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(kernel),'-initrd',str(initrd),'-append','console=ttyAMA0 rdinit=/init panic=-1 loglevel=8 audit=1 selinux=1 enforcing=1 androidboot.selinux=enforcing androidboot.hardware=mt8163 androidboot.mode=recovery']
(out/'command.json').write_text(json.dumps(cmd,indent=2))
with (out/'serial.log').open('w') as f:
 try:p=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,timeout=25);rc=p.returncode
 except subprocess.TimeoutExpired:rc=124
text=(out/'serial.log').read_text()
passed="Service 'rescue_test'" in text and 'exited with status 42' in text
(out/'result.json').write_text(json.dumps(dict(passed=passed,returncode=rc,kernel_sha256=hashlib.sha256(kernel.read_bytes()).hexdigest(),stock_init_sha256=hashlib.sha256(entries['init'][3]).hexdigest(),policy_sha256=hashlib.sha256(entries['sepolicy'][3]).hexdigest(),daemon_sha256=hashlib.sha256(entries['sbin/os-rescue'][3]).hexdigest(),test_only_service_added=True,physical=False),indent=2)+'\n')
print(text[-18000:]);sys.exit(0 if passed else 1)
