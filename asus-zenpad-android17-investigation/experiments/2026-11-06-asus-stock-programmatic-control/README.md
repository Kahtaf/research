# Stock programmatic recovery entry

Question: can the fixed repaired stock-kernel RAM diagnostic be entered once by a native RESTART2("recovery") request, with Enforcing restored and an unattended normal return?

Status: **blocked before any device action**. The saved stock boot SELinux policy denies `shell self:capability sys_boot`; the captured exact root helper stays `u:r:shell:s0`. The stock kernel checks this permission before dispatching RESTART2. UID 0 alone does not bypass it. No device, ADB, root, USB, SSH, cloud, reboot or flash operation was performed by this spike.

This spike preserves an actual fixed native syscall-boundary candidate, local build and binary-emulation evidence, and independent firmware/policy analysis. It does not approve a device launcher or modify the existing supervised writer. A production unattended controller cannot honestly be completed on the supplied direct-root entry route while preserving Enforcing and the unmodified stock policy.

Parent owns all live execution. The candidate must not be launched directly: identity, geometry, full p10 readback, BCB/cache, review and observer gates would belong to the blocked controller. First new-kernel boot remains excluded. User authorization for programmatic recovery is inherited from the parent's instruction; no further human approval is requested. Authorization does not resolve this technical blocker.

## Concrete blocker and limits

Both saved normal-boot backups match SHA256 `7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`. Their extracted, unmodified policy is `873141c3874066341dcb4e2c7be4eb3f664686635ee3f84d2c4100f557ae740f`. The locally compiled libsepol probe finds `shell self:capability sys_boot` denied, with `shell` nonpermissive. Captured `final-root-helper-check.txt` establishes UID 0 with `u:r:shell:s0`. The saved policy's default process transition for execution of a `shell_data_file` also stays `shell`; no current inode-label claim is made.

`kernel/reboot.c:288` checks `ns_capable(..., CAP_SYS_BOOT)` before validating or dispatching the reboot command. `security/selinux/hooks.c:2059` checks discretionary capabilities and then `cred_has_capability`, which evaluates the domain against itself. Thus even full UID-0 capabilities are insufficient with the saved policy Enforcing. Returning `-EPERM` is failure, never a reason to retry or leave SELinux Permissive. `setenforce` is also denied while Enforcing; restoring from Permissive can still succeed because that access is checked in the old permissive state. No policy injection, domain change, service-command fallback or enforcement bypass is provided.

This is a source/policy conclusion, not a freshly executed syscall result on the tablet. The helper's namespace-link checks are another deliberately conservative unresolved deployment gate: the original build configs have `CONFIG_NAMESPACES` unset, and an `IKCFG_ST` embedded config was not found in the exact decompressed kernel. If namespace links are absent, the candidate refuses. A later implementation must establish the exact-stock namespace arrangement rather than weakening this check based on an absent file.

## Outputs and validation

- [source/entry.c](source/entry.c) and [artifacts/build-v1/entry](artifacts/build-v1/entry): actual static AArch64 ELF, with no interpreter or dynamic segment, built using Apple clang 21 and Rust LLD 22.1.6. Takes no arguments other than argv[0]; ignores the environment. Reads fixed SELinux/namespace paths, writes only `1` to SELinux enforce when needed, and makes at most one Linux syscall 142 with `(0xfee1dead, 672274793, 0xa1b2c3d4, "recovery")`. Every returning reboot syscall is a nonzero exit. No raw block write, BCB clear, alternate mode, shell execution, poweroff or retry exists in this ELF.
- [evidence/build.json](evidence/build.json), [evidence/entry-disassembly.txt](evidence/entry-disassembly.txt): toolchain commands, source/tool/binary hashes and actual ELF disassembly. This is a syscall-boundary candidate, **not a standalone guarded deployment tool**.
- [evidence/audit.json](evidence/audit.json), [evidence/kernel-permission-path.txt](evidence/kernel-permission-path.txt): exact stock policy denial, captured root context, stock image/kernel checks, two immutable recovery backups, GPT CRC validation and pins for existing writer/root/observer inputs. Candidate `7d74df…` / full `6c6a3f…` and wrapped kernel `b0e5d4…` were independently checked; two byte-mutation fixtures are refused.
- [evidence/offline-boundary.json](evidence/offline-boundary.json): actual compiled ELF emulation, **18 cases** covering UID/eUID/argument failures, enforcement read/open/write/close/readback failures, wrong PID/user namespace, last-moment enforcement failure, one fixed syscall, `EPERM`, other error, unexpected zero return and a simulated nonreturning syscall. Host subprocess/socket/device access is prohibited by audit hooks. These are mocked Linux syscall effects, not an emulated Linux kernel.
- The same report executes actual saved LK Thumb instructions: **all 65,536 PDN1 inputs** for the predicate, actual mode-selection caching, clear/commit with busy polls, adjacent-bit preservation, second-predicate false after a successful stubbed clear, and main-path assertion/download branches. Non-PMIC callees are explicitly stubbed and listed; no C reimplementation is presented as firmware execution.
- Actual charger function at `0x41e13d68` calls `rtc_boot_check(0)` at `0x41e13d94`, before its low-battery branch. With cached recovery mode 2, the emulated 3800 mV path reaches the later main call (two RTC checks); 3000 mV reaches the poweroff-function entry after the first clear. Battery/charger hardware calls are stubs; the poweroff implementation is **not executed**. Assertion/download paths before the charger can still bypass clearing. See [evidence/independent-lk-disassembly.txt](evidence/independent-lk-disassembly.txt).
- A permanently busy PMIC stub leaves the real firmware polling until the emulator instruction budget stops it. A deliberately dropped PDN1 write lets the real function return 1 while the recovery predicate remains true. Neither the commit routine nor the diagnostic's timer proves physical PMIC success or protects a bootloader stall.

The saved GPT proves `para` is p12, start 225576, 1024 sectors; `cache` is p24, start 662824, 409600 sectors. Exact recovery fstab maps `para` to `/misc`. The BCB byte offset has **not** been independently derived, and no current BCB/cache command contents were read. No guessed offset is used. The preloader's complete control flow was not emulated.

## Parent continuation

Run these local-only checks from the ideas workspace:

```sh
python3 -B 2026-11-06-asus-stock-programmatic-control/source/audit.py
2026-11-06-asus-stock-programmatic-control/.venv/bin/python -B 2026-11-06-asus-stock-programmatic-control/tests/offline_boundary.py
```

The build script creates `artifacts/build-v1` exclusively and refuses to overwrite it. For a reviewed rebuild, choose a fresh build directory in a separate local revision of the script and compare ELF hashes. Pinned emulator dependencies are Unicorn 2.1.4 and Capstone 5.0.6, installed only inside this spike's `.venv`; installation output is retained. Original successful evidence is retained as `offline-boundary-v1.json`; no failing test fixtures occurred.

There are **no live preflight/execute/return commands** for this result. Providing them would imply the Enforcing entry route had passed a gate that it fails. [evidence/unattended-stock-contract.json](evidence/unattended-stock-contract.json) is explicitly blocked and unapproved, with no executable flag or override. The prior reviewed supervised manifest and writer CLI are unchanged. No `--supervised` assertion is made.

The next useful parent decision is whether an independently audited, fixed entry mechanism can possess `sys_boot` while Enforcing, within the authorized policy constraints. Merely changing the review JSON cannot solve this. Any alternative userspace reboot route still requires a full BCB-side-effect audit. Do not install the diagnostic merely to try the known-denied entry route.

Only after resolving that boundary should a production wrapper be implemented around the pinned writer: unchanged backup/layout/kernel/full-readback/inverse guards and shared lock; truthful unattended stock-only review; fresh p10 candidate/BCB/cache/stock-health checks; a ready USB observer before durable entry intent; single entry dispatch; independent 120-second in-image return with a bounded 420-second observation window; separate missing-report and actual-stock-return outcomes; fresh Enforcing/SDK24/real-serial/fingerprint/boot-complete checks; optional parent-owned short USB TCP re-enable; then one guarded exact-stock inverse with full readback. Unknown completion/transport never authorizes a write or entry retry. No boot loop, generic serial selection, ADB-server termination or new key is permitted.

The observer/controller state machine, root launch/trap envelope, current BCB/cache guard, TCP recovery, automatic inverse integration and their transport-fault tests were **not implemented**, because the required entry mechanism is blocked. This is the requested precise-blocker handback, not a claim that a fully functional unattended controller was delivered. Parent's system-backup milestone is data readiness only and was not contacted or used as runtime acceptance evidence here.
