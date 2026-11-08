from pathlib import Path
import difflib,hashlib,json,os,shlex,shutil,subprocess as s,sys
R=Path('/srv/android/asus-network-runtime');T=Path('/srv/android/lineage24');mode=sys.argv[1];O=R/('platform-build-'+mode);O.mkdir();os.environ['TMPDIR']=str(R/'tmp')
old=(R/'inputs/platform-source/bpfloader.rs').read_text();new=old
if mode=='legacy':
 new=new.replace('    // If this is true, the file is allowed to be missing.\n', '    // Minimum actual kernel version for this optional feature/test object.\n    min_kver: u32,\n    // If this is true, the file is allowed to be missing.\n')
 new=new.replace('    allow_missing: false,','    allow_missing: false,\n    min_kver: KVER_NONE,',1)
 new=new.replace('        filename: "/system/etc/bpf/bpfRingbufProg.bpf",','        filename: "/system/etc/bpf/bpfRingbufProg.bpf",\n        // A debug-only ring-buffer self-test; ring buffers were added in 5.8.\n        min_kver: kver(5, 8, 0),')
 new=new.replace('    info!("Loading {}", file_desc.filename);','    info!("Loading {}", file_desc.filename);\n    if kernel_version()? < file_desc.min_kver {\n        info!("Skip {} below its kernel minimum", file_desc.filename);\n        return Ok(());\n    }')
 assert new!=old
 (R/'patches/12-platform-ringbuf-selftest-minimum.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/loader/bpfloader.rs',tofile='b/loader/bpfloader.rs')))
src=O/'bpfloader.rs';src.write_text(new)
cmd=shlex.split((R/'evidence/platform-rust-command.txt').read_text().split(' && ')[0]);assert cmd.pop(0)=='PWD=/proc/self/cwd'
original='out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/unstripped/bpfloader'
for i,arg in enumerate(cmd):
 cmd[i]=arg.replace(original,str(O/'bpfloader'))
 if cmd[i]=='system/bpf/loader/bpfloader.rs':cmd[i]=str(src)
shutil.copyfile(T/(original+'.clang.rsp'),O/'bpfloader.clang.rsp')
cmd+=['-Zthreads=1','-C','link-arg=-Wl,--threads=1']
env=os.environ.copy();env['PWD']='/proc/self/cwd'
with (O/'build.log').open('w') as f:p=s.run(cmd,cwd=T,env=env,stdout=f,stderr=s.STDOUT)
(O/'command.json').write_text(json.dumps(dict(argv=cmd,exit=p.returncode,cwd=str(T),source_sha256=hashlib.sha256(new.encode()).hexdigest()),indent=2)+'\n')
print('rust build',mode,p.returncode,flush=True)
if p.returncode:print((O/'build.log').read_text()[-12000:]);raise SystemExit(p.returncode)
s.run([str(T/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-strip'),'-g',str(O/'bpfloader'),'-o',str(R/'artifacts'/('bpfloader-'+mode))],check=True)
print('artifact sha256',hashlib.sha256((R/'artifacts'/('bpfloader-'+mode)).read_bytes()).hexdigest())
