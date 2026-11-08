# Frozen sources and review boundaries

The kernel baseline is `717bb3c9e13ce573cfdd2dda856debd27a0fa17f`. The source
subset was copied from the preceding SOC spike's frozen kernel-base, then the
unchanged measured-battery 0001 and checked-SOC 0002 patches were applied locally.
No active VM source was queried or changed. `evidence/frozen-source-sha256.json`
records every frozen input; `patch-manifest.json` records prerequisites,
overlapping before/after hashes and unchanged DT/model guards. The staged patch
is strictly incremental after SOC, not an overlay onto the original baseline.

Original ASUS reference charger sources were copied from the earlier kernel
bring-up's `sources/power-probe/{bq25896.c,charging_hw_bq25896.c}`. The existing
power-port's policy/control remain the starting implementation. The 4.208 V and
512 mA conservative runtime requests are values present in the original ASUS
CV/current tables and below the reviewed 4.352 V / 1920 mA maxima. The original
board NTC/model tables are unchanged. The power-port's normal GPIO routing,
cover/OTG exclusions, NTC and safety-timer preservation remain in force.

The exact chip reference is [TI BQ25896 SLUSC76C, revision C, May 2018](https://www.ti.com/lit/ds/symlink/bq25896.pdf),
frozen as `source/reference/bq25896-rev-c.pdf`. The relevant sections are 9.2.8
(ADC), 9.2.9 and 9.3 (fault reads and watchdog/default mode), and 9.4 register
tables. REG0C needs two reads for past/current fault information, while NTC bits
report current state. Watchdog expiry restores defaults and may charge; it is
not an off failsafe. REG12 is charge-path current with 50 mA steps, not net pack
current. The one-shot conversion has a documented 1000 ms maximum; this patch
requires an observed busy/done transition with a 1200 ms polling allowance.

Checked BC1.2 follows the frozen MT8163 `pmic_chr_type_det.c` sequence. Its
register fields are independently checked against the pinned MT6323
`upmu_sw.h`/`upmu_hw.h`, which show why the old inline accessors lose errors.
The source's B2 code uses VREF=1 despite its comment saying 2; this patch follows
the code. The frozen `usb20_phy.c` documents the existing PHY MMIO init/release
contract. Their actual strong-symbol selection, clock and mux behavior still
need target build/hardware validation. The old external classifier is not used
for increased current permission.

The model host oracle/fixtures are frozen from the SOC spike and checked against
its unchanged production interpolation functions. The full original ASUS
battery_meter.c is also retained. Only the checked transaction/publication and
charger-aware sampling behavior change; no new calibration or alternate model
is introduced. The PMIC ADC and NTC bodies remain the preceding tested source.

The public stock baseline and a narrow BQ-register excerpt were copied from
parent evidence. The full private log was not copied; its local provenance and
hash are recorded. Stock reported USB charging, 87%, 29.0 C, 4132 mV battery and
4976 mV charger with Android 7 healthy/Enforcing. That proves no new-kernel
behavior and no charge gain test. The initial BQ snapshot at ~0.54 seconds shows
ID 0x06 but is not validated charging policy; later writes differ. No calibration,
private key, user data, device operation or cloud upload is part of this spike.
