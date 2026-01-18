import SwiftUI
import AVFoundation

struct ContentView: View {
    @StateObject var cameraManager = CameraManager()
    @State private var selectedCameraID: String = ""
    @State private var useMock: Bool = false
    @State private var whitePoint: String = "D65 (6500K)"
    @State private var gamma: String = "2.2 (SDR)"
    @State private var showCalibration = false
    
    let accentColor = Color(red: 0, green: 0.82, blue: 1.0) // #00D1FF
    
    var body: some View {
        VStack(alignment: .leading, spacing: 25) {
            // Header
            VStack(alignment: .leading, spacing: 4) {
                Text("MUCH MONITOR")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.white)
                Text("PRO COLOR ENGINE v2.0 (NATIVE)")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(accentColor)
                
                Divider()
                    .background(Color.white.opacity(0.1))
                    .padding(.top, 10)
            }
            .padding(.horizontal, 40)
            .padding(.top, 30)
            
            ScrollView {
                VStack(spacing: 20) {
                    // Camera Card
                    VStack(alignment: .leading, spacing: 15) {
                        Text("KAMERA SENSOR")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(.gray)
                        
                        HStack {
                            Picker("", selection: $selectedCameraID) {
                                if cameraManager.availableCameras.isEmpty {
                                    Text("No cameras found").tag("")
                                } else {
                                    ForEach(cameraManager.availableCameras, id: \.uniqueID) { device in
                                        Text(device.localizedName).tag(device.uniqueID)
                                    }
                                }
                            }
                            .pickerStyle(.menu)
                            .labelsHidden()
                            
                            Button(action: {
                                cameraManager.refreshCameras()
                            }) {
                                Image(systemName: "arrow.clockwise")
                                    .font(.system(size: 16))
                            }
                            .buttonStyle(.plain)
                        }
                        
                        Toggle("Gunakan Mock Camera (Testing)", isOn: $useMock)
                            .font(.system(size: 10))
                            .foregroundColor(.gray)
                    }
                    .padding(25)
                    .background(Color(red: 0.07, green: 0.07, blue: 0.07))
                    .cornerRadius(12)
                    
                    // Parameters Card
                    VStack(alignment: .leading, spacing: 15) {
                        Text("TARGET PARAMETER")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(.gray)
                        
                        Grid(alignment: .leading, horizontalSpacing: 20, verticalSpacing: 15) {
                            GridRow {
                                Text("White Point")
                                    .foregroundColor(.white.opacity(0.8))
                                Picker("", selection: $whitePoint) {
                                    Text("D65 (6500K)").tag("D65")
                                    Text("D50 (5000K)").tag("D50")
                                }
                                .labelsHidden()
                            }
                            GridRow {
                                Text("Gamma")
                                    .foregroundColor(.white.opacity(0.8))
                                Picker("", selection: $gamma) {
                                    Text("2.2 (SDR)").tag("2.2")
                                    Text("2.4 (Video)").tag("2.4")
                                }
                                .labelsHidden()
                            }
                        }
                    }
                    .padding(25)
                    .background(Color(red: 0.07, green: 0.07, blue: 0.07))
                    .cornerRadius(12)
                    
                    Text("PRO TIPS: Redupkan lampu & bersihkan layar monitor.")
                        .font(.system(size: 11, weight: .medium).italic())
                        .foregroundColor(.gray)
                        .padding(.top, 10)
                }
                .padding(.horizontal, 40)
            }
            
            // Footer Action
            VStack {
                ModernButton(title: "MULAI KALIBRASI", action: {
                    showCalibration = true
                }, backgroundColor: Color.blue)
                
                ModernButton(title: "LAUNCH STUDIO ICC COMPANION", action: {
                    // Launch helper
                }, backgroundColor: Color(white: 0.1), foregroundColor: accentColor)
                .padding(.top, 10)
            }
            .padding(.horizontal, 40)
            .padding(.bottom, 40)
        }
        .frame(width: 550, height: 750)
        .background(Color(red: 0.03, green: 0.03, blue: 0.03))
        .preferredColorScheme(.dark)
        .fullScreenCover(isPresented: $showCalibration) {
            CalibrationOverlayView(cameraManager: cameraManager) {
                showCalibration = false
            }
        }
    }
}
