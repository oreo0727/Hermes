# Sheldon phone voice roadmap

## Phase 1: free phone browser voice

Status: implemented in the operator portal floating Sheldon bubble.

- Uses the browser `SpeechRecognition` / `webkitSpeechRecognition` API for push-to-talk transcription.
- Sends the transcript through the existing `/api/chat` Sheldon route.
- Reads Sheldon's response back with browser `speechSynthesis`.
- Costs nothing beyond running the existing Hermes portal.
- Best fit: quick car check-ins over Tailscale from a phone browser.

Important constraint: mobile browsers may require a secure context for microphone and speech APIs. If voice is disabled on the phone, serve the portal over HTTPS instead of plain HTTP.

## Phase 2: higher-quality voice agent

Use OpenAI Realtime/WebRTC only when we want natural low-latency speech-to-speech and are comfortable with API usage.

- Phone connects to Hermes over WebRTC.
- Hermes creates a short-lived Realtime session or brokers the SDP server-side.
- Sheldon tools stay server-side so project state, memory, and execution controls do not leak to the browser.
- This is better for conversational driving mode, interruption handling, and richer voice behavior.

## Phase 3: phone-call mode

If browser access is awkward in the car, use a SIP/phone-number bridge.

- A provider such as Twilio forwards a phone call into a Realtime/SIP session.
- Hermes sideband control connects Sheldon to tools and project state.
- This is the most car-native path, but it introduces phone-number/SIP provider cost.

## Safety rules

- No destructive actions from voice without explicit confirmation.
- Read back the planned action before executing file/project mutations.
- Keep the first voice mode push-to-talk, not wake-word always-listening.
- Prefer short spoken summaries while driving.
