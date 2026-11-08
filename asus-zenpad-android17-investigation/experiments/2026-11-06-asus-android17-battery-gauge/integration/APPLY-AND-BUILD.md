# Apply/build handoff to the graphics/build owner

All commands below are **instructions**, not commands executed by this agent.
Schedule them after the graphics owner's live-source work; do not overlap builds.
Copy only this spike's `patches/`, `scripts/apply.py`, and evidence manifests to
the builder. No credentials, hardware calibration or private userdata is needed.

From a staged copy of this spike, run the read-only preflight:

```sh
python3 scripts/apply.py /srv/android/asus-android17/kernel-bpf-fd
```

It requires exact HEAD `717bb3c9e13ce573cfdd2dda856debd27a0fa17f`, matches the base
hashes of touched files and unchanged charger guard/DT, and runs git apply --check.
It reports an already-applied exact result without rewriting anything. If
another owner has since changed the revision/files, rebase and review the patch;
do not overwrite their work.

Apply after that check, when the build owner is ready:

```sh
python3 scripts/apply.py /srv/android/asus-android17/kernel-bpf-fd --apply
```

For an existing configured output, explicitly enable the new config. Merely
changing the defconfig does not update an existing `.config`. Prefer a fresh
output directory, retaining the known BPF/configfs kernel configuration:

```sh
kernel_src=/srv/android/asus-android17/kernel-bpf-fd
battery_out=/srv/android/asus-android17/build-battery-diag
# Refuse an existing output; choose a new name for a later revision.
test ! -e "$battery_out"
mkdir "$battery_out"
cp /srv/android/asus-android17/build-bpf-fd/.config "$battery_out/.config"
"$kernel_src/scripts/config" --file "$battery_out/.config" --enable ASUS_P00A_BATTERY_DIAGNOSTIC
make -C "$kernel_src" O="$battery_out" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ olddefconfig
# Confirm this remained =y after dependency resolution.
grep '^CONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC=y$' "$battery_out/.config"
make -C "$kernel_src" O="$battery_out" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ -j8 Image.gz-dtb
```

Record the actual compiler, configuration, complete build exit status/log and
Image.gz-dtb/DTB hashes under the build owner's evidence. Check the compiled DT:
PMIC channel numbers 6/7/4/5, swchr_power_path=1, rbat_pull_down_r=30000; charging
opt-in still absent. `drivers/misc/mediatek/power/mt8163/asus_p00a/battery_diag.o`
and the changed PMIC/BQ/common objects must be rebuilt and linked, not just DT.
Do not reuse the old image's hash as evidence for this patch.

No kernel/ARM64 compilation has been performed by the battery agent. A later
successful build still does not validate measurements or charging. Do not deploy
or flash from these instructions. The Health startup incompatibility and SOC
continuation in REPORT.md apply even if this build succeeds.

Local repeatable host/source checks, executed in this spike:

```sh
python3 scripts/stage_patch.py
python3 scripts/check_host.py
python3 scripts/verify_source.py
```
