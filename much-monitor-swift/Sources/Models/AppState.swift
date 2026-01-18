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
            // Update CameraManager mock state if needed, 
            // though CameraManager might handle it internally if we bound it differently.
            // For now, views verify this flag.
        }
    }
    
    // Calibration Data
    @Published var latestMetrics: [String: Any]? = nil
    
    // Navigation/Window Control (Optional helpers)
    
    init() {
        // Initial setup if needed
    }
}
