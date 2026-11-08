# Build infrastructure retired

Status: **REMOVED AND API-VERIFIED ABSENT**, 2026-11-08T17:40:38.901064+00:00.

Deleted the one owned Android build VM and its single auto-delete 600 GB pd-balanced disk, and released its reserved regional IPv4 address. Fresh successful Compute API list queries found no remaining experiment instance, disk or reserved address. No new snapshots, disks, buckets, service accounts, firewall rules or networks were created by archival cleanup; unrelated resources were not changed.

The VM was started only for read-only compact source/provenance export, then deleted after export verification and a local Git checkpoint. No native build was run. Generated Android17 images and rebuildable caches were intentionally discarded with the disk; their historical hashes, upstream identities and source changes remain in this archive. The existing original stock BOOT/SYSTEM/RECOVERY images were rehashed on the owner's Mac and match their recorded hashes. Those and existing private calibration backups remain local and outside Git; calibration completeness is not newly qualified.

The Android17 goal is parked. No tablet partition was read/written or rebooted as part of cleanup. Future work needs fresh infrastructure; old VM paths in historical reports no longer exist.
