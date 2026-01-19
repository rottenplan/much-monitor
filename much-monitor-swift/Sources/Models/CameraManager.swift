import Foundation
import AVFoundation
import Vision
import CoreImage

class CameraManager: NSObject, ObservableObject {
    @Published var availableCameras: [AVCaptureDevice] = []
    @Published var selectedDevice: AVCaptureDevice?
    @Published var currentFrame: CGImage?
    
    let session = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    private let sessionQueue = DispatchQueue(label: "com.muchmonitor.sessionQueue")
    private let ciContext = CIContext() // Reuse context for performance
    
    // Frame Tracking
    @Published var isReceivingFrames: Bool = false
    private var lastFrameTime: Date?
    private var healthCheckTimer: Timer?

    
    override init() {
        super.init()
        refreshCameras()
    }
    
    func refreshCameras() {
        var deviceTypes: [AVCaptureDevice.DeviceType] = [.builtInWideAngleCamera, .externalUnknown]
        if #available(macOS 14.0, *) {
            deviceTypes.append(.continuityCamera)
        }
        
        let discoverySession = AVCaptureDevice.DiscoverySession(
            deviceTypes: deviceTypes,
            mediaType: .video,
            position: .unspecified
        )
        
        let devices = discoverySession.devices
        
        // Filter out virtual cameras (similar to Python logic)
        let filtered = devices.filter { device in
            let name = device.localizedName.lowercased()
            let virtualKeywords = ["desk view", "virtual", "software", "obs", "snap"]
            return !virtualKeywords.contains { name.contains($0) }
        }
        
        // Prioritize iPhone/Continuity
        self.availableCameras = filtered.sorted { d1, d2 in
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
        }
    }
    
    func startSession() {
        guard let device = selectedDevice else { 
            print("CameraManager: No device selected to start session.")
            return 
        }
        
        print("CameraManager: Attempting to start session with device: \(device.localizedName)")
        
        // Start Health Check on Main Thread
        DispatchQueue.main.async {
            self.startHealthCheck()
        }
        
        sessionQueue.async {
            self.session.beginConfiguration()
            
            // Remove existing inputs
            self.session.inputs.forEach { self.session.removeInput($0) }
            
            do {
                let input = try AVCaptureDeviceInput(device: device)
                if self.session.canAddInput(input) {
                    self.session.addInput(input)
                    print("CameraManager: Input added.")
                } else {
                    print("CameraManager: Could not add input.")
                }
                
                if self.session.canAddOutput(self.videoOutput) {
                    self.session.addOutput(self.videoOutput)
                    self.videoOutput.setSampleBufferDelegate(self, queue: DispatchQueue(label: "videoQueue"))
                    print("CameraManager: Output added.")
                }
                
                self.session.commitConfiguration()
                self.session.startRunning()
                print("CameraManager: Session startRunning() called. Running: \(self.session.isRunning)")
            } catch {
                print("CameraManager: Error setting up camera: \(error)")
            }
        }
    }
    
    func stopSession() {
        DispatchQueue.main.async {
            self.stopHealthCheck()
            self.isReceivingFrames = false
        }
        sessionQueue.async {
            self.session.stopRunning()
        }
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
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
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
