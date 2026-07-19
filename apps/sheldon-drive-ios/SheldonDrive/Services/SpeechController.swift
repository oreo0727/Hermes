import AVFoundation
import Foundation
import Speech

final class SpeechController: NSObject, ObservableObject, SFSpeechRecognizerDelegate {
    enum SpeechError: LocalizedError {
        case recognizerUnavailable
        case permissionDenied
        case audioEngineUnavailable

        var errorDescription: String? {
            switch self {
            case .recognizerUnavailable:
                return "Speech recognition is not available right now."
            case .permissionDenied:
                return "Microphone or speech recognition permission was denied."
            case .audioEngineUnavailable:
                return "The audio engine could not start."
            }
        }
    }

    private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private let audioEngine = AVAudioEngine()
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?

    @Published private(set) var isListening = false

    override init() {
        super.init()
        recognizer?.delegate = self
    }

    func requestPermissions() async -> Bool {
        let speechAllowed = await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status == .authorized)
            }
        }
        let micAllowed = await withCheckedContinuation { continuation in
            AVAudioSession.sharedInstance().requestRecordPermission { allowed in
                continuation.resume(returning: allowed)
            }
        }
        return speechAllowed && micAllowed
    }

    @MainActor
    func start(
        onPartial: @escaping (String) -> Void,
        onFinal: @escaping (String) -> Void,
        onError: @escaping (Error) -> Void
    ) {
        guard recognizer?.isAvailable == true else {
            onError(SpeechError.recognizerUnavailable)
            return
        }

        recognitionTask?.cancel()
        recognitionTask = nil

        let audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession.setCategory(.record, mode: .measurement, options: [.duckOthers])
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            onError(error)
            return
        }

        let request = SFSpeechAudioBufferRecognitionRequest()
        request.shouldReportPartialResults = true
        recognitionRequest = request

        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.removeTap(onBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            request.append(buffer)
        }

        audioEngine.prepare()
        do {
            try audioEngine.start()
            isListening = true
        } catch {
            onError(SpeechError.audioEngineUnavailable)
            return
        }

        recognitionTask = recognizer?.recognitionTask(with: request) { [weak self] result, error in
            guard let self else { return }
            if let result {
                let transcript = result.bestTranscription.formattedString
                onPartial(transcript)
                if result.isFinal {
                    Task { @MainActor in
                        self.stop()
                        onFinal(transcript)
                    }
                }
            }
            if let error {
                Task { @MainActor in
                    self.stop()
                    onError(error)
                }
            }
        }
    }

    @MainActor
    func stop() {
        if audioEngine.isRunning {
            audioEngine.stop()
        }
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        recognitionTask?.cancel()
        recognitionTask = nil
        isListening = false
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }
}
