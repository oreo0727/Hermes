import Foundation

@MainActor
final class DriveChatViewModel: ObservableObject {
    @Published var endpointText: String {
        didSet { UserDefaults.standard.set(endpointText, forKey: "hermesEndpoint") }
    }
    @Published var messages: [ChatMessage] = [
        ChatMessage(role: .assistant, content: "Sheldon Drive is online. Tap the mic, ask for a project status, and keep your eyes on the road.")
    ]
    @Published var transcript = ""
    @Published var status = "Ready"
    @Published var isListening = false
    @Published var isSending = false
    @Published var lastError = ""

    private let chatClient = HermesChatClient()
    private let speech = SpeechController()
    private let voice = VoicePlayback()
    private var sessionId = ""

    init() {
        endpointText = UserDefaults.standard.string(forKey: "hermesEndpoint") ?? "http://100.71.8.121:8799"
    }

    var endpointURL: URL? {
        URL(string: endpointText.trimmingCharacters(in: .whitespacesAndNewlines))
    }

    func requestPermissions() {
        Task {
            let allowed = await speech.requestPermissions()
            if allowed {
                status = "Ready"
            } else {
                status = "Permission needed"
                lastError = "Enable microphone and speech recognition in Settings."
            }
        }
    }

    func toggleListening() {
        if isListening {
            speech.stop()
            isListening = false
            status = "Ready"
            return
        }

        lastError = ""
        transcript = ""
        status = "Listening"
        isListening = true
        speech.start(
            onPartial: { [weak self] partial in
                Task { @MainActor in
                    self?.transcript = partial
                }
            },
            onFinal: { [weak self] final in
                Task { @MainActor in
                    self?.isListening = false
                    self?.status = "Sending"
                    await self?.send(final, speakReply: true)
                }
            },
            onError: { [weak self] error in
                Task { @MainActor in
                    self?.isListening = false
                    self?.status = "Voice error"
                    self?.lastError = error.localizedDescription
                }
            }
        )
    }

    func sendTypedMessage() {
        let outgoing = transcript
        transcript = ""
        Task {
            await send(outgoing, speakReply: true)
        }
    }

    func repeatLastSheldonReply() {
        guard let reply = messages.last(where: { $0.role == .assistant }) else { return }
        voice.speak(reply.content)
    }

    func stopSpeaking() {
        voice.stop()
    }

    private func append(_ role: ChatMessage.Role, _ content: String) {
        let cleaned = content.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cleaned.isEmpty else { return }
        messages.append(ChatMessage(role: role, content: cleaned))
    }

    func send(_ text: String, speakReply: Bool) async {
        let cleaned = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cleaned.isEmpty else {
            status = "Ready"
            return
        }
        guard let endpointURL else {
            status = "Endpoint error"
            lastError = "Enter a valid Hermes URL."
            return
        }

        append(.user, cleaned)
        isSending = true
        status = "Contacting Sheldon"
        lastError = ""

        do {
            let response = try await chatClient.send(endpoint: endpointURL, sessionId: sessionId, messages: messages)
            if let newSession = response.sessionId, !newSession.isEmpty {
                sessionId = newSession
            }
            let reply = response.content?.trimmingCharacters(in: .whitespacesAndNewlines)
            let finalReply = reply?.isEmpty == false ? reply! : "I received the message, but no response text came back."
            append(.assistant, finalReply)
            if speakReply {
                voice.speak(finalReply)
            }
            status = response.fastPath == true ? "Fast route" : "Ready"
        } catch {
            let message = "I could not reach Hermes: \(error.localizedDescription)"
            append(.assistant, message)
            voice.speak(message)
            status = "Connection error"
            lastError = error.localizedDescription
        }

        isSending = false
    }
}
