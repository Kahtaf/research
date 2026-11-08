# Stock-only rescue commissioning artifact

Question: can the reviewed stock-kernel rescue be packaged with only actual
original SYSTEM/BOOT records, enabling later positive read-only commissioning?

Status: offline assembly and independent-container verification complete.
No target actions or execution approval.
This is a two-role commissioning artifact, not an Android17 install image.
Userdata remains disabled and the narrow reviewed policy is unchanged.

Inputs are the independently reviewed block-kind recovery image, verified
cloud SYSTEM and local stock BOOT, source adapter and exact parent backup
receipts. The manifest builder must freshly read and verify its held sources.
No private factory bytes are uploaded or included. Manifest/review inputs and
all outputs stay in this spike; prior artifacts remain unchanged.

The builder completed a fresh held-FD verification of all 3,753,902,080 public
stock SYSTEM bytes on the existing VM and checked the local original BOOT.
`artifacts/rescue.SOURCE.json` records those closed source sessions; it does not
authorize a later transfer or replace its fresh preflight.

The candidate is `artifacts/stock-pair-candidate/UNTESTED-STOCK-ONLY-commissioning.img`:
9,635,840 bytes, SHA256 `154853e37436d17c44d873e177f25efd605ecda4e69e8d2148dd840b60bee6c7`.
Its full padded p10 pin is
`cb30e1dd1faf0016bca0a875a80757798993651b19e8c5213626edeece93556b`.
The 115,288-byte manifest contains 3,580 original SYSTEM chunks and 16 original
BOOT chunks. Compressed ramdisk is 2,158,760 bytes, leaving 2,035,544 bytes before
the fixed reservation. Only `rescue.manifest` changed inside the reviewed image.
The separate independent parser verified stock kernel, policy, contexts, keys,
command line and all other cpio contents. No new target protocol or permission.

`session-contract.UNAPPROVED.json` deliberately remains PARENT_REVIEW_REQUIRED.
Its `armed=true` describes the image's two records, not an execution approval.
Deployment, positive physical descriptor/readback checks and reconciliation
remain pending. This artifact enables no p26 provisioning or new OS pair.

Continue by inspecting the actual assembled image/manifest/contract and its
source provenance. Physical readback, reconciliation and any later mutation
require parent review and current device conditions. See the ordered plan in
`../2026-11-06-asus-rescue-commissioning-plan/README.md`. Never reuse an unarmed
image's recovery pin for this artifact. No full OS or userdata approval follows.
