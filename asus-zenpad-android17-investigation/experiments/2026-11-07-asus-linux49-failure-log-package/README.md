# Unchanged Linux 4.9 with existing configfs failure logger

Question: can one bounded physical trial of the existing 4.9 kernel produce usable
PID1/USB or retained failure-log evidence with the already compiled configfs logger?

Status: **packaged; one essential package/preservation check passed and one
isolated actual installer `main()` PLAN passed (both exit 0).** No live validation,
installation, reboot, physical GO, or fullOS GO. No kernel variant, helper edit,
compile, device/network/SSH/private-input access, broad tests, review, or subagent.

## Inputs and scope

The exact kernel/header/DT source is
[`early-watchdog-handoff/artifacts/candidate.img`](../2026-11-07-asus-early-watchdog-handoff/artifacts/candidate.img),
SHA-256 `c83a4465dd209d7c2979b7b156e9d5bd8f350d81f121fa29e51579871e3a2cb4`.
Its existing timer/watchdog/UART/driver behavior is unchanged. The compiled
[`Image.gz-dtb`](artifacts/Image.gz-dtb), 7711225 bytes, remains exactly
`a49b87313d35d803e3ffaa2be2c60a3c678ccbc46efd5831651d2bd44ae4ee03`.
The copied [config](artifacts/resolved.config) remains
`708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1`.

The **entire wrapped ramdisk**, 258567 bytes, was extracted unchanged from
[`failure-log/artifacts/candidate.img`](../2026-11-07-asus-stock-usb-reporter-failure-log/artifacts/candidate.img),
SHA-256 `cd3cf35840129247e93b7df899d8948d811745c48e156935f9bcdd937dee0dd2`.
Its extracted `init` equals the pinned already compiled
[`init`](artifacts/init), 597888 bytes, SHA-256
`f410df21053fcac5f418c7d64749f19bae7921e5cc13f5c37fe5f9e99268752d`.
The source is copied unchanged as [init.c](source/init.c) for provenance; no helper
was edited or compiled. This is the **configfs error logger**, not the stock-only
legacy backend whose init begins `631a…` and requires 3.18.35.

The helper retains actual-uname product `ASUS-PID1:<actual uname.release>`,
read-only RAM FAT `P49RAM/PROBE.TXT`, serial `P499342cbf13bf044d4b655`, run
`9342cbf1-3bf0-44d4-b655-a1ca30146a99`, marker
`ASUS-RAM-FAILLOG-20261107-R1`, and nominal 60-second reboot behavior. Byte
preservation does not prove those paths execute under 4.9 or that logs survive.

The parent supplied the diagnosis that stock PID1 ran but configfs `G/UDC` bind
returned EBUSY because built-in `android_usb` owns the controller. The subsequent
stock-only legacy backend physically passed descriptor, read-only FAT, and
Android return, as recorded in the public
[physical result](../2026-11-07-asus-stock-legacy-usb-trial/evidence/physical-result.json).
The host observer needed the `diskutil` interpretation correction:
`WritableMedia=false` / `WritableVolume=false`; there was no host write. This
stock-specific success **does not prove the 4.9 path**. The last control retained-log
collector stopped at its first pre-root `getenforce` query, before a root command;
that collection is not needed for the positive stock USB result. No private logs
were read by this packaging spike.

## Deliverables

| Output | Bytes | Actual SHA-256 |
| --- | ---: | --- |
| [candidate.img](artifacts/candidate.img) | 7974912 | `cc367b543eebea476b15a9033648c9547e48c7ac02d8c42856b372623bffb265` |
| [candidate.p10.raw](artifacts/candidate.p10.raw) | 16740352 | `0b1a3c45751d688ba304743dc74e73f7030586c6fafece32eedf0da39c86455d` |

The [packaging receipt](evidence/packaging-receipt.json) records actual hashes,
changed offsets and all preservation assertions. The existing `bootformat.py`
and `fdt.py` helpers were copied unchanged; no packaging framework was introduced.

## Exact preservation and delta

The compressed Image stream (7647604 bytes,
`128ff88e113c895757ea50358056c2b9d3d0fcd3305de31aabf727fa10396c91`)
and raw Image (17277440 bytes,
`e1f5bb0a417d1819773719ffa09d01c96884ac29363900e3a5c1a7f36b55c72c`)
are byte-identical both to the source candidate and to the compiled artifact.
Every hardware DT property, DT layout/reservations/strings, config, kernel wrapper,
header load address/page, and header/chosen arguments is preserved. Arguments stay
`androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1`.

The pinned source candidate and its existing packaging contract establish
**4.9 payload start `0x44000000`**, excluding the 512-byte MTK wrapper. The donor
stock FDT/header and its `0x44000200` token were not imported. Bounds are:

| Value | Source 4.9 package | New package |
| --- | --- | --- |
| Chosen start | `0x44000000` | `0x44000000` |
| Compressed payload length, excluding wrapper | 255139 (`0x3e4a3`) | 258055 (`0x3f007`) |
| Chosen end, exclusive | `0x4403e4a3` | `0x4403f007` |
| Wrapped ramdisk length | 255651 | 258567 |

Only `/chosen/linux,initrd-end` changes in the DT: two byte offsets, 55874 and
55875 (wrapped-kernel offsets 7703990 and 7703991). Kernel length and its wrapper
remain exact. The Android header changes only ramdisk size (offsets 16–17) and
required boot ID (offsets 576–595). The exact donor ramdisk replaces the old one;
required zero alignment/p10 padding is regenerated. Candidate length grows 4096
bytes; full p10 remains 16740352 bytes. There is no other payload or kernel change.

## Installer and isolated PLAN

[install.py](source/install.py) is minimally specialized from
`2026-11-07-asus-stock-legacy-ram-usb-reporter/source/install.py` using only five
substitutions: compact hash, full hash, length, profile, and appending the supplied
current installed p10 preimage
`80270c24e310b5dd2a8e1e9e21b35a2f3d39c87dc2db25271d97b7d85da733eb`.
All original allowed preimages remain. `execute`, `Transport`, `Guard`, both legacy
adapters, and all other installer text are byte-identical. See [install.diff](source/install.diff).
The supplied current hash was not freshly observed here.

Exactly one isolated installer `main()` PLAN passed:
[output](evidence/install-plan.json), [isolation receipt](evidence/plan-isolation-receipt.json).
Only in memory, `b.local_inputs` used the pinned public original stock header
template and `a.check_sources` became a no-op to avoid private backup/root-helper
readers. The delivered installer was unchanged. Audit hooks prohibited private
and device inputs, subprocesses, and sockets. This **is not live validation**:
private backup, root dependency/source pins, identity, live preimage, USB and log
retention were not validated. No approval was fabricated or inferred from PLAN.

## Parent continuation: one bounded physical trial

Under the parent's existing physical authorization and established fresh identity,
preimage and Power-fallback checks, the parent install command is:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-failure-log-package/source/install.py --execute
```

This command has **not** been executed here; it installs only and does not reboot.
Require full installed-p10 readback
`0b1a3c45751d688ba304743dc74e73f7030586c6fafece32eedf0da39c86455d`
and verified cleanup before the parent's single recovery entry. Observe the
unchanged USB identity/read-only RAM report if available, nominal 60-second
return, Android return, and retained fixed-marker lines using the parent's
existing private-safe collection procedure. Do not read or write normal OS
partitions as part of this reporter trial. The logger's RAM-only fallback cannot
survive a reboot if its kernel sink is unavailable.

This is **one bounded next physical trial, not fullOS GO**. If it still provides
no usable evidence, stop kernel variants and report the early-boot trace blocker.
Do not expand this package into more probes or rerun packaging/PLAN; continue
from the existing artifacts and the one physical outcome.
