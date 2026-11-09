# Original 3.18 MT8163 speaker route audit

2026-11-08. Offline, read-only audit; no tablet, SSH, ADB, mixer, GPIO or calibration operations. No playback qualification is claimed.

## Result

A small speaker route is strongly supported by the original kernel and retained stock firmware XML: playback PCM **hw:0,0**, `Audio_Speaker_class_Switch=CLASSAB`, `Speaker_Amp_Switch=On`, then `Ext_Speaker_Amp_Switch=On`. Shutdown reverses the two amplifier switches. This is a candidate for a reviewed bounded experiment, not an instruction to enable the amplifier now. Confirm the actual running kernel config and loaded codec DT GPIO before the first write: there are materially different conditional GPIO paths in this source.

The existing private/live/current-display-audio-inventory.txt:4 records `00-00: MultiMedia1_PLayback mt-soc-codec-tx-dai-0`; line30 records pcmC0D0p. This is stronger than guessing PCM numbering from source. The original mt_soc_machine.c:706–718 puts MultiMedia1/DL1 first and names the matching codec TX DAI. Headphone `Audio_Amp_L_Switch`/`Audio_Amp_R_Switch` are **not** required by the stock speaker-only XML path.

## Exact evidence

All kernel paths below are relative to `../2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/`. Codec means `sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.c`; DL1 means its sibling `mt_soc_pcm_dl1.c`.

* Retained `../2026-11-05-asus-latest-android-feasibility/evidence/device/vendor/etc/audio_device.xml:32–41` explicitly supplies the three-control speaker startup and external-amp-first shutdown order. Lines8–14 separately identify headphone controls. This is stock configuration evidence, not proof that every stock HAL branch consumes that path.
* Codec:2240–2257 registers the exact names above, `Audio_Speaker_PGA_gain`, lineout/headset gains, `Ext_Amp_Gain`, `AUD_CLK_BUF_Switch`, and `Audio_DAC_SampleRate` (speaker class/gain controls are at1881–1896). CLASSAB is spelled exactly so; the alternative class-D enum has the source typo `CALSSD` (1801).
* DL1:378–428 prepares sample format, I2S DAC, interrupt timing and AFE; 432–452 connects I05→O03 and I06→O04 and enables DL1. Thus separate userspace interconnect mixer writes are not indicated for this PCM. Start with S16_LE stereo 48000 Hz. Codec:652–671 receives runtime sample rate in its DAI callbacks; default DAC rate is48000 at97. Prefer matching48k rather than introducing an independent manual clock/sample-rate recipe.
* Codec:1291–1382 powers the DAC if needed, sequences the analog voice-buffer/speaker path, runs class-AB power-up when built with CONFIG_MTK_SPEAKER, and applies speaker gain. `TurnOnDacPower` at962–984 enables required clocks and PMIC DL; there is no evidence to add a separate `AUD_CLK_BUF_Switch` write to this minimal path.
* Stock ARM64 HAL `evidence/device/vendor/lib64/hw/audio.primary.mt8163.so` retains `OpenSpeakerPath`, `CloseSpeakerPath`, speaker-PMIC and external-speaker-amp open/close symbols plus exact mixer strings. Strings support the route family, but do not prove its control-call ordering, PCM selection or selected platform variant. No disassembly was needed to establish XML order.

## Conservative volume and a critical misleading control

Use `Audio_Speaker_PGA_gain` enum **`0Db` (index1)** for the initial candidate, plus an independently generated PCM signal at **-40 dBFS peak**, about one second long with a short fade at each edge. That digital level is a proposed conservative experiment setting, not an OEM loudness specification or measured acoustic safety guarantee. Use actual playback silence for setup/cleanup, not enum `Mute`.

Codec:128 defaults Speaker_pga_gain to1. Its gain table at1804–1807 starts `Mute`, `0Db`, `4Db`...; both Apply_Speaker_Gain (365–379) and the setter (1828–1857) clamp index below1 to1. Consequently **`Mute` is not a trustworthy hardware mute**, and the highest labels do not even correspond directly to applied values (indices above11 clamp11). Disable both route switches to mute/power down. Do not choose maximum gain.

`Lineout_PGAL_GAIN`/`Lineout_PGAR_GAIN` (1917–1980) look like attenuation controls, but their actual register writes are under `#if 0`; they only retain values. They cannot be relied on to attenuate this experiment. `Ext_Amp_Gain` has labels6/12/18/24dB, but Apply_Ext_Amp_Gain (2080–2087) is a no-op under CONFIG_MTK_SPEAKER; it is not needed for the minimal route.

## AW8736 / AW8737S and GPIO uncertainty

The exact original MT8163 codec defines AW8736_MODE_CTRL at84. It contains the familiar three rising-edge,2µs-gap mode3 sequence, labelled0.8W (1430–1442 and1528–1540); other modes are labelled higher power. **Presence of this macro does not prove it executes.**

Original `arch/arm64/configs/asus8163_tb_380_m_defconfig:364` sets CONFIG_MTK_SPEAKER=y. In the CONFIG_OF external-amp function (1444–1510), the direct `gpio_set_value(pin_extspkamp,1/0)` occurs outside `#ifndef CONFIG_MTK_SPEAKER`; the low/reset, AW8736 pulse and25ms warmup block is inside that guard. With SPEAKER=y, those pulse/warmup lines are skipped and the direct GPIO gate is used. With SPEAKER disabled and nonlegacy OF, pinctrl high/low is used instead (AudDrv_Gpio.c:188–220), not the legacy AW8736 pulse macro. Do not implement userspace pulse trains or infer mode3 from a source define.

Codec:3545–3554 reads `extspkamp-gpio` from compatible `mediatek,mt8163-soc-codec-63xx`. `arch/arm64/boot/dts/mt8163.dtsi:983–986` gives that codec **GPIO28**. A separate audio node at887 has `<24 0>` and the Z380M board's extamp pinctrl states at469–483 select **GPIO24**. These are distinct source mechanisms; picking GPIO24 merely because the board pinctrl mentions it would be wrong for the SPEAKER=y direct-codec path. Confirm the loaded DT and effective config before asserting which path the actual stock binary uses. `of_get_named_gpio` errors are also not robustly validated in this original code, another reason to check the retained/loaded DT first.

No AW8737S identifier was found in the original MT8163 audio driver or original DTS search. Its mention in the historical4.9 audit is a lead, not original3.18 board identification. The source cannot establish physical amplifier part number or required pulse mode from that name. Stock HAL XML routes through the driver and is preferable to manually reproducing GPIO behavior. Calibration, NVRAM, efuse, speaker trim and test controls are outside this experiment and must remain untouched.

## Smallest next step and proposed experiment

1. **Read-only gate:** capture actual `amixer -c0 controls` and `contents` (or tinyalsa mixer listing), `/proc/asound/cards`, `/proc/asound/pcm`, PCM0 playback hw_params when idle, effective `/proc/config.gz` flags CONFIG_OF/CONFIG_MTK_LEGACY/CONFIG_MTK_SPEAKER, and loaded DT codec `compatible`/`extspkamp-gpio` plus phandle resolution. Only inspect those named DT properties; no broad sysfs reads. If loaded DT/config is already retained, parse it offline first. Save baseline control values privately. Missing evidence is this exact effective-config/DT/control snapshot, not a new driver or calibration dump.
2. After parent review and satisfying that gate, build a bounded helper with unconditional cleanup: verify idle PCM and all expected enum names, set0Db, prepare a48k stereo silence stream, set CLASSAB, enable Speaker_Amp, then Ext_Speaker_Amp, allow at least25ms settling, emit one-second faded -40dBFS signal, return to silence, disable Ext first then Speaker, close PCM. Restore changed non-power baseline settings. Timeout/disconnect cleanup must power down those two switches; reject a non-idle or initially powered route rather than disrupting another client. This PCM-before-route staging is a conservative proposed experiment order; XML proves relative amplifier order, not PCM versus amplifier timing.
3. Read back switches off, check PCM stopped and bounded kernel error output, and request physical audibility confirmation. If silent, stop and inspect evidence; do not escalate gain or try alternative GPIO modes. Only after this physical pass consider a persistent ALSA route/helper and browser audio integration.

No implementation or tablet changes were made by this audit.
