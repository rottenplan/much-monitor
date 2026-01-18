import SwiftUI
import AVFoundation

struct ContentView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.openWindow) var openWindow
    
    @State private var selectedCameraID: String = ""
    @State private var showAbout = false
    @State private var showCompanionAlert = false
    
    let accentColor = Color(red: 0, green: 0.82, blue: 1.0) // #00D1FF
    
    var body: some View {
        ZStack {
            // Background for the whole window
            Color(red: 0.03, green: 0.03, blue: 0.03)
                .ignoresSafeArea()
            
            // 1. DASHBOARD UI
            VStack(alignment: .leading, spacing: 25) {
                // Header
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("MUCH MONITOR")
                            .font(.system(size: 32, weight: .bold))
                            .foregroundColor(.white)
                        Text("PRO COLOR ENGINE v2.0 (NATIVE)")
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(accentColor)
                    }
                    
                    Spacer()
                    
                    Button(action: { showAbout = true }) {
                        HStack(spacing: 6) {
                            Image(systemName: "person.circle")
                            Text("ABOUT ME")
                        }
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.white.opacity(0.6))
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.white.opacity(0.05))
                        .cornerRadius(6)
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, 40)
                .padding(.top, 30)
                
                VStack(spacing: 0) {
                    Divider()
                        .background(Color.white.opacity(0.1))
                }
                .padding(.horizontal, 40)
                
                VStack(spacing: 20) {
                    // Camera Card
                    VStack(alignment: .leading, spacing: 15) {
                        Text("KAMERA SENSOR")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(.gray)
                        
                        HStack {
                            Picker("", selection: $selectedCameraID) {
                                if appState.cameraManager.availableCameras.isEmpty {
                                    Text("No cameras found").tag("")
                                } else {
                                    ForEach(appState.cameraManager.availableCameras, id: \.uniqueID) { device in
                                        Text(device.localizedName).tag(device.uniqueID)
                                    }
                                }
                            }
                            .pickerStyle(.menu)
                            .labelsHidden()
                            .onChange(of: selectedCameraID) { newValue in
                                appState.cameraManager.selectedDevice = appState.cameraManager.availableCameras.first(where: { $0.uniqueID == newValue })
                            }
                            
                            Button(action: {
                                appState.cameraManager.refreshCameras()
                            }) {
                                Image(systemName: "arrow.clockwise")
                                    .font(.system(size: 16))
                            }
                            .buttonStyle(.plain)
                        }
                        
                        Toggle("Gunakan Mock Camera (Testing)", isOn: $appState.useMock)
                            .font(.system(size: 10))
                            .foregroundColor(.gray)
                            
                            // 2. Color Space Selection
                            VStack(alignment: .leading, spacing: 6) {
                                Text("TARGET GAMUT (RUANG WARNA)")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundColor(.gray)
                                
                                Picker("", selection: $appState.colorSpace) {
                                    Text("sRGB (Standard Web/PC)").tag("sRGB")
                                    Text("Rec.709 (HD TV/Video)").tag("Rec709")
                                    Text("Adobe RGB (Print/Photo)").tag("AdobeRGB")
                                    Text("DCI-P3 (Cinema/Apple)").tag("P3")
                                }
                                .labelsHidden()
                                .pickerStyle(.menu)
                                .frame(maxWidth: .infinity)
                            }
                            
                            Divider().background(Color.white.opacity(0.1))
                            
                            // 3. Sensor Model Selection
                            VStack(alignment: .leading, spacing: 6) {
                                Text("OPTIMISASI SENSOR")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundColor(.gray)
                                
                                Picker("", selection: $appState.sensorModel) {
                                    Text("Generic / Webcam").tag("Generic")
                                    Text("iPhone 11 Series").tag("iPhone 11")
                                    Text("iPhone 12 Series").tag("iPhone 12")
                                    Text("iPhone 13 Series").tag("iPhone 13")
                                    Text("iPhone 14 Series").tag("iPhone 14")
                                    Text("iPhone 15/16 Series").tag("iPhone 15")
                                }
                                .labelsHidden()
                                .pickerStyle(.menu)
                                .frame(maxWidth: .infinity)
                            }
                            
                            Divider().background(Color.white.opacity(0.1))
                            
                            // 4. Start Button Hint
                             VStack(spacing: 6) {
                                Text("SIAP KALIBRASI?")
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundColor(.gray)
                            }
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
                                Picker("", selection: $appState.whitePoint) {
                                    Text("D65 (6500K)").tag("D65 (6500K)")
                                    Text("D50 (5000K)").tag("D50 (5000K)")
                                }
                                .labelsHidden()
                            }
                            GridRow {
                                Text("Gamma")
                                    .foregroundColor(.white.opacity(0.8))
                                Picker("", selection: $appState.gamma) {
                                    Text("2.2 (SDR)").tag("2.2 (SDR)")
                                    Text("2.4 (Video)").tag("2.4 (Video)")
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
                        .padding(.top, 5)
                    
                    // Action Dashboard
                    VStack(spacing: 12) {
                        ModernButton(title: "MULAI KALIBRASI", action: {
                            openWindow(id: "calibration")
                        }, backgroundColor: Color.blue)
                        
                        ModernButton(title: "LAUNCH STUDIO ICC COMPANION", action: {
                            launchCompanion()
                        }, backgroundColor: Color(white: 0.1), foregroundColor: accentColor)
                    }
                    .padding(.top, 10)
                }
                .padding(.horizontal, 40)
                .padding(.bottom, 30)
            }
            .frame(width: 500, height: 800)
            .fixedSize() // Enforce fixed size preventing window resizing beyond this 
        }
        .preferredColorScheme(.dark)
        .alert(isPresented: $showCompanionAlert) {
            Alert(
                title: Text("Much Monitor Control Aktif!"),
                message: Text("Menubar Companion sekarang aktif di sistem Anda. Cek bar menu bagian atas untuk akses cepat."),
                dismissButton: .default(Text("SAYA MENGERTI"))
            )
        }
        .sheet(isPresented: $showAbout) {
            AboutView()
        }
    }
    
    func launchCompanion() {
        // Find the absolute path to the python script
        // Assuming current structure: .../much-monitor/much-monitor-swift
        // Companion is at: .../much-monitor/much-monitor-python/menubar_helper.py
        
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3")
        
        // We need the parent path
        let currentPath = FileManager.default.currentDirectoryPath
        let parentPath = (currentPath as NSString).deletingLastPathComponent
        let scriptPath = (parentPath as NSString).appendingPathComponent("much-monitor-python/menubar_app.py")
        
        process.arguments = [scriptPath]
        
        do {
            try process.run()
            self.showCompanionAlert = true
        } catch {
            print("Failed to launch companion: \(error)")
        }
    }
    
    func toggleCalibrationMode(_ enable: Bool) {
        guard let window = NSApp.windows.first(where: { $0.isVisible && ($0.isKeyWindow || $0.isMainWindow || $0.className.contains("Window")) })
            ?? NSApp.mainWindow
            ?? NSApp.windows.first else { return }
        
        if enable {
            // 1. Float on Top (Level changed to Floating)
            window.level = .floating
            
            // 2. Go Full Screen
            if !window.styleMask.contains(.fullScreen) {
                window.toggleFullScreen(nil)
            }
            
            // 3. Keep screen from sleeping
            // (Optional: can add PowerSource code here if needed)
        } else {
            // 1. Return to Normal Level
            window.level = .normal
            
            // 2. Exit Full Screen
            if window.styleMask.contains(.fullScreen) {
                window.toggleFullScreen(nil)
            }
        }
    }
}

struct AboutView: View {
    @Environment(\.dismiss) var dismiss
    let accentColor = Color(red: 0, green: 0.82, blue: 1.0)
    
    var body: some View {
        VStack(spacing: 25) {
            HStack {
                Spacer()
                Button(action: { dismiss() }) {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 20))
                        .foregroundColor(.gray)
                }
                .buttonStyle(.plain)
            }
            .padding(.top, 20)
            .padding(.horizontal, 20)
            
            Image(systemName: "cpu.fill")
                .font(.system(size: 60))
                .foregroundColor(accentColor)
                .padding(.bottom, 10)
            
            VStack(spacing: 8) {
                Text("MUCH MONITOR PRO")
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(.white)
                Text("Version 2.0.0 (Native Build)")
                    .font(.system(size: 12))
                    .foregroundColor(.gray)
            }
            
            VStack(spacing: 15) {
                Text("Dibuat dengan ❤️ untuk komunitas kreatif dan profesional warna. Aplikasi ini dirancang untuk memberikan akurasi warna level studio menggunakan sensor kamera native.")
                    .font(.system(size: 13))
                    .foregroundColor(.gray)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 40)
                
                Divider()
                    .background(Color.white.opacity(0.1))
                    .padding(.horizontal, 60)
                
                VStack(spacing: 5) {
                    Text("DEVELOPED BY")
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(accentColor)
                    Text("Muchdas")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(.white)
                }
            }
            
            Spacer()
            
            Text("© 2024 Much Monitor Project. All rights reserved.")
                .font(.system(size: 9))
                .foregroundColor(.white.opacity(0.3))
                .padding(.bottom, 20)
        }
        .frame(width: 400, height: 500)
        .background(Color(red: 0.05, green: 0.05, blue: 0.05))
        .preferredColorScheme(.dark)
    }
}
