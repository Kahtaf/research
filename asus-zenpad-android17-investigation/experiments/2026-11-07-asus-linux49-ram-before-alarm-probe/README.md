# RAM PID1 observations before alarm

Question: which existing storage and CLOCK_MONOTONIC observations finish before the previously unfinished alarm(10) boundary?

Status: **one candidate compiled and packaged; the essential exact source-order/static ELF/kernel/package preservation check and one isolated default installer PLAN passed. No physical GO, device/ADB command, installation or recovery trial. VM 8549823276971553556 is verified TERMINATED after compile/fetch.** Parent owns installation, recovery trial, interpretation and nearby Power fallback. No further candidate is prepared.

Base: `../2026-11-07-asus-linux49-ram-primitive-probe`, including its `source/init.c` and compile_once/package/finalize/plan_only scripts. Physical Linux 4.9 and RAM PID1 are already proven. The four parent public evidence files from `../2026-11-07-asus-linux49-ram-primitive-trial/evidence` are copied under `evidence/parent-*` and pinned in `parent-public-pins.json`. Actual helper b388... last emitted alarm-arm begin, without end. Android auto-returned. Saved PL reset code was 32 versus normal 2; **32 meaning UNKNOWN**. No watchdog, thermal, timer, firmware or kernel change/inference is made. Original private factory data and raw retained/kernel logs were not opened.

Fresh helper identity: `ASUS49-PREALARM run=5fa3e2cd-430d-4bbb-8b37-1adff9bb9439`. Unchanged kernel entry UUID: `23cdb057-295c-4b42-9ade-a4324162ad02`; its marker is not fresh helper evidence.

## Artifacts

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| candidate.img | 7972864 | `37b91769f1236a8e332f84b61cb451293e22c24040bd26d81316427694315ebc` |
| candidate.p10.raw | 16740352 | `14a651dc2c1862f2d8a68153134d95864db495d0382f687a617ff27513e9c1c6` |
| init | 532448 | `3be54479f2dfa8fdd08f35ba637ba3e195125f1971a788704031e5ac8261ed2d` |
| initramfs.cpio.gz | 254463 | `2643ee1f95cdd3052caa13f5417096dcbee874f4d6a77f35dc27195571ba6ccd` |
| Image.gz-dtb (unchanged) | 7713482 | `97b7e1199d607f852bf52ff7766e8aa079fee92986cd3d473b765a45adbf45fb` |
| resolved.config (unchanged) | 126443 | `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1` |

The exact parent p10 admission appended by this installer is `8e002fd9f9b7797470fd03d94da44c0f3479c6fdfefe00b8ecd1136bc53534fb`. This is a supplied pin, not a fresh device observation. Existing stock/earlier admissible preimages remain unchanged.

## Minimal helper change and expected records

`source/init.diff` is the exact source diff from the primitive probe: fresh UUID/tag and movement of existing code only. SIGALRM setup, handler, bounded reader functions, finish/reboot path, and single 100 ms sleep are unchanged. On the successful path the expected records are:

1. Existing sink creation/open/unlink, actual getpid=1; existing sigemptyset and sigaction(SIGALRM) begin/end.
2. Before alarm-arm: uname begin/end and actual sysname/release/version/machine; mount begin/end for proc and sysfs only, with actual rc/errno. A mount failure follows the unchanged finish path rather than proceeding.
3. Before alarm-arm: opendir/readdir/closedir begin/end and directory-complete for `/sys/class/mmc_host` then `/sys/class/block`. Unchanged limits: 32 non-dot entries, at most 34 readdir calls per directory, names shorter than 128 bytes.
4. Before alarm-arm: stat.node begin/end for fixed `mmcblk0`, `mmcblk0p1`, `mmcblk1`, `mmcblk1p1`. Only for present nodes, the same `dev`, `size`, `removable`, `device/type` under `/sys/class/block` get open.readonly, one read.once.max128, close begin/end and a truncation flag if full. No new attributes, CID/serial/calibration/private reads, block opens, USB/configfs or persistent mounts/writes.
5. Before alarm-arm: clock_gettime begin/end path=before-sleep with the actual first CLOCK_MONOTONIC sample or error.
6. alarm.nominal10s.timer-dependent begin/end around alarm(10). If it returns, exactly one unchanged CLOCK_MONOTONIC relative100ms sleep (100000000 ns, no retry), its error-number and libc errno, then after-sleep clock_gettime and delta if both samples succeeded. Delta now includes the intervening alarm-arm and logging, and does not calibrate physical frequency or prove a precise 100 ms elapsed duration.
7. Existing observation complete, sink.write.error and finish: block SIGALRM, cancel alarm and attempt normal reboot once; a returning reboot parks. Interpret actual rc/errno; a begin without end identifies an unfinished boundary, not its cause. Missing nodes/attributes remain observations, not failure to read private data.

**No alarm is armed during enumeration or the first clock sample. Count/byte bounds do not impose a wall-clock timeout on a syscall. Parent's nearby Power fallback remains required. Even once armed, SIGALRM depends on the same kernel timers/interrupts and is not independent protection.** Existing automatic return is prior observation only. The unchanged finish failure paths remain unchanged, including parking if SIGALRM blocking fails. Nonblocking logging remains capped at 768 records under 768 bytes each, with one write/no retry per record; missing retained output is not proof of success.

## Preservation and limited validation

`evidence/source-order-receipt.json` proves the source equals the exact prior source plus the authorized identity/reorder. `packaging-receipt.json` verifies static AArch64 ELF64 with no PT_INTERP/PT_DYNAMIC, exact parent image/full-p10 pins, unchanged compiled kernel/config, compressed kernel stream and raw Image, hardware DT tokens, DT reservations/layout, kernel MTK wrapper, command line and all load addresses. Only chosen/linux,initrd-end changes in the runtime DT, to `0x4403e1ff` from parent `0x4403e4f4`; start remains 0x44000000. Compressed initramfs is 254463 bytes excluding its 512-byte MTK wrapper, below the unchanged 258055-byte assembly exclusion. Android header edits are restricted to ramdisk size and boot ID; ramdisk wrapper edits are payload length only. Cpio retains only root-owned init mode 100755 and dev/proc/sys directories mode 040755.

Installer edits are only candidate image/full hashes, actual size if changed, profile and exact parent preimage addition. `source/install.diff` records them. execute, Transport, Guard and adapter/helper files are byte-identical to the primitive probe. Helpers were copied with shutil.copy2; `source/adb` is verified 0755. Receipts pin the delivered scripts and dependencies.

One C compiler invocation: `aarch64-linux-gnu-gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`, compiler SHA `cd90adc7801f4595267f61a5d25bd3a0c6beb2f9f1f107ab919a97a12972dc9a`, unchanged flags `-static -Os -s -ffunction-sections -fdata-sections -Wl,--gc-sections -Wall -Wextra`. Exit 0, 2 inherited ignored signal-handler write-result warnings retained in `evidence/compile-1.log`. Existing VM identity/id/project/zone/labels and host IP_REDACTED were verified before start and after start; unchanged product-kit remote.py SSH uses known-host alias compute.8549823276971553556. All new remote files are under `/srv/android/asus-linux49-ram-before-alarm-probe-20261107`. Only the small helper, source echo and compiler evidence were fetched; kernel stayed local. No kernel/source/product build, cloud resource creation or resource cap change. The first two start/stop cycles failed before compilation and remain preserved in the original lifecycle receipts. Parent resumed once, allowed the VM to finish booting, verified SSH readiness, and completed the sole compiler invocation. `evidence/parent-ssh-continuation` records readiness and the third-cycle verified final TERMINATED state. All failed connection logs are preserved; no failed C compile occurred.

One actual installer main default PLAN used the inherited isolated public-reader substitutions in memory: pinned public stock-header template and explicit public code hash subset. Subprocess/network/private/device/root-payload access was denied. Delivered guards/readers remain unchanged. `install-plan.json` and `plan-isolation-receipt.json` disclose that private stock backup and full private/root-helper dependency chain were deliberately not validated. No helper emulation, broad tests, physical replay or physical/fullOS GO.

## Parent continuation

Review hashes, source diff and receipts, then perform fresh identity/preimage checks using the existing parent procedure. Exact parent install command from `/OWNER_HOME/Documents/workspace/ideas` (provided only; not executed):

```sh
python3 -B 2026-11-07-asus-linux49-ram-before-alarm-probe/source/install.py --execute
```

Installer installs/readbacks only and does not reboot. Parent owns the separate recovery entry, bounded observation, nearby Power fallback, stock-return verification and interpretation. Match the fresh helper UUID/tag, actual uname and begin/end boundaries. No outcome for this candidate has been observed. Keep this spike and all evidence unchanged; no next implementation or physical GO is authorized by this handoff.

## Parent execution continuation

After the implementation-only validation above, parent reconnected authenticated ADB TCP (the first get-serialno had refused before any root/staging/write operation), verified the same stock boot and Enforcing, then installed once. Run `139140d6-fbfa-4d68-bbaf-bda5809a3ab7` returned `installed_full_hash_verified`, one write, cleanup verified. The separate trial is tracked in `../2026-11-07-asus-linux49-prealarm-trial`. The implementation-only no-device claims above describe preparation, not this later parent execution. VM is verified TERMINATED.
