from pathlib import Path
R=Path(__file__).resolve().parents[1]
def replace(s,a,b,count=1):
 assert s.count(a)==count,(a[:100],s.count(a),count)
 return s.replace(a,b)
p=R/'preimage/sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.c';s=p.read_text()
s=replace(s,'static bool mAnaSuspend;','''static bool mAnaSuspend;
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
#include "p00a_stock_gate.h"
#endif''')
s=replace(s,'for (i = 0; i < AUDIO_ANALOG_DEVICE_MAX; i++)\n\t\tmCodec_data->mAudio_Ana_DevicePower[i] =\n\t\t    mCodec_data->mAudio_BackUpAna_DevicePower[i];','''for (i = 0; i < AUDIO_ANALOG_DEVICE_MAX; i++) {
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
		/* Gate remains quiescent across suspend; userspace must re-enable. */
		if (i == AUDIO_ANALOG_DEVICE_OUT_EXTSPKAMP)
			continue;
#endif
		mCodec_data->mAudio_Ana_DevicePower[i] =
		    mCodec_data->mAudio_BackUpAna_DevicePower[i];
	}''')
s=replace(s,'\t\tSavePowerState();','''#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
		p00a_gate_suspend(true);
#endif
		SavePowerState();''')
s=replace(s,'\t\tRestorePowerState();','''		RestorePowerState();
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
		p00a_gate_suspend(false);
#endif''')
start=s.index('#ifdef CONFIG_OF',s.index('static int Speaker_Amp_Set'))
end=s.index('static int Ext_Speaker_Amp_Get',start)
old=s[start:end]
s=s[:start]+'''#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
static int Ext_Speaker_Amp_Change(bool enable)
{
	return p00a_gate_set(enable);
}
#else
'''+old+'#endif /* CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE */\n\n'+s[end:]
# Generic implementations unchanged; only the selected board wrapper returns errors.
a=s.index('static int Ext_Speaker_Amp_Get');b=s.index('static void Headphone_Speaker_Switch_Change',a)
s=s[:a]+'''static int Ext_Speaker_Amp_Get(struct snd_kcontrol *kcontrol,
	struct snd_ctl_elem_value *ucontrol)
{
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
	int ret = p00a_gate_get();

	if (ret < 0)
		return ret;
	ucontrol->value.integer.value[0] = ret;
#else
	ucontrol->value.integer.value[0] = mCodec_data->
		mAudio_Ana_DevicePower[AUDIO_ANALOG_DEVICE_OUT_EXTSPKAMP];
#endif
	return 0;
}

static int Ext_Speaker_Amp_Set(struct snd_kcontrol *kcontrol,
	struct snd_ctl_elem_value *ucontrol)
{
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
	long value = ucontrol->value.integer.value[0];

	if (value != 0 && value != 1)
		return -EINVAL;
	return Ext_Speaker_Amp_Change(value);
#else
	if (ucontrol->value.integer.value[0]) {
		Ext_Speaker_Amp_Change(true);
		mCodec_data->mAudio_Ana_DevicePower[
			AUDIO_ANALOG_DEVICE_OUT_EXTSPKAMP] = true;
	} else {
		mCodec_data->mAudio_Ana_DevicePower[
			AUDIO_ANALOG_DEVICE_OUT_EXTSPKAMP] = false;
		Ext_Speaker_Amp_Change(false);
	}
	return 0;
#endif
}

'''+s[b:]
# Test controls must not overwrite the checked board gate state after failure.
s=replace(s,'''\t\tmCodec_data->
		mAudio_Ana_DevicePower[AUDIO_ANALOG_DEVICE_OUT_EXTSPKAMP]
		= false;
		Ext_Speaker_Amp_Change(false);''','''#ifndef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
		mCodec_data->
		mAudio_Ana_DevicePower[AUDIO_ANALOG_DEVICE_OUT_EXTSPKAMP] = false;
#endif
		Ext_Speaker_Amp_Change(false);''')
# Test-control shutdown follows the stock external-off before internal-off order.
a=s.index('static void ADC_LOOP_DAC_Off');b=s.index('static void ADC_LOOP_DAC_Func',a)
part=s[a:b];ext_start=part.index('\n\tif (mCodec_data->\n\t\tmAudio_Ana_DevicePower[AUDIO_ANALOG_DEVICE_OUT_EXTSPKAMP]')
ext_end=part.index('\n\tif (mCodec_data->',ext_start+3)
ext=part[ext_start:ext_end];part=part[:ext_start]+part[ext_end:]
insert=part.index('\n\tif (mCodec_data->')
part=part[:insert]+ext+part[insert:];s=s[:a]+part+s[b:]
# Allocation failure must abort the real codec callback instead of dereferencing NULL.
s=replace(s,'''#if 0
	if (!mCodec_data) {
		pr_err("Failed to allocate private data\\n");
		return -ENOMEM;
	}
#endif''','''	if (!mCodec_data) {
		pr_err("Failed to allocate private data\\n");
		return -ENOMEM;
	}''')
s=replace(s,'''static int mtk_mt6323_codec_dev_probe(struct platform_device *pdev)
{
''','''static int mtk_mt6323_codec_dev_probe(struct platform_device *pdev)
{
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
	int ret = p00a_gate_probe(&pdev->dev);

	if (ret)
		return ret;
#endif
''')
s=replace(s,'''\tsnd_soc_unregister_codec(&pdev->dev);
	return 0;
}

#ifdef CONFIG_OF''','''#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
	p00a_gate_stop(&pdev->dev);
#endif
	snd_soc_unregister_codec(&pdev->dev);
	return 0;
}

#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
static void mtk_mt6323_codec_dev_shutdown(struct platform_device *pdev)
{
	p00a_gate_stop(&pdev->dev);
}
#endif

#ifdef CONFIG_OF''')
s=replace(s,'''\t.remove = mtk_mt6323_codec_dev_remove,
};''','''	.remove = mtk_mt6323_codec_dev_remove,
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
	.shutdown = mtk_mt6323_codec_dev_shutdown,
#endif
};''')
s=replace(s,'''\tif( mt_soc_get_dts_config() < 0 ) {''','''#ifndef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
	if( mt_soc_get_dts_config() < 0 ) {''')
s=replace(s,'''\tret = platform_driver_register(&mtk_codec_6323_driver);''','''#endif
	ret = platform_driver_register(&mtk_codec_6323_driver);''')
# Omit the obsolete generic AW DT parser in the board profile as well as its call.
s=replace(s,'static int  mt_soc_get_dts_config(void)', '#ifndef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE\nstatic int  mt_soc_get_dts_config(void)')
a=s.index('static int  mt_soc_get_dts_config');b=s.index('\n#if 0\nstatic int Auddrv_getGPIO_info',a)
s=s[:b]+'\n#endif /* !CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE */\n'+s[b:]
# The codec callback owns its allocation; removal permits a clean later rebind.
s=replace(s,'''static int mt6323_codec_remove(struct snd_soc_codec *codec)
{
	pr_debug("%s()\\n", __func__);
	return 0;
}''','''static int mt6323_codec_remove(struct snd_soc_codec *codec)
{
	pr_debug("%s()\\n", __func__);
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
	p00a_gate_stop(codec->dev);
	mutex_lock(&p00a_gate_lock);
	snd_soc_codec_set_drvdata(codec, NULL);
	kfree(mCodec_data);
	mCodec_data = NULL;
	mInitCodec = false;
	mutex_unlock(&p00a_gate_lock);
#endif
	return 0;
}''')
(R/'candidate'/p.relative_to(R/'preimage')).write_text(s)
p=Path('sound/soc/mediatek/Kconfig');s=(R/'preimage'/p).read_text()+'''
config ASUS_P00A_STOCK_SPEAKER_GATE
	bool "P00A public stock speaker gate software contract (unqualified)"
	depends on SND_SOC_MT8163 && MTK_SPEAKER && OF && GPIOLIB
	depends on OF_GPIO && PINCTRL_MT8163
	depends on !AMP_AW8737S && !MTK_LEGACY
	default n
	help
	  Restrict this candidate to the declared P00A stock GPIO28 gate.
	  This does not qualify the fitted component, route or physical hardware.
''';(R/'candidate'/p).write_text(s)
for p in [Path('resolved.config'),Path('arch/arm64/configs/asus_p00a_defconfig')]:
 s=(R/'preimage'/p).read_text();s=replace(s,'CONFIG_AMP_AW8737S=y','# CONFIG_AMP_AW8737S is not set\nCONFIG_ASUS_P00A_STOCK_SPEAKER_GATE=y');(R/'candidate'/p).write_text(s)
p=Path('arch/arm64/boot/dts/mediatek/asus-p00a.dts');s=(R/'preimage'/p).read_text()
s=replace(s,'''\t\t\t"audi2s1-mode1",
			"extamp-pullhigh",
			"extamp-pulllow";''','''			"audi2s1-mode1";''')
s=replace(s,'\tpinctrl-5 = <&aud_pins_extamp_high>;\n\tpinctrl-6 = <&aud_pins_extamp_low>;\n','')
a=s.index('\taud_pins_extamp_high:');b=s.index('\taud_pins_i2s1_mode0:',a);s=s[:a]+s[b:]
s+='''
/* PUBLIC STOCK SOFTWARE CONTRACT ONLY; fitted hardware/route unqualified. */
/ {
	soc {
		mt_soc_codec_name@11220000 {
			asus,p00a-stock-speaker-gate;
			extspkamp-gpio = <&pio 28 0>;
		};
	};
};
'''
soc=(R/'inputs/api/arch/arm64/boot/dts/mediatek/mt8163.dtsi').read_text()
assert 'mt_soc_codec_name@11220000 {' in soc
(R/'candidate'/p).write_text(s)
p=Path('sound/soc/mediatek/mt_soc_audio_8163/AudDrv_Gpio.c');s=(R/'preimage'/p).read_text()
s=replace(s,'''\tfor (i = 0; i < ARRAY_SIZE(aud_gpios); i++) {''','''	for (i = 0; i < ARRAY_SIZE(aud_gpios); i++) {
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
		if (i == GPIO_EXTAMP_HIGH || i == GPIO_EXTAMP_LOW)
			continue;
#endif''')
s=replace(s,'''static int AudDrv_GPIO_EXTAMP_Set(int bEnable)
{''','''static int AudDrv_GPIO_EXTAMP_Set(int bEnable)
{
#ifdef CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE
	return -EOPNOTSUPP;
#else''')
a=s.index('static int AudDrv_GPIO_EXTAMP_Set');b=s.index('\nint AudDrv_GPIO_EXTAMP_Gain_Set',a);part=s[a:b];part=replace(part,'\treturn retval;\n}','\treturn retval;\n#endif\n}');s=s[:a]+part+s[b:];(R/'candidate'/p).write_text(s)
print('Staged owned codec/gpio/Kconfig/DT and two configuration copies')
