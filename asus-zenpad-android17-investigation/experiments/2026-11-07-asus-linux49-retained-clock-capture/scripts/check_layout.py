"""One focused acceptance unit: exercise the actual recorder body with host stubs.
This is synthetic capture-layout QA, never a boot/device execution fixture.
"""
from pathlib import Path
import json,re,subprocess,sys
from decode import decode,SIZE
R=Path(__file__).resolve().parents[1]
identity=json.loads((R/'evidence/identity.json').read_text());uuid=identity['run_uuid']
s=(R/'source/arch/arm64/kernel/asus_retained_trace.c').read_text()
body=s[s.index('/* Fixed ASCII checkpoints'):s.index('static bool __init trace_overlaps')]
body=re.sub(r'^#include .+\n','',body,flags=re.M)
tag=next(l for l in (R/'source/arch/arm64/kernel/asus_entry_tag.h').read_text().splitlines() if l.startswith('#define ASUS_CAPTURE_TAG'))
stubs=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define __init
#define BUILD_BUG_ON(x) _Static_assert(!(x), #x)
#define READ_ONCE(x) (x)
#define WRITE_ONCE(x,v) ((x)=(v))
#define smp_store_release(p,v) (*(p)=(v))
#define smp_load_acquire(p) (*(p))
#define U64_MAX UINT64_MAX
#define ALIGN(x,a) (((x)+(a)-1)&~((a)-1))
typedef uint64_t u64; typedef uint32_t u32;
static int cpu,irq,nmi,lockfail,trace_lock;
static int in_irq(void){return irq;}
static int in_nmi(void){return nmi;}
static int in_interrupt(void){return irq||nmi;}
static int raw_smp_processor_id(void){return cpu;}
static struct {int pid;} task={1};
#define current (&task)
#define raw_spin_trylock_irqsave(lock,flags) ((void)(lock),(flags)=0,!lockfail)
#define raw_spin_unlock_irqrestore(lock,flags) ((void)(lock),(void)(flags))
struct trace_header {u32 sig,off_pl,off_lpl,sz_pl,off_lk,off_llk,sz_lk,padding[3],sz_buffer,off_linux,off_console,log_start,log_size,sz_console;};
static void __clean_dcache_area_poc(void *p,unsigned int n);
'''
tail=r'''
static unsigned char backing[16384] __attribute__((aligned(64)));
static unsigned char interrupted[5952];
static int snapshot_next;
static void __clean_dcache_area_poc(void *p,unsigned int n) {
 if(snapshot_next && cap_area && p==cap_area+192 && n==64 && *(char*)p=='!') {
  memcpy(interrupted,cap_area,5952);snapshot_next=0;
 }
}
static void save(const char *name,void *p,size_t n){FILE*f=fopen(name,"wb");assert(f);assert(fwrite(p,1,n,f)==n);fclose(f);}
int main(void){
 struct trace_header*h=(void*)backing;
 u64 mono,counter,event;unsigned int prior;
 h->off_console=256;h->log_size=91;h->sz_console=sizeof(backing)-256;
 memset(backing+256,'E',91);cap_init(h);
 assert(cap_area && h->log_size==128+5952);prior=h->log_size;
 for(unsigned i=0;i<91;i++)assert(backing[256+i]=='E');
 mono=asus_capture_mono_enter(12,0x1111);assert(mono);
 counter=asus_capture_counter_enter(0x2222);assert(counter);
 asus_capture_exit(counter,0x123456789abc,0);
 cpu=1;asus_capture_mono_seq(mono,12,2);asus_capture_exit(mono,0,12);
 assert(cap_rows[0].f[C_ENTER]==cap_rows[0].f[C_EXIT]);assert(cap_rows[0].f[C_CPU_EXIT]==1);
 for(cpu=0;cpu<4;cpu++){
  irq=1;event=asus_capture_event_enter(0x3333+cpu,0x4444+cpu,1,2);assert(event);
  counter=asus_capture_counter_enter(0x2222);assert(counter);asus_capture_exit(counter,0x9000+cpu,0);
  if(cpu!=3)asus_capture_exit(event,0,0);
 }
 irq=0;cpu=0;
 snapshot_next=1;mono=asus_capture_mono_enter(14,0x1111);assert(mono&&!snapshot_next);
 assert(h->log_size==prior);save("synthetic-valid.rows",cap_area,5952);save("synthetic-interrupted.rows",interrupted,5952);
 assert(!asus_capture_mono_enter(14,0x1111));assert(cap_area[137]=='1');
 save("synthetic-loss.rows",cap_area,5952);
 return 0;
}
'''
code=stubs+'\n'+tag+'\n'+body+tail
(R/'qa/capture-layout.c').write_text(code)
q=subprocess.run(['cc','-std=gnu11','-Wall','-Wextra','-Werror','-o',str(R/'qa/capture-layout'),str(R/'qa/capture-layout.c')],capture_output=True,text=True)
(R/'qa/compile.log').write_text(q.stdout+q.stderr);q.check_returncode()
subprocess.run([str(R/'qa/capture-layout')],cwd=R/'qa',check=True)
valid=decode((R/'qa/synthetic-valid.rows').read_bytes(),uuid)
torn=decode((R/'qa/synthetic-interrupted.rows').read_bytes(),uuid)
loss=decode((R/'qa/synthetic-loss.rows').read_bytes(),uuid)
assert valid['status']=='COMPLETE_CAPTURE_ROWS' and len(valid['records'])==15
by={d['row']:d for d in valid['records']}
assert by[0]['enter']!=by[0]['exit'] and by[0]['complete']==1 and by[0]['entries']==2
assert by[1]['raw']==0x123456789abc and by[1]['complete']==1 and not by[1]['matches_latest_parent']
assert by[14]['enter']!=by[14]['exit'] and by[14]['function']==0x3336 and by[14]['pc']==0x4447
assert by[13]['matches_latest_parent'] and by[13]['complete']==1
assert torn['status']=='UNKNOWN' and 0 in torn['invalid_rows']
assert loss['status']=='UNKNOWN' and loss['loss_latched']
for n,d in [('valid',valid),('interrupted',torn),('loss',loss)]:
 (R/'qa'/('decoded-'+n+'.json')).write_text(json.dumps(d,indent=2)+'\n')
receipt=dict(status='PASS',unit='one actual-recorder-body host layout/commit/token acceptance',synthetic=True,target_execution=False,area_bytes=SIZE,original_markers_preserved=True,append_log_size_advanced_once=True,migration_token_matched=True,separate_task_IRQ_rows_four_cpus=True,returned_counter_preserved=True,nested_entry_latches_unknown=True,interrupted_update_rejected=True,complete_rows_accepted=True)
(R/'evidence/capture-layout-check.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
