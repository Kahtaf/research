# Userdata block labels

Question: Do actual SDK37 production context inputs label physical userdata for the existing fsck policy, independently of virtual vda?

Status: Completed native metadata/policy unit. Confirmed production mapping gap; device-only candidate staged, active source unchanged. Old runtime denial's exclusive cause and runtime resolution remain unproven.

Outputs: [report](REPORT.md), [candidate patch](candidate/candidate.patch), [proposed device file](candidate/candidate-device-file_contexts), [native evidence](evidence/native-evidence.json), [final evidence](evidence/final-evidence.json), and public metadata/source snapshots under `evidence/snapshots/`.

Continuation: Parent verifies preimage and accepts the candidate into its namespace/VINTF incremental batch, then repeats lookup/checkfc on new generated inputs. The separate exact vda mapping described in the report belongs only to the next genuine fixture. Do not rerun historical attempt scripts over their retained prefix. No runtime/physical/flash GO is claimed.
