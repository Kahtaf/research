# Offline build and reproduction

Read `REPORT.md` and `PROTOCOL.md` first. Nothing in this file authorizes a
connection to the tablet. The original commissioning artifact and source trees
are inputs only.

The owned Linux fixture is
`/srv/android/2026-11-06-asus-ram-original-recovery-restorer` on the existing
builder. `scripts/remote.py` used the existing SSH configuration by filename;
no private key was opened or copied by these scripts. It refuses to create an
already existing fixture. `scripts/update_remote.py` is the recorded development
revision archiver; do not rerun completed revision names. Earlier artifacts and
failed evidence remain in `revisions/r1`, `revisions/r2`, `revisions/r3` there.

`scripts/build_remote.py` is the exact sequential compiler/test recipe. It sets
one CPU affinity and RLIMIT_AS=1 GiB, suppresses core dumps, uses an owned TMPDIR
and reuses pinned existing Android libsepol/context tools read-only. It creates
policy outputs exclusively and assembly refuses existing candidate directories.
It does not start, stop, resize or otherwise manage cloud resources.

Assembly order is essential:

1. `scripts/prepare.py`: verify both public recovery copies and the exact
   original commissioning image; extract only public recovery inputs. Create
   the fixed stock manifest pin and an unarmed zero-record identity manifest.
2. Compile `source/rescue.c` with `-DP10_HANDOFF`; derive policy with
   `source/policy_build.c`; compile the actual Android7 file contexts.
3. `scripts/assemble_core.py`: deterministic first archive, four-byte alignment,
   generated immutable core pins. No helper binary is part of this container.
4. Compile `source/p10_restore.c` into static AArch64 helper, then
   `scripts/assemble_final.py`: canonical helper archive, Android/MTK image,
   zero-padded p10, unapproved contract and fixed external host binding.
5. Run bounded core/session/receipt/regression/policy/layout tests.
   `tests/reproduce.py` performs a second complete byte reproduction in a new
   owned subdirectory. It does not repeat completed large SYSTEM/data workloads.

The recorded compiler flags are `-static -O2 -Wall -Wextra -Werror
-Wno-unused-function -Wno-misleading-indentation -Wl,--build-id=none`.
Source, compiler/tool and output pins are in the delivered inventories/evidence.
Tests built with host adapters are never placed in the candidate image.

On the laptop, the independent artifact verifier is:

```
python3 -B scripts/verify_container.py
python3 -B scripts/verify_delivery.py
```

The first reads only this candidate and its original public recovery payload.
The second verifies the finished delivery inventories and non-approval state.
Neither contacts a device or VM. It does not perform runtime commissioning.

A later operational STOCK-only build is a separate parent review action. The
current recipes deliberately select the zero-record manifest and generate
`ARMED=False`; the target's two-role/exact-manifest gate refuses restoration.
Do not reuse this candidate's full pin for a changed build. Future five-role
rescue profiles require their own binding and review; there is no wildcard
profile, hash override or generic image writer.
