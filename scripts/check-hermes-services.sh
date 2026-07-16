#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${HERMES_OPERATOR_PORTAL_PORT:-${OPENCLAW_OPERATOR_PORTAL_PORT:-8799}}"
PORTAL_URL="http://127.0.0.1:${PORT}/"
ALL_GATEWAY_SERVICES=(
  hermes-operator-gateway.service
  hermes-app-dev-gateway.service
  hermes-game-dev-gateway.service
  hermes-creative-dev-gateway.service
)

snapshot_ok=false
unhealthy_profiles=()
if snapshot_json="$(python3 -m hermes_stack.scaffold --root-dir "$ROOT_DIR" snapshot 2>/dev/null)"; then
  snapshot_ok=true
  while IFS= read -r profile; do
    [[ -n "$profile" ]] && unhealthy_profiles+=("$profile")
  done < <(SNAPSHOT_JSON="$snapshot_json" python3 - <<'PY'
import json
import os
import sys

try:
    snapshot = json.loads(os.environ["SNAPSHOT_JSON"])
except (KeyError, json.JSONDecodeError):
    raise SystemExit(1)

profiles = {
    profile.get("key"): profile
    for profile in snapshot.get("profiles", [])
    if isinstance(profile, dict) and profile.get("key")
}

for key, profile in profiles.items():
    runtime = profile.get("runtime") or {}
    connected_platforms = set(runtime.get("connected_platforms") or [])
    healthy = bool(runtime.get("live")) and bool(profile.get("api_server_live"))
    if key == "operator" and profile.get("discord_token_present"):
        healthy = healthy and "discord" in connected_platforms
    if not healthy:
        print(key)
PY
)
fi

portal_ok=false
if curl -fsS --max-time 10 "$PORTAL_URL" >/dev/null; then
  portal_ok=true
fi

if [[ "$snapshot_ok" == true && "${#unhealthy_profiles[@]}" -eq 0 && "$portal_ok" == true ]]; then
  echo "Hermes watchdog: all gateways and portal are healthy."
  exit 0
fi

if [[ "$snapshot_ok" != true ]]; then
  echo "Hermes watchdog: snapshot unavailable, restarting all Hermes gateways and portal."
  systemctl --user restart "${ALL_GATEWAY_SERVICES[@]}" hermes-operator-portal.service
  exit 0
fi

restart_services=()
restart_portal=false
for profile in "${unhealthy_profiles[@]}"; do
  case "$profile" in
    operator)
      restart_services+=("hermes-operator-gateway.service")
      restart_portal=true
      ;;
    app-dev)
      restart_services+=("hermes-app-dev-gateway.service")
      ;;
    game-dev)
      restart_services+=("hermes-game-dev-gateway.service")
      ;;
    creative-dev)
      restart_services+=("hermes-creative-dev-gateway.service")
      ;;
  esac
done

if [[ "${#restart_services[@]}" -gt 0 ]]; then
  echo "Hermes watchdog: restarting unhealthy gateways: ${unhealthy_profiles[*]}"
  systemctl --user restart "${restart_services[@]}"
fi

if [[ "$portal_ok" != true || "$restart_portal" == true ]]; then
  if [[ "$portal_ok" != true ]]; then
    echo "Hermes watchdog: portal unhealthy, restarting portal."
  else
    echo "Hermes watchdog: restarting portal to follow operator recovery."
  fi
  systemctl --user restart hermes-operator-portal.service
fi
