#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-corsali-development}"
REGION="${REGION:-us-central1}"
REPOSITORY="${REPOSITORY:-opensigner-poc}"
APP_SERVICE="${APP_SERVICE:-opensigner-poc-app}"
IFRAME_SERVICE="${IFRAME_SERVICE:-opensigner-poc-iframe}"
SHIELD_SERVICE="${SHIELD_SERVICE:-opensigner-poc-shield}"
CLOUD_SQL_INSTANCE="${CLOUD_SQL_INSTANCE:-opensigner-poc-mysql}"
CLOUD_SQL_CONNECTION_NAME="${CLOUD_SQL_CONNECTION_NAME:-${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE}}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${APP_SERVICE}:$(date +%Y%m%d%H%M%S)"
IFRAME_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IFRAME_SERVICE}:$(date +%Y%m%d%H%M%S)"
SHIELD_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SHIELD_SERVICE}:$(date +%Y%m%d%H%M%S)"

: "${GOOGLE_CLIENT_ID:?set GOOGLE_CLIENT_ID}"
: "${SHIELD_API_KEY:?set SHIELD_API_KEY}"

gcloud config set project "${PROJECT_ID}"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com sqladmin.googleapis.com

gcloud artifacts repositories describe "${REPOSITORY}" --location "${REGION}" >/dev/null 2>&1 ||
  gcloud artifacts repositories create "${REPOSITORY}" --repository-format=docker --location "${REGION}"

gcloud builds submit services/iframe --tag "${IFRAME_IMAGE}"
gcloud run deploy "${IFRAME_SERVICE}" \
  --image "${IFRAME_IMAGE}" \
  --region "${REGION}" \
  --allow-unauthenticated \
  --port 8080
IFRAME_URL="$(gcloud run services describe "${IFRAME_SERVICE}" --region "${REGION}" --format='value(status.url)')"

gcloud builds submit services/shield --tag "${SHIELD_IMAGE}"
gcloud run deploy "${SHIELD_SERVICE}" \
  --image "${SHIELD_IMAGE}" \
  --region "${REGION}" \
  --allow-unauthenticated \
  --port 8080 \
  --args server \
  --service-account "opensigner-poc-shield@${PROJECT_ID}.iam.gserviceaccount.com" \
  --set-secrets "DB_USER=opensigner-mysql-username:latest,DB_PASS=opensigner-mysql-password:latest,DB_NAME=opensigner-shield-mysql-database:latest" \
  --set-env-vars "DB_DRIVER=mysql,DB_HOST=127.0.0.1,DB_PORT=3306,CLOUD_SQL_CONNECTION_NAME=${CLOUD_SQL_CONNECTION_NAME},OPENFORT_BASE_URL=${APP_URL:-https://placeholder.invalid}"
SHIELD_URL="$(gcloud run services describe "${SHIELD_SERVICE}" --region "${REGION}" --format='value(status.url)')"

gcloud builds submit app --tag "${IMAGE}"

deploy_app() {
  local public_app_url="$1"
  gcloud run deploy "${APP_SERVICE}" \
    --image "${IMAGE}" \
    --region "${REGION}" \
    --allow-unauthenticated \
    --port 8080 \
    --service-account "opensigner-poc-app@${PROJECT_ID}.iam.gserviceaccount.com" \
    --add-cloudsql-instances "${CLOUD_SQL_CONNECTION_NAME}" \
    --set-secrets "APP_SESSION_SECRET=opensigner-app-session-secret:latest,GOOGLE_CLIENT_SECRET=opensigner-google-client-secret:latest,MYSQL_USERNAME=opensigner-mysql-username:latest,MYSQL_PASSWORD=opensigner-mysql-password:latest,MYSQL_DATABASE=opensigner-mysql-database:latest,OPENSIGNER_JWT_PRIVATE_KEY=opensigner-jwt-private-key:latest,OPENSIGNER_JWT_PUBLIC_KEY=opensigner-jwt-public-key:latest,SHARE_ENCRYPTION_KEY=opensigner-hot-share-key:latest,SHIELD_API_SECRET=opensigner-shield-api-secret:latest,OPENSIGNER_DEVELOPER_ENCRYPTION_PART=opensigner-developer-encryption-part:latest" \
    --set-env-vars "^|^APP_URL=${public_app_url}|GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}|MYSQL_SOCKET_PATH=/cloudsql/${CLOUD_SQL_CONNECTION_NAME}|SHIELD_URL=${SHIELD_URL}|SHIELD_API_KEY=${SHIELD_API_KEY}|NEXT_PUBLIC_OPENSIGNER_IFRAME_URL=${IFRAME_URL}/index.html|NEXT_PUBLIC_HOT_STORAGE_URL=${public_app_url}|NEXT_PUBLIC_SHIELD_URL=${public_app_url}/api/shield-proxy|NEXT_PUBLIC_SHIELD_API_KEY=${SHIELD_API_KEY}|NEXT_PUBLIC_CHAIN_ID=${NEXT_PUBLIC_CHAIN_ID:-1}|ALLOWED_ORIGINS=${public_app_url},${IFRAME_URL}"
}

deploy_app "${APP_URL:-https://placeholder.invalid}"
APP_URL_ACTUAL="$(gcloud run services describe "${APP_SERVICE}" --region "${REGION}" --format='value(status.url)')"

if [[ -z "${APP_URL:-}" ]]; then
  deploy_app "${APP_URL_ACTUAL}"
  gcloud run services update "${SHIELD_SERVICE}" \
    --region "${REGION}" \
    --update-env-vars "OPENFORT_BASE_URL=${APP_URL_ACTUAL}"
fi

cat <<EOF
Deployed:
  App:    ${APP_URL:-${APP_URL_ACTUAL}}
  iFrame: ${IFRAME_URL}
  Shield: ${SHIELD_URL}

Add this Google OAuth redirect URI:
  ${APP_URL:-${APP_URL_ACTUAL}}/api/auth/google/callback
EOF
