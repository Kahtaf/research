from pathlib import Path
import json,hashlib,re,resource,os,signal
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30));signal.alarm(45);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
R=Path('/srv/android/asus-stock-gpio28-review-20261106-r1');rel='sound/soc/mediatek/mt_soc_audio_8163/mt_soc_pcm_routing.c';p=R/'kernel'/rel
h=hashlib.sha256(p.read_bytes()).hexdigest();assert h==json.loads((R/'evidence/baseline-source-manifest.json').read_text())[rel]=='c458de71bb3c2cccd8b0d39a4c7c6e3a75f962cc8bdda44697eacca4f30bbd3a'
s=p.read_text();n='mtk_routing_pm_ops_suspend';m=re.search(r'(?m)^static int '+n+r'\([^;]*?\)\s*\n\{',s);pos=m.end();d=1
while d:d+=(s[pos]=='{')-(s[pos]=='}');pos+=1
body=s[m.start():pos]+'\n'
assert hashlib.sha256(body.encode()).hexdigest()=='1bdb2f35e42845f0a376d5786a74a4ce72f09e733f6d19a020a2c2ebd6279e47'
r=dict(exact_selected_path=str(p),sha256=h,callback_sha256=hashlib.sha256(body.encode()).hexdigest(),callback=body,pm_callback_registered='.suspend = mtk_routing_pm_ops_suspend' in s and '.pm = &mtk_routing_pm_ops' in s,earlier_suffix_loop_receipt='Earlier routing-PM-source-binding files record last _amzn variant; preserve those and use this exact-path correction',test_callback_identical_to_actual_pinned_BMC=True)
q=R/'evidence/routing-PM-exact-selected-source.json';assert not q.exists();q.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
