"""Stage a supplemental patch over the delivered e9 retained-writer source."""
from pathlib import Path
import difflib,hashlib,json,shutil,subprocess
R=Path(__file__).resolve().parents[1];W=R.parent;BASE=W/'2026-11-07-asus-linux49-retained-boot-trace/patched'
rels=['arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/setup.c','include/linux/asus_retained_trace.h']
original={p:(BASE/p).read_text() for p in rels};new=original.copy()
p=rels[0];s=new[p]
s=s.replace('#include <linux/initrd.h>','#include <linux/initrd.h>\n#include <linux/io.h>\n#include <linux/sizes.h>')
s=s.replace('#include <asm/cacheflush.h>', '#include <asm/cacheflush.h>\n#include <asm/early_ioremap.h>')
s=s.replace('static struct trace_header *trace;','''/* One fixmap slot is at most 256 KiB on this tree. Never map the full ring
 * before paging. Only the guarded Linux reason area and entry text are touched.
 */
#define EARLY_MAP_SIZE SZ_256K
static const char early_marker[] =
	"ASUS-e9-retained-v2 00 arm64_memblock_init returned; before paging_init\\n";
static bool early_committed __initdata;
static struct trace_header *trace;''')
s=s.replace('void __init asus_retained_trace_init(void)','static void __init trace_init(bool early)')
s=s.replace('/* paging_init has made the sole normal-cacheable linear mapping usable. */\n\th = __va(TRACE_BASE);','''/* Match PAGE_KERNEL normal-cacheable attributes; never use early_ioremap's
	 * Device alias. The temporary mapping is removed before paging_init.
	 */
	h = early ? early_memremap(TRACE_BASE, EARLY_MAP_SIZE) : __va(TRACE_BASE);
	if (!h)
		goto refuse;''')
start=s.index('\t/* Preserve PL/LK headers and payloads.')
end=s.index('\nrefuse:',start)
s=s[:start]+'''	/* Additional early-map bounds do not weaken any OEM/DT/memblock guard.
	 * Layouts outside this window retain the original post-paging path.
	 */
	if (early && (h->off_linux > EARLY_MAP_SIZE - TRACE_RR_SIZE ||
		      h->off_console > EARLY_MAP_SIZE - (sizeof(early_marker) - 1)))
		goto unmap;
	if (!early && early_committed &&
	    (h->log_start || h->log_size != sizeof(early_marker) - 1 ||
	     memcmp((char *)h + h->off_console, early_marker,
		    sizeof(early_marker) - 1)))
		goto unmap;

	/* Preserve PL/LK headers and payloads. Preserve the committed early text
	 * when switching from the temporary fixmap to the linear mapping.
	 */
	if (!early_committed) {
		h->log_start = 0;
		__clean_dcache_area_poc(h, sizeof(*h));
		h->log_size = 0;
		__clean_dcache_area_poc(h, sizeof(*h));
		memset((char *)h + h->off_linux, 0, TRACE_RR_SIZE);
		__clean_dcache_area_poc((char *)h + h->off_linux, TRACE_RR_SIZE);
	}
	WRITE_ONCE(trace, h);
	if (early) {
		asus_retained_trace_write(early_marker, sizeof(early_marker) - 1);
		early_committed = h->log_size == sizeof(early_marker) - 1;
		WRITE_ONCE(trace, NULL);
	} else {
		asus_retained_trace_mark("ASUS-e9-retained-v2 01 paging_init returned; trace ready");
	}
unmap:
	if (early)
		early_memunmap(h, EARLY_MAP_SIZE);
	return;''' + s[end:]
# Existing header guard failure must unmap a successful temporary mapping.
start=s.index('\tpl_end =');end=s.index('\t/* Additional early-map bounds')
part=s[start:end];assert part.count('goto refuse;')==1
s=s[:start]+part.replace('goto refuse;','goto unmap;')+s[end:]
s+='''
void __init asus_retained_trace_early_init(void)
{
	trace_init(true);
}

void __init asus_retained_trace_init(void)
{
	trace_init(false);
}
'''
new[p]=s
new[rels[1]]=new[rels[1]].replace('\tarm64_memblock_init();','\tarm64_memblock_init();\n\tasus_retained_trace_early_init();')
new[rels[2]]=new[rels[2]].replace('void __init asus_retained_trace_init(void);','void __init asus_retained_trace_early_init(void);\nvoid __init asus_retained_trace_init(void);').replace('static inline void asus_retained_trace_init(void) { }','static inline void asus_retained_trace_early_init(void) { }\nstatic inline void asus_retained_trace_init(void) { }')
patch='';pins={}
for p in rels:
 for d,txt in [('trace-before',original[p]),('trace-after',new[p])]:
  dest=R/'source'/d/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(txt)
 pins[p]=dict(before_sha256=hashlib.sha256(original[p].encode()).hexdigest(),after_sha256=hashlib.sha256(new[p].encode()).hexdigest())
 patch+=''.join(difflib.unified_diff(original[p].splitlines(True),new[p].splitlines(True),fromfile='a/'+p,tofile='b/'+p))
(R/'source/early-retained-checkpoint.patch').write_text(patch)
# Apply once to disposable copies and compare the real resulting files.
qa=R/'qa/trace-patch-final';assert not qa.exists();shutil.copytree(R/'source/trace-before',qa)
proc=subprocess.run(['patch','--batch','-p1','-i',str(R/'source/early-retained-checkpoint.patch')],cwd=qa,capture_output=True,text=True)
assert proc.returncode==0,proc.stderr
for p in rels:assert (qa/p).read_text()==new[p]
# Shared safety guards and post-paging write algorithm are preserved exactly.
def chunk(s,a,z):return s[s.index(a):s.index(z,s.index(a))]
assert chunk(original[rels[0]],'void asus_retained_trace_write','void __init asus_retained_trace_init')==chunk(new[rels[0]],'void asus_retained_trace_write','static void __init trace_init')
assert chunk(original[rels[0]],'\tpl_end =','\t/* Preserve PL/LK').replace('goto refuse;','goto unmap;')==chunk(new[rels[0]],'\tpl_end =','\t/* Additional early-map bounds')
assert chunk(original[rels[0]],'\tBUILD_BUG_ON','\t/* paging_init')==chunk(new[rels[0]],'\tBUILD_BUG_ON','\t/* Match PAGE_KERNEL')
(R/'evidence/next-trace-patch.json').write_text(json.dumps(dict(status='STAGED_SUPPLEMENTAL_PATCH_NOT_FULL_KERNEL_BUILT',base_patch_sha256=hashlib.sha256((W/'2026-11-07-asus-linux49-retained-boot-trace/retained-boot-trace.patch').read_bytes()).hexdigest(),patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),files=pins,applies_cleanly=True,all_original_safety_guards_exact=True,append_cache_commit_lock_algorithm_exact=True,early_marker='ASUS-e9-retained-v2 00 arm64_memblock_init returned; before paging_init',early_mapping='early_memremap(0x44400000, 0x40000); PAGE_KERNEL normal cacheable; unmapped before paging_init',full_reservation='0x44400000..0x44480000',physical_proof=False),indent=2)+'\n')
print(proc.stdout)
