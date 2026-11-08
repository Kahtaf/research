# Minimal-platform TEE continuation — stopped at final link

Question: can the same reduced-consumer experiment build after restoring the ancestor TEE selection accidentally removed during preparation?

Status: **config gate passed; the single authorized continuation failed at final linking. STOPPED.** Initial failure/source/config/partial output remain preserved. No retry, repair, add-back, warning suppression, new helper compile, recovery package, PLAN, decoder tests or device action. The exact VM is verified TERMINATED and this spike's SSH master is closed. This experiment still has no physical trial.

The corrected ancestor DEVAPC branch compiled. Its actual object contains `Enable TEE...Request IRQ in TEE.`, omits the REE request-IRQ message, and its probe calls `devm_clk_get` without the REE request-IRQ/start-devapc path. That establishes branch selection and object compilation only; TEE runtime and protection remain unqualified.

The final linker found these retained callers with unresolved dependencies:

| Actual caller | Missing symbol | Relevant unchanged minimal configuration |
|---|---|---|
| `met_tracing_record_cmdline` | `tracing_record_cmdline` | `FTRACE=n` |
| `virtual_sensor_set_cur_state` | `setMaxbrightness` | `VS_BACKLIGHT_COOLER=y`, `MTK_LEDS=n`, `FB=n` |
| `battery_meter_dts_probe` | `register_netdevice_notifier` | checked battery/SOC retained; `NET=n` |
| `battery_meter_dts_remove` | `unregister_netdevice_notifier` | same retained battery/network dependency |

These are actual link/relocation failures, not a runtime result or a diagnosis of the prior physical stall. No attempt was made to restore those consumers, remove keepers or provide stubs. The accepted stop boundary applies.

| Exact input/output | SHA256 / value |
|---|---|
| Initial failed config | `add8f8e85e0fe007364da835f2d45d91663551876387ba4a695e410d4c1cc7bb` |
| Parent pre-olddefconfig requested input | `daf3ece9c39d8758491796acb6a767a3e24f080d8973becc67248d97048fd3fe` |
| Actual resolved config, unchanged after make | `6f8abd4290b19aad386770200825d3065e74fd8fb311d4b1b20c7af2cc621dc6` |
| Reused static ARM64 helper | `37e9e2a2d73447947fb33e57e9513fa6079517b571f5a41bc58fbb91f84633fc`, 772248 bytes |
| Actual partial DT, identical to initial attempt | `156e92ec5d4f5c4bd20169128c8aed0a89b43636d945d648392aaaec8b9bf82e`, 65873 bytes |
| DEVAPC TEE object | `18d1f6538cbb9589805c985d9e3b76351f833fafbc8d7d46d83abe64742bd0c3` |
| Retained initrd | payload 319962 bytes; `0x44000000..0x4404e1da` |
| Source/run UUID | `a60fca94-e760-4ce5-a790-5c9a818ce406` |

One olddefconfig changed only two effective selections: `MTK_IN_HOUSE_TEE_SUPPORT` and `MTEE_CMA_SECURE_MEMORY`, both to ancestor `y`. OF and CMA were already y. Every other effective failed-minimal value remains. The exact textual diff also materializes `# CONFIG_MTK_SEC_VIDEO_PATH_SUPPORT is not set` when the TEE dependency makes that symbol visible; its effective value remains n, preserving the explicitly reviewed secure-video consumer removal. This is not a third selection or add-back. See [config-gate.json](evidence/config-gate.json), [the full textual diff](evidence/config-vs-failed.patch), and [visibility explanation](evidence/config-gate-interpretation.json).

The independent ordinary copy preserved kernel/out mtimes and checked distinct inodes for 66217 files before build; no `.cmd` execution history or timestamp was edited. Native Kbuild regenerated the owned output's `source` symlink normally. Final source hash comparison against the initial failed tree found only `arch/arm64/kernel/asus_entry_tag.h`, with the actual resolved config hash refreshed. DTS, entry guard geometry/calibrated admission, short 89-byte cmdline, hardware/reservations, helper and initramfs remain unchanged. The secure pool is enabled and the actual partial DT matches the initial attempt byte-for-byte.

Correction to the initial stopped unit's narrative: a partial compiled DT did exist there. It is now explicitly pinned and verified identical; neither attempt produced an Image or final vmlinux. The original frozen handoff has not been edited.

History: one initial compiler failure, then this one authorized config-corrected link failure — **two kernel make invocations total**. One helper compile total, none here. No full clean, extra RLIMIT_AS, timeout-kill, driver edits or new hardware-writing code.

Review [the link failure receipt](evidence/link-failure-receipt.json), [complete compiler/linker log](evidence/kernel-compile.log), [TEE object disassembly](evidence/devapc-TEE-branch.disasm), and four `evidence/failure-call-*.disasm` files. [BUILD-STOP.md](BUILD-STOP.md) records commands and continuation limits. Partial kernel/out remain remote at `/srv/android/asus-minimal-platform-build-r2-20261108`. Original failed prefix and preparation remain unchanged.

Continuation: parent reviews the new dependency blockers. No further build/config/source change or physical action is authorized by this handoff. There is no genuine candidate, full-p10 pin, System.map or installer to review or execute. Package/profile/PLAN/decoder work required a real successful Image and was not run. Retained thermal/PMIC/BQ inhibition, battery/SOC/notifications, CPUFreq/SPM/HPS/idle and watchdog/power-key paths are explicit, with no physical qualification or fault-localization claim.
