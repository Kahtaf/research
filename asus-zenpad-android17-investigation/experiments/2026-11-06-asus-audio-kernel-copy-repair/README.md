# ASUS P00A DL1/UL1 kernel callback repair

Question: what does the actual Linux4.9 ALSA `.copy` contract require, and can the inherited MT8163 transport/accounting defects be repaired without changing audio routes or activating hardware?

Status: bounded implementation complete. Two genuine ARM64 objects compile with exit0;6,838,600 exact-production-body assertions pass under ASan/UBSan. Patch application and source/header/object provenance verify. This is **future parent input only**, not a linked kernel, integrated product or hardware qualification.

Start with [the handoff](report/HANDOFF.md), [contract audit](report/CONTRACT.md), [review](report/REVIEW.md), and [test receipts](report/TESTS.md). Apply only the [three-file patch](patches/audio-copy.patch) after checking [exact pre/post hashes](patches/pre-post.json) against a future independently owned source revision. `report/SOURCE-PINS.json` records the physical BMC156 parent pins.

Run `python3 scripts/verify_bundle.py` for local software-only artifact verification. Optional kernel-root argument checks preimages read-only; it never patches that target. `scripts/generate_tests.py` extracts the production bodies; `compile_remote.py` and `test_remote.py` document the executed owned-builder commands, not permission to overwrite another fixture. `evidence/initial-edit-script.py` is historical draft evidence, not a regeneration tool.

Continuation: keep the parent's currently composing r3 kit, original source/out and existing seals unchanged. Parent owns any later full kernel build, reviewed integration and independently authorized hardware commissioning. Speaker amp topology and microphone route/calibration remain **UNRESOLVED**; both HAL routes remain unqualified. No device, amplifier, mixer, GPIO, charging opt-in, private calibration/key-content or cloud lifecycle action was performed.
