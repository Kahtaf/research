# WMT readiness contract: stock wmt_loader / wmt_launcher (Opus 5.5 consult)

Status: offline static analysis of the exact stock binaries in `private/stock-deps/system/vendor/bin/` and stock `system/lib64/libc.so`, done with the retained Capstone 5.0.9 venv and Apple LLVM objdump. No tablet operation was performed, nothing was implemented, and nothing was fetched. **This does not establish that a cold boot works.** All addresses below are file virtual addresses in the stripped stock ELFs. The stock libc still has its local symbols.

## Conclusion

1. **The launcher's loop is a hard readiness gate with no timeout. It is the observed blocker.** In `main` (`0x2588`, which the GOT slot at `0x7e08` passes to `__libc_init`), the launcher does `property_get("service.wcn.driver.ready", buf, NULL)` (`0x2628`). On a length ≤0 it logs `"get property(%s) failed"` (`0x2664`). Otherwise it does `strcmp(buf,"yes")` (`0x2658`, then `cbnz → 0x2618`). Every miss runs `usleep(0x493e0)` = 300 ms (`0x261c`) and loops. The only exit is the value `"yes"` → `0x267c` → `open("/dev/stpwmt", O_RDWR|O_NOCTTY)` (`0x2690`). This matches the trace: 304 × 300 ms nanosleeps, and log-endpoint probes from the error-log call on each pass, with no stpwmt open.
2. **Without a property area, `property_get` can never return "yes".** Stock libc `__system_properties_init` (`0x27630`) checks `/dev/__properties__` once at process start. If it is missing, every `property_get` later returns the empty default and makes no syscall. This is what the trace shows: the `newfstatat`/`openat` at the start, then nothing. So the missing Android property service is a real blocker, but only for reads. Nothing in the launcher's gate depends on `property_set` or on the property socket.
3. **`-h` is not a help-only operation.** `getopt("m:d:b:c:p:n:?")` (`0x290c`) runs only *after* the readiness wait, after the stpwmt open and after the chip-ID query. An unknown option goes to `0x3cd8` → usage (`0x42e4`), which logs and calls `exit(1)`. On a system that reports ready, `-h` would open `/dev/stpwmt` and issue the chip-ID ioctl before exiting.
4. **The launcher has a chip-ID fallback through a kernel ioctl, so the chip-ID property is not needed.** After stpwmt opens, it calls `property_get("persist.mtk.wcn.combo.chipid")` (`0x277c`). A length of 0 goes to `0x27c0`/`0x27d4`, then `ioctl(stpwmt_fd, 0x8004a016, 0)` (`0x27e4`). A result of −1 means a 300 ms retry loop (`0x2804 → 0x276c`). If the property *exists*, its `strtoul` value is used without the ioctl, so a wrong or empty-string value would select the wrong chip path (for example `0x288c` "invalid chip id"). **Leave this property absent.**
5. **Loader contract (`main` at `0xb10`), all reached through `/dev/wmtdetect`:**
   - Opens `/dev/wmtdetect` with `O_RDWR|O_NOCTTY`, retrying every 300 ms forever (`0xb5c`–`0xbc8`).
   - `property_get(persist…chipid)` (`0xbe4`). If it is absent or unknown, it goes to the detect path `0xfc4`:
     - ioctl `0x80047706`: external power-on.
     - ioctl `0x80047702`: external detect.
     - If that fails, ioctl `0x80047703`: SoC chip ID.
   - `property_set(persist…chipid)` (`0x10b4`). On failure it **only logs** (`0x10bc`).
   - ioctl `0x40047701` with the chip ID (`0x11d4`). It then maps the chip ID and calls ioctl `0x80047705` (`0x1248`), then ioctl `0x80047704` "kernel module init" (`0x1290`).
   - Closes the fd, `chown`s `/proc/driver/wmt_dbg` and `/proc/driver/wmt_aee` to 2000:1000, then calls `property_set("service.wcn.driver.ready","yes")` (`0x13c4`). The process exit status is that `property_set` return (`0x1424`).
   - **The loader sets ready even when module init failed.** The failure branch at `0x12a4` logs and then falls through to `0x12b8` → `0x13c4`. Only a chip ID of −1 (`0x1494`) skips the set. So the loader's own ready signal is a potential false ready.
   - Without a property service, the loader's `property_set` fails. A non-zero exit status therefore does **not** mean init failed, and an exit status of 0 cannot be expected. Logs go to the absent logd and are lost.
6. **Minimal stock property area (preferred over LD_PRELOAD).** Stock libc supports a legacy single-file area. If `stat()` says the path is not a directory (`0x27718`), `__system_properties_init` calls `map_prop_area(path, legacy)` (`0x2777c`). `map_prop_area` (`0x27474`) requires:
   - `open(O_RDONLY|O_NOFOLLOW|O_CLOEXEC)`;
   - `st_uid == 0 && st_gid == 0`, mode without group/other write (`& 0x12 == 0`);
   - size ≥ 0x80;
   - a `PROT_READ`, `MAP_SHARED` mapping;
   - magic `0x504f5250` at +8 and version `0xfc6ed0ab` at +0xc (`0x275cc`–`0x275f4`). The compat version `0x45434f76` selects a different read path; don't use it.

   The libc code confirms this layout: data at +0x80; trie node `prop_bt` with namelen at +0, prop +4, left +8, right +0xc, children +0x10, name +0x14; `prop_info` with serial +0 (length = serial>>24), value +4, name +0x60, 4-byte aligned.

   A root-owned, read-only file holding one entry gives the launcher its gate without injecting any code into the stock process. `property_set` still fails harmlessly. The launcher's `persist.mtk.wcn.patch.version` set at `0x209c` only logs on failure. The other diagnostic gets at `0x31f4`–`0x38a8` (`ro.build.type`, `ro.aee.build.info`, fwlog/dump keys) take their absent-value branches. I have not traced those defaults to completion.

   An LD_PRELOAD shim is **not needed**, and it would need a bionic-compatible build toolchain.

## Readiness rule (no false ready)

Write `service.wcn.driver.ready=yes` only when **both** of these hold:

- the single loader run shows ioctl `0x80047704` returned 0. Capture this with an Alpine `strace -e trace=ioctl` around that one run, because the loader's logs are lost;
- the kernel has registered the WMT character devices: the stpwmt major is present in `/proc/devices` or its sysfs class entry exists, and the node is created from those live numbers.

Never infer ready from the loader's exit status or from its `property_set`. Create the area file *before* starting the launcher, because libc reads it only once at start. Never run the loader again on a warm kernel.

## Path and dependency contract (for the launcher gate only)

- In the chroot: `/system/bin/linker64` and the stock `system/lib64` closure (matching the hashes in `private/live/stock-deps-manifest.json`), `/vendor` → `/system/vendor`, `/dev/null`, `/dev/urandom` and `/proc`.
- `/dev/__properties__`: a regular file, root:root, mode 0444 or 0644, built offline, holding only `service.wcn.driver.ready`.
- Optional, missing and harmless: `/dev/socket/logdw`, `/dev/pmsg0`, `/sys/devices/system/cpu/online`, `libnetd_client.so`, `/dev/socket/property_service`.
- After the gate: `/dev/stpwmt`, and from options/defaults `/dev/ttyMT2`, `/system/vendor/firmware/WMT.cfg` and `/system/etc/firmware` (`0x2a30`–`0x2b68`). These are outside the gate test.

## ONE minimal next experiment (hardware-free)

Run the same sealed chroot as `bionic-with-proc`: **no WMT nodes at all** (assert that `/dev/stpwmt`, `/dev/wmtdetect` and `/dev/wmtWifi` are absent before the run), `/sys` not mounted, and the loader **not run**. Add only a legacy `/dev/__properties__` file built offline to the contract above. Run the stock launcher twice under `strace -f` with a kill-after deadline (TERM, then SIGKILL checked against the exact PID and exe), each run about 3 s and with no arguments:

- **Negative control:** the file contains `service.wcn.driver.ready=no`. Expect: the area opens and maps successfully, the 300 ms loop continues, and `/dev/stpwmt` is never opened.
- **Positive:** the file contains `=yes`. Expect: the area maps, the property loop ends, then `openat("/dev/stpwmt") = -ENOENT` repeats every 300 ms (loop `0x26c0`–`0x26f4`).

Pass condition: only the positive run reaches the stpwmt open. That proves the property-area format and the exact gate on stock binaries, without touching hardware and without a warm-kernel loader rerun. If the area fails to map in both runs, check the file's owner and mode and SELinux denials before you look at the format. This experiment does not qualify cold WMT init. That still needs the single-loader-run strace evidence in the recovery capsule.
