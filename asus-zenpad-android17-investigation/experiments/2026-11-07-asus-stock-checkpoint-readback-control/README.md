# Stock checkpoint readback control

Question: does the existing stock fiq setter record 167 in the current field immediately before normal reset, or is the zero observed only after reset/snapshot/readback?

Status: **PACKAGED; one actual binary/ABI/preservation check and one isolated PLAN passed. No physical/OS flash GO.** Parent owns one future supervised RECOVERY trial. No device, network, SSH, private input, compilation, VM startup, installation, reboot or subagent was used. No further build or experiment was performed.

Important outputs: `artifacts/candidate.img`, `artifacts/candidate.p10.raw`, `evidence/packaging-receipt.json`, exact instruction/data changes and disassembly, and one isolated installer PLAN. `source/package_control.py` performs the bounded packaging and preservation check; `source/plan_only.py` runs the isolated PLAN with disclosed in-memory substitutes for private input readers.

The first physical scalar control returned to normal Android boot `4776f9ba-2fcb-41e4-a0fb-5e4ef37dbe5c`, with read-only RAM FAT USB reporting and the expected normal reset route observed. Its saved value was 0 instead of 167. The original first ARCH_RESET message disappeared as intended, while following `arch_reset: cmd = NULL` and the stack remained. That establishes the missing observation to add: the actual current field before reset. See the existing sibling trial's `evidence/{RESULT.json,saved-step.json,reset-log-summary.json,instrumentation-observation.json}`. This result does not establish 4.9 nonexecution.

The public donor is `../2026-11-07-asus-stock-legacy-ram-usb-reporter/artifacts/candidate.img`, SHA-256 `dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427`. Its uncompressed kernel is pinned to `db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a`. This candidate is made directly from that donor, not by accumulating the preceding scalar-control patch.

The stock `aee_rr_show_fiq_step` slot is 48 bytes. The replacement occupies 44 bytes (11 instructions); its final original 4-byte RET remains untouched. It saves x29/x30 on a 16-byte aligned frame, establishes x29, loads 167 into w0, calls the unchanged setter, immediately calls the unchanged **current** getter, moves the actual return w0 into printf argument w1, resolves the existing format address in x0, calls printk, restores x29/x30/SP, and returns. It uses no other callee-saved register. See `evidence/diagnostic-wrapper.disasm` and `evidence/setter-current-getter.disasm` for actual instructions and targets.

The wrapper BL targets are setter `0xffffffc0006976c8`, current getter `0xffffffc0006976f0`, and printk `0xffffffc000abe7a8`. The setter and current getter load current pointer `0xffffffc001278560`; the original saved diagnostic uses pointer `0xffffffc001278568`. The getter reads the field selected by the current header's offset at +0x2c, or returns zero if the current pointer is NULL. Its return is logged as `%u`; the wrapper does not substitute the requested constant for the observed result. Setter initialization/pointer guards, visibility and retention remain uncalibrated.

The only handler change is its diagnostic BL at `0xffffffc000800278`. The original x0 format-address ADD at 26c remains intact and is ignored by the wrapper. The existing x2/x1 stores at 270/274 precede the call, and their reloads at 27c/280 follow it. Reset argument reconstruction and BL arch_reset at 28c are unchanged, and the printk return is unused. All reset/watchdog operations, hardware/DT, addresses and bootargs remain exact. No code cave, BSS, trampoline, kernel growth, direct field write, interface/policy change, panic, module, or force-loading was introduced. The original diagnostic callback is repurposed only in this RECOVERY control; it is unused by the preserved RAM reporter. The subsequent normal Android saved reader runs the unmodified BOOT kernel.

Exact raw-kernel replacement spans below use little-endian byte order. Raw Image base is `0xffffffc000080000`. The spans cover 63 bytes, of which 60 differ. All raw bytes outside these three spans are identical.

```text
VA 0xffffffc000695368 / raw offset 0x615368 / 44 bytes
before 015f00f0fd7bbfa9fd03009121b442f9222c40b942000034224862b8013d00d021e028918005ed97fd7bc1a8
after  fd7bbfa9fd030091e0148052d5080094de080094e103002a003d00d000e0289108a51094fd7bc1a8c0035fd6

VA 0xffffffc000800278 / raw offset 0x780278 / 4 bytes
before 4cf90a94
after  3c54fa97

VA 0xffffffc000e37a38 / raw offset 0xdb7a38 / 15 bytes including NUL
before 2066697120737465703a2025752000
after  013141375f524541443d2575200a00
```

The old format is `b' fiq step: %u \x00'`; the replacement is `b'\x011A7_READ=%u \n\x00'`. Priority 1 matches the console priority physically observed in the replaced reset message and its adjacent message. The space before newline pads within the same 15-byte NUL span; adjacent data is untouched. Expected text for a matching current value is `A7_READ=167 ` followed by newline.

- Before-reset `A7_READ=167`, then saved 0: the setter recorded the expected current value; investigate loss during reset/snapshot or the saved reader path.
- Before-reset `A7_READ=0`: the setter did not record the expected value as observed through the current getter. Initialization/current-pointer guard or another no-store/current-field issue remains possible; this alone cannot identify which.
- Before-reset 167 and saved 167: this new sequence is calibrated for that trial. Added readback/logging could affect visibility or timing; it does not retrospectively prove the previous sequence preserved the scalar.
- Missing readback log: **UNKNOWN**, including whether the wrapper ran or whether text delivery/retention failed. Any other value is a nonmatching actual current observation, not successful calibration. No case proves 4.9 nonexecution.

The complete wrapped compressed ramdisk is unchanged (262357 bytes, SHA-256 `f2430b3e0ec09076e11654758e9c8a2e45f62f07208a79bc612095ae751c05e3`), including its static AArch64 init helper (597952 bytes, SHA-256 `631a0aa5e72ee4110357ddac12bc5e5436ef3b1924cf64355f6fae99dc96d272`). The appended DT is unchanged (62482 bytes, SHA-256 `a627db960f72733f52e52426b553477153bcdaa5865a3127eb29a2a5df48d53d`). Compression uses the existing level-9 pattern and exact original ten-byte gzip metadata. Only required MTK payload length, Android kernel length/ID and container padding may change. Both aligned image and full-partition padding were checked as zero. No BOOT/SYSTEM patch was made.

```text
artifacts/candidate.img       7745536 bytes
SHA-256 042c1a63a699f6a978c589341801580a5c4f46fde23832ad174f42c763940260

artifacts/candidate.p10.raw   16740352 bytes
SHA-256 d6949069eaa498fcfbc27be707d01dffd7099992c5eb71e2c7c3926639851355

decompressed patched Image   16963568 bytes (same length as donor)
SHA-256 610c7e459f8493ab668f59834c9db469e7a98b2e658a610d51ca6233c4cdcf91
```

The installer specializes the existing scalar control only in candidate/full-p10 hashes, profile and appended allowed physical p10 preimage `b403e999805fcbbc76b988100cad5c49f13f5ca33fb70e99b555d6292e2107db`. Its candidate-length check remains 7745536, because the aligned image length coincides. `execute`, `Transport`, `Guard`, legacy adapters and original admissions are byte-identical; reversing the authorized substitutions reproduces the complete parent installer. See `source/install.diff` and `evidence/packaging-receipt.json`.

Exactly one `main()` PLAN passed through `source/plan_only.py`. It substituted `b.local_inputs` with the pinned public `2026-11-07-asus-stock-kernel-version-control/artifacts/original.img` and `a.check_sources` with a no-op **in memory only**, avoiding private stock-backup and root-helper/manifest reads. The delivered installer retains those readers and guards. This isolated PLAN does not validate private input/source manifests, device identity, health or a fresh p10 preimage. See `evidence/install-plan.json` and `evidence/plan-isolation-receipt.json`.

Parent command from the ideas workspace for the unchanged admission workflow's default PLAN:

```sh
python3 2026-11-07-asus-stock-checkpoint-readback-control/source/install.py
```

Only the parent may decide whether to use the existing `--execute` installation mode after its own admission checks and supervised physical fallback. No physical/OS flash GO is given here. The installer targets RECOVERY p10 only and does not reboot. Parent owns the single future physical trial and subsequent read-only console/saved-field interpretation. Neither prior donor return nor the first scalar control proves automatic return for this modified image. Stop this implementation here; do not run another build, broad test/review, or future experiment.
