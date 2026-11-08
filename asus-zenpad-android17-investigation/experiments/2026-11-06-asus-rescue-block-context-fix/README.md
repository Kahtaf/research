# Rescue labels by inode kind

Question: can the recovery's custom block labels be restricted to block nodes,
so ordinary by-name symlinks retain their stock labels and existing permissions?

Status: parent implementation and actual compiled lookup checks pass: 17
context lookups and 6 existing-policy checks. A new UNARMED image is packaged.
The
original rescue image, policy, source, daemon and manifests remain unchanged.
All output is offline; no target operations or arming.

The old derived contexts had nine block-node/alias overrides with no file-kind
selector. The review's actual compiled lookup labels symlinks with those custom
block types, while actual policy denies their lnk_file read/getattr. This fix
adds `-b` only to those nine rows. It adds no policy permission. Block-mode
best-match lookup must still select the exact custom node type; symlink-mode
lookup must select a stock type that the daemon can already follow.

Important outputs: source/prepare.py, artifacts/file_contexts, compilation and
lookup/policy evidence. Continuation: compile with the already pinned Android7
compiler, verify actual compiled lookups for both inode kinds and exact policy
decisions, then package a NEW unarmed candidate and review that variant. Actual
stock ueventd label assignment and physical positive descriptor checks remain
separate commissioning gates. Do not flash the old or new variant from a static
lookup result alone.

New unarmed artifact: `artifacts/candidate-kind-fix/UNTESTED-target-rescue-block-kinds.img`,
9,541,632 bytes, SHA-256
`299e65cbc1b5290b1e9ef89e0495ca5b8eac63d0d6e486d15611624ba63d35ea`;
full p10 padding SHA-256
`225151bafbb86d0b72abd72299888524b13cb8b651bec7d7b617dc0cbc913f6b`.

Only the compiled `file_contexts.bin` cpio entry changes. Its SHA-256 is
`7723428608524a84b06144e4d48836c65219fe48503f230070567063b50b3f89`.
Kernel, init, adbd, daemon, proxy, public key, manifest and policy are byte-exact
to the previous delivery. No SELinux permission is added. Actual Android7
compiler/library lookups select custom block types for block-mode node/alias
lookups and stock `block_device` for symlink-mode aliases. The existing policy
allows following those stock links. It still denies p10/disk writes and default
userdata access. Source and command evidence are in artifacts and
evidence/compiled-validation.

This fixes the label-class mismatch in the static contract. Stock ueventd's
actual assignments and positive hardware descriptor/alias checks still require
physical commissioning; the zero-record manifest cannot prove those checks by
status alone. The original complete rescue review remains unfinished after a
provider failure and must be completed before arming a writer.
