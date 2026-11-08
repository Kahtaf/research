from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
p=R/'inputs/tests/contract.c';s=p.read_text()
s=s.replace('#define DEFINE_MUTEX(n) int n','#include <pthread.h>\n#define DEFINE_MUTEX(n) pthread_mutex_t n = PTHREAD_MUTEX_INITIALIZER')
s=s.replace('(void)(p);locks++;','pthread_mutex_lock(p);locks++;').replace('(void)(p);locks--;','locks--;pthread_mutex_unlock(p);')
s=s.replace('assertions++;','__sync_fetch_and_add(&assertions,1);')
s=s.replace('events[512]','events[65536]').replace('event_count<500','event_count<65530')
s=s.replace('int main(void){','static int original_main(void){')
s+='''
/* Independent adversarial extensions; actual production/API includes unchanged. */
static void *contending_controls(void *unused)
{
 int i,r; (void)unused;
 for(i=0;i<500;i++) {
  r=set(1);CHECK(r==0||r==1||r==-ESHUTDOWN);
  r=get();CHECK(r==0||r==1);
  r=set(0);CHECK(r==0||r==1);
 }
 return NULL;
}
static void *concurrent_shutdown(void *unused)
{
 (void)unused;mtk_mt6323_codec_dev_shutdown(&pdev);return NULL;
}
int main(void)
{
 pthread_t a,b,c;int i;
 CHECK(original_main()==0);
 reset();mapped_gpio=0;CHECK(core_probe()==0);CHECK(set(1)==1&&get()==1);detach();
 reset();mapped_gpio=ARCH_NR_GPIOS-1;CHECK(core_probe()==0);CHECK(set(1)==1);detach();
 reset();mapped_gpio=-1;rejected(-1);
 reset();property_elems=2;rejected(-EINVAL);CHECK(lookup_calls==0);
 reset();property_elems=4;rejected(-EINVAL);CHECK(lookup_calls==0);
 reset();property_elems=0;rejected(-EINVAL);
 reset();args_count=0;rejected(-EINVAL);CHECK(node_puts==1);
 reset();args_count=3;rejected(-EINVAL);CHECK(node_puts==1);
 reset();local_flags=2;rejected(-EINVAL);CHECK(node_puts==1&&lookup_calls==0);
 reset();parse_error=-EPROBE_DEFER;rejected(-EPROBE_DEFER);CHECK(node_puts==0);
 reset();CHECK(core_probe()==0);CHECK(set(1)==1);{struct device alien={0};CHECK(p00a_gate_stop(&alien)==0&&get()==1);p00a_gate_release(&alien);CHECK(get()==1&&requested);}detach();
 reset();CHECK(platform_probe()==0);mtk_mt6323_codec_dev_shutdown(&pdev);CHECK(mt6323_codec_probe(&codec)==0);bound=1;CHECK(set(1)==-ESHUTDOWN&&get()==0);detach();
 reset();CHECK(core_probe()==0);output_errors=2;CHECK(set(1)==-EIO&&get()==-EIO);CHECK(!p00a_gate_on&&high_calls==1);CHECK(set(1)==-EIO&&high_calls==1);CHECK(set(0)==1&&get()==-EIO);detach();
 reset();CHECK(core_probe()==0);CHECK(set(1)==1);output_errors=2;SetAnalogSuspend(true);CHECK(get()==-EIO);SetAnalogSuspend(false);CHECK(set(1)==-EIO&&get()==-EIO);detach();
 reset();CHECK(core_probe()==0);mt6323_codec_remove(&codec);bound=0;CHECK(!mCodec_data&&!mInitCodec&&requested);CHECK(mt6323_codec_probe(&codec)==0);bound=1;CHECK(set(1)==-ESHUTDOWN&&get()==0);detach();
 reset();CHECK(core_probe()==0);CHECK(pthread_create(&a,NULL,contending_controls,NULL)==0);CHECK(pthread_create(&b,NULL,contending_controls,NULL)==0);CHECK(pthread_join(a,NULL)==0);CHECK(pthread_join(b,NULL)==0);CHECK(get()==0&&locks==0);detach();
 reset();CHECK(core_probe()==0);CHECK(pthread_create(&a,NULL,contending_controls,NULL)==0);CHECK(pthread_create(&b,NULL,contending_controls,NULL)==0);CHECK(pthread_create(&c,NULL,concurrent_shutdown,NULL)==0);CHECK(pthread_join(a,NULL)==0);CHECK(pthread_join(b,NULL)==0);CHECK(pthread_join(c,NULL)==0);CHECK(get()==0&&set(1)==-ESHUTDOWN&&locks==0);{int last_high=-1;for(i=0;i<event_count;i++)if(events[i]=='H')last_high=i;CHECK(last_high<0||strchr(events+last_high,'L')!=NULL);}detach();
 printf("PASS independent total %d cases, %d assertions; real pthread gate contention and shutdown; mocked hardware only\\n",cases,assertions);
 return 0;
}
'''
(R/'inputs/tests/adversarial.c').write_text(s)
(R/'evidence/adversarial-extraction.json').write_text(json.dumps(dict(original_contract_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),extended_contract_sha256=hashlib.sha256(s.encode()).hexdigest(),production_bodies='unchanged verbatim includes copied from candidate; hashes verified against actual source'),indent=2)+'\n')
print('Added 17 adversarial cases including real pthread contention and shutdown races')
