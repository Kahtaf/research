import json,re
from source import ROOT,REL,funcs,fn,edit_fn,private_graph
p=ROOT/'preimage'/REL/'mt_soc_codec_63xx.c';s=p.read_text();fs,calls,direct,reach=private_graph(s)
public=[f['name'] for f in fs if 'static ' not in f['prefix'] and f['name'] in reach];assert set(public)=={'SetAnalogSuspend','UpdateHeadsetGain','OpenAnalogHeadphone','SetMicPGAGain','InitCodecDefault'},public
controls={f['name'] for f in fs if f['name'] in reach and 'struct snd_kcontrol' in f['params']}
(ROOT/'evidence/private-consumer-audit.json').write_text(json.dumps({'source':'preimage/'+str(REL/'mt_soc_codec_63xx.c'),'external_private_roots':public,'nonprivate_external_roots':[f['name'] for f in fs if 'static ' not in f['prefix'] and f['name'] not in reach],'control_roots_to_guard':sorted(controls),'private_direct':sorted(direct),'private_reachable':sorted(reach),'calls':{n:sorted(c) for n,c in calls.items() if n in reach}},indent=2)+'\n')
s=s.replace('static DEFINE_MUTEX(Ana_Ctrl_Mutex);','''/* Lock order: codec state -> analog/GPIO amp locks -> gate lock. */
DEFINE_MUTEX(mt8163_codec_state_mutex);
static DEFINE_MUTEX(codec_registration_mutex);
static DEFINE_MUTEX(Ana_Ctrl_Mutex);''')
s=s.replace('static bool mAnaSuspend;','''/* Intent outlives private allocations; applied state belongs to one allocation. */
static bool mAnaSuspend;
static bool mAnalogSuspendApplied;''')
s=s.replace('#endif\nvoid SetAnalogSuspend(bool bEnable)','#endif\n#include "codec_state_controls.h"\nvoid SetAnalogSuspend(bool bEnable)',1)
# Existing analog sequence is internal-only; the public boundary owns the state lock.
s=edit_fn(s,'SetAnalogSuspend',lambda t:t.replace('void SetAnalogSuspend(', 'static void SetAnalogSuspend_locked(').replace('mAnaSuspend','mAnalogSuspendApplied').replace('''#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
		p00a_gate_suspend(true);
#endif
''','').replace('''#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
		p00a_gate_suspend(false);
#endif
''',''))
f=next(f for f in funcs(s) if f['name']=='SetAnalogSuspend_locked');s=s[:f['end']]+'''

void SetAnalogSuspend(bool bEnable)
{
	mutex_lock(&mt8163_codec_state_mutex);
	/* Record even detached PM transitions; only an intended resume clears it. */
	mAnaSuspend = bEnable;
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
	p00a_gate_suspend(bEnable);
#endif
	if (mInitCodec && mCodec_data)
		SetAnalogSuspend_locked(bEnable);
	mutex_unlock(&mt8163_codec_state_mutex);
}
'''+s[f['end']:]
# Helpers with no external callers are made private rather than exporting unlocked access.
s=s.replace('void SetMicPGAGain(void)','static void SetMicPGAGain(void)').replace('void InitCodecDefault(void)','static void InitCodecDefault(void)')
# Keep external API names; internal calls do not recurse into the boundary mutex.
s=re.sub(r'\bUpdateHeadsetGain\(', 'UpdateHeadsetGain_locked(',s)
s=s.replace('void UpdateHeadsetGain_locked(void)','static void UpdateHeadsetGain_locked(void)')
f=next(f for f in funcs(s) if f['name']=='UpdateHeadsetGain_locked');s=s[:f['end']]+'''

void UpdateHeadsetGainLocked(void)
{
	lockdep_assert_held(&mt8163_codec_state_mutex);
	if (mInitCodec && mCodec_data)
		UpdateHeadsetGain_locked();
}

void UpdateHeadsetGain(void)
{
	mutex_lock(&mt8163_codec_state_mutex);
	UpdateHeadsetGainLocked();
	mutex_unlock(&mt8163_codec_state_mutex);
}
'''+s[f['end']:]
s=edit_fn(s,'OpenAnalogHeadphone',lambda t:t.replace('void OpenAnalogHeadphone(', 'static void OpenAnalogHeadphone_locked('))
f=next(f for f in funcs(s) if f['name']=='OpenAnalogHeadphone_locked');s=s[:f['end']]+'''

void OpenAnalogHeadphone(bool bEnable)
{
	mutex_lock(&mt8163_codec_state_mutex);
	if (mInitCodec && mCodec_data && (!bEnable || !mAnaSuspend))
		OpenAnalogHeadphone_locked(bEnable);
	mutex_unlock(&mt8163_codec_state_mutex);
}
'''+s[f['end']:]
# Every selected private-state control is entered through a lifetime/readiness boundary.
for name in sorted(controls):
 f=next(f for f in funcs(s) if f['name']==name);s=s[:f['end']]+'\nCODEC_STATE_CONTROL('+name+')\n'+s[f['end']:]
for m in reversed(list(re.finditer(r'static const struct snd_kcontrol_new \w+\[\] = \{.*?\n\};',s,re.S))):
 text=m[0]
 def sub(t):return t[0] if not t[1] or t[1] not in controls else 'CODEC_CONTROL('+t[1]+')'
 text=re.sub(r'"(?:\\.|[^"\\])*"|\b(\w+)\b',sub,text)
 s=s[:m.start()]+text+s[m.end():]
# ASoC can call init/remove while routing PM remains registered independently.
# ALSA callback readers may hold controls_rwsem before taking the state mutex.
# Register controls without that mutex; the separate writer lock spans init/remove.
f=next(f for f in funcs(s) if f['name']=='mt6323_codec_probe')
t=f['text'];a=t.index('\tsnd_soc_dapm_new_controls');b=t.index('\n\t/* here to set  private data */',a)
controls_block=t[a:b]
s=s[:f['start']]+t[:a]+t[b:]+s[f['end']:]
s=s.replace('\tstruct snd_soc_dapm_context *dapm = &codec->component.dapm;\n','',1)
insert=s.index('static int mt6323_codec_probe(')
s=s[:insert]+'static void mt6323_codec_add_controls(struct snd_soc_codec *codec)\n{\n\tstruct snd_soc_dapm_context *dapm = &codec->component.dapm;\n\n'+controls_block+'\n}\n\n'+s[insert:]
s=edit_fn(s,'mt6323_codec_probe',lambda t:t.replace('static int mt6323_codec_probe(', 'static int mt6323_codec_probe_locked('))
f=next(f for f in funcs(s) if f['name']=='mt6323_codec_probe_locked');s=s[:f['end']]+'''

static int mt6323_codec_probe(struct snd_soc_codec *codec)
{
	int ret;

	mutex_lock(&codec_registration_mutex);
	mutex_lock(&mt8163_codec_state_mutex);
	if (mInitCodec) {
		mutex_unlock(&mt8163_codec_state_mutex);
		mutex_unlock(&codec_registration_mutex);
		return 0;
	}
	mutex_unlock(&mt8163_codec_state_mutex);
	/* Never take ALSA controls_rwsem with the private-state mutex held. */
	mt6323_codec_add_controls(codec);
	mutex_lock(&mt8163_codec_state_mutex);
	mAnalogSuspendApplied = false;
	ret = mt6323_codec_probe_locked(codec);
	if (!ret) {
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
		p00a_gate_suspend(mAnaSuspend);
#endif
		if (mAnaSuspend)
			SetAnalogSuspend_locked(true);
	}
	mutex_unlock(&mt8163_codec_state_mutex);
	mutex_unlock(&codec_registration_mutex);
	return ret;
}
'''+s[f['end']:]
def remove(t):
 t=t.replace('''#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
	p00a_gate_stop''','''#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
	mutex_lock(&codec_registration_mutex);
	mutex_lock(&mt8163_codec_state_mutex);
	p00a_gate_stop''')
 t=t.replace('\tmInitCodec = false;','\tmInitCodec = false;\n\tmAnalogSuspendApplied = false;')
 return t.replace('\tmutex_unlock(&p00a_gate_lock);','\tmutex_unlock(&p00a_gate_lock);\n\tmutex_unlock(&mt8163_codec_state_mutex);\n\tmutex_unlock(&codec_registration_mutex);')
s=edit_fn(s,'mt6323_codec_remove',remove)
for name in ['mtk_mt6323_codec_dev_remove','mtk_mt6323_codec_dev_shutdown']:
 s=edit_fn(s,name,lambda t:t.replace('\tp00a_gate_stop(&pdev->dev);','\tmutex_lock(&mt8163_codec_state_mutex);\n\tp00a_gate_stop(&pdev->dev);\n\tmutex_unlock(&mt8163_codec_state_mutex);'))
(ROOT/'candidate'/REL/'mt_soc_codec_63xx.c').write_text(s)
# Gate mutex is nested, never recursively used as the lifetime lock.
s=(ROOT/'preimage'/REL/'p00a_stock_gate.h').read_text()
for name in ['p00a_gate_cache','p00a_gate_output_locked','p00a_gate_set','p00a_gate_get','p00a_gate_suspend','p00a_gate_stop']:
 # An assertion at entry is structural documentation, not runtime lifetime protection.
 def assertion(t):
  # Put after local declarations to retain kernel GNU89 declaration ordering.
  lines=t.splitlines();ix=2
  while ix<len(lines) and (not lines[ix].strip() or re.match(r'\s*(?:int|struct \w+ \*|bool) [^=;]+(?:=[^;]+)?;',lines[ix])):ix+=1
  lines.insert(ix,'\tlockdep_assert_held(&mt8163_codec_state_mutex);');return '\n'.join(lines)
 s=edit_fn(s,name,assertion)
s=edit_fn(s,'p00a_gate_release',lambda t:t.replace('\tp00a_gate_stop(dev);','\tmutex_lock(&mt8163_codec_state_mutex);\n\tp00a_gate_stop(dev);').replace('\tmutex_unlock(&p00a_gate_lock);','\tmutex_unlock(&p00a_gate_lock);\n\tmutex_unlock(&mt8163_codec_state_mutex);'))
def probe(t):
 t=t.replace('\tmutex_lock(&p00a_gate_lock);','\tmutex_lock(&mt8163_codec_state_mutex);\n\tmutex_lock(&p00a_gate_lock);')
 t=t.replace('\t\tmutex_unlock(&p00a_gate_lock);','\t\tmutex_unlock(&p00a_gate_lock);\n\t\tmutex_unlock(&mt8163_codec_state_mutex);')
 t=t.replace('\tp00a_gate_suspended = false;','\tp00a_gate_suspended = mAnaSuspend;')
 return t.replace('\tmutex_unlock(&p00a_gate_lock);\n\treturn devm_add_action','\tmutex_unlock(&p00a_gate_lock);\n\tmutex_unlock(&mt8163_codec_state_mutex);\n\treturn devm_add_action')
s=edit_fn(s,'p00a_gate_probe',probe);(ROOT/'candidate'/REL/'p00a_stock_gate.h').write_text(s)
s=(ROOT/'preimage'/REL/'AudDrv_Gpio.c').read_text()
def headset(t):
 t=t.replace('\tmutex_lock(&aud_amp_mutex);','\tmutex_lock(&mt8163_codec_state_mutex);\n\tmutex_lock(&aud_amp_mutex);')
 t=t.replace('UpdateHeadsetGain();','UpdateHeadsetGainLocked();')
 return t.replace('\tmutex_unlock(&aud_amp_mutex);','\tmutex_unlock(&aud_amp_mutex);\n\tmutex_unlock(&mt8163_codec_state_mutex);')
s=edit_fn(s,'AudDrv_GPIO_Headset_Changed',headset);(ROOT/'candidate'/REL/'AudDrv_Gpio.c').write_text(s)
s=(ROOT/'preimage'/REL/'mt_soc_codec_63xx.h').read_text();s=s.replace('void UpdateHeadsetGain(void);','''void UpdateHeadsetGain(void);
#include <linux/mutex.h>
/* Acquire before aud_amp_mutex; Locked helper requires this mutex throughout. */
extern struct mutex mt8163_codec_state_mutex;
void UpdateHeadsetGainLocked(void);''');(ROOT/'candidate'/REL/'mt_soc_codec_63xx.h').write_text(s)
print('Guarded',len(controls),'private-state control callbacks;',len(public),'external private roots audited')
