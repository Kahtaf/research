#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-corsali-development}"

gcloud config set project "${PROJECT_ID}"
gcloud services enable iam.googleapis.com run.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com sqladmin.googleapis.com

for account in opensigner-poc-app opensigner-poc-shield; do
  gcloud iam service-accounts describe "${account}@${PROJECT_ID}.iam.gserviceaccount.com" >/dev/null 2>&1 ||
    gcloud iam service-accounts create "${account}"
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member "serviceAccount:${account}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role roles/cloudsql.client \
    --condition=None \
    --quiet >/dev/null
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member "serviceAccount:${account}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role roles/secretmanager.secretAccessor \
    --condition=None \
    --quiet >/dev/null
done

cat <<'EOF'
Create these Secret Manager secrets before deploy:

opensigner-app-session-secret
opensigner-google-client-secret
opensigner-mysql-host
opensigner-mysql-username
opensigner-mysql-password
opensigner-mysql-database
opensigner-shield-mysql-database
opensigner-jwt-private-key
opensigner-jwt-public-key
opensigner-hot-share-key
opensigner-shield-api-secret
opensigner-developer-encryption-part

Generate local values:
  openssl rand -base64 32
  openssl rand -hex 32
  openssl genrsa -out opensigner-jwt-private.pem 2048
  openssl rsa -in opensigner-jwt-private.pem -pubout -out opensigner-jwt-public.pem
EOF
