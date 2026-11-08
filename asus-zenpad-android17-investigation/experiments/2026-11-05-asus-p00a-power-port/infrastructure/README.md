# Android 17 build VM

Status, 6 November: VM running for the resumed Android 17 goal. The labeled disk
retains the pinned platform, successful init/ADB/header/network module builds,
hardware/EROFS/network/ID kernel candidates and passing generic ARM64 BPF tests.
The first ID API adaptation also passes virtual lifecycle/permission/failure
tests. Nothing has been flashed. See the sibling kernel-backport and virtual
validation STATUS.md files. The previous generic product configuration failure
has been cleared by the real ASUS product.

The latest resource state is recorded in resumed-20261106.json. The external IP
changed after restart; use fresh GCP discovery when connecting. Existing SSH host
identity is compute.8549823276971553556. A brief GCP account reauthentication gap
was cleared by the user; direct SSH with that verified host alias worked during
the gap. All original resource labels and the 12-hour automatic stop remain.

Project `PROJECT_REDACTED`, zone `us-central1-a`, VM and boot disk both named `PROJECT_REDACTED`. Instance: `e2-standard-16` (16 x86-64 vCPUs, 64 GiB RAM). Disk: 600 GiB `pd-balanced`, automatically deleted when the instance is deleted. Guest: Ubuntu 24.04 LTS, 16 GiB swap, build workspace `/srv/android` owned by `android`.

Every created label-capable resource (VM and disk) carries `experiment=asus-p00a-android17`, `owner=kahtaf`, `purpose=rom-build`, `created-by=codex`, `created=2026-11-05`, `expires=2026-11-12`. `expires` is an inventory label, not automatic deletion. The VM automatically stops after 12 hours of a run and does not automatically restart. Stopping retains the disk and its charges. There are no new buckets, snapshots, reserved IP addresses, firewall rules, networks or service accounts. The external address is ephemeral. The VM uses the existing default network, has no service account/scopes, and rejects project-wide SSH keys. No services are published by the build setup.

SSH key: `~/.ssh/asus_p00a_android17` on this Mac, outside the workspace. Only its public half was supplied in instance metadata. Connect:

```sh
gcloud compute ssh android@PROJECT_REDACTED --project=PROJECT_REDACTED --zone=us-central1-a --ssh-key-file="$HOME/.ssh/asus_p00a_android17"
```

`bootstrap.sh` installs build dependencies. `sync-platform.sh` initializes LineageOS 24 at manifest commit `e4b71068f6ee045ff30e4865a8d82f4047eb78ea`; its AOSP projects use Android 17. Project branches in that manifest are resolved during sync, so retain `/srv/android/logs/resolved-manifest.xml` before any build. This is platform source, not an ASUS product or flashable ROM.

Estimated public list cost is approximately US$0.54/hour for compute plus US$0.082/hour for the 600 GiB disk, external IPv4 and any egress. Discounts/taxes/billing currency may change the bill. Disk alone is approximately US$60/month while retained. Sources: [VM pricing](https://cloud.google.com/products/compute/pricing/general-purpose), [disk pricing](https://cloud.google.com/compute/disks-image-pricing). No spending commitment or paid license was created.

Stop compute while retaining work:

```sh
gcloud compute instances stop PROJECT_REDACTED --project=PROJECT_REDACTED --zone=us-central1-a
```

Teardown (destroys this VM and its source/build disk): `bash infrastructure/teardown.sh` from the spike root. The script checks the experiment label before deletion. Do not run it while work needs to be retained. `resources.json`, `disk.json` and `../evidence/gcp-provision.log` record the created resources.


6 November, 12:02 UTC build-memory update: added /swapfile-asus-extra (16 GiB,
mode 0600) on the existing experiment disk, activated for this VM run. Combined
swap is 32 GiB. No new GCP resource or machine-type change. It is not in fstab;
reactivate explicitly on a later run if needed. The Android 17 compatibility
build's Soong analysis peaked near 59 GiB RSS and completed successfully after
4m53s; the process released its RAM. Keep the active build running. Resource
teardown remains deletion of the labeled VM and retained disk.


## 6 November: address reservation and full-image build window

The idle r7 graphics checkpoint passed before renewal. Current SSH IP
IP_REDACTED was promoted to regional static address
`PROJECT_REDACTED` in `PROJECT_REDACTED/us-central1`, to keep
source-reading agents and build scripts stable across the restart. It carries
experiment=asus-p00a-android17, owner=kahtaf, purpose=rom-build, created-by=codex,
created=2026-11-06 and expires=2026-11-12. Add this address to teardown after VM
removal/detachment:

```
gcloud compute addresses delete PROJECT_REDACTED --project=PROJECT_REDACTED --region=us-central1
```

The extra16GiB swapfile is now in/etc/fstab as well, retaining32GiB total after
restart. Parent is renewing the runtime from12h to24h at this idle checkpoint
before the full-image build; see the orchestration spike's evidence for actual
post-restart state. No live build was stopped.

6 November,23:37UTC parent audit: live API checks confirmed the VM,600GB boot disk
and reserved address retain all experiment labels. The cleanup script now includes
the reserved address, validates disk/address labels plus the exact single attached
disk before deletion, and lists remaining addresses as well as VMs/disks. Script
syntax and the read-only attachment query passed. No teardown or cloud mutation
was performed. Evidence: ../../2026-11-06-asus-build-resource-audit/.
