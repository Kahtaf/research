from pathlib import Path
import sys,json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'));import bootformat as b
A=R/'artifacts';sha=lambda x:hashlib.sha256(x).hexdigest()
(R/'tests/probe_binding.h').write_text('#define PROBE_HELPER_SHA "'+sha((A/'p10-restore').read_bytes())+'"\n#define PROBE_INIT_SHA "'+sha((A/'core-inputs/init').read_bytes())+'"\n')
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wl,--build-id=none','tests/concat_probe.c','-o','artifacts/concat-probe']
p=subprocess.run(cmd,cwd=R,capture_output=True,text=True);assert p.returncode==0,p.stderr
# Candidate's two members are exact; a separate third test-only cpio holds probe.
rd=(A/'core.cpio.gz').read_bytes()+(A/'candidate/helper.cpio').read_bytes()+b.make_cpio({'concat-probe':(0o100755,0,0,(A/'concat-probe').read_bytes())})
(A/'concat-test.initramfs').write_bytes(rd)
kernel=Path('/srv/android/asus-target-rescue/build/compat-out/arch/arm64/boot/Image')
cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-cpu','cortex-a53','-accel','tcg,thread=single,tb-size=16','-smp','1','-m','384','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(kernel),'-initrd',str(A/'concat-test.initramfs'),'-append','console=ttyAMA0 rdinit=/concat-probe panic=-1 loglevel=5']
try:
 p=subprocess.run(cmd,capture_output=True,timeout=25);rc=p.returncode;output=p.stdout+p.stderr
except subprocess.TimeoutExpired as e:rc=124;output=(e.stdout or b'')+(e.stderr or b'')
(R/'evidence/concat-guest.log').write_bytes(output)
passed=b'CONCAT_TWO_MEMBERS_ACTUAL_HELPER_EXEC_PASS_NO_DEVICE_IO' in output
(R/'evidence/concat-guest.json').write_text(json.dumps(dict(passed=passed,command=cmd,returncode=rc,kernel_sha256=sha(kernel.read_bytes()),actual_candidate_members=True,test_only_third_member=True,stock_hardware_kernel=False,physical_validation=False,block_devices_attached=False),indent=2)+'\n')
assert passed,output[-3000:]
print('CONCAT_GUEST_PASS')
