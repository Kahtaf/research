# Final SD installer with the working stock kernel

Question: can the actual Android 17 installation and stock rollback sources be
joined to the stock-kernel SD recovery, including the mount permission that
worked on the tablet?

Status: actual final assembly and default PLAN_ONLY completed successfully; no deployment or card arming. The stock kernel, init, daemon, SD mount
and shell client have physically executed. The CHECK source preflight exceeded
its 600-second deadline; it did not certify the complete source set. Production
source verification remains required before writes. Linux 4.9 hardware startup
is still unproved, so this assembly is not a full-OS flash approval.

`scripts/assemble.py` preserves the existing five-role admission and packaging
functions, exact original stock kernel, four production executables, contexts,
normal install order and selected stock fallback. Its only common-rootfs change
is the physically exercised one-permission SD mount policy repair.

Outputs, manifest/arm inputs and execution controls remain in ignored, private
local directories. Nothing is copied to the tablet or card by assembly. Normal
installation keeps this recovery. Stock fallback requires a separate explicit
selection and ends in power-off with OEM reset required.

Continuation: inspect `evidence/assembly.json`, then resolve the actual Linux
4.9 startup boundary before arming an installation. Do not copy selectors or
triggers to the SD merely because packaging succeeds. Preserve prior images,
card reports and failed CHECK evidence.

## Actual output

- Candidate: 9,779,200 bytes; SHA256
  `e338bcf7f4af68cf3e280287f1c76abc6b1de413fac806dcb25f874741284a29`.
- Full p10: 16,740,352 bytes; SHA256
  `bbc945ff6f581adef7b60cb166c1f9103700d74ab5dc0e381d189bef6f7c267b`.
- Exact original wrapped stock kernel `b0e5…0880`, unchanged stock header
  bootargs, production executables and contexts. Only common-entry change:
  corrected policy `b922…584`.
- Actual five-role manifest `9fe4…534`; normal order SYSTEM, DATA, BOOT.
- `evidence/assembly.json`, `deployment-plan.json`, `installer.patch` and
  `source-pins.json` describe actual artifacts and preserved transport/engine.

The default command below was executed once and returned PLAN_ONLY, exit0,
`device_contacted=false`. It does not copy selectors or reboot:

```sh
python3 -B 2026-11-07-asus-stock-sd-final-assembly/source/install.py
```

Adding `--execute` stages and fully verifies this exact recovery image only.
Do that only when the parent has selected this recovery for the next actual
trial. Actual Android installation additionally needs the separately bound SD
mode and execute trigger; none has been copied to the card. Do not treat this
readiness statement as evidence that Linux4.9 boots or the full source preflight
finished. Existing stock fallback still requires the separately documented OEM
reset after provisioning DATA.
