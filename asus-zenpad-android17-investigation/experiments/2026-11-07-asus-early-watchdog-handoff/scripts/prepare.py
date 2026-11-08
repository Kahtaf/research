from pathlib import Path
import subprocess,shutil,json,hashlib,difflib,resource
from initcall_evidence import analyze
R=Path('/srv/android/asus-early-watchdog-handoff-20261107'); B=Path('/srv/android/asus-early-uart-disabled-kernel-20261107'); K=R/'kernel';O=R/'out';E=R/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,indent=2)+'\n')
assert not K.exists() and not O.exists() and not (E/'prepare-status.json').exists(),'Existing owned attempt refused'
save('prepare-status.json',dict(status='preparing',source_copy='cp -a; no hardlinks',full_tree_rehash=False))
assert resource.getrlimit(resource.RLIMIT_AS)==(-1,-1)
assert shutil.disk_usage(R).free>25*1024**3
assert (B/'out/.config').stat().st_size==126443 and sha(B/'out/.config')=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
assert (B/'out/arch/arm64/boot/Image.gz-dtb').stat().st_size==7711217 and sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='063dad1d9cc03b1c335dd712c9fcb0c36a006e5e99ebee4577e73e669613ac2d'
selected=['drivers/watchdog/mtk_wdt.c','drivers/watchdog/watchdog_core.c','drivers/watchdog/watchdog_dev.c','drivers/base/platform.c','drivers/base/init.c','drivers/of/platform.c','arch/arm64/kernel/setup.c','arch/arm64/kernel/asus_retained_trace.c','include/linux/device.h','include/linux/platform_device.h','include/linux/init.h','include/linux/module.h','init/main.c','drivers/tty/serial/8250/Kconfig','drivers/tty/serial/8250/Makefile']
assert sha(B/'kernel/arch/arm64/kernel/asus_retained_trace.c')=='8373baa301650d2bf3befe547df11a3079e22c51aec8a207de64eae0f1bb3348'
pins={str(B/'kernel'/n):dict(bytes=(B/'kernel'/n).stat().st_size,sha256=sha(B/'kernel'/n)) for n in selected}
for n in ['.config','arch/arm64/boot/Image.gz-dtb','System.map']:pins[str(B/'out'/n)]=dict(bytes=(B/'out'/n).stat().st_size,sha256=sha(B/'out'/n))
save('baseline-selected-pins.json',pins)
save('baseline-initcalls.json',analyze(B/'out/vmlinux',6))
config=(B/'out/.config').read_text()
for symbol in ['DOUGLAS','GIZA','SERIAL_8250_CONSOLE','SERIAL_EARLYCON','SERIAL_CORE_CONSOLE','SERIAL_8250_FSL']:
 assert 'CONFIG_'+symbol+'=y\n' not in config and 'CONFIG_'+symbol+'=m\n' not in config
for symbol in ['SERIAL_8250','SERIAL_8250_MT6577','SERIAL_CORE']:assert 'CONFIG_'+symbol+'=y\n' in config
subprocess.run(['cp','-a',str(B/'kernel'),str(K)],check=True)
copy={n:dict(sha256=sha(K/n),independent_inode=(B/'kernel'/n).stat().st_ino!=(K/n).stat().st_ino) for n in selected}
assert all(v['independent_inode'] and v['sha256']==pins[str(B/'kernel'/n)]['sha256'] for n,v in copy.items())
save('source-copy.json',copy)
n='drivers/watchdog/mtk_wdt.c';before=(K/n).read_text();needle='module_platform_driver(mtk_wdt_driver);'
assert before.count(needle)==1
replacement='''static int __init mtk_wdt_driver_init(void)
{
	return platform_driver_register(&mtk_wdt_driver);
}
arch_initcall(mtk_wdt_driver_init);

static void __exit mtk_wdt_driver_exit(void)
{
	platform_driver_unregister(&mtk_wdt_driver);
}
module_exit(mtk_wdt_driver_exit);'''
after=before.replace(needle,replacement)
(K/n).write_text(after)
assert after.replace(replacement,needle)==before
(R/'source/mtk_wdt.before.c').write_text(before);(R/'source/mtk_wdt.after.c').write_text(after)
patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+n,tofile='b/'+n));(R/'source/watchdog-initcall.patch').write_text(patch)
save('patch-receipt.json',dict(only_source_edit=n,before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=sha(K/n),patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),all_other_bytes_in_file_preserved=True,module_behavior='arch_initcall maps to module_init under MODULE; macro-equivalent init/exit function names and calls retained',hardware_register_policy_changes=False))
O.mkdir();shutil.copyfile(B/'out/.config',O/'.config')
save('prepare-status.json',dict(status='ready',source_copy='cp -a; selected independent inodes verified',full_tree_rehash=False,config_sha256=sha(O/'.config'),source_edits=[n]))
print('Prepared single-file candidate; baseline actual initcall pointers verified')
