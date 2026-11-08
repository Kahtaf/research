# P00A speaker reconciliation: evidenced branch blocker

The exact stock software path includes the MTK internal speaker and a separate **GPIO28 gate**. The earlier assertion that OEM `CONFIG_MTK_SPEAKER=y` makes the entire `Ext_Speaker_Amp_Switch` inert is false: it suppresses the generic GPIO24/AW8736 section, but ASUS added `gpio_set_value(pin_extspkamp, 1/0)` **outside that guard**. The public stock boot binary confirms this ASUS branch. Disabling AW8737S alone cannot preserve the stock software topology.

No source/config patch is staged. Fitted amplifier identity, GPIO28's electrical role, and active stock route selection remain unestablished. This is a bounded implementation blocker, with the source and binary discrepancy resolved. HAL routes remain unqualified. No physical/flash GO.

## Evidence and exact compilation

Inputs are independent copies under `inputs/`, with original path, byte count and SHA256 in `evidence/input-pins.json`. Combined audio sources and Kconfig/Makefiles match the complete r5 source manifest; BMC changes concern the already documented nine paths. The physical complete BMC Image/config/DTB are verified directly:

- Image.gz-dtb `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`.
- Resolved config `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`.
- Appended DTB equals the separate `a099d0538b270e23ec0d034b507eef9248252a3c459a11aa70edb6520bfd2b77` artifact byte for byte.
- The HAL file named `source/stock/resolved.config` is **combined r5**, hash `067090e0…`, not the OEM stock boot's extracted config.

OEM defconfig has `CONFIG_MTK_SPEAKER=y` (line 364). Its ARM64 OF source uses the nonlegacy branch. No embedded IKCONFIG was found in the actual public stock Image; a complete exact stock resolved configuration cannot be reconstructed from that defconfig alone. Actual stock symbols and instructions independently confirm the internal speaker and ASUS GPIO branch. The source archive release and shipping firmware release are different; this report claims a match of the inspected behavior, not source-to-binary reproducibility of the whole OEM kernel.

Combined defconfig lines 251–255 explicitly enable MT8163, MTK_SPEAKER and AMP_AW8737S. Both amplifier options default **n** in `inputs/combined/sound/soc/mediatek/Kconfig:136,225`. AW8737S has no direct dependency on, exclusion from, or reverse select by MTK_SPEAKER. Its visibility is inherited through SOUND → SND → SND_SOC. The resolved config selects those menus and MT8163=y, MTK_SPEAKER=y, AMP_AW8737S=y, OF=y, and has no CONFIG_MTK_LEGACY entry. `CONFIG_SND_SOC_MT8163_AMZN` and `CONFIG_MTK_SND_SOC_NEW_ARCH` are off. This is an explicit board-defconfig selection, not a Kconfig default turning itself on. All-definition/reverse-dependency search receipts are retained; no `olddefconfig` or full/target kernel build was run.

`inputs/combined/sound/soc/mediatek/Makefile:19` enters the MT8163 directory. Its Makefile compiles the codec/GPIO/AFE/machine objects under MT8163 and the internal speaker object under MTK_SPEAKER. AW8737S changes conditionally compiled code within the codec/AFE objects, rather than selecting a separate probed amplifier driver.

## Stock-matched public boot and disassembly

Public WW-5.3.20.0 boot member hash is `a175ed39c9e9642756dd28f1d006b39937d17f290da6af69dda6d4b52d6f910d` (10,004,736 bytes). Zero-padding those public bytes to 16,740,352 gives `7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`, matching the existing public audit/rollback receipts for both original boot captures. No original partition backup contents were opened. The stock topology receipt records the matching WW_P00A-V5.3.20-20180809 fingerprint. This is an offline historical match, not a new measurement of the currently running kernel.

`binary_evidence.py` extracts the actual Images and validates embedded kallsyms address/count/name/marker/token structures: stock 70,337 absolute symbols; combined 42,362 relative symbols. Since these are raw Images, it wraps unchanged instruction bytes in an ELF container with generated symbol metadata; it does not assemble replacement instructions or manufacture a stock ELF. Native Apple LLVM disassembles the real public bytes. ARM64 Image offset and `_stext` mapping are controlled with exact OF string cross-references (`address-mapping-controls.json`); final verification compares the ELF text byte for byte to the input Image.

| Public binary | Actual evidence |
|---|---|
| Stock `Ext_Speaker_Amp_Set` at `ffffffc000910f28` | Reads the cached GPIO number; nonzero on-path calls `gpio_to_desc` at `…0fbc`, then `gpiod_set_raw_value` with 1 at `…0fc4`; off-path calls it with 0 at `…0f7c`. There are no AW pulse/delay/EXTAMP-select calls in this setter. |
| Stock codec init at `ffffffc000f510fc` | Looks up `mediatek,mt8163-soc-codec-63xx`, gets `extspkamp-gpio` through `of_get_named_gpio_flags`, stores that GPIO, and registers the codec driver. |
| Stock internal speaker | `Speaker_Amp_Change` at `ffffffc000912194` calls the class-specific open/close implementations. `Speaker_ClassAB_Open` at `ffffffc0009194a8` and close at `ffffffc00091954c` operate PMIC registers via `Ana_Set_Reg`. |
| Combined external setter at `ffffff8008948770` | AW sequence is inlined: seven select calls high/low/high/low/high/low/high, six `__udelay` calls, and 25 ms `msleep`; off has the eighth select call low. |
| Combined codec init at `ffffff8008f48e38` | Matches a codec/audiosys node and reads `switch-mode-delay`; missing-property path returns -22 **before** `__platform_driver_register`. |
| Combined internal speaker | Internal ClassAB open/close calls and implementations remain compiled. Presence does not establish codec registration, an active route or sound. |

The separate `*-codec-probe-disassembly.txt` receipts also show stock probe GPIO request/direction-output calls and their absence from the combined probe. Full selected function disassembly and all embedded symbols are in `evidence/{stock-public,bmc}-disassembly.txt` and `*-symbols.tsv`.

## GPIO ownership and the actual stock call chain

Stock XML `speaker_output/turnon` requests CLASSAB, Speaker_Amp_Switch On, then Ext_Speaker_Amp_Switch On; turnoff requests external Off then internal Off. `AudioParamOptions.xml` says `MTK_AUDIO_SPEAKER_PATH=int_spk_amp`. XML/options are static software intent, not proof of runtime selection or fitted component identity.

OEM codec `inputs/oem/asus-original/kernel-3.18/sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.c`:

- Lines 1291–1409: `Speaker_Amp_Set` → `Speaker_Amp_Change` → DAC/voice-buffer/PMIC speaker clocks → selected ClassAB/D/receiver open/close → `Apply_Speaker_Gain`. No GPIO24 pulse call occurs in that internal function.
- Lines 1412–1510: under OF, ASUS declares `pin_extspkamp`; on/off write that pin at 1461–1462 / 1494–1495 **before** the generic `#ifndef CONFIG_MTK_SPEAKER` blocks. Therefore internal speaker plus external gate is a valid compiled combination in OEM software.
- Lines 1594–1614: the external mixer setter calls the external change function and updates its cache.
- Lines 3544–3552 and 3622–3626: codec init obtains `extspkamp-gpio` from DT. Codec probe at 3452–3458 requests it and sets output low. Error handling in this old OEM API is not a model for a new port; do not copy its unchecked/error-valued GPIO handling blindly.

Actual stock appended DT: `/soc/mt_soc_codec_name@11220000/extspkamp-gpio = <0x0d 28 0>`, with phandle 0x0d resolving to the MT8163 GPIO controller. This identifies **GPIO28, flags0**, as the software gate. It does not identify a fitted AW part.

Both actual DTBs also contain GPIO24 function0 (`pins=0x1800`) audio `audexamphigh/low` pinctrl states and references from the DL1 GPIO consumer. Their presence is not board-population evidence. Both simultaneously assign GPIO24 to `/soc/usb@11270000`, `usb_dpn_sel-gpio`, with the `usb-dpn-sel-pin` state. Thus GPIO24 has competing described consumers, not exclusive speaker ownership. No pinctrl-debug or live ownership observation was performed. USB/radio/charging code/config were not changed.

The combined codec DT lacks the stock GPIO28 `extspkamp-gpio` property, and its codec source lacks the ASUS GPIO28 gate/lookup/probe handling. Generic `AudDrv_GPIO_EXTAMP_Select` chooses the GPIO24 high/low pinctrl states. Its optional headset-sharing mode is absent in these DTBs. AW **mode4 is a pulse-command mode, not GPIO mux function4**.

Combined source `mt_soc_codec_63xx.c:1515–1613` places AW mode4 outside the MTK_SPEAKER guard. Contrary to the prior ledger's fixed 2 µs description, it uses the variable `switch_mode_delay`, initialized to **0** at line 93 and populated from DT only. No `switch-mode-delay` exists anywhere in the pinned combined DTB. `mt_soc_get_dts_config` (4013–4032) fails and `mtk_mt6323_codec_init` (4119–4122) returns -EINVAL. This proves the static init failure for the exact appended DT; it does **not** show pulses occurred or that an external bootloader could not alter DT. Do not add a guessed delay to bypass this block.

AW-related AFE changes also include an `Audio_Ext_Speaker` control and `setUsingExtSpeaker` state selecting an alternate `SetDLSrc2` constant. This is a distinct control, not the stock external gate. No alternate gain, amplitude, calibration or default is proposed.

## Controls and counterfactual checks

`evidence/host-checks.json` records execution of verbatim source fragments with mocked GPIO/pinctrl/delay/registration boundaries. Nothing opens a device or sleeps/toggles hardware. Generated fragments, compile/preprocessor outputs and command receipts are retained.

| Host variant (OF, nonlegacy, MTK_SPEAKER=y) | Observed mock behavior |
|---|---|
| OEM source, GPIO value28 from public DT | GPIO28 high then low; no generic select, delay or warmup calls. |
| Combined AW=y, external function isolated from init | high/low/high/low/high/low/high; six delay arguments0; 25 ms mock warmup; final low on disable. This is a latent code-path test, not an initialization/physical result. |
| Combined AW=n, counterfactual only | Zero GPIO/pinctrl/delay calls in external function. **Stock GPIO28 behavior is also absent.** |
| Combined init, exact missing-property boundary, AW=y | -22, registration counter0. |
| Combined init, same boundary, AW=n | 0, registration counter1; does not prove a functional codec or complete stock topology. |

The combined internal `Speaker_Amp_Change` preprocesses identically (normalized hash `6edea3228fa95dd80a89cba96dee3b3946b9aa001b79dbacf556c7b044a5d7ab`) with AW on/off: actual ClassAB open/close and Apply_Speaker_Gain calls remain. The real stock and BMC disassemblies independently retain internal ClassAB calls. This disproves the need to remove MTK_SPEAKER to eliminate AW pulses; it also disproves AW-off alone as stock-software parity.

The pre/post receipt is explicit: **zero staged source/config changes**; post equals the pinned preimage. `config-accounting.json` contains the exact defconfig/resolved hashes and a computed, nonserialized one-symbol counterfactual hash. That counterfactual was not resolved by olddefconfig and is not an integration artifact. Charging/radio/sensor/memory configuration is byte-for-byte unchanged.

The historical seven mixer queries provide idle/cache values only: CLASSAB, MIC1 ACC/ADC1, preamp OPEN and amps/ADC off. The unprivileged first query failed. Existing root queries succeeded without route activation. Card0 `mt-snd-card`, PCM0 playback/PCM1 capture identify software endpoints; none qualifies the speaker, microphone, gain or wiring.

## Decision and bounded continuation

Relative to the exact public stock software, the combined defconfig explicitly enables an incompatible generic AW8737S path and omits ASUS's GPIO28 gate. AW8737S is present in the base tree's karnak defconfig and other board DTs have the delay property; the feature is not P00A-specific. This is strong evidence of a board-port mismatch. It is **not** proof that the P00A has no external component, that an AW8737S is fitted, or that GPIO28 can safely be driven by a new kernel.

Required evidence before choosing an enable/disable implementation:

1. Exact P00A/Z380M board-revision schematic/BOM, or equivalent identifiable component/wiring evidence, mapping PMIC speaker outputs, GPIO28 and GPIO24 to their fitted functions. Identify whether GPIO28 controls an amplifier, analog switch, power gate or another element; identify the part and applicable command semantics if it is an amplifier. No part identity follows from `extspkamp-gpio` or generic pinctrl labels.
2. Separately authorized stock normal-playback transition evidence showing which mixer controls the selected stock HAL actually changes and shuts down, and which stock per-unit data that path requires. Idle enum state and route XML cannot substitute. This spike authorizes no new observation or playback.
3. Confirm the selected runtime DT equals the public stock/combined DT under review, or supply a public exact bootloader DT-fixup contract. Do not assume a fixup supplies the missing delay. No device access is included here.

After those facts, a separate owner can implement one board-specific GPIO28 gate using the established stock source/DT contract, preserve the PMIC internal ClassAB sequence and stock off ordering, remove only demonstrably unrelated AW paths for this board, and handle GPIO acquisition/errors using the actual Linux4.9 APIs. Keep GPIO24 USB ownership intact. First prove config dependencies and all on/off/suspend/test-path callers offline against exact preimages; negative tests must show no GPIO24 pulses, positive tests must preserve the required GPIO28 and internal paths. Do not implement this as a generic dual-option combination or a guessed DT timing property. No patch application, full/target build, product integration or HAL qualification follows automatically.

## Reproduction and constraints

Run from this spike, sequentially: `python3 scripts/collect.py`, `python3 scripts/binary_evidence.py`, `python3 scripts/host_checks.py`, `python3 scripts/receipts.py`, `python3 scripts/final_verify.py`. These read only the allowlisted local public paths and write only inside this spike. They require existing local Python3, Apple clang/LLVM and the recorded sibling artifacts. No download/install is part of reproduction.

Extraction is bounded to 64 MiB uncompressed per Image. Subcommands have finite 45 s wall/30 s CPU and 128 MiB output-file bounds; the binary decoder has a 45 s CPU bound. Compilation is small host fragments only, sequential, no workers/make/ninja. Darwin lacks sched_setaffinity, and this host rejects the requested 1 GiB RLIMIT_AS. Hard one-core affinity and a hard 1 GiB address-space guarantee cannot be claimed; the limitation is captured in `darwin-constraints.json`. Recorded child resident high-water values support the small-run footprint (41,107,456 bytes in the final recorded host replay; this is a child high-water statistic, not a hard process-tree memory cap). These constraints rule out pretending a Linux full-kernel build/config resolution occurred on this host.

No subagents, device/ADB/root/USB/mixer/PCM/GPIO/playback/capture/charging activity, network/SSH/cloud/VM action, active source/out changes, private calibration/key contents, or rejected PCM audio-copy patch work occurred. Final verification rehashes every copied original input and the real binary text. The blocker is fitted-topology evidence, not a failed physical test.
