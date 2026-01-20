import SwiftUI
import AVFoundation

struct CalibrationOverlayView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.openWindow) var openWindow
    @Environment(\.dismiss) var dismiss
    
    // State for Calibration Workflow
    enum CalibrationPhase {
        case idle
        case preparing // NEW: Grey screen to lock WB
        case measuringBlack
        case measuringWhite
        case measuringGrayScale // NEW: Gray Ramps for Gamma
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
    @State private var isStarting = false // Debounce flag
    
    // VALIDATION: Debounce for window lifecycle
    @State private var sessionStopTask: Task<Void, Never>? = nil
    
    // Macbeth Colors (24)
    private let macbethRGBs: [(Double, Double, Double)] = [
        (115/255, 82/255, 68/255),   (194/255, 150/255, 130/255), (98/255, 122/255, 157/255),
        (87/255, 108/255, 67/255),   (133/255, 128/255, 177/255), (103/255, 189/255, 170/255),
        (214/255, 126/255, 44/255),  (80/255, 91/255, 166/255),   (193/255, 90/255, 99/255),
        (94/255, 60/255, 108/255),   (157/255, 188/255, 64/255),  (224/255, 163/255, 46/255),
        (56/255, 61/255, 150/255),   (70/255, 148/255, 73/255),   (175/255, 54/255, 60/255),
        (175/255, 54/255, 60/255),   (187/255, 86/255, 149/255),  (8/255, 133/255, 161/255),
        (243/255, 243/255, 242/255), (200/255, 200/255, 200/255), (160/255, 160/255, 160/255),
        (122/255, 122/255, 121/255), (85/255, 85/255, 85/255),    (52/255, 52/255, 52/255)
    ]
    
    @State private var window: NSWindow? // Reference to the window
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // ... (Keep existing content inside ZStack)
                // 1. Fullscreen Color Patch
                if phase == .preparing {
                    Color(white: 0.5).ignoresSafeArea() // Grey Reference
                } else if phase == .measuringBlack {
                    Color.black.ignoresSafeArea()
                } else if phase == .measuringWhite {
                    Color.white.ignoresSafeArea()
                } else if phase == .measuringGrayScale {
                    targetColor.ignoresSafeArea() // Use targetColor which will be set to gray levels
                } else if phase == .calibrating {
                    targetColor.ignoresSafeArea()
                } else {
                    Color.black.ignoresSafeArea()
                }
                
                // 2. Alignment Guide (Phone Outline Only, No Circle)
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
                // .opacity(isPaused ? 0.0 : 1.0) // Keep visible as requested

                
                // ERROR OVERLAY (Positioned ABOVE the Guide)
                if let msg = validationMessage, isPaused {
                    VStack(spacing: 12) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.system(size: 40))
                            .foregroundColor(.yellow)
                        
                        Text("VALIDATION FAILED")
                            .font(.system(size: 20, weight: .bold))
                            .foregroundColor(.white)
                        
                        Text(msg)
                            .font(.system(size: 14))
                            .foregroundColor(.red)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                        
                        Text("Adjust camera or lighting. Retrying...")
                            .font(.system(size: 12))
                            .foregroundColor(.gray)
                    }
                    .padding(20)
                    .background(Color.black.opacity(0.85))
                    .cornerRadius(16)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(Color.red.opacity(0.5), lineWidth: 1)
                    )
                    .frame(width: 300) // Slightly narrower for side placement
                    // Position: LEFT of the Phone Guide
                    // Phone Guide Width = 350. Half = 175.
                    // We want it to the left: CenterX - 175 - Padding(50) - HalfWidthOfError(150)
                    // = CenterX - 375.
                    .position(x: (geometry.size.width / 2) - 375, y: geometry.size.height / 2)
                }

                // 3. Sidebar Control Station (Top Layer - Always Accessible)
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
                                let statusText: String = {
                                    switch phase {
                                    case .idle: return "READY TO CONNECT"
                                    case .preparing: return "PREPARING CAMERA..."
                                    case .measuringBlack: return "MEASURING BLACK LEVEL"
                                    case .measuringWhite: return "MEASURING WHITE PEAK"
                                    case .measuringGrayScale: return "MEASURING GRAY SCALE"
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
                            .buttonStyle(.plain)
                            .disabled((!appState.cameraManager.isReceivingFrames && phase == .idle) || isStarting)
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
             // Cancel any pending stop
             sessionStopTask?.cancel()
             sessionStopTask = nil
             
             // Check if running to avoid restart
             if !appState.cameraManager.session.isRunning {
                 appState.cameraManager.startSession()
             }
        }
        .onDisappear {
            print("CalibrationOverlayView: onDisappear triggered")
            // Debounce Stop (wait 0.5s) to survive view rebuilds
            sessionStopTask = Task {
                 try? await Task.sleep(nanoseconds: 500_000_000) // 500ms
                 await MainActor.run {
                     calibrationTask?.cancel()
                     appState.cameraManager.stopSession()
                 }
            }
        }
    }
    

    
    // ... startCalibration and others ...

    func startCalibration() {
        guard phase == .idle else { return }
        phase = .preparing
        isStarting = true
        
        // Disable button for 2 seconds to prevent accidental stop (double click)
        Task {
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            await MainActor.run { isStarting = false }
        }
        
        calibrationTask = Task {
            let logic = CalibrationLogic()
            logic.targetColorSpace = appState.colorSpace
            
            // --- STEP 0: PREPARE & LOCK WB ---
            // Show Grey Screen
            await MainActor.run { phase = .preparing }
            // Wait for STRICT adaptation (User Request: Consistency)
            try? await Task.sleep(nanoseconds: 3_000_000_000) // 3 Seconds
            
            // LOCK SETTINGS
            print("CalibrationOverlayView: Locking Camera Settings (WB/Exposure)")
            await MainActor.run {
                appState.cameraManager.lockConfiguration()
            }
            // Small pause to ensure lock applies
            try? await Task.sleep(nanoseconds: 500_000_000)
            
            // --- STEP 1: MEASURE BLACK BASELINE ---
            await MainActor.run { phase = .measuringBlack }
            try? await Task.sleep(nanoseconds: 1_500_000_000) // Wait for screen to settle
            
            var blackRef: RGB?
            // MOCK: Set black
            if appState.useMock { appState.cameraManager.mockTargetColor = (0, 0, 0) }
            
            // Average Black
            var accBlack = (r: 0.0, g: 0.0, b: 0.0)
            var countBlack = 0
            for _ in 0..<10 {
                if let frame = appState.cameraManager.getAverageRGB() {
                    accBlack.r += frame.r; accBlack.g += frame.g; accBlack.b += frame.b
                    countBlack += 1
                }
                try? await Task.sleep(nanoseconds: 50_000_000) // 50ms interval
            }
            
            if countBlack > 0 {
                blackRef = RGB(r: accBlack.r / Double(countBlack), g: accBlack.g / Double(countBlack), b: accBlack.b / Double(countBlack))
                // Temporarily show checkmark
                await MainActor.run { self.showCheckmark = true }
                try? await Task.sleep(nanoseconds: 500_000_000)
                await MainActor.run { self.showCheckmark = false }
            }
            
            // --- STEP 2: MEASURE WHITE BASELINE ---
            await MainActor.run { phase = .measuringWhite }
            try? await Task.sleep(nanoseconds: 1_500_000_000) 
            
            var whiteRef: RGB?
            // MOCK: Set white
            if appState.useMock { appState.cameraManager.mockTargetColor = (1, 1, 1) }

            // Average White
            var accWhite = (r: 0.0, g: 0.0, b: 0.0)
            var countWhite = 0
            for _ in 0..<10 {
                if let frame = appState.cameraManager.getAverageRGB() {
                    accWhite.r += frame.r; accWhite.g += frame.g; accWhite.b += frame.b
                    countWhite += 1
                }
                try? await Task.sleep(nanoseconds: 50_000_000)
            }

            if countWhite > 0 {
                whiteRef = RGB(r: accWhite.r / Double(countWhite), g: accWhite.g / Double(countWhite), b: accWhite.b / Double(countWhite))
                 // Temporarily show checkmark
                await MainActor.run { self.showCheckmark = true }
                try? await Task.sleep(nanoseconds: 500_000_000)
                await MainActor.run { self.showCheckmark = false }
            }
            
            // Set Baseline
            if let b = blackRef, let w = whiteRef {
                logic.setBaseline(black: b, white: w)
                
                // --- NEW: VALIDATE SCREEN PRESENCE ---
                let check = logic.validateBaseline()
                if !check.isValid {
                    await MainActor.run {
                        self.isPaused = true
                        self.validationMessage = check.message
                    }
                    
                    // Wait indefinitely/retry? For now, 4 seconds delay then Cancel/Restart
                    try? await Task.sleep(nanoseconds: 4_000_000_000)
                    
                    // Stop
                    await MainActor.run { stopCalibration() }
                    return
                }
            }
            
            // --- STEP 3: MEASURE GRAY SCALE (GAMMA) ---
            await MainActor.run { phase = .measuringGrayScale }
            let grayLevels: [Double] = [0.25, 0.50, 0.75]
            
            for level in grayLevels {
                 await MainActor.run {
                    self.targetColor = Color(white: level)
                    // MOCK FEEDBACK
                    if self.appState.useMock {
                         self.appState.cameraManager.mockTargetColor = (level, level, level)
                    }
                }
                try? await Task.sleep(nanoseconds: 1_000_000_000) // 1s adapt
                
                // Average Gray
                var accGray = (r: 0.0, g: 0.0, b: 0.0)
                var countGray = 0
                for _ in 0..<10 {
                    if let frame = appState.cameraManager.getAverageRGB() {
                        accGray.r += frame.r; accGray.g += frame.g; accGray.b += frame.b
                        countGray += 1
                    }
                    try? await Task.sleep(nanoseconds: 50_000_000)
                }
                
                if countGray > 0 {
                    let avgRGB = RGB(r: accGray.r / Double(countGray), g: accGray.g / Double(countGray), b: accGray.b / Double(countGray))
                    logic.recordGraySample(targetLevel: level, measured: avgRGB, sensorModel: appState.sensorModel)
                     
                     // Temporarily show checkmark
                    await MainActor.run { self.showCheckmark = true }
                    try? await Task.sleep(nanoseconds: 300_000_000)
                    await MainActor.run { self.showCheckmark = false }
                }
            }
            
            // --- STEP 4: COLOR PATCHES ---
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
                    
                    // MOCK FEEDBACK
                    if self.appState.useMock {
                        self.appState.cameraManager.mockTargetColor = (r, g, b)
                    }
                }
                
                // 1. Wait for Screen Refresh & Sensor Adapt
                try? await Task.sleep(nanoseconds: 800_000_000)
                
                // Retry Loop
                var isValid = false
                while !isValid && !Task.isCancelled {
                    // Capture Data with Averaging (10 frames)
                    var accR = 0.0, accG = 0.0, accB = 0.0
                    var sampleCount = 0
                    
                    for _ in 0..<10 {
                        if let captured = appState.cameraManager.getAverageRGB() {
                            accR += captured.r
                            accG += captured.g
                            accB += captured.b
                            sampleCount += 1
                        }
                         // Short sleep between frames to capture noise distribution
                        try? await Task.sleep(nanoseconds: 30_000_000) // 30ms
                    }
                    
                    if sampleCount > 0 {
                        let finalR = accR / Double(sampleCount)
                        let finalG = accG / Double(sampleCount)
                        let finalB = accB / Double(sampleCount)
                        
                        let measuredRGB = RGB(r: finalR, g: finalG, b: finalB)
                        
                        let validation = logic.validateSample(
                            target: targetRGB, 
                            measured: measuredRGB,
                            sensorModel: appState.sensorModel
                        )
                        
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
                        // Capture Failed (No frames)
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
                    
                    // STOP CAMERA IMMEDIATELY
                    appState.cameraManager.unlockConfiguration()
                    appState.cameraManager.stopSession()
                    
                    toggleCalibrationMode(false)
                    openWindow(id: "results")
                    dismiss() // Close calibration window
                }
            }
        }
    }
    
    func stopCalibration() {
        print("CalibrationOverlayView: stopCalibration() called")
        phase = .idle
        calibrationTask?.cancel()
        calibrationTask = nil
        // UNLOCK SETTINGS
        appState.cameraManager.unlockConfiguration()
        // STOP SESSION IMMEDIATELY
        appState.cameraManager.stopSession()
        
        // JUST CLOSE OVERLAY (User Request)
        // openWindow(id: "main") // Removed to prevent duplicates/crashes
        
        // toggleCalibrationMode(false) // REMOVED: Causing crash on dismiss (Red Screen Force Close)
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
