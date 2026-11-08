from pathlib import Path
import difflib, shutil
R=Path(__file__).resolve().parents[1]
P=R/'patched'
files=['arch/arm64/Kconfig.debug','arch/arm64/kernel/Makefile','arch/arm64/kernel/setup.c','kernel/printk/printk.c','init/main.c']
for f in files:
 p=P/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'source'/f,p)
def replace(f,a,b):
 p=P/f;s=p.read_text();assert s.count(a)==1,(f,a);p.write_text(s.replace(a,b))
replace('arch/arm64/Kconfig.debug','endmenu','''config ASUS_P00A_RETAINED_BOOT_TRACE
	bool "ASUS P00A stock-compatible retained startup trace"
	depends on OF_RESERVED_MEM && PRINTK && ARM64_4K_PAGES
	help
	  Diagnostic only: retain the first startup printk text in the existing
	  MTK ram_console reservation for the shipped 3.18 last_kmsg reader.
	  Refuse unexpected runtime DT or retained header layouts. No storage I/O.
	  Say N outside a controlled diagnostic build.

endmenu''')
replace('arch/arm64/kernel/Makefile','extra-$(CONFIG_EFI)', 'arm64-obj-$(CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE) += asus_retained_trace.o\n\nextra-$(CONFIG_EFI)')
for f in ['arch/arm64/kernel/setup.c','kernel/printk/printk.c','init/main.c']:
 replace(f,'#include <linux/kernel.h>','#include <linux/kernel.h>\n#include <linux/asus_retained_trace.h>')
replace('arch/arm64/kernel/setup.c','\tpaging_init();','\tpaging_init();\n\tasus_retained_trace_init();')
replace('kernel/printk/printk.c','\tlog_next_seq++;\n\n\treturn msg->text_len;', '\tlog_next_seq++;\n\n\tasus_retained_trace_write(log_text(msg), msg->text_len);\n\treturn msg->text_len;')
for old,label in [('\tsetup_arch(&command_line);','02 setup_arch returned'),('\tinit_IRQ();','04 init_IRQ returned'),('\ttime_init();','06 time_init returned')]:
 replace('init/main.c',old,old+'\n\tasus_retained_trace_mark("'+label+'");')
for old,label in [('\tinit_IRQ();','03 before init_IRQ'),('\ttime_init();','05 before time_init')]:
 replace('init/main.c',old,'\tasus_retained_trace_mark("'+label+'");\n'+old)
p=P/'include/linux/asus_retained_trace.h';p.parent.mkdir(parents=True,exist_ok=True)
p.write_text('''/* Diagnostic interface; disabled builds compile all calls away. */
#ifndef _LINUX_ASUS_RETAINED_TRACE_H
#define _LINUX_ASUS_RETAINED_TRACE_H
#include <linux/init.h>
#include <linux/types.h>
#include <linux/string.h>
#ifdef CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE
void __init asus_retained_trace_init(void);
void asus_retained_trace_write(const char *text, unsigned int len);
#else
static inline void asus_retained_trace_init(void) { }
static inline void asus_retained_trace_write(const char *text, unsigned int len) { }
#endif
static inline void asus_retained_trace_mark(const char *text)
{
	asus_retained_trace_write(text, strlen(text));
}
#endif
''')
# New implementation is kept as a reviewable source artifact next to this script.
p=P/'arch/arm64/kernel/asus_retained_trace.c';p.write_text((R/'scripts/asus_retained_trace.c').read_text())
files += ['include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_retained_trace.c']
out=[]
for f in files:
 old=(R/'source'/f).read_text().splitlines(True) if (R/'source'/f).exists() else []
 new=(P/f).read_text().splitlines(True)
 out.extend(difflib.unified_diff(old,new,fromfile='a/'+f if old else '/dev/null',tofile='b/'+f))
(R/'retained-boot-trace.patch').write_text(''.join(out))
(R/'diagnostic.config').write_text('CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE=y\n')
print('Staged',len(files),'files;',len(out),'patch lines')
