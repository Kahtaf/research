# Minimal-platform Linux 4.9 preparation

Question: can one substantially reduced, protection-preserving platform complete normal-priority RAM compute and five timer-driven PID1 wakeups?

Status: **prepared for parent review; stopped before compilation, packaging, device contact or trial.** One resolved design, no configuration matrix, children or new model consultation. The prior Opus whole-plan and parent contract were read; the accepted protection-preserving boundary governs this design. The exact existing VM was started only for source/config resolution, the owned SSH master was closed, and VM ID `8549823276971553556` is verified `TERMINATED` in `evidence/after.stdout`.

The proposal removes independent display/GPU-rendering/media/audio/camera/sensor/touch/USB/MMC/storage/network consumers. It retains CPU0 through `nr_cpus=1 maxcpus=1`, normal IRQ/preemption, calibrated retained text, and the vendor protection dependency closure. CPUFreq/base power and battery/SOC diagnostics cannot simply be switched off while preserving their existing thermal/control paths. Consequently SPM/idle/HPS, BAT_thread, SOC, notifications, charger supervision and thermal sampling remain. This is a meaningful whole-class removal experiment, with a substantial retained vendor closure that the parent must accept before building.

| Input | Exact identity |
|---|---|
| Remote clean ancestor | `/srv/android/asus-linux49-calibrated-entry-build-20261107/{kernel,out}` |
| Ancestor compiled Image.gz-dtb | `97b7e1199d607f852bf52ff7766e8aa079fee92986cd3d473b765a45adbf45fb` |
| Ancestor full p10 / UUID | `c89bedfba2bd8550580f394bb4774018523855b622851d563a56975746f99bb5` / `23cdb057-295c-4b42-9ade-a4324162ad02` |
| Ancestor/current source-bound config | `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1` |
| Proposed resolved config | `04d93e9d2864f23d9fb5a9dcc0958be39e69f07a43d20b1a428042a098893314` |
| Owned independent preparation prefix | `/srv/android/asus-minimal-platform-preparation-20261108` |
| New source/run UUID | `a60fca94-e760-4ce5-a790-5c9a818ce406` |

The ancestor has no Git metadata. Its historical release label includes `g717bb3c9e13c-dirty`; that is not a newly verified Git HEAD. Exact provenance is the ancestor path, compiled/config pins, original source-copy/upload receipts, and selected source hashes verified again in `evidence/08_freeze_design.json`. The ancestor Image and config remain unchanged. Actual earlier physical entry/RAM-PID1 evidence is copied in `evidence/baseline-physical-RESULT.json`. Latest physical recovery is the owner-supplied battery-uevent candidate full p10 `d78e6ddd7f4a555201515df3aef6d8d7f15203c20e3b8d201ea7eb2f4c5df081`; no fresh observation was made.

Review these outputs:

- [The single combined config/DT/source/helper delta](minimal-platform.delta.patch), targeting `out/.config`, `kernel/…` and `helper/…` in an independent prefix.
- [Resolved configuration](config/resolved.config), [all derived changes](config/derived-changes.json), and [99 explained DT status paths](dt/status-manifest.json).
- [Keeper/removal matrix and exact dependency conflicts](DEPENDENCIES.md), with selected ancestor ELF calls in `evidence/baseline-linked-*.txt`.
- [RAM PID1 C source](source/ram_pid1.c) and [run contract](RUN-CONTRACT.md): actual uname/normal scheduler; 2M volatile unsigned compute/checksum; five actual SIGALRM waits with before/after IRQ/monotonic observations; normal reboot on success or clear error.
- [Pending build commands, pins and packaging boundaries](PENDING-BUILD.md).

Static checks passed: warning-free final olddefconfig using an existing host `conf` executable (no compilation), keeper config equality, existing-DTB path checks, tag length, and exact application of the combined patch in a disposable independent review copy. `evidence/design-check.json` records the checks. One initial Kconfig resolution exposed the Android default selector's forced USB/network/framebuffer options; one dependency correction resolved the same design. Its intermediate config is evidence only, not another candidate.

Continuation: parent reviews the retained closure, source/config/DT delta and helper contract before authorizing one build. The remaining risks are unbuilt link/DT/helper correctness, retained vendor-work liveness, finite retained-buffer capacity, unqualified physical protection paths and unproved normal reboot. Five nominal one-second timer returns are functional evidence, not calibrated elapsed time or a guaranteed timeout; manual Power fallback is accepted. No engineering protection qualification, physical GO, storage/OS admission or automatic next variant is asserted.
