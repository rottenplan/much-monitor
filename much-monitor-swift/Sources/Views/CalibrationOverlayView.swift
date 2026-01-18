import SwiftUI

struct CalibrationOverlayView: View {
    @ObservedObject var cameraManager: CameraManager
    let onFinish: () -> Void
    
    @State private var currentStep = 0
    @State private var totalSteps = 63
    @State private var patchColor = Color.white
    @State private var isCalibrating = false
    @State private var showCheckmark = false
    
    var body: some View {
        ZStack {
            // Full Screen Patch Color
            patchColor
                .ignoresSafeArea()
            
            // Alignment Guide (Center)
            Rectangle()
                .stroke(Color.blue, lineWidth: 5)
                .frame(width: 300, height: 300)
                .position(x: NSScreen.main?.visibleFrame.width ?? 1000 / 2, y: (NSScreen.main?.visibleFrame.height ?? 800) / 4)
            
            // Sidebar Control Station (Bottom Right)
            VStack {
                Spacer()
                HStack {
                    Spacer()
                    VStack(spacing: 12) {
                        // Live Preview
                        if let frame = cameraManager.currentFrame {
                            Image(frame, scale: 1.0, label: Text("Preview"))
                                .resizable()
                                .aspectRatio(contentMode: .fill)
                                .frame(width: 320, height: 240)
                                .clipped()
                                .cornerRadius(8)
                                .overlay(RoundedRectangle(cornerRadius: 8).stroke(showCheckmark ? Color.green : Color.gray.opacity(0.3), lineWidth: 1))
                        }
                        
                        // Info Panel
                        VStack(alignment: .trailing, spacing: 10) {
                            Text("Langkah \(currentStep + 1)/\(totalSteps)")
                                .font(.system(size: 20, weight: .bold))
                                .foregroundColor(showCheckmark ? .green : .blue)
                            
                            Text(showCheckmark ? "✓ Data Terbaca" : "Sejajarkan lensa dengan kotak.\nKunci FOCUS & EXPOSURE di iPhone.")
                                .font(.system(size: 11))
                                .foregroundColor(.gray)
                                .multilineTextAlignment(.trailing)
                            
                            if isCalibrating {
                                Text("Mohon tidak menggerakkan kamera.")
                                    .font(.system(size: 9, weight: .medium).italic())
                                    .foregroundColor(.red.opacity(0.7))
                            }
                        }
                        .padding(20)
                        .background(Color(red: 0.07, green: 0.07, blue: 0.07))
                        .cornerRadius(12)
                        .overlay(RoundedRectangle(cornerRadius: 12).stroke(showCheckmark ? Color.green : Color.gray.opacity(0.3), lineWidth: 1))
                    }
                    .padding(30)
                }
            }
            
            // Start Button (If not calibrating)
            if !isCalibrating {
                Button(action: startCalibration) {
                    Text("SAYA SUDAH SIAP, MULAI KALIBRASI")
                        .font(.system(size: 18, weight: .bold))
                        .padding(.horizontal, 40)
                        .padding(.vertical, 20)
                        .background(Color.green)
                        .foregroundColor(.black)
                        .cornerRadius(10)
                }
                .buttonStyle(.plain)
                .position(x: (NSScreen.main?.visibleFrame.width ?? 1000) / 2, y: (NSScreen.main?.visibleFrame.height ?? 800) * 0.8)
            }
        }
    }
    
    func startCalibration() {
        isCalibrating = true
        // Sequence logic will go here
    }
}
