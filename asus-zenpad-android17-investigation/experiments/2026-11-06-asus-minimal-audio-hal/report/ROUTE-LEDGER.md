# Exact public route ledger — P00A/MT8163

This is a source/stock-configuration ledger, **not a physical sound result**. Both delivered route profiles are unqualified. Kernel control existence, a successful setter, a source comment, and stock XML presence do not establish a safe fitted-board route.

All cited files are independent public copies under `source/`, with original paths and SHA256 in `evidence/source-pins.json`. `kernel/` means `/srv/android/asus-build-continuation/kernel`; `oem/` is ASUS public kernel3.18. The physical combined r5 image pin remains `46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401`; resolved config pin is `067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f`. That kernel has never booted. No kernel file was edited.

## Card, PCM, framing and clocks

| Item | Exact source evidence | Qualification |
|---|---|---|
| Card | `mt_soc_machine.c:1157` defines `snd_soc_card_mt.name = "mt-snd-card"`. `soc-core.c:1881` uses `SNDRV_DEFAULT_IDX1`, so numbering is allocated at registration. | Card **0 is a candidate**, not a source-guaranteed numeric card ID. Runtime card-name and PCM identity must agree. |
| Playback PCM | `mt_soc_machine.c:862–883`: first DAI link `MultiMedia1`, `MT_SOC_DL1_STREAM_NAME`, `MT_SOC_DL1DAI_NAME`, `MT_SOC_DL1_PCM`, `MT_SOC_CODEC_TXDAI_NAME`. `soc-core.c:585,1660` assigns rtd order and passes it to `soc_new_pcm`. | Source candidate device **0 playback**. OEM machine starts with the same DL1/UL1 order. No live card/PCM inventory was used. |
| Capture PCM | Second DAI link `MultiMedia2`, `MT_SOC_UL1_STREAM_NAME`, `MT_SOC_UL1DAI_NAME`, `MT_SOC_UL1_PCM`, `MT_SOC_CODEC_RXDAI_NAME`. | Source candidate device **1 capture**. |
| DL1 signal | `mt_soc_pcm_dl1.c:389–470` configures sample format, I2S DAC, rate, then I05→O03 and I06→O04; MEM_DL1 channels/rate and IRQ1 follow runtime. | Userspace does not duplicate these AFE connections with guessed mixer writes. |
| UL1 signal | `mt_soc_pcm_capture.c:110–162` configures ADC I2S and VUL, I03→O09 and I04→O10, IRQ2, then VUL rate. | Mapping an ADC input to the fitted microphone still requires the analog source route. |
| Format declarations | `mt_soc_pcm_common.h:128–140`: S/U16, S/U24, S/U32, each LE/BE. DL1 and capture both use this broad declaration. Code separately handles 32-bit as 24-bit aligned in a 32-bit word. | This HAL offers **S16_LE only**, never treats broad driver declarations as tested capability. |
| Rates | DL1 constraint list: 8000,11025,12000,16000,22050,24000,32000,44100,48000,88200,96000,176400,192000. Capture constraint list: same first nine through48000, despite its initial hardware descriptor's 192000 maximum. | HAL offers **48000 only** in both directions, also present in stock XML. |
| Channels | Both PCM descriptors use normal min1/max2. | HAL profile is stereo output and mono input; actual mono ADC channel selection remains a commissioning prerequisite. |
| Period/buffer | DL1 max48KiB, periods1–4; capture max48KiB. HAL480 frames ×4 periods =1920 frames. At48kHz: period10ms, ring40ms; output1920bytes/period, input960bytes/period. | These are frame/ring durations, **not a bound on kernel ioctl wall time**. No physical latency claim. |
| Copy alignment | DL1 copy rounds `copy_size` with `Align64ByteSize` (`dl1.c:527`); capture rounds requested byte count (`capture.c:473`). | HAL rejects non64-byte-aligned calls, limits calls to one ring, handles partial **frame** results and returns byte counts. If a short result leaves an unaligned tail, it shuts down and returns the actual short result instead of resubmitting a tail the driver would truncate. |
| Error caveat | Capture callback returns0 on several `copy_to_user_fromio`/invalid-buffer branches and ends with `read_count >> 2`; DL1 has zero-return paths too. | This HAL cannot repair a kernel callback reporting successful transfer without data. Parent must audit ALSA callback contract/error propagation before physical capture qualification; no kernel patch is bundled. |
| Prepare order | Codec prepare updates `mBlockSampleRate` from runtime (`codec.c:627–650`). | HAL opens/configures PCM, explicitly prepares it **before analog enable**, then transfers. It does not power ADC at an assumed default rate. |

Literal names in `AudDrv_Def.h`: DL1 CPU `mt-soc-dl1dai-driver`, platform `mt-soc-dl1-pcm`, codec DAI `mt-soc-codec-tx-dai`, stream **`MultiMedia1_PLayback`**; UL1 CPU `mt-soc-ul1dai-driver`, platform `mt-soc-ul1-pcm`, codec DAI `mt-soc-codec-rx-dai`, stream **`MultiMedia1_Capture`** (despite machine link MultiMedia2). These strings distinguish stream names from numeric PCM IDs.

## Stock configuration and board divergence

`source/stock/audio_policy_configuration.xml` declares primary HAL3.0, primary playback S16 at44100/48000 stereo, input S16 at8000/16000/32000/44100/48000 and mono/stereo/voice masks. It also advertises fast/headset/FM/voice and additional modules. The new policy deliberately restricts itself to the implemented future PCM profile and C API2.0; it does not copy those additional capabilities. The legacy `/vendor/etc/audio_policy.conf` is captured too, but its primary output is44100 and its comments describe a generic template; it is not stronger evidence than the XML.

`AudioParamOptions.xml` has `MTK_AUDIO_SPEAKER_PATH=int_spk_amp`, `MTK_DUAL_MIC_SUPPORT=no`, `MTK_TB_WIFI_3G_MODE=WIFI_ONLY`, `MTK_AUDIO_HD_REC_SUPPORT=yes`. Options are vendor parser inputs, not observed runtime selection. They do not authorize copying vendor DSP tuning into a new HAL.

`audio_device.xml` gives the following **literal stock sequences**, retained as evidence, not activated by this bundle:

- `speaker_output/turnon`: `Audio_Speaker_class_Switch=CLASSAB`, `Speaker_Amp_Switch=On`, `Ext_Speaker_Amp_Switch=On`. Turnoff: external Off then speaker Off.
- `ext_speaker_output`: external On/Off alone. `headphone_output`: right then left `Audio_Amp_*_Switch` On; this is a headphone path, not a speaker mapping.
- `builtin_Mic_SingleMic/turnon`: `Audio_MicSource1_Setting=ADC1`, ADC1 On, ADC2 On, preamp1 `IN_ADC1`, preamp2 `IN_ADC3`. Turnoff: preamp1 OPEN, ADC1 Off, ADC2 Off. The XML also contains Mic1, Mic3, DualMic and BackMic variants; their presence does not identify the selected path or justify enabling all ADCs.
- Mic type entries separately select ACC/DCC/DMIC/DCCECM modes. The options above alone do not determine the fitted input mode.

**GPIO/mode discrepancy:** OEM Z380M DTS and combined DTS both define external amplifier high/low pinctrl states on **GPIO24, function GPIO24 (mode0)**. OEM codec contains AW8736 MODE3 (commented0.8W) pulse code, but its nonlegacy external enable block is under `#ifndef CONFIG_MTK_SPEAKER`; the OEM defconfig has `CONFIG_MTK_SPEAKER=y`. The combined resolved config also has `CONFIG_MTK_SPEAKER=y` **and additionally `CONFIG_AMP_AW8737S=y`**. Combined `Ext_Speaker_Amp_Change` therefore executes AW8737 MODE4 (four pulses, 2µs edges, 25ms warmup) outside that conditional. Those comments do not identify the physically fitted amplifier or prove a safe0.8W limit. Replaying the stock external-switch write on this kernel has materially different semantics. **Do not activate it or toggle Audio_Ext_Speaker to try alternatives.** Next source target is to reconcile the ASUS internal-speaker topology with the added AW8737S path in a separate kernel revision owned by the parent.

Public stock init does not resolve this discrepancy. `ueventd.rc:58` gives `/dev/snd/*` mode0660 system:audio; `init.mt8163.rc:139` creates `/data/nvram/media` media:audio; audio command daemons are ATCI services, not route definitions. No old daemon, calibration directory permissions, or legacy framework library is installed here.

## Mixer controls and exact enum domains

Enum indices below are zero-based and names are case-sensitive. Source setters can have weaker validation or do nothing; the HAL's route engine validates exact enum names and scalar type before any write. There is **no global maxgain initialization**.

| Controls | Enum values / indices | Actual constraints |
|---|---|---|
| Audio_Amp_L_Switch, Audio_Amp_R_Switch | Off0, On1 | Headphone buffer/DAC path; DC compensation is applied here. Deferred. |
| Speaker_Amp_Switch | Off0, On1 | Internal PMIC speaker/voice-buffer sequence and `Apply_Speaker_Gain`. It is not equivalent to Audio_Amp_L/R. |
| Ext_Speaker_Amp_Switch | Off0, On1 | GPIO/pulse divergence above; gated. |
| Audio_Speaker_class_Switch | **CALSSD**0, CLASSAB1, RECEIVER2 | Exact source spelling is CALSSD. Stock speaker path chooses CLASSAB; do not silently normalize names. |
| Audio_Speaker_PGA_gain | Mute0, 0Db1, 4Db2, 5Db3,6Db4,7Db5,8Db6,9Db7,10Db8,11Db9,12Db10,13Db11,14Db12,15Db13,16Db14,17Db15 | Setter and Apply_Speaker_Gain clamp index to1–11. **Mute0 becomes0dB**, not mute; index15 does not produce17dB through this path. Power switch Off is needed for shutdown. Candidate initial analog gain, only after internal path qualification:0Db, not maximum. |
| Headset_PGAL_GAIN / Headset_PGAR_GAIN | 9Db0,7Db1,5Db2,3Db3,1Db4,-1Db5,-3Db6,-5Db7 | Do not apply these to speaker simply because their names exist. |
| Lineout_PGAL_GAIN / Lineout_PGAR_GAIN | 8Db0 through-10Db18 in1dB steps, -40Db19 | Register writes in these setters are `#if 0`; cached state changes are not proof of analog attenuation. |
| Ext_Amp_Gain | 6dB0,12dB1,18dB2,24dB3 | Not proof of AW8737S power-mode selection; do not use as an attenuation substitute. |
| Audio_Ext_Speaker | false0,true1 (AW8737S conditional) | Calls `setUsingExtSpeaker`; it has no getter and is not a stock route qualification. |
| Audio_ADC_1_Switch / Audio_ADC_2_Switch | Off0,On1 | Real mode-selected ADC power callbacks, main/ref source branching. |
| Audio_ADC_3_Switch / Audio_ADC_4_Switch | Off0,On1 | Current getters/setters are removed/no-op. Success must not be interpreted as working ADC3/4. |
| Audio_Preamp1_Switch / Audio_Preamp2_Switch | OPEN0,IN_ADC1 1,IN_ADC2 2,IN_ADC3 3 | Select source mux; exact board main/reference wiring still requires observations. |
| Audio_PGA1/2/3/4_Setting | -6Db0,0Db1,6Db2,12Db3,18Db4,24Db5 | PGA1/2 real gain writes; PGA3/4 stubs must not be used. Candidate first mic gain is-6Db only after ACC/source qualification. No calibration value is inferred. |
| Audio_MicSource1/2/3/4_Setting | ADC1 0,ADC2 1,ADC3 2,ADC4 3 | ACC source1 branches interpret0 as main mic,1 headset,2 reference. Mere enum support does not establish every physical ADC. |
| Audio_MIC1/2/3/4_Mode_Select | ACCMODE0,DCCMODE1,DMIC2,DCCECMDIFFMODE3,DCCECMSINGLEMODE4 | DCC callback logs not-supported but returns true. **Do not advertise DCC as working.** |
| Board Channel Config | Stereo0,MonoLeft1,MonoRight2 | Machine getter uses DT `channel-type`; setter is a no-op. Observe actual channel identity before choosing mono capture. |
| I2S low Jitter function | Off0,On1 | No reason to enable it for this fixed48kHz profile. |

## Mic bias and record route

`TurnOnADcPowerACC` (`codec.c:2510–2638`) applies mic PGA values, enables L/R reference/bias paths, selects source1 main/headset/reference branches, sets MICBIAS `AUDTOP_CON8` bit0x8, and enables L/R ADC/PGA. When no ADC remains enabled, it clears ADC/PGA and bias and disables the UL path. `TurnOnADcPowerDmic` separately sets digital-mic clock/bias; it is not interchangeable with ACC. DCC/DCCECM are not implemented in this source despite success returns.

The delivery therefore provides no enabled microphone sequence. Required remaining facts are the selected stock mic-type control, source/preamp controls, ADC1/2 state, actual capture channel placement, and matching combined-kernel control semantics. A normal record route must not be replaced with a loopback/sine-test/calibration route. No micbias/sysfs/direct PMIC writes are added by the HAL.
