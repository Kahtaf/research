#!/bin/bash
# Explicit teardown: destroys the experimental VM and its source/build disk.
set -euo pipefail
project=PROJECT_REDACTED
zone=us-central1-a
name=PROJECT_REDACTED
address=PROJECT_REDACTED
region=us-central1
actual=$(gcloud compute instances describe "$name" --project="$project" --zone="$zone" --format='value(labels.experiment)')
[ "$actual" = asus-p00a-android17 ] || { echo 'Experiment label mismatch; refusing.' >&2; exit 1; }
disk_label=$(gcloud compute disks describe "$name" --project="$project" --zone="$zone" --format='value(labels.experiment)')
address_label=$(gcloud compute addresses describe "$address" --project="$project" --region="$region" --format='value(labels.experiment)')
[ "$disk_label" = asus-p00a-android17 ] && [ "$address_label" = asus-p00a-android17 ] || { echo 'Disk/address experiment label mismatch; refusing.' >&2; exit 1; }
attached=$(gcloud compute instances describe "$name" --project="$project" --zone="$zone" --format='value(disks[].source)')
[ "$attached" = "https://www.googleapis.com/compute/v1/projects/$project/zones/$zone/disks/$name" ] || { echo 'Unexpected attached disk set; refusing.' >&2; exit 1; }
gcloud compute instances delete "$name" --project="$project" --zone="$zone" --delete-disks=all
gcloud compute addresses delete "$address" --project="$project" --region="$region"
# The separately reserved builder address is removed after VM detachment.
# Confirm no experiment VM, disk or address remains:
gcloud compute instances list --project="$project" --filter='labels.experiment=asus-p00a-android17'
gcloud compute disks list --project="$project" --filter='labels.experiment=asus-p00a-android17'
gcloud compute addresses list --project="$project" --filter='labels.experiment=asus-p00a-android17'
