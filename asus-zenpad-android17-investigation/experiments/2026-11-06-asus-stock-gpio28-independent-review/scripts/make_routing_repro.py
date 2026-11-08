from pathlib import Path
import re,hashlib,json
R=Path(__file__).resolve().parents[1]
def fn(s,n):
 m=re.search(r'(?m)^(?:static )?(?:int|bool) '+n+r'\([^;]*?\)\s*\n\{',s);assert m,n
 p=m.end();d=1
 while d:d+=(s[p]=='{')-(s[p]=='}');p+=1
 return s[m.start():p]+'\n'
p=R.parent/'2026-11-05-asus-p00a-power-port/sources/kernel/sound/soc/mediatek/mt_soc_audio_8163/mt_soc_pcm_routing.c'
q=R/'inputs/inputs/api/sound/soc/mediatek/mt_soc_audio_8163/mt_soc_afe_control.c'
a=fn(p.read_text(),'mtk_routing_pm_ops_suspend');b=fn(q.read_text(),'ConditionEnterSuspend')
s=(R/'inputs/tests/contract.c').read_text().replace('int main(void){','static int original_main(void){')
s+='''
static bool AudDrvSuspendStatus,mFMEnable,mOffloadEnable;
static bool get_voice_status(void){return false;}
static void AudDrv_Suspend_Clk_Off(void){CHECK(false);}
'''+b+a+'''
int main(void){
 CHECK(original_main()==0);reset();CHECK(core_probe()==0);detach();
 CHECK(!AudDrvSuspendStatus&&!mFMEnable&&!mOffloadEnable);
 fprintf(stderr,"REPRO: actual separately registered routing PM suspend, idle FM/offload/voice false, after codec detach\\n");
 mtk_routing_pm_ops_suspend(&pdev.dev);return 2;
}
'''
(R/'inputs/tests/lifetime-routing-pm.c').write_text(s)
(R/'evidence/routing-repro-extraction.json').write_text(json.dumps(dict(public_baseline_path=str(p),routing_file_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),actual_routing_callback_sha256=hashlib.sha256(a.encode()).hexdigest(),actual_condition_sha256=hashlib.sha256(b.encode()).hexdigest(),no_rejected_patch_access=True),indent=2)+'\n')
print('Extracted actual routing PM callback and AFE suspend condition')
