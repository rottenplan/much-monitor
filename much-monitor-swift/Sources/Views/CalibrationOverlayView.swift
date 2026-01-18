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
        GeometryReader { geometry in
            ZStack {
                // Full Screen Patch Color
                patchColor
                    .frame(width: geometry.size.width, height: geometry.size.height)
                    .ignoresSafeArea()
                
                // Alignment Guide (Center)
                Rectangle()
                    .stroke(Color.blue, lineWidth: 5)
                    .frame(width: 300, height: 300)
                    .position(x: geometry.size.width / 2, y: geometry.size.height / 3)
                
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
                    VStack {
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
                        
                        Text("Pastikan ruangan gelap untuk hasil terbaik.")
                            .font(.system(size: 11))
                            .foregroundColor(.gray)
                            .padding(.top, 10)
                    }
                    .position(x: geometry.size.width / 2, y: geometry.size.height * 0.8)
                }
                
                // Persistent Exit Button (Top Right)
                Button(action: onFinish) {
                    HStack {
                        Image(systemName: "xmark.circle.fill")
                        Text("BATAL / KELUAR")
                            .font(.system(size: 11, weight: .bold))
                    }
                    .foregroundColor(.white.opacity(0.4))
                    .padding(10)
                    .background(Color.black.opacity(0.5))
                    .cornerRadius(20)
                }
                .buttonStyle(.plain)
                .position(x: geometry.size.width - 100, y: 50)
            }
        }
        .onAppear {
            cameraManager.startSession()
        }
        .onDisappear {
            cameraManager.stopSession()
        }
    }
    
    func startCalibration() {
        isCalibrating = true
        // Sequence logic will go here
    }
}
