#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DESTINATION="${DESTINATION:-generic/platform=iOS Simulator}"

if ! command -v xcodebuild >/dev/null 2>&1; then
  echo "xcodebuild not found. Run this on macOS with Xcode installed." >&2
  exit 1
fi

xcodebuild \
  -project SheldonDrive.xcodeproj \
  -scheme SheldonDrive \
  -configuration Debug \
  -destination "$DESTINATION" \
  CODE_SIGNING_ALLOWED=NO \
  build
