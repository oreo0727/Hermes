import SwiftUI

struct DriveChatView: View {
    @StateObject private var viewModel = DriveChatViewModel()
    @FocusState private var textFieldFocused: Bool

    var body: some View {
        ZStack {
            background
            VStack(spacing: 0) {
                header
                messages
                controls
            }
        }
        .preferredColorScheme(.dark)
        .onAppear {
            viewModel.requestPermissions()
        }
    }

    private var background: some View {
        LinearGradient(
            colors: [
                Color(red: 0.04, green: 0.05, blue: 0.13),
                Color(red: 0.10, green: 0.12, blue: 0.27),
                Color(red: 0.05, green: 0.07, blue: 0.16)
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
        .overlay(alignment: .topTrailing) {
            Circle()
                .fill(Color.orange.opacity(0.18))
                .frame(width: 240, height: 240)
                .blur(radius: 24)
                .offset(x: 92, y: -80)
        }
        .overlay(alignment: .bottomLeading) {
            Circle()
                .fill(Color.blue.opacity(0.20))
                .frame(width: 220, height: 220)
                .blur(radius: 26)
                .offset(x: -90, y: 120)
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 14) {
                ZStack {
                    Circle()
                        .fill(LinearGradient(colors: [.orange.opacity(0.8), .blue.opacity(0.55)], startPoint: .topLeading, endPoint: .bottomTrailing))
                    Text("S")
                        .font(.system(size: 30, weight: .black, design: .rounded))
                        .foregroundStyle(.white)
                }
                .frame(width: 58, height: 58)
                VStack(alignment: .leading, spacing: 3) {
                    Text("HERMES DRIVE")
                        .font(.caption.weight(.heavy))
                        .foregroundStyle(Color.white.opacity(0.48))
                        .tracking(1.8)
                    Text("Talk to Sheldon")
                        .font(.system(size: 30, weight: .black, design: .rounded))
                        .foregroundStyle(.white)
                }
                Spacer()
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("Tailscale endpoint")
                    .font(.caption.weight(.bold))
                    .foregroundStyle(Color.white.opacity(0.56))
                TextField("Hermes URL", text: $viewModel.endpointText)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
                    .autocorrectionDisabled()
                    .focused($textFieldFocused)
                    .padding(12)
                    .foregroundStyle(.white)
                    .background(Color.black.opacity(0.22), in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 16, style: .continuous)
                            .stroke(Color.white.opacity(0.10))
                    )
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 18)
        .padding(.bottom, 12)
    }

    private var messages: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 12) {
                    ForEach(viewModel.messages) { message in
                        MessageBubble(message: message)
                            .id(message.id)
                    }
                }
                .padding(.horizontal, 18)
                .padding(.vertical, 10)
            }
            .onChange(of: viewModel.messages.count) { _ in
                guard let last = viewModel.messages.last else { return }
                withAnimation(.spring(response: 0.36, dampingFraction: 0.86)) {
                    proxy.scrollTo(last.id, anchor: .bottom)
                }
            }
        }
    }

    private var controls: some View {
        VStack(spacing: 14) {
            if !viewModel.lastError.isEmpty {
                Text(viewModel.lastError)
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(Color.red.opacity(0.95))
                    .frame(maxWidth: .infinity, alignment: .leading)
            }

            TextEditor(text: $viewModel.transcript)
                .frame(minHeight: 62, maxHeight: 120)
                .scrollContentBackground(.hidden)
                .padding(10)
                .foregroundStyle(.white)
                .background(Color.black.opacity(0.24), in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(Color.white.opacity(0.10))
                )
                .focused($textFieldFocused)

            HStack(spacing: 12) {
                Button {
                    viewModel.toggleListening()
                } label: {
                    Label(viewModel.isListening ? "Listening" : "Hold Court", systemImage: viewModel.isListening ? "waveform.circle.fill" : "mic.circle.fill")
                        .font(.system(size: 18, weight: .black, design: .rounded))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 18)
                }
                .buttonStyle(PrimaryDriveButtonStyle(active: viewModel.isListening))

                Button {
                    viewModel.sendTypedMessage()
                } label: {
                    Image(systemName: viewModel.isSending ? "hourglass" : "paperplane.fill")
                        .font(.system(size: 22, weight: .bold))
                        .frame(width: 58, height: 58)
                }
                .buttonStyle(SecondaryDriveButtonStyle())
                .disabled(viewModel.isSending)
            }

            HStack {
                Text(viewModel.status)
                    .font(.footnote.weight(.heavy))
                    .foregroundStyle(statusColor)
                Spacer()
                Button("Repeat Reply") {
                    viewModel.repeatLastSheldonReply()
                }
                .font(.footnote.weight(.bold))
                .foregroundStyle(Color.orange)
                Button("Quiet") {
                    viewModel.stopSpeaking()
                }
                .font(.footnote.weight(.bold))
                .foregroundStyle(Color.white.opacity(0.64))
            }
        }
        .padding(18)
        .background(.ultraThinMaterial)
    }

    private var statusColor: Color {
        if viewModel.status.localizedCaseInsensitiveContains("error") {
            return .red
        }
        if viewModel.isListening || viewModel.isSending {
            return .orange
        }
        return .green
    }
}

struct PrimaryDriveButtonStyle: ButtonStyle {
    let active: Bool

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundStyle(active ? Color.black : Color.white)
            .background(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .fill(active ? Color.orange : Color.blue.opacity(configuration.isPressed ? 0.70 : 0.92))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 22, style: .continuous)
                    .stroke(Color.white.opacity(0.18))
            )
            .scaleEffect(configuration.isPressed ? 0.97 : 1)
    }
}

struct SecondaryDriveButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundStyle(Color.white)
            .background(
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(Color.white.opacity(configuration.isPressed ? 0.18 : 0.10))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .stroke(Color.white.opacity(0.12))
            )
    }
}

#Preview {
    DriveChatView()
}
