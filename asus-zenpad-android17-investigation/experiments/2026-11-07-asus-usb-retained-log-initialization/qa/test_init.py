#!/usr/bin/env python3
"""Run the staged writer itself with host-only kernel/mapping stand-ins."""
from pathlib import Path
import subprocess
root = Path(__file__).resolve().parents[1]
source = (root / 'source/arch/arm64/kernel/asus_retained_trace.c').read_text()
preamble = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
typedef uint32_t u32; typedef uint64_t u64; typedef uint32_t __be32;
typedef uint64_t phys_addr_t;
#define __init
#define __initdata
#define SZ_256K 0x40000U
#define U64_MAX UINT64_MAX
#define PAGE_SIZE 4096
#define ALIGN(x,a) (((x)+((a)-1)) & ~((typeof(x))(a)-1))
#define READ_ONCE(x) (x)
#define WRITE_ONCE(x,v) ((x)=(v))
#define DEFINE_RAW_SPINLOCK(x) int x
#define raw_spin_trylock_irqsave(lock,flags) ((void)(lock),(flags)=0,1)
#define raw_spin_unlock_irqrestore(lock,flags) ((void)(lock),(void)(flags))
#define min(a,b) ((a)<(b)?(a):(b))
#define BUILD_BUG_ON(x) _Static_assert(!(x), #x)
#define pr_warn(...) ((void)0)
static unsigned char ram[0x80000], before[0x80000], image[2];
#define _text image
#define _end (image + 1)
static unsigned long initrd_start, initrd_end;
phys_addr_t __fdt_pointer;
#define __pa_symbol(x) 0x40000000ULL
#define __pa(x) ((u64)(x))
#define __va(x) ((void) (x), ram)
#define of_get_flat_dt_root() 0
#define of_flat_dt_is_compatible(n,s) 1
#define of_get_flat_dt_size() 64
#define of_scan_flat_dt(callback,arg) ((void)(callback), ((struct trace_dt_check *)(arg))->matches=1)
#define memblock_is_region_memory(b,s) 1
#define memblock_is_map_memory(p) 1
#define memblock_is_reserved(p) 1
static const void *of_get_flat_dt_prop(unsigned long n,const char *s,int *len) { return NULL; }
static u32 be32_to_cpup(const __be32 *p) { return *p; }
static u64 of_read_number(const __be32 *p,int n) { return 0; }
static bool mapped;
static unsigned header_cleans; static u32 first_start, first_size, second_start, second_size;
static void *early_memremap(u64 base,unsigned size) { assert(size==0x40000); mapped=true; return ram; }
static void early_memunmap(void *p,unsigned size) { assert(p==ram); mapped=false; }
static void __clean_dcache_area_poc(void *p,unsigned size) {
  if (p==ram && size==64) {
    u32 *w=(u32 *)ram;
    if(header_cleans==0) { first_start=w[13]; first_size=w[14]; }
    if(header_cleans==1) { second_start=w[13]; second_size=w[14]; }
    header_cleans++;
  }
  assert((unsigned char *)p >= ram);
  assert((unsigned char *)p + size <= ram + (mapped ? 0x40000 : sizeof(ram)));
}
void asus_retained_trace_write(const char *,unsigned);
static void asus_retained_trace_mark(const char *s) { asus_retained_trace_write(s,strlen(s)); }
'''
tests = r'''
static struct trace_header *fresh(u32 lk) {
 memset(ram,0xa5,sizeof(ram)); early_committed=false; trace=NULL; mapped=false; header_cleans=0;
 struct trace_header *h=(void *)ram;
 h->sig=TRACE_SIG; h->off_pl=64; h->sz_pl=64; h->off_lpl=128;
 h->off_lk=384; h->sz_lk=lk; h->off_llk=384+ALIGN(lk,64);
 return h;
}
static void untouched_firmware(void) { assert(!memcmp(ram,before,40)); }
int main(void) {
 struct trace_header *h=fresh(64);
 memset((char *)h+40,0,24); memcpy(before,ram,sizeof(ram));
 trace_init(true); assert(early_committed && !trace && !mapped);
 assert(h->sz_buffer==TRACE_SIZE && h->off_linux==512 && h->off_console==1536);
 assert(!memcmp(ram+h->off_console,early_marker,sizeof(early_marker)-1));
 untouched_firmware(); assert(!memcmp(ram+EARLY_MAP_SIZE,before+EARLY_MAP_SIZE,TRACE_SIZE-EARLY_MAP_SIZE));
 trace_init(false); assert(trace==h && h->log_size>sizeof(early_marker)-1);
 assert(!memcmp(ram+h->off_console,early_marker,sizeof(early_marker)-1));
 puts("PASS 1: zero Linux fields initialized, early-to-linear marker preserved");
 h=fresh(64); h->log_start=UINT32_MAX; h->log_size=UINT32_MAX;
 memcpy(before,ram,sizeof(ram)); trace_init(true);
 assert(early_committed && h->log_start==0 && h->log_size==sizeof(early_marker)-1); untouched_firmware();
 assert(first_start==0 && first_size==UINT32_MAX && second_start==0 && second_size==0);
 puts("PASS 2: stale Linux metadata/counters do not reject valid firmware layout");
 for(int kind=0;kind<6;kind++) {
  h=fresh(64);
  if(kind==0) h->sig=0;
  if(kind==1) h->off_lpl++;
  if(kind==2) h->off_llk++;
  if(kind==3) h->off_pl=TRACE_SIZE;
  if(kind==4) h->sz_lk=UINT32_MAX;
  if(kind==5) {h->sz_lk=0;h->off_llk=h->off_lk;h->off_lpl=512;h->off_pl=448;}
  memcpy(before,ram,sizeof(ram)); trace_init(true);
  assert(!trace && !early_committed && !memcmp(ram,before,sizeof(ram)));
 }
 puts("PASS 3: bad signature, PL/LK inconsistency, overflow/range and overlap rejected without writes");
 h=fresh(0x21000); memcpy(before,ram,sizeof(ram)); trace_init(true);
 assert(!early_committed && !trace && !memcmp(ram,before,sizeof(ram)));
 trace_init(false); assert(trace==h && h->log_size>0); untouched_firmware();
 puts("PASS 4: layout beyond 256 KiB left untouched early; valid linear fallback initializes");
 for(int kind=0;kind<7;kind++) {
  h=fresh(64); trace_init(true); assert(early_committed);
  if(kind==0) h->sz_buffer++;
  if(kind==1) h->off_linux++;
  if(kind==2) h->off_console++;
  if(kind==3) h->sz_console++;
  if(kind==4) h->log_start++;
  if(kind==5) h->log_size++;
  if(kind==6) ram[h->off_console]^=1;
  memcpy(before,ram,sizeof(ram)); trace_init(false);
  assert(!trace && !memcmp(ram,before,sizeof(ram)));
 }
 puts("PASS 5: changed committed metadata or marker rejected without writes");
 return 0;
}
'''
translation_unit = root / 'qa/host_init.c'
translation_unit.write_text(preamble + '\n'.join(line for line in source.splitlines() if not line.startswith('#include')) + tests)
subprocess.run(['clang', '-std=gnu11', '-O0', '-fsanitize=address,undefined', str(translation_unit), '-o', str(root / 'qa/host_init')], check=True)
result = subprocess.run([str(root / 'qa/host_init')], capture_output=True, text=True)
(root / 'qa/results.txt').write_text(result.stdout + result.stderr)
print(result.stdout + result.stderr, end='')
result.check_returncode()
