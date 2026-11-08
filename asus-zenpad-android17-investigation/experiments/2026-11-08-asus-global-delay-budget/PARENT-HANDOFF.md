# Parent review and physical outcome contract

One diagnostic preparation is complete. One native kernel make at -j8 succeeded, one actual recovery-only candidate was packaged, and one isolated main() PLAN passed. No device, ADB, private calibration, stock payload, physical install/reboot or product/other worker process operation occurred. No automatic physical GO, next variant or repeat is authorized.

Review [PINS.md](PINS.md), [kernel.diff](source/kernel.diff), [installer diff](source/install.diff), [audit decision](evidence/audit-decision.json), [linked instruction proof](evidence/linked-instruction-proof.md), [packaging receipt](evidence/packaging-receipt.json) and [isolated PLAN limits](evidence/plan-isolation-receipt.json). Complete native build log, final source manifest, actual System.map/config/DT, source preimages and final modified sources are local. The exact build prefix is `/srv/android/asus-global-delay-budget-20261108`; source/out/cache remain there, independently copied without hardlinks. Ancestors and earlier failures/cache remain preserved. This is not a clean rebuild claim.

The current installed recovery preimage was supplied by the owner as `9939e802ab349dd01fe5ab9c643f2ce0d3219846e3f54513a9b1e9982146965c`. It is the sole appended admission, not newly observed. Common installer execute/Transport/Guard blocks and inherited adapters/readers are unchanged. The installer still targets recovery p10 only, performs full readback and does not reboot.

From this workspace, parent review commands are:

```sh
cd /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-global-delay-budget
shasum -a 256 -c SHA256SUMS
python3 -B source/install.py
```

The worker's isolated PLAN substituted only in-memory source checking and the stock-input reader. It used the pinned public r3 diagnostic candidate solely as a header geometry fixture, never an original/stock payload. It forbade subprocess/socket/device/private/stock reads. It did not validate private root/backup chains, real stock geometry, fresh target identity or current installed bytes. The delivered real PLAN retains all those inherited readers; refusal is a stop, not permission to bypass them.

Only if the parent separately owns and authorizes the physical installation phase, the existing guarded entry point is:

```sh
python3 -B source/install.py --execute
```

There is one later parent-owned physical exposure at most. Parent owns recovery entry, evidence capture and independently verified normal-stock return. No BOOT/SYSTEM/DATA write follows. Preserve the original complete raw retained bytes without trimming, rewriting or accepting arbitrary transport framing. Retain the installation/readback receipt, pre/post stock boot IDs, raw SHA256, capture/completeness/retained-capacity evidence and separate normal-stock-return evidence. The known cached LASTPC epoch remains unproved; its old numeric PC was r3 __delay+0x44 CMP, not MRS. The new kernel changes offsets; use this exact map.

Fresh kernel UUID is `a4e847a5-f502-4562-8e6a-c9a358e3f22f`. Require one unique exact fresh entry tag from `source/minimal-profile.json`, tied to this full p10 `b3ff63a119f791e8d38ab75d2586aba52cf77086026cdfb7ff3fab706d1474c1`. The entry's assembly payload and C authentication constants both contain that UUID; duplicated binary constants do not authorize duplicate physical console entries. Terminal exhaustion prefix is:

```text
ASUS49-DELAY-BUDGET run=a4e847a5-f502-4562-8e6a-c9a358e3f22f
```

The helper is intentionally reused with UUID `a60fca94-e760-4ce5-a790-5c9a818ce406`. Its source, binary and complete ramdisk remain byte-identical; it was not rebuilt. The old helper UUID alone cannot prove a fresh run. The new pinned package/profile distinguishes `kernel_run_uuid` and `helper_run_uuid` and binds both through the full image. The r3 validator's one-UUID equality was reported before adapting only package metadata admission. No helper logic changed. The old r3 decoder is not an acceptance decoder for this distinct image/identity pair; no decoder variant was introduced in this preparation.

The ceiling is `1UL<<24` = 16,777,216 completed continuing iterations of a single invocation, reset on each entry. Each counted iteration already observed the original unsigned `last-start < requested` condition and completed its YIELD. At the ceiling it immediately dumps the stack and panics; it does not make a final extra counter read or return early. Saved `last` is from the Bth true condition, before that iteration's YIELD. An invocation that reaches this ceiling could have satisfied its next original condition; this remains a deliberate diagnostic fail-stop, not a proof the delay could never finish. Zero/already-completed requests return on the unchanged false condition. No claim equates iterations with counter cycles or elapsed time.

The actual conversion audit is in `evidence/audit-decision.json` with source/linked contexts. DT declares 13,000,000 for /timer; HZ=250 makes lpj_fine=52,000 in ARM64 time_init. This is a declared conversion input, not a runtime counter-rate calibration. udelay uses rounded 4295/2^32 arithmetic; __const_udelay performs the unchanged unsigned product and >>32. The largest reconstructed linked constant request is 5000 us -> 65,000 requested cycles under that declared conversion. Larger mdelay values are split into repeated udelay(1000). These cycle numbers do not bound loop iterations. Variable generic regulator/regmap/SPI requests remain, and legitimate long invocations may trip. No concrete incompatible required iteration count was found; no universal safe budget was established.

Panic reports original start/last in hexadecimal, requested cycles, exactly 16777216 iterations and caller identity. The exact source hashes bare `%p`, so the `caller=` field can be hashed or `(ptrval)`; do not call it a raw PC. Authoritative `caller_symbol=%pS` uses the separate un-hashed symbol+offset route under KALLSYMS=y and identifies a PC against the fetched map. Explicit dump_stack supplies the call chain, including callers above the generic conversion wrappers. Missing/ambiguous publication remains UNKNOWN. To resolve a retained symbol+offset offline, substitute actual values in this parent command (not a device command):

```sh
python3 -B - '__const_udelay' '0x28' <<'PYCODE'
from pathlib import Path
import sys
rows=[x.split() for x in Path('artifacts/System.map').read_text().splitlines()]
hits=[int(x[0],16) for x in rows if len(x)==3 and x[2]==sys.argv[1]]
assert len(hits)==1, 'Ambiguous or missing symbol'
print(hex(hits[0]+int(sys.argv[2],0)))
PYCODE
```

That offset is an example, not observed target evidence. Match the actual backtrace and correct return-address interpretation to the native disassembly before naming a polling subsystem. Immediate __delay caller can be __const_udelay/__udelay/__ndelay; use the higher frames rather than guessing.

CONFIG_PANIC_TIMEOUT=1 is untouched. Existing panic itself uses mdelay; counter/read, retention, printk/backtrace, notifier, nested panic and reset paths can stall. Automatic physical stock return is not guaranteed. Existing parent manual Power fallback remains part of the physical contract. No post-exhaustion helper completion is expected from a fail-stop.

A fresh matching exhaustion message, interpretable caller symbol/PC plus backtrace, coherent saved values and exact exposure binding localize one invocation reaching the budget. They do not prove a frozen/global-broken counter, identify an exclusive root cause or establish that the requested hardware delay was illegitimate. Interpret requested cycles and caller before attributing cause.

Without exhaustion, only exact fresh entry + truthful reused-helper binding + actual expected uname + SCHED_OTHER policy/priority/nice 0 + successful one-CPU gate + correct compute result + all five ordered timer before/return pairs with IRQ and monotonic growth + helper success/normal-reboot request + independently verified fresh normal-stock return establish bounded minimal liveness under this diagnostic perturbation. The unchanged helper computes 2,000,000 volatile iterations, state 0x2093acf8 and checksum 4296231513146560. All five timer pairs remain necessary. This is not shipping, hardware protection, storage or fullOS qualification.

Partial/no diagnostic, ambiguous identity, capture loss/truncation/saturation, missing caller/backtrace or unproved stock return is UNKNOWN and stops. Absence is never a negative against the delay family: the guard cannot rule out a stuck counter-read instruction, repeated short calls, starvation, failure before publication or another obstacle. No automatic physical repetition or next variant. Experiment 3 remains open until its actual liveness criteria pass; experiments 4/5 and Android17 first flash remain gated.
