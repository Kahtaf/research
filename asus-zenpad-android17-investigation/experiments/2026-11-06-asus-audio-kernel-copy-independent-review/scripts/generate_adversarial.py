from pathlib import Path
import re,hashlib,json
p=Path(__file__).resolve().parents[1];i=p/'inputs';w=p/'adversarial';(w/'tests').mkdir(parents=True,exist_ok=True)
for f in ['generated.c','cases.c','shim.h']:(w/'tests'/f).write_bytes((i/'tests'/f).read_bytes())
s=(w/'tests/shim.h').read_text().replace('struct status { int state; };','struct status { int state; unsigned long hw_ptr; };\nstruct control { unsigned long appl_ptr; };')
s=s.replace('unsigned frame_bits, channels;','struct control *control; unsigned long hw_ptr_wrap, boundary; unsigned frame_bits, channels;')
s=s.replace('pthread_mutex_t lock; };','pthread_mutex_t lock; int f_flags; };')
s=s.replace('#define SNDRV_PCM_STATE_PREPARED 2','#define SNDRV_PCM_STATE_OPEN 0\n#define SNDRV_PCM_STATE_SETUP 1\n#define SNDRV_PCM_STATE_DISCONNECTED 8\n#define SNDRV_PCM_STATE_PREPARED 2')
s=s.replace('static void lock_spin(spinlock_t *p) {', 'static void (*review_before_ring_lock)(void);\nstatic void lock_spin(spinlock_t *p) { if(review_before_ring_lock) { void (*h)(void)=review_before_ring_lock; review_before_ring_lock=NULL; h(); }')
(w/'tests/shim.h').write_text(s)
records=[]
def fn(rel,name):
 s=(i/'source/original'/rel).read_text();m=re.search(r'^(?:static )?[^;{}#\n]+\b'+name+r'\([^;{}]*\)\n\{',s,re.M);assert m
 body=s[m.start():s.index('\n}',m.end())+2];records.append({'source':rel,'function':name,'sha256':hashlib.sha256(body.encode()).hexdigest()});return body
head='''#define main supplied_suite_main
#include "generated.c"
#undef main
#define snd_pcm_stream_lock_irq(s) stream_lock(s)
#define snd_pcm_stream_unlock_irq(s) stream_unlock(s)
static int snd_pcm_running(struct snd_pcm_substream *s) { return s->runtime->status->state == SNDRV_PCM_STATE_RUNNING; }
static int snd_pcm_update_hw_ptr(struct snd_pcm_substream *s) { (void)s; abort(); }
static void snd_pcm_set_state(struct snd_pcm_substream *s,int state) { s->runtime->status->state=state; }
static long snd_pcm_playback_hw_avail(struct snd_pcm_runtime *r) { return r->control->appl_ptr-r->status->hw_ptr; }
'''
funcs=fn('sound/core/pcm_lib.c','snd_pcm_lib_ioctl_reset')+'\n'+fn('sound/core/pcm_native.c','snd_pcm_pre_prepare')+'\n'+fn('sound/core/pcm_native.c','snd_pcm_post_prepare')+'\n'+fn('sound/core/pcm_native.c','snd_pcm_playback_rewind')
tests=r'''
static void equal_irq(void) {
 setup(false,2,16,256,128,128); status.state=SNDRV_PCM_STATE_RUNNING; enabled[0]=true;
 hw_cur[0]=0x1040;
 /* Pointer samples the first hardware 64-byte advance; then two ALSA wrap chunks refill the ring. */
 CHECK(mtk_pcm_pointer(&stream)==16); CHECK(block->u4DataRemained==64);
 CHECK(call(32,32)==0); CHECK(call(0,16)==0); CHECK(block->u4DataRemained==256);
 int before=block->u4DataRemained;
 Auddrv_DL1_Interrupt_Handler();
 CHECK(block->u4DataRemained==0); CHECK(block->u4DMAReadIdx==64);
 hw_cur[0]=0x1080; CHECK(mtk_pcm_pointer(&stream)==SNDRV_PCM_POS_XRUN);
 printf("R1 REPRO: same-cursor IRQ after pointer+refill, remained %d -> 0 with no DMA advance; next real 64-byte advance falsely XRUNs\n",before);
}
static void recovery(void) {
 for(int cap=0;cap<2;cap++) {
  setup(cap,2,16,256,cap?0:128,cap?192:128);
  status.state=SNDRV_PCM_STATE_RUNNING;enabled[cap]=true;copy_hook=dma_expire;
  CHECK(call(cap?0:32,16)==-EPIPE);
  CHECK(status.state==SNDRV_PCM_STATE_RUNNING);
  CHECK(snd_pcm_pre_prepare(&stream,0)==-EBUSY);
  printf("R2 REPRO %s: post-user-copy DMA expiry returns -EPIPE, PCM remains RUNNING, exact pre_prepare returns -EBUSY\n",cap?"UL1":"DL1");
 }
}
static void cursors(void) {
 static struct control ctl;
 setup(false,2,16,256,0,0); rt.control=&ctl; ctl.appl_ptr=0; status.hw_ptr=0;
 CHECK(call(0,16)==0); ctl.appl_ptr=16; /* the real write loop publishes this after success */
 CHECK(snd_pcm_pre_prepare(&stream,0)==0);
 CHECK(snd_pcm_lib_ioctl_reset(&stream,NULL)==0);snd_pcm_post_prepare(&stream,0);
 CHECK(ctl.appl_ptr==0); CHECK(block->u4WriteIdx==64);
 CHECK(call(ctl.appl_ptr,16)==-EPIPE);
 puts("R3 REPRO: successful 16-frame prepared write, exact ALSA reset/post_prepare -> appl_ptr 0, ring write index 64; next write -EPIPE");
 setup(false,2,16,256,0,0);rt.control=&ctl;ctl.appl_ptr=0;status.hw_ptr=0;
 CHECK(call(0,16)==0);ctl.appl_ptr=16;
 CHECK(snd_pcm_playback_rewind(&stream,16)==16);CHECK(ctl.appl_ptr==0);
 CHECK(call(0,16)==-EPIPE);
 puts("R3 REPRO: exact ALSA playback rewind accepts 16 frames, next valid write -EPIPE because driver cursor was not reconciled");
}
static void *reboot_thread(void *arg) { (void)arg; assert(!stream_depth); mtk_afe_reboot(NULL,0,NULL); return NULL; }
static void reboot_at_commit(void) { pthread_t t; CHECK(!pthread_create(&t,NULL,reboot_thread,NULL)); CHECK(!pthread_join(t,NULL)); }
static void arm_reboot(void) { review_before_ring_lock=reboot_at_commit; }
static void reboot_race(void) {
 setup(false,2,16,256,0,128); status.state=SNDRV_PCM_STATE_RUNNING;enabled[0]=true;
 copy_hook=arm_reboot;
 /* Next pointer-ring acquisition is after the final generation comparison. */
 CHECK(call(0,16)==0);CHECK(!enabled[0]);CHECK(block->u4DataRemained==64);CHECK(block->u4WriteIdx==64);
 CHECK(dl1_copy_generation==2);
 puts("R5 REPRO: exact mock reboot notifier stops DL1 on another pthread without stream lock; in-flight callback commits 64 bytes after reset and returns 0");
}
int main(int argc,char **argv) { (void)argv; if(argc>1) { pMemControl=NULL; return mtk_afe_reboot(NULL,0,NULL); } equal_irq(); recovery(); cursors(); reboot_race(); printf("PASS %u adversarial assertions reproduced defects; no hardware\n",assertions); return 0; }
'''
(w/'tests/adversarial.c').write_text(head+funcs+'\nstruct notifier_block { int unused; };\n#define NOTIFY_DONE 0\nstatic int afe_emergency_stop;\nstatic void AudDrv_Clk_On(void) {}\nstatic void AudDrv_Clk_Off(void) {}\n'+fn('sound/soc/mediatek/mt_soc_audio_8163/mt_soc_pcm_dl1.c','mtk_afe_reboot')+tests)
(p/'evidence/adversarial-provenance.json').write_text(json.dumps({'exact_extra_functions':records,'boundary_changes':'Owned shim adds ALSA state/control fields and macros; snd_pcm_running uses RUNNING for these cases; snd_pcm_update_hw_ptr aborts if reached (none of these core cases should call it). Driver prepare is source-audited, not executed. Caller appl_ptr publication between callback and reset is explicit in the test. Supplied generated.c and cases.c are unchanged.'},indent=2)+'\n')
