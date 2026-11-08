from pathlib import Path
import difflib,hashlib,json,shutil
R=Path(__file__).resolve().parents[1];I=json.loads((R/'evidence/identity.json').read_text());S=R/'source';B=S/'base'
files=['kernel/printk/printk.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h']
for n in files:
 p=S/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((B/n).read_bytes())
def edit(n,old,new):
 p=S/n;s=p.read_text();assert s.count(old)==1,(n,old);p.write_text(s.replace(old,new))
n='kernel/printk/printk.c'
start=(S/n).read_text().index('static ssize_t devkmsg_write(')
end=(S/n).read_text().index('\nstatic ssize_t devkmsg_read(',start)
s=(S/n).read_text();f=s[start:end]
assert f.count('return -ENOMEM;')==f.count('return -EFAULT;')==1
f=f.replace('\tssize_t ret = len;','\tssize_t ret = len;\n\tu32 write_seq;')
f=f.replace('\tbuf = kmalloc(len+1, GFP_KERNEL);','\twrite_seq = asus_devkmsg_boundary(0, len, 0);\n\tbuf = kmalloc(len+1, GFP_KERNEL);')
f=f.replace('\tif (buf == NULL)\n\t\treturn -ENOMEM;','\tif (buf == NULL) {\n\t\tasus_devkmsg_boundary(write_seq, ret, -ENOMEM);\n\t\treturn -ENOMEM;\n\t}')
f=f.replace('\t\tkfree(buf);\n\t\treturn -EFAULT;','\t\tkfree(buf);\n\t\tasus_devkmsg_boundary(write_seq, ret, -EFAULT);\n\t\treturn -EFAULT;')
f=f.replace('\tkfree(buf);\n\treturn ret;','\tkfree(buf);\n\tasus_devkmsg_boundary(write_seq, ret, ret);\n\treturn ret;')
# An unselected or refused entry returns 0. Do not interpret a return as a new entry.
f=f.replace('asus_devkmsg_boundary(write_seq, ret,', 'asus_devkmsg_boundary(write_seq, ret,')
f=f.replace('\t\tasus_devkmsg_boundary(write_seq, ret, -ENOMEM);','\t\tif (write_seq)\n\t\t\tasus_devkmsg_boundary(write_seq, ret, -ENOMEM);')
f=f.replace('\t\tasus_devkmsg_boundary(write_seq, ret, -EFAULT);','\t\tif (write_seq)\n\t\t\tasus_devkmsg_boundary(write_seq, ret, -EFAULT);')
f=f.replace('\tasus_devkmsg_boundary(write_seq, ret, ret);','\tif (write_seq)\n\t\tasus_devkmsg_boundary(write_seq, ret, ret);')
(S/n).write_text(s[:start]+f+s[end:])
n='include/linux/asus_retained_trace.h'
edit(n,'void asus_retained_trace_write(const char *text, unsigned int len);','void asus_retained_trace_write(const char *text, unsigned int len);\n/* seq=0 admits an entry; nonzero seq records its original return value. */\nu32 asus_devkmsg_boundary(u32 seq, size_t len, ssize_t rc);')
edit(n,'static inline void asus_retained_trace_write(const char *text, unsigned int len) { }','static inline void asus_retained_trace_write(const char *text, unsigned int len) { }\nstatic inline u32 asus_devkmsg_boundary(u32 seq, size_t len, ssize_t rc) { return 0; }')
n='arch/arm64/kernel/asus_entry_tag.h';s=(S/n).read_text().replace('f53fadc2-5cd5-4c44-b5a3-7a65567c6935',I['kernel_uuid']);s=s.replace('profile=sparse-fifo-v1','profile=devkmsg-boundary-v1 format=1 pid1_write_budget=768');(S/n).write_text(s)
I['mode']=next(l.split('"')[1] for l in s.splitlines() if l.startswith('#define ASUS_SPARSE_MODE'))
with (S/n).open('a') as f:f.write('\n#define ASUS_DEVKMSG_PREFIX "ASUS49-KMSG run='+I['kernel_uuid']+' v=1 "\n')
(R/'evidence/identity.json').write_text(json.dumps(I,indent=2)+'\n')
n='arch/arm64/kernel/asus_retained_trace.c'
edit(n,' if (sparse_prefix(text, len, ASUS_SPARSE_WDT_PREFIX,',' if (sparse_prefix(text, len, ASUS_DEVKMSG_PREFIX,\n                   sizeof(ASUS_DEVKMSG_PREFIX) - 1))\n  return true;\n if (sparse_prefix(text, len, ASUS_SPARSE_WDT_PREFIX,')
emitter='''/* One task (actual PID1) owns this counter; user signals cannot nest a
 * devkmsg syscall on its kernel stack. The writer alone masks IRQs briefly.
 * A refused/dropped publication is never evidence of an original operation.
 */
u32 noinline notrace asus_devkmsg_boundary(u32 seq, size_t len, ssize_t rc)
{
 static u32 writes;
 char line[160];
 unsigned int n;
 if (current->pid != 1 || !in_task())
  return 0;
 if (!seq) {
  if (writes >= 768) {
   if (writes == 768) {
    ++writes;
    n = scnprintf(line, sizeof(line), ASUS_DEVKMSG_PREFIX
                  "UNKNOWN reason=write-budget limit=768");
    asus_retained_trace_write(line, n);
   }
   return 0;
  }
  seq = ++writes;
  n = scnprintf(line, sizeof(line), ASUS_DEVKMSG_PREFIX
                "WENT seq=%u len=%zu", seq, len);
 } else {
  n = scnprintf(line, sizeof(line), ASUS_DEVKMSG_PREFIX
                "WRET seq=%u len=%zu rc=%zd", seq, len, rc);
 }
 asus_retained_trace_write(line, n);
 return seq;
}

'''
edit(n,'/* No printk, clocks, allocation, sleep, or hardware access on this path. */\nvoid noinline notrace asus_sparse_wdt_record',emitter+'/* No printk, clocks, allocation, sleep, or hardware access on this path. */\nvoid noinline notrace asus_sparse_wdt_record')
patch='';pins={}
for n in files:
 a=(B/n).read_bytes();z=(S/n).read_bytes();pins[n]=dict(before=hashlib.sha256(a).hexdigest(),after=hashlib.sha256(z).hexdigest())
 patch+=''.join(difflib.unified_diff(a.decode().splitlines(True),z.decode().splitlines(True),fromfile='a/'+n,tofile='b/'+n))
(S/'changes.patch').write_text(patch);(R/'evidence/prepost.json').write_text(json.dumps(pins,indent=2)+'\n')
for n in ['bootformat.py','fdt.py','adb','legacy_adb.py']:
 shutil.copy2(R.parent/'2026-11-08-asus-ram-compute-completion-only/source'/n,S/n)
print(patch)
