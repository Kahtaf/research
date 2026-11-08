# GPIO28 lifetime/suspend repair — source candidate for fresh independent review

Both reviewed lifecycle findings are fixed in a **new, unqualified source candidate**, relative to the completed GPIO28 source-port candidate. The prior source port and independent review are unchanged. No target object/kernel/image build, integration, hardware operation, qualification change or physical GO occurred.

The incremental patch is `patches/lifecycle-from-gpio28-candidate.patch`. It changes five paths: codec C, GPIO C, their shared codec header, the gate header, and a new control-boundary header. Exact pre/post hashes and the new-header absence requirement are in `evidence/pre-post-pins.json`. It replayed with fuzz0 into fresh owned copies and matched all five postimages. No config/DT/routing-source change is included.

## Findings, preserved failures and corrected behavior

The review's HANDOFF and original negative logs are pinned under `inputs/review/`. Its actual test sources/generated bodies are copied under `baseline/`. Both NULL failures were rerun locally with their verbatim old production bodies and UBSan: direct exported PM after detach and **the actual independent routing PM callback** after detach. Darwin UBSan terminates with SIGABRT (-6), whereas the preserved Linux review logs exited1. The stale-suspend reproduction also reran and accepted On with old `mAnaSuspend=true` / gate suspended=false. These expected failures are retained in `evidence/baseline-*-run.txt` and their command records; they are not passing safety checks.

Corrected production-body tests pass the same lifecycle sequences:

- Routing PM after detach records suspend intent without dereferencing codec data or accessing an unowned GPIO. Detached gain, headphone and guarded mixer readers also avoid private access.
- Suspend → detach → complete reprobe → repeated suspend keeps analog intent and gate interlock active. On returns -EBUSY until an explicit intended resume. No test reset is inserted between these lives.
- Suspend/resume while absent updates the persistent intent; the next probe inherits the latest intent. Backup power state from an old allocation is not restored into a new one.

The selected routing source is exactly `sound/soc/mediatek/mt_soc_audio_8163/mt_soc_pcm_routing.c`, SHA256 **`c458de71bb3c2cccd8b0d39a4c7c6e3a75f962cc8bdda44697eacca4f30bbd3a`**. It is copied as preimage/candidate but byte-identical and absent from the patch. The host includes its actual `mtk_routing_pm_ops_suspend/resume` and the pinned AFE's actual `ConditionEnterSuspend`. No suffix search or `_amzn` variant selects this caller. No excluded PCM-copy repair source or patch was accessed.

## Lifetime/readiness and lock ordering

`mt8163_codec_state_mutex` protects private pointer ownership, readiness, analog suspend intent/applied state and **the full duration of every audited external private-state access**. A reader does not unlock after a NULL check. Initialization/publication and removal/free use the same state mutex. The existing gate mutex stays nested inside it, so PM does not recursively acquire the gate lock as its lifetime lock.

The audit found five original non-static roots with direct/transitive private-state access:

| Root | New rule |
| --- | --- |
| SetAnalogSuspend | Hold state mutex; record requested intent even while absent; only enter the analog body when ready. |
| OpenAnalogHeadphone | Hold state mutex throughout the original analog body; absent calls do nothing, and an On request is also suppressed while suspended. The void ABI is preserved. |
| UpdateHeadsetGain | Hold state mutex throughout the original gain body; internal callers use the locked implementation without reacquiring the mutex. |
| SetMicPGAGain | No selected external caller; now static and reached only inside protected analog call chains. Gain body unchanged. |
| InitCodecDefault | No selected external caller; now static, called by protected initialization only. Default body unchanged. |

All original non-private exported roots are listed separately in `evidence/private-consumer-audit.json`; register-only/stub/frequency helpers do not reach `mCodec_data`. Static analog helpers are reached from these protected roots, initialization, or guarded controls. Every original codec-C private pointer reference is mapped to an audited function, except its global declaration. The separate gate header's cache/access functions require the same state mutex and contain lockdep assertions.

**46 private-state ALSA control callbacks** are registered through `CODEC_CONTROL(name)` wrappers. Each wrapper holds the state mutex from readiness check through the original callback and return, returning -ENODEV when detached/unready. Original internal speaker/class/PGA callback bodies remain intact. Static internal calls use the underlying functions, not the locking boundary wrappers, avoiding recursive locks. Source checks verify every affected control-table reference selects its guarded wrapper. Conditional source callbacks remain conditional; 46 is the source audit count, not a claim that every control appears in the selected runtime card.

The GPIO headset callback formerly called the public gain function while holding `aud_amp_mutex`. Simply adding a codec lock to that public function would invert the codec→GPIO lock order. It now takes the state mutex **before** `aud_amp_mutex` and invokes `UpdateHeadsetGainLocked`, which asserts that contract. Its gain-before/after `AudDrv_GPIO_Amp_Apply` ordering is preserved. The shared header declares this explicit locked API; its two GPIO callers are audited. The public `UpdateHeadsetGain` remains available and protected for other callers.

There is also an ALSA control-list ordering boundary. Actual `snd_soc_add_codec_controls` reaches `snd_ctl_add`, which takes `controls_rwsem` for writing; mixer readers can hold that semaphore before entering a codec callback. Initialization therefore does **not** hold the private-state mutex while adding controls. A separate `codec_registration_mutex` serializes entire codec init/remove writers. Initialization checks readiness under the state mutex, releases it for control registration, then acquires it for allocation, defaults, ready publication and suspend reconciliation. PM/readers can progress during registration and see unready state. Removal holds registration→state→gate through the free. Platform unregister and devres action registration execute outside the state critical section to avoid calling back into it recursively.

Relevant nesting is:

1. Init/remove writer mutex, when needed, precedes state mutex.
2. ALSA control registration takes its list lock **without** state mutex; a control callback enters state after the framework's list lock.
3. State precedes existing analog/GPIO amp locks and gate lock. GPIO headset notification follows that same order.

The actual ASoC/core control sources are pinned in `inputs/api/`; this is not an inferred register-callback model. Native tests model the framework service boundaries, not all kernel lock classes. Real ARM64/kernel lockdep validation remains required.

## Suspend intent across allocation lifetimes

`mAnaSuspend` is the persistent requested state. Only `SetAnalogSuspend(bEnable)` changes it, under the state mutex, including calls while detached. It is not blindly cleared by teardown or probe.

`mAnalogSuspendApplied` belongs to the current private allocation. It is reset during teardown/fresh initialization so an old allocation's backups cannot be applied to a new one. The existing analog sequence lives in `SetAnalogSuspend_locked`, driven by that allocation-specific applied flag.

Gate acquisition seeds `p00a_gate_suspended` from the persistent intent under the state mutex. Codec initialization reconciles it again before releasing the state mutex and applies the suspend sequence to the new initialized state if the intent remains active. Redundant suspend still synchronizes the gate interlock even if the analog sequence is already applied. Only an intended resume clears the interlock. If resume arrives while absent, that intent is also preserved for the next probe.

The gate remains an explicit On/Off command interface. Resume does not automatically assert the external gate or restore a stale external On cache. No new GPIO, timing, gain, pulse, calibration or fitted-hardware decision is introduced.

## Host evidence and its limits

`evidence/corrected-final-run.txt` passes **38 inherited scenarios plus 12 new lifecycle scenarios** with UBSan and warnings-as-errors. The final recorded run has **14,672 total assertions**, scheduling-dependent, and **52 allocations matched by 52 frees**. Assertions are checks, not independent scenarios.

New tests execute extracted **actual modified production bodies**, including PM, private init/remove, mixer boundaries, gain/headphone entries, the GPIO headset path, the unchanged routing PM/AFE bodies and existing kernel GPIO/devres adapters. `evidence/production-extraction.json` binds 35 function/header extracts to their production sources. Mocks supply types, hardware/framework service boundaries and scheduling hooks; they do not replace the lifecycle state machine being tested.

Four deterministic cases park PM, gain, headphone and a mixer getter inside their actual protected access. A real pthread mutex is held; a concurrent removal starts, cannot complete/free while the access is parked, then completes after release. A fifth case parks private initialization and demonstrates that independent PM waits until publication completes. An ALSA ordering case holds a synthetic control-list reader while init waits to register controls: the reader can still enter the state guard and return unready, allowing init to proceed. This catches the state→control-list inversion rather than relying on a passing gate-only race test.

The bounded stress run interleaves five actors:24 complete detach/reprobe cycles;64 actual routing suspend/resume pairs;128 gain/headphone iterations;128 actual GPIO headset notifications;128 guarded mixer-reader iterations. Same-device driver/card bind/unbind operations remain serialized by the lifecycle actor, as expected from framework ownership; the independent PM and external readers run concurrently. Real mutex ownership/LIFO checks catch recursion and unbalanced unlocks. An intermediate unmatched-unlock test failure was retained and corrected before the final run. No claim of exhaustive scheduling or full kernel-framework emulation is made; TSan/ASan were not run.

Source/static checks additionally prove:

- Nine complete internal speaker/class/PGA/headset-speaker functions are byte-identical. Three additional gain/default brace bodies are unchanged when made private or moved behind a boundary. Internal headset gain call sites only retarget the same calculation to its locked implementation.
- Config, defconfig, Kconfig, DTS and the selected routing file are byte-identical to this unit's preimages. The complete candidate config stays `26c59e0afa3f6438fafea4b5379b898c9b1fcaf05adf1d7e14db93b2e976bd13`. Charging/radio/sensors/memory options remain untouched.
- Selected codec preprocessing retains ClassAB calls and excludes AW mode/delay/state and generic GPIO24 EXTAMP-select references. GPIO28 binding/flags and GPIO24 USB ownership remain exactly the prior source candidate's topology. No new DTB was generated.
- HAL routes stay false with unchanged `routes.c` SHA256 `006c73c4d3d42f18da3f8b53fddc625a38b00b88704b93730fecb015839ebec8`.

## Command state, not electrical success

All gate/cache statements mean **command state after reported GPIO API success**. The review's actual MT8163 boundary reproduction is retained under `inputs/review/remote/evidence/mtk-boundary-run.log`. The controller discards relevant `regmap_write` statuses and may return GPIO API success despite those lower-level errors. This unit does not modify that controller. It cannot guarantee electrical low, register programming success, glitch-free mux transition, safe amplitude, fitted component identity or speaker function. A native fixture returning GPIO errors tests only failures that escape the lower layers.

## Fresh independent review and remaining gates

Review the incremental patch against the exact five pre/post pins, including the new control header absence requirement. The prior seven-path GPIO28 candidate must be the baseline; this is not a replacement patch against the original BMC tree. The complete relevant candidate/preimage copies are supplied. Applying or integrating into an existing tree was not performed or authorized here.

A fresh independent review should re-check all 46 registration boundaries, every exported private-state path, writer/control-list and GPIO lock orders, and suspend intent during absent/partial/bound/removed states. Repeat actual whole-translation-unit ARM64 compilation of codec/GPIO and header-dependent callers, real linking/config/DTS verification and kernel lockdep/PM behavior only in a separately authorized unit. **The old independent review's successful ARM64 objects belong to the old candidate and do not validate these new sources.** No target object, full kernel, image or product build was run in this unit.

Fitted topology/electrical evidence, normal active stock-route observations, private calibration restoration/consumption contracts, physical commissioning and recovery gates remain outstanding. No route flag, approval or qualification changed. This package supplies no build/image/integration/hardware/physical/flash GO.

## Reproduction and bounds

- Preserved negative replay recipe: `python3 scripts/replay_failures.py` (expected old failures; writes only here).
- Corrected fixture generation: `python3 scripts/make_tests.py`; compile/run commands and flags are in `scripts/run_host.py` and `evidence/commands.jsonl`.
- `scripts/verify_package.py` creates an exact owned patch replay and refuses to overwrite its existing replay directory. Use `scripts/final_verify.py` for read-only rehashing of the completed package.

All commands ran serially with no build workers. Each subprocess has45s wall/30s CPU and128MiB output-file bounds; test scheduling hooks have2s deadlines. Pthread concurrency is intentional within one finite native test process. Darwin has no sched_setaffinity, and rejects the requested1GiB AS/DATA/RSS setrlimit values. `evidence/host-limits.json` records this and an observed child high-water of57,049,088 bytes, not an aggregate process-tree peak or hard one-core/1GiB enforcement claim.

No subagents, device/ADB/root/USB/mixer/PCM/GPIO/playback/capture/charging/radio activity, network/SSH/VM/cloud, AOSP/active source/out access or mutation, full-kernel/target build, private data or excluded PCM copy-repair work occurred. Only pinned public local sources/receipts and owned copies were used. Original pinned inputs are rehashed before handoff.
