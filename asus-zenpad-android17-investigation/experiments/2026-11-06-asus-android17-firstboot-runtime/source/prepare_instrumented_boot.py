from pathlib import Path
import shutil,json,hashlib,difflib
R=Path('/srv/android/asus-firstboot-runtime');I=R/'inputs/boot-r7';shutil.copytree(R/'inputs/boot-r6',I,symlinks=True);root=I/'root';p=root/'system/etc/init/hw/init.rc';before=p.read_text();after=before.replace('on early-init\n','''on early-init
    # Fixture-only read-only measurements before the unchanged platform commands.
    write /dev/kmsg FIRSTBOOT_ENFORCEMENT_BEGIN
    copy /sys/fs/selinux/enforce /dev/kmsg
    write /dev/kmsg FIRSTBOOT_INIT_SID_BEGIN
    copy /proc/1/attr/current /dev/kmsg
    write /dev/kmsg FIRSTBOOT_INIT_SID_END
''',1).replace('    start ueventd\n','''    start ueventd
    # Fixture-only observer: a real shell-domain process and property IPC client.
    wait /dev/console 10
    exec_start firstboot-observer
''',1);assert before!=after;p.write_text(after)
# Remove the later observer trigger: it now runs before an unavailable apexd aborts boot.
f=root/'system/etc/init/firstboot-observe.rc';text=f.read_text();text=text.replace('\non init\n    start firstboot-observer\n','\n');f.write_text(text)
(I/'fixture-init-instrumentation.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='product/system/etc/init/hw/init.rc',tofile='fixture/system/etc/init/hw/init.rc')))
(I/'instrumentation-manifest.json').write_text(json.dumps(dict(before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=hashlib.sha256(after.encode()).hexdigest(),scope='read-only init SID/enforcing observations; bounded console wait; shell observer uses genuine property service, no completion-property writes; all existing platform commands retained'),indent=2));print('instrumented input prepared')
