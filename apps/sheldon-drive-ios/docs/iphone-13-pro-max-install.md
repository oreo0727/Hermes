# iPhone 13 Pro Max install notes

Target device: iPhone 13 Pro Max.

## Xcode Settings

- Project: `SheldonDrive.xcodeproj`
- Scheme: `SheldonDrive`
- Bundle ID: `com.oreo0727.hermes.sheldondrive`
- Deployment target: iOS 16.0+
- Device family: iPhone
- Default Hermes endpoint: `http://100.71.8.121:8799`

## Install On The Phone

1. Open the project on a Mac with Xcode.
2. Connect the iPhone 13 Pro Max over USB or trusted Wi-Fi.
3. Select the physical iPhone as the destination.
4. Select your Apple Account/team in Signing & Capabilities.
5. Press Run.
6. On first launch, approve microphone and speech recognition prompts.

If the phone refuses the developer app, open:

```text
Settings -> General -> VPN & Device Management
```

Then trust your developer profile.

## Simulator Smoke Test

From a Mac:

```bash
cd apps/sheldon-drive-ios
./scripts/build-for-iphone13-promax.sh
```

The simulator build proves the project compiles, but speech and Tailscale behavior should be tested on the real iPhone.
