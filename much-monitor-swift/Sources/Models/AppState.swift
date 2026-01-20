import SwiftUI
import Combine

class AppState: ObservableObject {
    @Published var cameraManager = CameraManager()
    
    // User Settings
    @Published var sensorModel: String = "iPhone 11"
    @Published var colorSpace: String = "sRGB"
    @Published var whitePoint: String = "D65 (6500K)"
    @Published var gamma: String = "2.2 (SDR)"
    @Published var useMock: Bool = false {
        didSet {
            cameraManager.isMockMode = useMock
            // If we toggle while running, we might want to restart session, but usually this is done before start.
            // If session is running, switch?
            if cameraManager.session.isRunning || cameraManager.isReceivingFrames {
                cameraManager.stopSession()
                cameraManager.startSession()
            }
        }
    }
    
    // Calibration Data
    @Published var latestMetrics: [String: Any]? = nil
    
    // Navigation/Window Control (Optional helpers)
    
    init() {
        // Initial setup if needed
    }
}
