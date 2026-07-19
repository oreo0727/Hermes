# Sheldon Drive iOS

Native SwiftUI push-to-talk companion for Hermes/Sheldon.

Primary target device: **iPhone 13 Pro Max**.

## What It Does

- Uses native iOS speech recognition for push-to-talk.
- Sends the transcript to the existing Hermes portal chat endpoint.
- Reads Sheldon's reply aloud with native iOS speech synthesis.
- Defaults to the current Tailscale endpoint: `http://100.71.8.121:8799`.
- Keeps OpenAI/Reatime voice out of the first version so the app can run without new API spend.

## Build And Install

This repo was generated on Linux, so the app cannot be built here. To install it on your iPhone:

1. Copy or pull this repo on a Mac with Xcode installed.
2. Open `apps/sheldon-drive-ios/SheldonDrive.xcodeproj`.
3. Select the `SheldonDrive` target.
4. In **Signing & Capabilities**, select your Apple Account/team.
5. Connect your iPhone by USB or Wi-Fi.
6. Choose your iPhone as the run destination.
7. Press **Run**.

The app needs microphone and speech-recognition permission on first launch.

For a simulator compile smoke test on a Mac:

```bash
cd apps/sheldon-drive-ios
./scripts/build-for-iphone13-promax.sh
```

## Server Assumption

Your iPhone must be connected to Tailscale and able to reach:

```text
http://100.71.8.121:8799/api/chat
```

The app allows HTTP through App Transport Security for this private Tailscale use case.

## Next Upgrades

- Add an always-listening wake button mode for parked/non-driving use.
- Add a spoken confirmation gate before destructive Hermes actions.
- Add OpenAI Realtime/WebRTC if we want lower latency natural voice-to-voice.
- Add CarPlay-style larger controls if Apple entitlement/distribution requirements make sense.
