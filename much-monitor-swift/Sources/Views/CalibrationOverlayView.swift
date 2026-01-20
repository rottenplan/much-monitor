import SwiftUI
import AVFoundation

struct CalibrationOverlayView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.openWindow) var openWindow
    @Environment(\.dismiss) var dismiss
    
    // State for Calibration Workflow
    enum CalibrationPhase {
        case idle
        case measuringBlack
        case measuringWhite
        case calibrating
        case completed
    }
    
    @State private var phase: CalibrationPhase = .idle
    @State private var currentStep = 0
    @State private var totalSteps = 24
    
    // Ui & Validation
    @State private var targetColor: Color = .black
    @State private var validationMessage: String? = nil
    @State private var isPaused = false
    @State private var showCheckmark = false
    
    @State private var calibrationTask: Task<Void, Never>? = nil
    
    // Macbeth Colors (24)
    private let macbethRGBs: [(Double, Double, Double)] = [
        (115/255, 82/255, 68/255),   (194/255, 150/255, 130/255), (98/255, 122/255, 157/255),
        (87/255, 108/255, 67/255),   (133/255, 128/255, 177/255), (103/255, 189/255, 170/255),
        (214/255, 126/255, 44/255),  (80/255, 91/255, 166/255),   (193/255, 90/255, 99/255),
        (94/255, 60/255, 108/255),   (157/255, 188/255, 64/255),  (224/255, 163/255, 46/255),
        (56/255, 61/255, 150/255),   (70/255, 148/255, 73/255),   (175/255, 54/255, 60/255),
        (231/255, 199/255, 49/255),  (187/255, 86/255, 149/255),  (8/255, 133/255, 161/255),
        (243/255, 243/255, 242/255), (200/255, 200/255, 200/255), (160/255, 160/255, 160/255),
        (122/255, 122/255, 121/255), (85/255, 85/255, 85/255),    (52/255, 52/255, 52/255)
    ]
    
    @State private var window: NSWindow? // Reference to the window
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // ... (Keep existing content inside ZStack)
                // 1. Fullscreen Color Patch
                if phase == .measuringBlack {
                    Color.black.ignoresSafeArea()
                } else if phase == .measuringWhite {
                    Color.white.ignoresSafeArea()
                } else if phase == .calibrating {
                    targetColor.ignoresSafeArea()
                } else {
                    Color.black.ignoresSafeArea()
                }
                
                // 2. Alignment Guide (Phone Outline Only, No Circle)
                VStack(spacing: 20) {
                    ZStack {
                        RoundedRectangle(cornerRadius: 35)
                            .stroke(Color.white.opacity(0.3), lineWidth: 3)
                            .frame(width: 350, height: 750) // Enlarged Guide
                    }
                    
                    Text("Position your phone camera exactly on this line.\nEnsure the lens is clean & room lighting is dim.")
                        .font(.system(size: 14, weight: .medium))
                        .multilineTextAlignment(.center)
                        .foregroundColor(.white.opacity(0.9))
                        .padding(12)
                        .background(Color.black.opacity(0.6))
                        .cornerRadius(10)
                }
                .position(x: geometry.size.width / 2, y: geometry.size.height / 2)
                
                // 3. Sidebar Control Station (Bottom Right)
                VStack {
                    Spacer()
                    HStack {
                        Spacer()
                        VStack(spacing: 12) {
                            // Camera Preview Frame
                            ZStack {
                                CameraPreview(session: appState.cameraManager.session)
                                    .frame(width: 320, height: 240)
                                    .background(Color.black)
                                    .cornerRadius(12)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 12)
                                            .stroke(Color.white.opacity(0.2), lineWidth: 1)
                                    )
                                    .shadow(radius: 20)
                                
                                // Crop Area Indicator
                                Rectangle()
                                    .stroke(Color.green, lineWidth: 2)
                                    .frame(width: 160, height: 120)
                                
                                if showCheckmark {
                                    Image(systemName: "checkmark.circle.fill")
                                        .font(.system(size: 60))
                                        .foregroundColor(.green)
                                        .shadow(radius: 10)
                                        .transition(.scale.combined(with: .opacity))
                                }
                            }
                            
                            // Info / Step Counter
                            VStack(alignment: .trailing, spacing: 6) {
                            // Info / Step Counter
                            VStack(alignment: .trailing, spacing: 6) {
                                let statusText: String = {
                                    switch phase {
                                    case .idle: return "READY TO CONNECT"
                                    case .measuringBlack: return "MEASURING BLACK LEVEL"
                                    case .measuringWhite: return "MEASURING WHITE PEAK"
                                    case .calibrating: return "CALIB. PROCESS"
                                    case .completed: return "COMPLETE"
                                    }
                                }()
                                
                                Text(statusText)
                                    .font(.system(size: 10, weight: .bold))
                                    .foregroundColor(.gray)
                                
                                Text("\(currentStep + 1) / \(totalSteps)")
                                    .font(.system(size: 32, weight: .bold))
                                    .foregroundColor(.white)
                                
                                if isPaused {
                                    Text("PAUSED: Validation Failed")
                                        .foregroundColor(.yellow)
                                        .font(.system(size: 12, weight: .bold))
                                } else {
                                    Text(phase != .idle ? "Reading..." : "Waiting for Start...")
                                        .foregroundColor(.white.opacity(0.7))
                                        .font(.system(size: 12))
                                }
                            }
                            .padding(15)
                            .frame(maxWidth: 320) // Match preview width
                            .background(Color.black.opacity(0.6))
                            .cornerRadius(10)
                            
                            Button(action: {
                                if phase != .idle {
                                    stopCalibration()
                                } else {
                                    startCalibration()
                                }
                            }) {
                                HStack {
                                    if !appState.cameraManager.isReceivingFrames {
                                        Image(systemName: "video.slash.fill")
                                        Text("WAITING FOR CAMERA...")
                                    } else {
                                        Image(systemName: phase != .idle ? "stop.circle.fill" : "play.circle.fill")
                                        Text(phase != .idle ? "STOP" : "START (AUTO)")
                                    }
                                }
                                .font(.system(size: 14, weight: .bold))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 12)
                                .background(getButtonColor())
                                .foregroundColor(.white)
                                .cornerRadius(8)
                            }
                            .buttonStyle(.plain)
                            .disabled(!appState.cameraManager.isReceivingFrames && phase == .idle)
                            .frame(width: 320) // Match preview width
                            
                            // 5. Back Button
                            Button(action: {
                                stopCalibration()
                            }) {
                                HStack {
                                    Image(systemName: "arrow.uturn.backward.circle")
                                    Text("BACK TO MENU")
                                }
                                .font(.system(size: 14, weight: .bold))
                                .foregroundColor(.white.opacity(0.8))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 12)
                                .background(Color.gray.opacity(0.3))
                                .cornerRadius(8)
                            }
                            .buttonStyle(.plain)
                            .frame(width: 320)
                        }
                        .padding(40)
                    }
                }
                
                // ERROR OVERLAY
                if let msg = validationMessage, isPaused {
                    ZStack {
                        Color.black.opacity(0.8)
                            .ignoresSafeArea()
                        
                        VStack(spacing: 20) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .font(.system(size: 60))
                                .foregroundColor(.yellow)
                            
                            Text("COLOR VALIDATION FAILED")
                                .font(.system(size: 24, weight: .bold))
                                .foregroundColor(.white)
                            
                            Text(msg)
                                .font(.system(size: 16))
                                .foregroundColor(.red)
                                .padding(.horizontal, 40)
                                .multilineTextAlignment(.center)
                            
                            Text("Please adjust camera position or lighting.")
                                .font(.system(size: 14))
                                .foregroundColor(.gray)
                            
                            Text("Retrying in 1 second...")
                                .font(.system(size: 12))
                                .foregroundColor(.white.opacity(0.5))
                                .padding(.top, 10)
                        }
                    }
                }
            }
        }
        .background(WindowAccessor(window: $window)) // Bind window
        .onChange(of: window) { newWindow in
            if let win = newWindow {
                toggleCalibrationMode(true, for: win)
            }
        }
        .onAppear {
             print("CalibrationOverlayView: onAppear triggered")
             // NO AUTO_START!
             appState.cameraManager.startSession()
        }
        .onDisappear {
            calibrationTask?.cancel()
            appState.cameraManager.stopSession()
        }
    }
    
    }
    
    // ... startCalibration and others ...

    func startCalibration() {
        guard phase == .idle else { return }
        phase = .measuringBlack
        
        calibrationTask = Task {
            let logic = CalibrationLogic()
            logic.targetColorSpace = appState.colorSpace
            
            // --- STEP 1: MEASURE BLACK BASELINE ---
            await MainActor.run { phase = .measuringBlack }
            try? await Task.sleep(nanoseconds: 1_500_000_000) // Wait for screen to settle
            
            var blackRef: RGB?
            if let frame = appState.cameraManager.getAverageRGB() {
                blackRef = RGB(r: frame.r, g: frame.g, b: frame.b)
                // Temporarily show checkmark
                await MainActor.run { self.showCheckmark = true }
                try? await Task.sleep(nanoseconds: 500_000_000)
                await MainActor.run { self.showCheckmark = false }
            } else {
               // Fallback or Retry? For now, proceed with zero implies standard.
               // Ideally retry, but let's keep flow smooth. 0,0,0 is safe fallback.
            }
            
            // --- STEP 2: MEASURE WHITE BASELINE ---
            await MainActor.run { phase = .measuringWhite }
            try? await Task.sleep(nanoseconds: 1_500_000_000) 
            
            var whiteRef: RGB?
            if let frame = appState.cameraManager.getAverageRGB() {
                whiteRef = RGB(r: frame.r, g: frame.g, b: frame.b)
                 // Temporarily show checkmark
                await MainActor.run { self.showCheckmark = true }
                try? await Task.sleep(nanoseconds: 500_000_000)
                await MainActor.run { self.showCheckmark = false }
            }
            
            // Set Baseline
            if let b = blackRef, let w = whiteRef {
                logic.setBaseline(black: b, white: w)
            }
            
            // --- STEP 3: COLOR PATCHES ---
            await MainActor.run { 
                phase = .calibrating 
                currentStep = 0
                totalSteps = macbethRGBs.count
            }
            
            // Loop through patches
            for (index, colorTuple) in macbethRGBs.enumerated() {
                if Task.isCancelled { break }
                
                let (r, g, b) = colorTuple
                let targetColorDisplay = Color(red: r, green: g, blue: b)
                let targetRGB = RGB(r: r * 255.0, g: g * 255.0, b: b * 255.0)
                
                await MainActor.run {
                    self.currentStep = index
                    self.targetColor = targetColorDisplay
                }
                
                // 1. Wait
                try? await Task.sleep(nanoseconds: 600_000_000)
                
                // Retry Loop
                var isValid = false
                while !isValid && !Task.isCancelled {
                    // Capture Data
                    if let captured = appState.cameraManager.getAverageRGB() {
                        let measuredRGB = RGB(r: captured.r, g: captured.g, b: captured.b)
                        let validation = logic.validateSample(target: targetRGB, measured: measuredRGB)
                        
                        if validation.isValid {
                            isValid = true
                            await MainActor.run {
                                self.isPaused = false
                                self.validationMessage = nil
                            }
                            
                            logic.recordSample(
                                target: targetRGB,
                                measured: measuredRGB,
                                sensorModel: appState.sensorModel,
                                colorSpace: appState.colorSpace
                            )
                        } else {
                            // Invalid
                            await MainActor.run {
                                self.isPaused = true
                                self.validationMessage = validation.message ?? "Error"
                            }
                            try? await Task.sleep(nanoseconds: 1_500_000_000)
                        }
                    } else {
                        // Capture Failed
                        try? await Task.sleep(nanoseconds: 500_000_000)
                    }
                }
                
                if Task.isCancelled { break }
                
                await MainActor.run { self.showCheckmark = true }
                try? await Task.sleep(nanoseconds: 200_000_000)
                await MainActor.run { self.showCheckmark = false }
            }
            
            // Finish
            if !Task.isCancelled {
                let report = logic.analyze()
                await MainActor.run {
                    appState.latestMetrics = report
                    phase = .completed
                    toggleCalibrationMode(false)
                    openWindow(id: "results")
                    dismiss() // Close calibration window
                }
            }
        }
    }
    
    func stopCalibration() {
        phase = .idle
        calibrationTask?.cancel()
        calibrationTask = nil
        toggleCalibrationMode(false)
        dismiss()
    }
    
    func getButtonColor() -> Color {
        if !appState.cameraManager.isReceivingFrames && phase == .idle {
            return Color.gray.opacity(0.5)
        }
        return phase != .idle ? Color.red.opacity(0.8) : Color.blue.opacity(0.8)
    }
    
    func toggleCalibrationMode(_ enable: Bool, for specificWindow: NSWindow? = nil) {
        DispatchQueue.main.async {
            // Use specific window if provided, else captured, else keyWindow
            guard let win = specificWindow ?? self.window ?? NSApp.windows.first(where: { $0.isKeyWindow }) else { return }
            
            if enable {
                win.level = .floating
                if !win.styleMask.contains(.fullScreen) {
                    win.toggleFullScreen(nil)
                }
            } else {
                win.level = .normal
                 if win.styleMask.contains(.fullScreen) {
                    win.toggleFullScreen(nil)
                }
            }
        }
    }
}

// Robust Camera Preview (Unchanged)
// Helper to access the underlying NSWindow
struct WindowAccessor: NSViewRepresentable {
    @Binding var window: NSWindow?
    
    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async {
            self.window = view.window
        }
        return view
    }
    
    func updateNSView(_ nsView: NSView, context: Context) {}
}

struct CameraPreview: NSViewRepresentable {
    let session: AVCaptureSession
    
    func makeNSView(context: Context) -> PreviewView {
        let view = PreviewView()
        view.session = session
        return view
    }
    
    func updateNSView(_ nsView: PreviewView, context: Context) {
        if nsView.session != session {
            nsView.session = session
        }
    }
    
    class PreviewView: NSView {
        var videoPreviewLayer: AVCaptureVideoPreviewLayer {
            guard let layer = layer as? AVCaptureVideoPreviewLayer else {
                fatalError("Expected `AVCaptureVideoPreviewLayer` type for layer. Check returned layer class.")
            }
            return layer
        }
        
        var session: AVCaptureSession? {
            get {
                return videoPreviewLayer.session
            }
            set {
                videoPreviewLayer.session = newValue
                print("PreviewView: Session set on layer. Session running? \(newValue?.isRunning == true)")
            }
        }
        
        override func makeBackingLayer() -> CALayer {
            let layer = AVCaptureVideoPreviewLayer()
            layer.name = "cameraPreview"
            layer.videoGravity = .resizeAspectFill
            layer.backgroundColor = NSColor.black.cgColor
            return layer
        }
        
        init() {
            super.init(frame: .zero)
            self.wantsLayer = true
        }
        
        required init?(coder: NSCoder) {
            fatalError("init(coder:) has not been implemented")
        }
    }
}
