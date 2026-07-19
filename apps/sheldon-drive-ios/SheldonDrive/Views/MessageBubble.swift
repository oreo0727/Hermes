import SwiftUI

struct MessageBubble: View {
    let message: ChatMessage

    private var isUser: Bool {
        message.role == .user
    }

    var body: some View {
        HStack(alignment: .top) {
            if isUser { Spacer(minLength: 42) }
            VStack(alignment: isUser ? .trailing : .leading, spacing: 6) {
                Text(isUser ? "You" : "Sheldon")
                    .font(.caption.weight(.heavy))
                    .foregroundStyle(isUser ? Color.white.opacity(0.72) : Color.orange)
                Text(message.content)
                    .font(.body)
                    .foregroundStyle(Color.white.opacity(0.9))
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(14)
            .background(
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(isUser ? Color.blue.opacity(0.32) : Color.white.opacity(0.08))
                    .overlay(
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .stroke(isUser ? Color.blue.opacity(0.32) : Color.white.opacity(0.1))
                    )
            )
            if !isUser { Spacer(minLength: 42) }
        }
        .padding(.horizontal, 2)
    }
}
