# Stock kernel recompression and UTS version control

Question: can the physical recovery path execute a repackaged stock kernel, and then the same kernel with one UTS data byte changed, while the working SD-report ramdisk is held constant?

Status: **packaged and verified locally; no physical trial**. Both actual installers passed default PLAN_ONLY once, with device_contacted=false. No network, SSH, VM, kernel compilation, device/USB/root-helper contact, new test framework, or original/frozen file modification. All new files belong to this spike. The parent reports the ECC working image physically produced uname 3.18.35 / #1 and PID1; that physical observation was not repeated here. Packaging cannot establish a boot failure cause or an authentication mechanism.

A is `artifacts/original.img`: recompressed, unmodified stock raw Image. B is `artifacts/version2.img`: the same compression procedure after the single ASCII `1` → `2` change in `init_uts_ns.name.version`. Both use gzip.compress(compresslevel=9, mtime=0), append the exact original 62,482-byte FDT, and retain the ECC ramdisk byte-for-byte. Both images are 7,804,928 bytes; each zero-padded full p10 is 16,740,352 bytes. Deliveries total about 49.1 MB decimal, below 64 MiB, including compact receipts. No decompressed kernel file is retained.

| Control | Image SHA-256 | Full p10 SHA-256 |
| --- | --- | --- |
| A original | `f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140` | `d1f749b66197ee929fa9aa67abdb11da215e01c1e2880a5634c0ed28f94c91ea` |
| B version2 | `22937d2271cce9fcc8096c1bfa560392f121e16fc3e1ac5b1280ca55823838ef` | `731a20f3dea679c908e003778b14ebe1e7ebee780fa467abdd257859a9555383` |

The raw Image is 16,963,568 bytes. Before: `db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a`. After: `e4a022616e9c820b455f126aa6394f79e9a05b106926cc6d85302095ff679b88`. The only changed byte is raw offset **0xf22900 (15,870,208)**, virtual address **0xffffffc000fa2900**, `0x31` → `0x32`. Equal prefix and suffix comparisons prove that all kernel code and all other raw data remain identical. A decompresses exactly to the original; B decompresses exactly to that one-byte variant.

The field was located through the validated 70,337-symbol stock kallsyms decoder retained from `2026-11-07-asus-linux49-retained-boot-trace/scripts/inspect_stock.py`, not by selecting a matching version string. The named `__ksymtab_init_uts_ns` at 0xffffffc000edb680 contains the namespace pointer 0xffffffc000fa2838 and the matching `__kstrtab_init_uts_ns` pointer. The initial-task export resolves its nsproxy at task+0x9a0, whose +8 pointer resolves to that same namespace. Exact `sys_newuname` instructions read that path, add 4 for `name`, then copy 390 bytes to userspace. The six consecutive 65-byte fields match Linux, (none), 3.18.35, the exact supplied version, arm64, (none). Thus B's initial namespace supplies **#2 SMP PREEMPT Thu Aug 9 12:33:25 CST 2018** to uname if executed. This remains a runtime expectation until the parent collects a fresh report. The separate Linux banner at raw offset 0xa51100 still contains #1 and is byte-identical.

Input pins: working ECC image `eccfc87f28169bee14d0675f6ad31335f832ab25db46b013b03a06109b0df13d`; wrapped stock kernel `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`; wrapped SD ramdisk `51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46`; FDT `77e2d8fbeced5a827ede6c0b8589140e9211d8dc3ca77aaa31a1dd1787a9c455`. All were checked against the actual working-image bytes. Public source references are corroboration of layout, not a claim of exact build-source identity.

Preserved: page size 2048, Android addresses and bootargs, ramdisk and its MTK wrapper, kernel MTK wrapper except payload-size word, exact appended FDT, and SD helper/60-second report behavior/PROBE.ID `dbbb6afb-dd70-4c35-961e-9c977d7164a8` plus LF. Updated: actual wrapped kernel length, Android component lengths/image ID and zero alignment padding. No new initrd token is introduced; the pre-existing stock FDT token remains byte-identical. Actual new gzip decoding and the previous audit's LK backward-FDT-selection model both pass, selecting the original FDT at gzip-relative offset 7,414,580 in each candidate. This model check does not observe a physical handoff.

Important outputs:

- `scripts/build.py`: complete local packager; run with the existing audit interpreter shown below. It reads sibling public/local inputs and writes only this spike.
- `source/kallsyms.py`: retained stock decoder; `source/bootformat.py`: exact inherited format helper.
- `evidence/uts-proof.json`, `evidence/uts-path.disasm`, `evidence/source-excerpts.txt`: export, initial-namespace pointer path, source-layout corroboration and exact one-byte change.
- `evidence/packaging-receipt.json`: input pins, component/output hashes, sizes, actual parse/roundtrip/layout assertions and installer preservation.
- `evidence/install-original-plan.json`, `evidence/install-version2-plan.json`: actual once-per-candidate default PLAN_ONLY results.
- `SHA256SUMS`: exact hashes of all other delivered files, including source, receipts and both image/full-p10 pairs.

`source/install_original.py` and `source/install_version2.py` preserve the working installer's execute() and Transport source byte-for-byte; adb and legacy_adb.py are byte-identical copies. Only candidate path, image/full hashes, length, profile string and addition of the parent-supplied verified current p10 preimage `2bfdfb2c68c1abe97700b8c9dfb7386f32953a3de5900f08c373c51e011e30b9` changed. All inherited preimages, including original stock 902b..., remain. The current preimage was supplied as verified by the parent; no local device observation is claimed. Neither new control hash is admitted automatically. Shared mutation locking, complete p10 readback, one bounded inverse, unknown-stop behavior and no reboot are inherited unchanged. The exact adb shim still points to the inherited wifi-microsd legacy adapter; sibling transport/source dependencies must remain in place.

Continuation: parent alone verifies fresh PROBE.TXT absence, installs and boots A first, then collects and preserves its fresh SD report before considering B. A is the recompression/container baseline. If A works, prepare a fresh report absence again and boot B. If p10 still contains A, the B installer intentionally refuses it: parent may append A's exact full hash only after actual complete A readback, or use an already verified inherited preimage through the parent's existing workflow. Do not treat an automatically restored stock return, report absence, or packaging success as proof of kernel execution or of a failure cause. A fresh #2 uname.version report is the execution evidence sought for B. No hardware GO is issued here.

The following are the exact parent installation commands, provided for later parent-controlled trials; **neither was run by this task**. They do not reboot:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-kernel-version-control/source/install_original.py --execute
```

Only after A's report is preserved and the B install preimage is verified/admitted as described:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-kernel-version-control/source/install_version2.py --execute
```

Local reproduction (packaging only):

```sh
/OWNER_HOME/Documents/workspace/ideas/2026-11-05-asus-boot-access-audit/.venv/bin/python -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-kernel-version-control/scripts/build.py
```

Omit --execute for PLAN_ONLY. Reproduction overwrites local packages/receipts; regenerate SHA256SUMS if source or receipts change. Parent-owned physical reports should be preserved separately, never substituted into the host packaging claim.

## Parent physical results — 2026-11-07

Both controls passed. A fresh report contained3.18.35/#1 and was archived as RECOMP.TXT. B fresh report contained3.18.35/#2 and remains card PROBE.TXT, with exact host evidence/PROBE-version2.txt and physical-version2.json. Both full-p10 installations/readbacks/cleanup succeeded, each followed by one recovery request and a verified new normal Android boot. B current normal bootc328c9b4-fdaf-4b36-b3e0-5b36c13b3885. This proves modified stock-kernel data executes; Linux4.9 startup/hardware remain unproved. Host collector shell-level card rename initially failed permission; A archive used the existing root helper, B was deliberately retained. No SYSTEM/BOOT/DATA writes.
