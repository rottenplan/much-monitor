import Foundation
import AVFoundation
import Vision
import CoreImage

class CameraManager: NSObject, ObservableObject {
    @Published var availableCameras: [AVCaptureDevice] = []
    @Published var selectedDevice: AVCaptureDevice?
    @Published var currentFrame: CGImage?
    
    let session = AVCaptureSession()
    private var videoOutput: AVCaptureVideoDataOutput? // Changed to optional var to recreate
    private let sessionQueue = DispatchQueue(label: "com.muchmonitor.sessionQueue")
    private let bufferQueue = DispatchQueue(label: "com.muchmonitor.videoQueue") // Persistent buffer queue
    private let ciContext = CIContext() // Reuse context for performance
    
    // Frame Tracking
    @Published var isReceivingFrames: Bool = false
    private var lastFrameTime: Date?
    private var healthCheckTimer: Timer?
    
    // MOCK MODE
    @Published var isMockMode: Bool = false
    var mockTargetColor: (r: Double, g: Double, b: Double)? = nil // For testing validation
    private var mockTimer: Timer?

    
    private var discoverySession: AVCaptureDevice.DiscoverySession!
    private var devicesObserver: NSKeyValueObservation?
    
    override init() {
        super.init()
        checkPermission { granted in
            print("CameraManager: Init permission check: \(granted)")
        }
        setupDiscoverySession()
    }
    
    // Setup persistent session and KVO
    func setupDiscoverySession() {
        var deviceTypes: [AVCaptureDevice.DeviceType] = [
            .builtInWideAngleCamera,
            .externalUnknown
        ]
        if #available(macOS 14.0, *) {
            deviceTypes.append(.continuityCamera)
        }
        if #available(macOS 13.0, *) {
             deviceTypes.append(.deskViewCamera)
        }
        
        self.discoverySession = AVCaptureDevice.DiscoverySession(
            deviceTypes: deviceTypes,
            mediaType: .video,
            position: .unspecified
        )
        
        // Initial Refresh
        refreshCameras()
        
        // KVO Observer
        devicesObserver = discoverySession.observe(\.devices, options: [.new]) { [weak self] _, _ in
            print("CameraManager: KVO detected device change.")
            DispatchQueue.main.async {
                self?.refreshCameras()
            }
        }
    }
    
    func refreshCameras() {
        print("CameraManager: Refreshing cameras (KVO/Manual)...")
        // Use the persistent session's devices
        let devices = discoverySession.devices
        
        // Debug
        let os = ProcessInfo.processInfo.operatingSystemVersion
        print("CameraManager: OS Version: \(os.majorVersion).\(os.minorVersion).\(os.patchVersion)")
        print("CameraManager: Found \(devices.count) total devices.")
        for d in devices {
            print("  - \(d.localizedName) (ID: \(d.uniqueID))")
        }
        
        // Filter out virtual cameras (similar to Python logic)
        var finalDevices = devices.filter { device in
            let name = device.localizedName.lowercased()
            let virtualKeywords = ["desk view", "virtual", "software", "obs", "snap"]
            return !virtualKeywords.contains { name.contains($0) }
        }
        
        print("CameraManager: After filtering virtual cams: \(finalDevices.count) devices.")
        
        // FALLBACK: If real cameras are missing but we have *something* (like OBS), use it.
        if finalDevices.isEmpty && !devices.isEmpty {
            print("CameraManager: No real cameras found. Falling back to all available devices (e.g. Virtual/OBS).")
            finalDevices = devices
        }
        
        // Prioritize iPhone/Continuity
        self.availableCameras = finalDevices.sorted { d1, d2 in
            let n1 = d1.localizedName.lowercased()
            let n2 = d2.localizedName.lowercased()
            
            // Priority 1: Specific User Device "iPhone 11"
            if n1.contains("iphone 11") && !n2.contains("iphone 11") { return true }
            if !n1.contains("iphone 11") && n2.contains("iphone 11") { return false }
            
            // Priority 2: Any iPhone
            if n1.contains("iphone") && !n2.contains("iphone") { return true }
            return false
        }
        
        if self.selectedDevice == nil {
            self.selectedDevice = availableCameras.first
            if let first = availableCameras.first {
                print("CameraManager: Auto-selected device: \(first.localizedName)")
            } else {
                print("CameraManager: No suitable camera found to auto-select.")
            }
        }
    }
    
    func checkPermission(completion: @escaping (Bool) -> Void) {
        let status = AVCaptureDevice.authorizationStatus(for: .video)
        switch status {
        case .authorized:
            print("CameraManager: Access authorized.")
            completion(true)
        case .notDetermined:
            print("CameraManager: Access not determined. Requesting...")
            AVCaptureDevice.requestAccess(for: .video) { granted in
                print("CameraManager: Access request result: \(granted)")
                completion(granted)
            }
        case .denied, .restricted:
            print("CameraManager: Access denied or restricted.")
            completion(false)
        @unknown default:
            print("CameraManager: Unknown auth status.")
            completion(false)
        }
    }
    
    // startSession Modifications:
    func startSession() {
        print("CameraManager: startSession() called")
        checkPermission { granted in
            print("CameraManager: checkPermission result: \(granted)")
            guard granted else {
                print("CameraManager: Cannot start session. Permission denied.")
                return
            }
            
            // HEADLESS / MOCK CHECK
            if self.isMockMode {
                print("CameraManager: Starting MOCK Session...")
                self.startMockSession()
                return
            }
            
            guard let device = self.selectedDevice else { 
                print("CameraManager: No device selected to start session.")
                return 
            }
            
            print("CameraManager: Attempting to start session with device: \(device.localizedName)")
            
            // Start Health Check on Main Thread
            DispatchQueue.main.async {
                self.startHealthCheck()
            }
            
            self.sessionQueue.async {
                self.session.beginConfiguration()
                self.session.sessionPreset = .high 
                print("CameraManager: SessionPreset set to .high")
                
                // Remove existing inputs/outputs
                self.session.inputs.forEach { self.session.removeInput($0) }
                self.session.outputs.forEach { self.session.removeOutput($0) }
                
                // Create FRESH VideoOutput
                let newOutput = AVCaptureVideoDataOutput()
                newOutput.videoSettings = [
                    kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_32BGRA)
                ]
                newOutput.alwaysDiscardsLateVideoFrames = true // Optimize
                
                // Use persistent queue
                newOutput.setSampleBufferDelegate(self, queue: self.bufferQueue)
                self.videoOutput = newOutput
                
                
                do {
                    let input = try AVCaptureDeviceInput(device: device)
                    if self.session.canAddInput(input) {
                        self.session.addInput(input)
                        print("CameraManager: Input added.")
                    } else {
                        print("CameraManager: Could not add input.")
                    }
                    
                    if self.session.canAddOutput(newOutput) {
                        self.session.addOutput(newOutput)
                        print("CameraManager: Output added.")
                        
                        // Check Connection
                        if let connection = newOutput.connection(with: .video) {
                            connection.isEnabled = true
                            if connection.isVideoOrientationSupported {
                                connection.videoOrientation = .landscapeLeft // Or match device
                            }
                            print("CameraManager: Video connection enabled. Active? \(connection.isActive)")
                        }
                    }
                    
                    self.session.commitConfiguration()
                    self.session.startRunning()
                    print("CameraManager: Session startRunning() called. Running: \(self.session.isRunning)")
                } catch {
                    print("CameraManager: Error setting up camera: \(error)")
                }
                
                // Final Check
                print("CameraManager: Configuration committed. Inputs: \(self.session.inputs.count), Outputs: \(self.session.outputs.count)")
            }
        }
    }
    
    
    func startMockSession() {
        stopSession() // Clear any real session
        print("CameraManager: Mock Session Active")
        
        DispatchQueue.main.async {
            self.isReceivingFrames = true
            
            // Generate a frame every 100ms
            self.mockTimer?.invalidate()
            self.mockTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
                guard let self = self else { return }
                
                // Create a solid color frame based on mockTargetColor
                // REMOVED NOISE for stability in Mock Mode
                let color = self.mockTargetColor ?? (0.5, 0.5, 0.5)
                
                let r = min(1.0, max(0.0, color.r))
                let g = min(1.0, max(0.0, color.g))
                let b = min(1.0, max(0.0, color.b))
                
                let rgb: [UInt8] = [
                    UInt8(r * 255), UInt8(g * 255), UInt8(b * 255), 255
                ]
                
                let data = Data(bytes: rgb, count: 4)
                let provider = CGDataProvider(data: data as CFData)!
                let cgImage = CGImage(
                    width: 1, height: 1,
                    bitsPerComponent: 8, bitsPerPixel: 32, bytesPerRow: 4,
                    space: CGColorSpaceCreateDeviceRGB(),
                    bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue),
                    provider: provider,
                    decode: nil, shouldInterpolate: false, intent: .defaultIntent
                )
                
                self.currentFrame = cgImage
                self.lastFrameTime = Date()
            }
        }
    }

    func stopSession() {
        print("CameraManager: Stopping session.")
        DispatchQueue.main.async {
            self.stopHealthCheck()
            self.isReceivingFrames = false
        }
        sessionQueue.async {
            self.session.stopRunning()
            // Aggressively remove inputs to ensure Continuity Camera disconnects
            self.session.inputs.forEach { self.session.removeInput($0) }
            self.session.outputs.forEach { self.session.removeOutput($0) }
            print("CameraManager: Session stopped and inputs released.")
        }
        
        mockTimer?.invalidate()
        mockTimer = nil
    }
    
    private func startHealthCheck() {
        stopHealthCheck()
        self.healthCheckTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            guard let self = self else { return }
            if let last = self.lastFrameTime, Date().timeIntervalSince(last) < 2.0 {
                if !self.isReceivingFrames { self.isReceivingFrames = true }
            } else {
                if self.isReceivingFrames { self.isReceivingFrames = false }
            }
        }
    }
    
    private func stopHealthCheck() {
        healthCheckTimer?.invalidate()
        healthCheckTimer = nil
    }
    
    func lockConfiguration() {
        guard let device = selectedDevice else { return }
        do {
            try device.lockForConfiguration()
            
            // 1. Lock Focus
            if device.isFocusModeSupported(.locked) {
                device.focusMode = .locked
            }
            
            // 2. Lock Exposure
            if device.isExposureModeSupported(.locked) {
                device.exposureMode = .locked
            }
            
            // 3. Lock White Balance
            if device.isWhiteBalanceModeSupported(.locked) {
                device.whiteBalanceMode = .locked
                print("Locked WB to Current Values.")
            }
            
            device.unlockForConfiguration()
            print("Camera configuration LOCKED for calibration.")
        } catch {
            print("Failed to lock camera configuration: \(error)")
        }
    }
    
    func unlockConfiguration() {
        guard let device = selectedDevice else { return }
        do {
            try device.lockForConfiguration()
            
            if device.isFocusModeSupported(.continuousAutoFocus) {
                device.focusMode = .continuousAutoFocus
            }
            
            if device.isExposureModeSupported(.continuousAutoExposure) {
                device.exposureMode = .continuousAutoExposure
            }
            
            if device.isWhiteBalanceModeSupported(.continuousAutoWhiteBalance) {
                device.whiteBalanceMode = .continuousAutoWhiteBalance
            }
            
            device.unlockForConfiguration()
            print("Camera configuration UNLOCKED.")
        } catch {
            print("Failed to unlock camera configuration: \(error)")
        }
    }
    
    func getAverageRGB() -> (r: Double, g: Double, b: Double)? {
        guard let cgImage = self.currentFrame else { return nil }
        
        // Use CoreImage to get average color of the center region
        let ciImage = CIImage(cgImage: cgImage)
        let extent = ciImage.extent
        
        // Sample Center 1/4 Area (Center 50% width x 50% height) to avoid vignetting/edges
        let cropW = extent.width * 0.5
        let cropH = extent.height * 0.5
        let cropRect = CGRect(
            x: (extent.width - cropW) / 2.0,
            y: (extent.height - cropH) / 2.0,
            width: cropW,
            height: cropH
        )
        
        // Filter: Area Average
        let filter = CIFilter(name: "CIAreaAverage")
        filter?.setValue(ciImage, forKey: kCIInputImageKey)
        filter?.setValue(CIVector(cgRect: cropRect), forKey: kCIInputExtentKey)
        
        guard let outputImage = filter?.outputImage else { return nil }
        
        var bitmap = [UInt8](repeating: 0, count: 4)
        // Use persistent context
        self.ciContext.render(outputImage, 
                      toBitmap: &bitmap, 
                      rowBytes: 4, 
                      bounds: CGRect(x: 0, y: 0, width: 1, height: 1), 
                      format: .RGBA8, 
                      colorSpace: nil)
        
        // Convert to 0-255 Double
        return (Double(bitmap[0]), Double(bitmap[1]), Double(bitmap[2]))
    }
}

extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        // Debug frame delivery (throttle log)
        let timestamp = CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sampleBuffer))
        if Int(timestamp) % 5 == 0 {
             // Print once per 5 seconds of connection time roughly, or use a counter
             // simpler: random output or just checking if it works at all first
        }
        
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        
        // Debug print for first frame only to confirm flow
        if !self.isReceivingFrames {
             print("CameraManager: Received first frame! Timestamp: \(timestamp)")
        } else if Int(timestamp) % 2 == 0 {
             // Heartbeat log every ~2s
             print("CameraManager: Frame received at \(timestamp)")
        }
        // Create CIImage from buffer
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        // Use persistent context
        if let cgImage = self.ciContext.createCGImage(ciImage, from: ciImage.extent) {
            DispatchQueue.main.async {
                self.currentFrame = cgImage
                self.lastFrameTime = Date()
                if !self.isReceivingFrames { self.isReceivingFrames = true }
            }
        }
    }
}
