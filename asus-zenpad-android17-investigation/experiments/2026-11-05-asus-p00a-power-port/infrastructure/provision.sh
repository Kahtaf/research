#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
project=PROJECT_REDACTED
zone=us-central1-a
name=PROJECT_REDACTED
labels=experiment=asus-p00a-android17,owner=kahtaf,purpose=rom-build,created-by=codex,created=2026-11-05,expires=2026-11-12
if ! gcloud compute disks describe "$name" --project="$project" --zone="$zone" >/dev/null 2>&1; then
  gcloud compute disks create "$name" --project="$project" --zone="$zone" \
    --size=600GB --type=pd-balanced --image-family=ubuntu-2404-lts-amd64 \
    --image-project=ubuntu-os-cloud --labels="$labels" --quiet
fi
if ! gcloud compute instances describe "$name" --project="$project" --zone="$zone" >/dev/null 2>&1; then
  gcloud compute instances create "$name" --project="$project" --zone="$zone" \
    --machine-type=e2-standard-16 --network=default --no-service-account --no-scopes \
    --disk="name=$name,boot=yes,auto-delete=yes" --labels="$labels" \
    --description='Experimental ASUS P00A Android 17 build. Teardown by experiment=asus-p00a-android17; local infrastructure/README.md.' \
    --metadata=block-project-ssh-keys=true,enable-oslogin=false \
    --metadata-from-file=ssh-keys=ssh-keys.pub,startup-script=bootstrap.sh \
    --max-run-duration=12h --instance-termination-action=STOP --no-restart-on-failure \
    --shielded-secure-boot --quiet
fi
gcloud compute instances describe "$name" --project="$project" --zone="$zone" \
  --format='json(name,id,status,machineType,labels,disks,networkInterfaces,scheduling)' >resources.json
gcloud compute disks describe "$name" --project="$project" --zone="$zone" \
  --format='json(name,id,sizeGb,type,labels,users)' >disk.json
