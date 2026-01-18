import Foundation
import AVFoundation
import Vision
import CoreImage

class CameraManager: NSObject, ObservableObject {
    @Published var availableCameras: [AVCaptureDevice] = []
    @Published var selectedDevice: AVCaptureDevice?
    @Published var currentFrame: CGImage?
    
    private let session = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    private let sessionQueue = DispatchQueue(label: "com.muchmonitor.sessionQueue")
    
    override init() {
        super.init()
        refreshCameras()
    }
    
    func refreshCameras() {
        let discoverySession = AVCaptureDevice.DiscoverySession(
            deviceTypes: [.builtInWideAngleCamera, .externalUnknown, .continuityCamera],
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
            if n1.contains("iphone") && !n2.contains("iphone") { return true }
            return false
        }
        
        if self.selectedDevice == nil {
            self.selectedDevice = availableCameras.first
        }
    }
    
    func startSession() {
        guard let device = selectedDevice else { return }
        sessionQueue.async {
            self.session.beginConfiguration()
            
            // Remove existing inputs
            self.session.inputs.forEach { self.session.removeInput($0) }
            
            do {
                let input = try AVCaptureDeviceInput(device: device)
                if self.session.canAddInput(input) {
                    self.session.addInput(input)
                }
                
                if self.session.canAddOutput(self.videoOutput) {
                    self.session.addOutput(self.videoOutput)
                    self.videoOutput.setSampleBufferDelegate(self, queue: DispatchQueue(label: "videoQueue"))
                }
                
                self.session.commitConfiguration()
                self.session.startRunning()
            } catch {
                print("Error setting up camera: \(error)")
            }
        }
    }
    
    func stopSession() {
        sessionQueue.async {
            self.session.stopRunning()
        }
    }
}

extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        let ciImage = CIImage(cvPixelBuffer: pixelBuffer)
        let context = CIContext()
        if let cgImage = context.createCGImage(ciImage, from: ciImage.extent) {
            DispatchQueue.main.async {
                self.currentFrame = cgImage
            }
        }
    }
}
