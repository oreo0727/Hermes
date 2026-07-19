import Foundation

struct HermesChatClient {
    struct ChatResponse: Decodable {
        let ok: Bool?
        let sessionId: String?
        let content: String?
        let fastPath: Bool?

        enum CodingKeys: String, CodingKey {
            case ok
            case sessionId = "session_id"
            case content
            case fastPath = "fast_path"
        }
    }

    struct OutgoingMessage: Encodable {
        let role: String
        let content: String
    }

    struct ChatRequest: Encodable {
        let profile: String
        let fast: Bool
        let projectId: String
        let sessionId: String
        let messages: [OutgoingMessage]

        enum CodingKeys: String, CodingKey {
            case profile
            case fast
            case projectId = "project_id"
            case sessionId = "session_id"
            case messages
        }
    }

    func send(
        endpoint: URL,
        sessionId: String,
        messages: [ChatMessage]
    ) async throws -> ChatResponse {
        let chatURL = endpoint.appending(path: "api/chat")
        var request = URLRequest(url: chatURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 45
        let recentMessages = messages.suffix(12).map {
            OutgoingMessage(role: $0.role.rawValue, content: $0.content)
        }
        request.httpBody = try JSONEncoder().encode(
            ChatRequest(
                profile: "operator",
                fast: true,
                projectId: "",
                sessionId: sessionId,
                messages: recentMessages
            )
        )

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            let body = String(data: data, encoding: .utf8) ?? "No response body"
            throw URLError(.badServerResponse, userInfo: [NSLocalizedDescriptionKey: body])
        }
        return try JSONDecoder().decode(ChatResponse.self, from: data)
    }
}
