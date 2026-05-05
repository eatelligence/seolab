#!/usr/bin/env bash
# SEOLab — fresh Ubuntu 22.04 LTS install script.
# Usage:   sudo ./deploy/install.sh [DOMAIN]
# Example: sudo ./deploy/install.sh seolab.acme.com
#
# Idempotent. Safe to re-run. After successful run:
#   - Docker + Compose plugin installed
#   - Firewall hardened (22, 80, 443)
#   - SEOLab containers up
#   - Optional Caddy reverse proxy with automatic HTTPS (if DOMAIN provided)

set -euo pipefail

DOMAIN="${1:-}"
APP_DIR="${APP_DIR:-/opt/seolab}"
COMPOSE_USER="${SUDO_USER:-${USER}}"

log() { printf '\033[1;32m[seolab]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[seolab]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[seolab]\033[0m %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || err "Run as root: sudo $0"

# ---------- 1. base packages ----------
log "Updating apt cache..."
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg ufw fail2ban tzdata

# ---------- 2. Docker engine + compose plugin ----------
if ! command -v docker >/dev/null 2>&1; then
  log "Installing Docker..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | tee /etc/apt/sources.list.d/docker.list >/dev/null
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
  usermod -aG docker "$COMPOSE_USER" || true
else
  log "Docker already installed: $(docker --version)"
fi

# ---------- 3. firewall ----------
log "Configuring UFW..."
ufw --force reset >/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# ---------- 4. fail2ban (basic SSH protection) ----------
log "Enabling fail2ban..."
systemctl enable --now fail2ban || true

# ---------- 5. .env ----------
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
log "Project root: $PROJECT_ROOT"

if [[ ! -f .env ]]; then
  log "Creating .env from template — fill in API keys before going to production."
  cp .env.example .env
  SECRET=$(openssl rand -hex 32)
  sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET|" .env
  PGPASS=$(openssl rand -hex 16)
  sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$PGPASS|" .env
  sed -i "s|^POSTGRES_URL=.*|POSTGRES_URL=postgresql://seolab:$PGPASS@db:5432/seolab|" .env
  warn "Generated random SECRET_KEY and POSTGRES_PASSWORD; review .env"
else
  log ".env already exists — leaving in place"
fi

# ---------- 6. install dir ----------
if [[ "$PROJECT_ROOT" != "$APP_DIR" ]]; then
  log "Copying project to $APP_DIR..."
  mkdir -p "$APP_DIR"
  rsync -a --delete --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
    "$PROJECT_ROOT"/ "$APP_DIR"/
  cd "$APP_DIR"
fi

# ---------- 7. build & start ----------
log "Building images (first build can take 5-10 minutes)..."
docker compose pull --quiet || true
docker compose build
log "Starting stack..."
docker compose up -d
sleep 4
docker compose ps

# ---------- 8. optional Caddy front for HTTPS ----------
if [[ -n "$DOMAIN" ]]; then
  log "Installing Caddy for $DOMAIN (automatic Let's Encrypt)..."
  if ! command -v caddy >/dev/null 2>&1; then
    apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https curl
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
    apt-get update -qq
    apt-get install -y -qq caddy
  fi
  cat > /etc/caddy/Caddyfile <<EOF
$DOMAIN {
    encode gzip zstd
    reverse_proxy localhost:80
}
EOF
  systemctl reload caddy
  # Caddy needs 80/443 not the bare frontend container — bind frontend to 8080
  warn "Caddy is now proxying $DOMAIN -> localhost:80 (frontend container)."
  warn "If port 80 conflicts, edit docker-compose.yml HTTP_PORT to 8080 and update Caddyfile to reverse_proxy localhost:8080"
fi

log "Done."
log "API health: curl -s http://localhost/api/health | jq"
log "App UI:    http://localhost"
[[ -n "$DOMAIN" ]] && log "Public:    https://$DOMAIN"
