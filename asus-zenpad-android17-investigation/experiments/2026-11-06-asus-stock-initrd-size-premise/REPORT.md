# Finding

**The proposed retained-static-2-MiB mechanism is refuted on the exact LK's
successful recovery path. The physical failure's cause remains inconclusive.**
LK replaces the stock FDT bootargs and supplies the recognized ramdisk payload's
actual start/end. A 2 MiB input would truncate 5a61, but there is no evidence
that Linux received that bound. No kernel/DT/header patch is justified by this
premise. No image was built or modified.

This rechecks the earlier LK result against the **actual failed 5a61 bytes**,
the original initial/verify recovery, and pending 535a minimal probe. It also
establishes precedence in the **shipped 3.18 binary**, rather than borrowing
the 4.9 configuration or source behavior. See [audit.json](evidence/audit.json),
[kernel.disasm](evidence/kernel.disasm),
[lk-excerpts.disasm](evidence/lk-excerpts.disasm), and
[source-excerpts.txt](evidence/source-excerpts.txt).

# Exact static inputs and stream boundary

Both original recovery backups independently match SHA256
`902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`.
The failed compact image matches
`5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f`
(10,412,032 bytes); its zero-padded 16,740,352-byte p10 digest is
`3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`.
The minimal image matches
`535ad86471739967c0e68c058787cf2e5ac6bd844765b75d4bb576200a01d40e`.

All contain the same 7,472,341-byte wrapped kernel, SHA256
`b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`.
Its gzip is 7,409,347 bytes, expanding to 16,963,568 bytes, SHA256
`db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a`.
ARM64 header: text offset `0x80000`, image_size `0x12b5000` (19,615,744),
nominal extent `0x40080000..0x41335000`.

The following 62,482-byte FDT begins at wrapped-kernel offset 7,409,859,
SHA256 `77e2d8fbeced5a827ede6c0b8589140e9211d8dc3ca77aaa31a1dd1787a9c455`.
Header: structure offset 56/length 55,700, strings offset 55,756/length 6,726,
reservation offset 40, version 17/last-compatible 16. Its memreserve table is
empty; reserved-memory nodes are separate. Static `/chosen` has **neither**
`linux,initrd-start` nor `linux,initrd-end`, only:

```text
console=ttyS0,921600n1 root=/dev/ram initrd=0x44000200,0x200000
```

| Image | Wrapped ramdisk | Actual payload | LK-modeled exclusive end |
|---|---:|---:|---|
| Original recovery | 3,984,054 | 3,983,542 | `0x443cc8b6` |
| Failed 5a61 | 2,936,068 | 2,935,556 | `0x442ccb04` |
| Pending 535a | 282,848 | 282,336 | `0x44044ee0` |

All modeled starts are `0x44000000`, after wrapper removal. The earlier audit's
`0x442ccd04` includes the wrapper and is a conservative container bound; it is
512 bytes higher than the traced runtime payload end.

5a61 is **gzip plus aligned raw cpio**, not one compressed archive. First gzip:
2,159,874 bytes; expanded cpio: 5,167,616 bytes. Raw DEFLATE reaches EOS only
after payload byte **2,159,866**, excluding the eight-byte gzip trailer. Thus
even ignoring the trailer, 2 MiB is 62,714 bytes short. Bounded host zlib checks
show neither gzip nor raw DEFLATE EOF at 2 MiB. Two zero bytes follow gzip;
second raw cpio starts at 2,159,876 and its trailer ends at **2,935,472**;
84 final bytes are zero padding. Original recovery's stream also exceeds
2 MiB. The pending minimal stream fits. These are byte/format facts, not
execution or a diagnostic-size A/B comparison.

# Exact LK fixup chain

LK SHA256: `c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765`.
The inspector validates **2,429 retained reachable instructions** against that
binary, resolves chosen/property literals, and checks the recovery mode table.
Function names here describe instruction behavior; recovered LK debug symbols
are not claimed.

- Mode 2 selects `0x41e1e006`; header call `...e012 -> 0x41e04564`, payload
  call `...e038 -> 0x41e04980`, nonnegative-return path `...e058 -> ...de90`.
- Wrapper parser `0x41e04218` recognizes uppercase `RECOVERY` case-insensitively
  and returns wrapper+4, **2,935,556**, not Android's wrapped 2,936,068.
  Recovery source advances 512 at `0x41e04a76`; kernel staging adjustment is
  at `0x41e049f6`. The common copy `0x41e1deac` uses Android ramdisk address
  `0x44000000`, adjusted source, and recognized payload length. No 2 MiB clamp.
- Stacked arguments at `0x41e1df54` carry that destination/length into common
  handoff. `0x41e1d100..d136` sets four-byte BE initrd-start; `...d140..d176`
  adds the actual length and sets end. For 5a61: `44000000` / `442ccb04`.
  Setter failure exits the handoff toward a loop, rather than knowingly
  continuing with stale properties.
- `0x41e1d650..d664` sets `bootargs` from LK's complete accumulated buffer.
  It **replaces**, rather than appends to, the stock FDT property. The existing
  property setter's resize/length/memcpy branch is byte-checked too.
  Later optional DT hooks are NOPs. The header contains 68 bytes:
  `androidboot.selinux=enforcing bootopt=64S3,32N2,64N2 build_version=3`.
  LK's 99-character header copy retains all of it; it has no initrd token.
  LK's literal initial cmdline also has none.

The exact backward last-magic scan selects the same stock FDT for all four
inputs, at gzip-relative offset 7,409,347 (62,996-byte rounded copied tail).
This is not an alternative DT carrying a hidden 2 MiB handoff bound.

# Exact stock 3.18 precedence

All 70,337 kallsyms names, markers, and token indices validate. The 3.18
reference source is pinned but **not asserted to be the exact build tree**.
The following material facts are independently visible in the shipped binary:

- `setup_arch`: DT scan call at `0xffffffc000f16368`, before
  `parse_early_param` at `...f163e4`. The scanner invokes chosen processing.
- `early_init_dt_scan_chosen` at `...f4ad30` reads the two initrd properties
  (including LK's one-cell/four-byte values), converts physical bounds, and
  stores start at `0xffffffc0010b0098`, end at `...0090`.
  It then copies supplied bootargs. The compiled code uses replacement,
  without a FORCE/EXTEND override. No embedded IKCONFIG is claimed.
- `early_initrd` at `...f180dc` parses comma-separated start/size and writes
  those **same** locations. Its real setup tuple at `...f7c410` is named
  `initrd`, points to that function, and has early=1. Consequently an actual
  command-line initrd token processed later overrides DT properties. The
  static FDT token cannot do so after LK has replaced its containing bootargs.
- `populate_rootfs` at `...f15750..f1575c` loads those bounds, subtracts
  end-start, and calls `unpack_to_rootfs`. No fixed 2 MiB count appears there.
  Actual gunzip at `...f34d38` requests raw inflate (-15), requires stream-end
  return 1 at `...f34fc8`, and advances consumed count by eight trailer bytes
  at `...f34ff8`. This supports the stream-boundary distinction above.

# Decision and next action

No package change is recommended. 5a61's actual payload end is already
**1,258,748 bytes below** ram_console at `0x44400000`; it avoids static ATF
`0x43000000..0x43030000` and minirdump `0x44570000..0x44580000`. This checks
fixed ranges only; dynamic consys and runtime allocations remain unobserved.
Editing the stale host FDT to start `0x44000000`, end `0x442ccb04`, and removing
its initrd token would make saved metadata consistent while preserving the
decompressed Image and entire existing ramdisk/daemon/policy. **It would not
change this LK's successful handoff, so it is not a supported rescue fix.**

The exact missing branch is whether the physical attempt completed this
recovery load/64-bit/FDT-fixup path and entered Linux with these rewritten
properties and no later runtime-provider initrd token. Preloader state,
successful storage/copy/FDT operations, dynamic command-line values, and secure
monitor transfer are not executed by this semantic inspection. No final DT,
kernel command line, or retained initrd-unpack marker from that trial exists
in the supplied evidence. Do not infer those from logo/no USB or from historical
normal-boot bounds. Static mechanism refuted; actual handoff/failure unproved.

**Concrete next action:** preserve 5a61 and complete the already prepared
parent-owned physical trial of exact 535a under its existing safeguards,
requiring its fresh RAM report and normal-Android return. This exercises
stock kernel → minimal PID1 → RAM-backed USB, helping establish an independent
recovery route before full OS flash. Its success would not establish that
5a61 failed from initrd size: userspace also changes. To settle the size premise
physically, the parent needs retained final-DT bounds/bootargs or an early
unpack error from that exact handoff. No new collection or image is authorized
by this report, and this work does not alter the parent's active rootfix,
VINTF, or early-runtime tasks.

Reproduction passed with a 60-second CPU limit, bounded per-file inputs and
32 MiB decompression caps. All input hashes were rechecked after inspection.
Only small metadata, source excerpts, scripts and disassembly were emitted;
no full Image/FDT/ramdisk copy, network/VM/device access, process inspection,
candidate build, or frozen-input write occurred. Full packet remains <1 MiB.
