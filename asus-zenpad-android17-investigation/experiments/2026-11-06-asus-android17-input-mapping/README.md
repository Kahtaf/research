# Android 17 touchscreen and core-key mapping

Question: will Android's device-name lookup find the stock touch properties and
power/volume keys under the new kernel's input names?

Status: source-derived mapping staged; not integrated or tested on hardware.
No device commands, kernel/source mutations or build were needed.

The actual combined kernel driver names the device `Goodix Capacitive TouchScreen`.
The real SDK37 `InputDeviceIdentifier::getCanonicalName()` replaces its spaces
with underscores. The resulting name is `Goodix_Capacitive_TouchScreen.idc`.
The OEM's old `goodix-touchscreen.idc` has the two properties copied here:
touchscreen type and orientation awareness. No coordinate scaling, firmware
update, calibration generation or unused DT coordinate interpretation is added.

The actual MediaTek keypad registers `mtk-kpd`, so the keylayout filename stays
`mtk-kpd.kl`. This minimal layout copies the OEM Linux key mappings 116 POWER,
115 VOLUME_UP and 114 VOLUME_DOWN. It adds no unobserved wake flags or camera keys.

Outputs: `staged/device/asus/p00a/input/` and `evidence/input-mapping.json`.
`source/InputDevice.cpp` is the actual SDK37 naming/lookup implementation.
Its search order tries vendor/product/version-specific files before the device
name and includes `/vendor/usr/`; the staged vendor paths use that supported
lookup. A higher-priority matching config could still override these files.

Parent integration: copy the three staged files into a future candidate and add
the following to its `device.mk`:

```make
$(call inherit-product, device/asus/p00a/input/input-mapping.mk)
```

Preserve the running AOSP build and frozen integration-r1 candidate. The next
integration owner may compose this delta in its own new candidate and record the
resulting hashes. No HAL, VINTF or SELinux changes are required for these files.

Physical acceptance: inspect actual InputReader config selection and input names,
test touch corners/multitouch in both orientations, and test power/volume press,
release, wake and long press. Verify ranges reported by the actual controller;
these two properties are not proof of coordinate accuracy or suspend recovery.
