#!/bin/bash
# Public bootstrap only. App/auth credentials arrive later over SSH, never metadata.
set -euo pipefail
exec > >(tee -a /var/log/mercy-bootstrap.log) 2>&1
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg python3 rsync caddy
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
ARCH=$(dpkg --print-architecture)
printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian %s stable\n' "$ARCH" "$VERSION_CODENAME" > /etc/apt/sources.list.d/docker.list
apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
if ! id mercyhouse >/dev/null 2>&1; then
  useradd --uid 1100 --user-group --create-home --home-dir /opt/mercy-house --shell /usr/sbin/nologin mercyhouse
fi
usermod -aG docker mercyhouse
install -d -o mercyhouse -g mercyhouse -m 0750 /opt/mercy-house
# The web proxy is started only after its authenticated app-specific config arrives.
systemctl disable --now caddy || true
systemctl enable --now docker
# Bounded host logs and disk housekeeping; no shared Docker pruning.
mkdir -p /etc/systemd/journald.conf.d
printf '[Journal]\nSystemMaxUse=256M\n' > /etc/systemd/journald.conf.d/mercy.conf
systemctl restart systemd-journald
install -d /var/lib/mercy-house
printf 'ready\n' > /var/lib/mercy-house/bootstrap-ready
