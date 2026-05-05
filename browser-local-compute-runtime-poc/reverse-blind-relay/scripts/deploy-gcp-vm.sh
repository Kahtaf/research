#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELAY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PROJECT="${PROJECT:-corsali-development}"
ZONE="${ZONE:-us-central1-a}"
INSTANCE="${INSTANCE:-browser-local-reverse-relay}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-micro}"
DISK_SIZE="${DISK_SIZE:-10GB}"
NETWORK="${NETWORK:-default}"
TAG="${TAG:-browser-local-reverse-relay}"
FIREWALL_RULE="${FIREWALL_RULE:-allow-browser-local-reverse-relay}"
HTTP_PORT="${HTTP_PORT:-8080}"
CONTROL_TLS_PORT="${CONTROL_TLS_PORT:-8443}"
CONTROL_TLS_CERT_FILE="${CONTROL_TLS_CERT_FILE:-}"
CONTROL_TLS_KEY_FILE="${CONTROL_TLS_KEY_FILE:-}"
TCP_PORT="${TCP_PORT:-443}"
SESSION_HOST_SUFFIX="${SESSION_HOST_SUFFIX:-}"
REMOTE_DIR="${REMOTE_DIR:-/opt/browser-local-reverse-blind-relay}"
SERVICE_NAME="${SERVICE_NAME:-browser-local-reverse-relay}"

echo "Building relay"
npm --prefix "$RELAY_DIR" run build

TARBALL="$(mktemp -t browser-local-reverse-blind-relay.XXXXXX.tgz)"
trap 'rm -f "$TARBALL"' EXIT

COPYFILE_DISABLE=1 tar -C "$RELAY_DIR" -czf "$TARBALL" \
  package.json \
  package-lock.json \
  dist \
  README.md

if ! gcloud compute firewall-rules describe "$FIREWALL_RULE" \
  --project "$PROJECT" >/dev/null 2>&1; then
  gcloud compute firewall-rules create "$FIREWALL_RULE" \
    --project "$PROJECT" \
    --network "$NETWORK" \
    --direction INGRESS \
    --priority 1000 \
    --action ALLOW \
    --rules "tcp:${TCP_PORT},tcp:${HTTP_PORT},tcp:${CONTROL_TLS_PORT},tcp:80" \
    --source-ranges 0.0.0.0/0 \
    --target-tags "$TAG"
fi

if ! gcloud compute instances describe "$INSTANCE" \
  --project "$PROJECT" \
  --zone "$ZONE" >/dev/null 2>&1; then
  gcloud compute instances create "$INSTANCE" \
    --project "$PROJECT" \
    --zone "$ZONE" \
    --machine-type "$MACHINE_TYPE" \
    --image-family debian-12 \
    --image-project debian-cloud \
    --boot-disk-size "$DISK_SIZE" \
    --boot-disk-type pd-standard \
    --tags "$TAG" \
    --metadata=enable-oslogin=TRUE
fi

echo "Waiting for SSH"
for _ in {1..30}; do
  if gcloud compute ssh "$INSTANCE" \
    --project "$PROJECT" \
    --zone "$ZONE" \
    --command "true" >/dev/null 2>&1; then
    break
  fi
  sleep 5
done

echo "Installing Node.js on VM if needed"
gcloud compute ssh "$INSTANCE" \
  --project "$PROJECT" \
  --zone "$ZONE" \
  --command 'set -euo pipefail
if ! command -v node >/dev/null 2>&1 || ! node -v | grep -q "^v22"; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi
node -v
npm -v'

echo "Copying relay package"
gcloud compute scp "$TARBALL" "$INSTANCE:/tmp/browser-local-reverse-blind-relay.tgz" \
  --project "$PROJECT" \
  --zone "$ZONE"

echo "Installing systemd service"
gcloud compute ssh "$INSTANCE" \
  --project "$PROJECT" \
  --zone "$ZONE" \
  --command "set -euo pipefail
sudo useradd --system --home '$REMOTE_DIR' --shell /usr/sbin/nologin relay 2>/dev/null || true
sudo mkdir -p '$REMOTE_DIR'
sudo tar -xzf /tmp/browser-local-reverse-blind-relay.tgz -C '$REMOTE_DIR'
sudo chown -R relay:relay '$REMOTE_DIR'
cd '$REMOTE_DIR'
sudo -u relay npm ci --omit=dev
sudo tee /etc/systemd/system/${SERVICE_NAME}.service >/dev/null <<UNIT
[Unit]
Description=Browser Local Reverse Blind Relay
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=relay
Group=relay
WorkingDirectory=${REMOTE_DIR}
Environment=NODE_ENV=production
Environment=PORT=${HTTP_PORT}
Environment=CONTROL_TLS_PORT=${CONTROL_TLS_PORT}
Environment=CONTROL_TLS_CERT_FILE=${CONTROL_TLS_CERT_FILE}
Environment=CONTROL_TLS_KEY_FILE=${CONTROL_TLS_KEY_FILE}
Environment=TCP_PORT=${TCP_PORT}
Environment=SESSION_HOST_SUFFIX=${SESSION_HOST_SUFFIX}
ExecStart=/usr/bin/node ${REMOTE_DIR}/dist/index.js
Restart=always
RestartSec=3
AmbientCapabilities=CAP_NET_BIND_SERVICE
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now '${SERVICE_NAME}'
sudo systemctl restart '${SERVICE_NAME}'
sudo systemctl --no-pager --full status '${SERVICE_NAME}'"

EXTERNAL_IP="$(gcloud compute instances describe "$INSTANCE" \
  --project "$PROJECT" \
  --zone "$ZONE" \
  --format='value(networkInterfaces[0].accessConfigs[0].natIP)')"

echo "Relay deployed"
echo "Health: http://${EXTERNAL_IP}:${HTTP_PORT}/health"
echo "Raw TCP ingress: ${EXTERNAL_IP}:${TCP_PORT}"
if [[ -n "$CONTROL_TLS_CERT_FILE" && -n "$CONTROL_TLS_KEY_FILE" ]]; then
  echo "Control WSS: wss://<control-host>:${CONTROL_TLS_PORT}/browser/<sessionId>"
fi
