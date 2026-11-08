from audit import ROOT,SOURCE,REL,functions,H
import json

s=(ROOT/'tests/contract.c').read_text()
# Host boundary scheduling only. No production body is edited.
s=s.replace('if(action_error)return action_error;', 'phase_point("action");if(action_error)return action_error;')
s=s.replace("ev('R');if(request_error)","ev('R');phase_point(\"request\");if(request_error)")
s=s.replace("ev(value?'H':'L');if(initial_error", "ev(value?'H':'L');phase_point(\"output\");if(initial_error")
s=s.replace('static int AudDrv_GPIO_EXTHPAMP_Set(int enabled){(void)enabled;return 0;}', 'static int AudDrv_GPIO_EXTHPAMP_Set(int enabled){(void)enabled;phase_point("hp-output");return 0;}')
defaults=functions((SOURCE/'candidate'/REL/'mt_soc_codec_63xx.c').read_text())['InitCodecDefault']['text']
s=s.replace('static void InitCodecDefault(void){lockdep_assert_held(&mt8163_codec_state_mutex);phase_point("init");}',defaults)
s=s.replace('#include "lifecycle.c"','#define main supplied_main\n#include "lifecycle-adversarial.inc"\n#undef main\n#include "adversarial.c"')
(ROOT/'tests/adversarial-contract.c').write_text(s)
l=(ROOT/'tests/lifecycle.c').read_text()
l=l.replace('if(!strcmp(name,"Speaker_Amp_Get"))phase_point("control");', 'if(!strcmp(name,"Speaker_Amp_Get"))phase_point("control");if(!strcmp(name,"InitCodecDefault"))phase_point("init");')
l=l.replace('static void registration_point(void){','static void registration_point(void){phase_point("register");')
(ROOT/'tests/lifecycle-adversarial.inc').write_text(l)
(ROOT/'evidence/adversarial-extraction.json').write_text(json.dumps({'source':'candidate/'+str(REL/'mt_soc_codec_63xx.c'),'function':'InitCodecDefault','sha256':H(defaults.encode()),'transformation':'none; scheduling uses existing pr_debug service'},indent=2)+'\n')
print('Prepared owned fixture: original defaults body + host boundary scheduling; production unchanged')
