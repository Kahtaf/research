# Explicit next parent delta: touch and power/volume mappings

The parent supplied this delta after the integration/build kit was sealed as `9b9eea2ae274a873d99459ea4faa352dba1dd6a9ba8b5986fae0304047ee941b`. Following the parent's conditional instruction, the sealed kit, its selected candidate, exact manifests and historical receipts remain unchanged. This mapping is **not included** in the commands/product described by `HANDOFF.md`.

Source handoff: `../2026-11-06-asus-android17-input-mapping/README.md` and `evidence/input-mapping.json`. All three actual staged file hashes were independently rechecked; `evidence/deferred-input-delta.json` records them and the exact handoff-receipt hash.

The next parent-owned candidate should copy exactly:

```text
input/Goodix_Capacitive_TouchScreen.idc
ff9c53351559ea415c5bbb2aafd3472bbedd6f264646903d20189e41da2d8a55

input/mtk-kpd.kl
a940764c7807d582cb04cadeb3140566d6472353cf27a31a52a2e7aefcb0a942

input/input-mapping.mk
6ec0030412932f6dcef9795aa9d708425661ff2368282b6b4536e03f743c1a75
```

Add exactly this inheritance to that new candidate's `device.mk`:

```make
$(call inherit-product, device/asus/p00a/input/input-mapping.mk)
```

The contents retain only the two stock touch properties (`touch.deviceType=touchScreen`, `touch.orientationAware=1`) and key codes 116 POWER, 115 VOLUME_UP, 114 VOLUME_DOWN. The supplied source evidence establishes actual Goodix/mtk-kpd names and SDK37 canonicalization/vendor lookup. It does not execute InputReader or prove UI, touch geometry, wake, long press, suspend recovery or physical keys. No kernel, HAL, VINTF or policy change is part of this delta.

Compose a new candidate and a new reviewed kit binding it; do not modify frozen staging-r1, this sealed runtime/input set, old receipts or the running AOSP tree. Recompute the new candidate manifest and exact `device.mk` postimage, pin this delta receipt, and explicitly extend the integration selection check to the three new files and one inheritance line. The current exact-manifest gate intentionally rejects such additions until a new reviewed candidate/kit is bound. Preserve the existing kernel/config/packager and scoped-parity pins. Re-run bounded selection tests and a read-only live preflight; retain the original terminal/process/lock/one-shot rules.
