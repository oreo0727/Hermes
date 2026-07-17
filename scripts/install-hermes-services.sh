#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_SOURCE_DIR="$ROOT_DIR/deploy/systemd"
USER_UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

mkdir -p "$USER_UNIT_DIR"
install -m 0644 \
  "$UNIT_SOURCE_DIR/hermes-app-dev-gateway.service" \
  "$UNIT_SOURCE_DIR/hermes-game-dev-gateway.service" \
  "$UNIT_SOURCE_DIR/hermes-creative-dev-gateway.service" \
  "$UNIT_SOURCE_DIR/hermes-operator-gateway.service" \
  "$UNIT_SOURCE_DIR/hermes-operator-portal.service" \
  "$UNIT_SOURCE_DIR/hermes-always-on.service" \
  "$UNIT_SOURCE_DIR/hermes-operator-watchdog.service" \
  "$UNIT_SOURCE_DIR/hermes-operator-watchdog.timer" \
  "$USER_UNIT_DIR/"

systemctl --user daemon-reload
systemctl --user enable --now \
  hermes-operator-gateway.service \
  hermes-app-dev-gateway.service \
  hermes-game-dev-gateway.service \
  hermes-creative-dev-gateway.service \
  hermes-operator-portal.service \
  hermes-always-on.service
systemctl --user enable --now hermes-operator-watchdog.timer

linger_status=""
if command -v loginctl >/dev/null 2>&1; then
  linger_status="$(loginctl show-user "$USER" -p Linger --value 2>/dev/null || true)"
  if [[ "$linger_status" != "yes" ]]; then
    if loginctl enable-linger "$USER" >/dev/null 2>&1; then
      echo "Enabled systemd linger for $USER so Hermes starts after reboot without an active login."
    else
      echo "Systemd linger is not enabled yet."
      echo "Run 'sudo loginctl enable-linger $USER' if you want Hermes to survive reboots before login."
    fi
  fi
fi

echo "Hermes user services installed and started."
echo "Check status with:"
echo "  systemctl --user status hermes-operator-gateway.service"
echo "  systemctl --user status hermes-app-dev-gateway.service"
echo "  systemctl --user status hermes-game-dev-gateway.service"
echo "  systemctl --user status hermes-creative-dev-gateway.service"
echo "  systemctl --user status hermes-operator-portal.service"
echo "  systemctl --user status hermes-always-on.service"
echo "  systemctl --user status hermes-operator-watchdog.timer"
