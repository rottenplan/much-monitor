import SwiftUI
import AppKit

struct ScoreCard: View {
    let title: String
    let value: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 8) {
            Text(title)
                .font(.system(size: 9, weight: .bold))
                .foregroundColor(.gray)
            Text(value)
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(color)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
        .background(Color(white: 0.1))
        .cornerRadius(10)
    }
}

struct ResultsView: View {
    @EnvironmentObject var appState: AppState
    @Environment(\.dismiss) var dismiss
    
    // Derived from AppState
    private var metrics: [String: Any]? { appState.latestMetrics }
    private var wpTarget: String { appState.whitePoint }
    private var gammaTarget: String { appState.gamma }
    
    @State private var profileName: String = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd_HHmm"
        return "MuchMonitor_\(formatter.string(from: Date()))"
    }()
    @State private var saveDirectory: URL = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Documents")
    @State private var showSuccessAlert = false
    @State private var successMessage = ""
    
    let accentColor = Color(red: 0, green: 0.82, blue: 1.0)
    
    var body: some View {
        VStack(spacing: 0) {
            // Navigation Header
            HStack {
                Button(action: { dismiss() }) {
                    HStack(spacing: 5) {
                        Image(systemName: "chevron.left")
                        Text("BACK")
                    }
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(.gray)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(Color(white: 0.1))
                    .cornerRadius(8)
                }
                .buttonStyle(.plain)
                
                Spacer()
            }
            .padding(.top, 25)
            .padding(.horizontal, 35)

            // Scrollable Content for better resizing support
            ScrollView {
                VStack(spacing: 25) {
                    // Header
                    VStack(spacing: 8) {
                        Text("ANALYSIS COMPLETE")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(accentColor)
                        
                        let grade = (metrics?["grade"] as? String) ?? "GRADE A"
                        let isInvalid = grade == "INVALID" || grade == "ERROR"
                        
                        Text(grade)
                            .font(.system(size: 32, weight: .bold))
                            .foregroundColor(isInvalid ? .red : .white)
                    }
                    
                    // Target Info Badge
                    VStack(spacing: 4) {
                        Text("TARGET: \(wpTarget)  •  GAMMA \(gammaTarget)")
                            .font(.system(size: 9, weight: .bold))
                            .foregroundColor(.gray)
                        
                        if let sensor = metrics?["sensor_model"] as? String {
                            Text("SENSOR: \(sensor)")
                                .font(.system(size: 8, weight: .bold))
                                .foregroundColor(accentColor.opacity(0.7))
                        }
                        
                        if let cs = metrics?["color_space"] as? String {
                             Text("GAMUT: \(cs)")
                                .font(.system(size: 8, weight: .bold))
                                .foregroundColor(.white.opacity(0.6))
                        }
                    }
                    .padding(.horizontal, 15)
                    .padding(.vertical, 8)
                    .background(Color(white: 0.15))
                    .cornerRadius(5)
                    
                    // Score Row
                    HStack(spacing: 15) {
                        let avgDE = metrics?["avg_corrected"] as? Double ?? 0.0
                        let maxDE = metrics?["max_de"] as? Double ?? 0.0
                        let gamma = metrics?["detected_gamma"] as? Double ?? 2.2
                        
                        let avgColor = avgDE < 1.0 ? Color.green : (avgDE < 2.0 ? Color.blue : Color.orange)
                        ScoreCard(title: "AVERAGE dE00", value: String(format: "%.2f", avgDE), color: avgColor)
                        
                        let maxColor = maxDE < 3.0 ? Color.blue : Color.orange
                        ScoreCard(title: "MAXIMUM dE00", value: String(format: "%.2f", maxDE), color: maxColor)
                        
                        ScoreCard(title: "DETECTED GAMMA", value: String(format: "%.2f", gamma), color: .white)
                    }
                    
                    // Description
                    let description = (metrics?["description"] as? String) ?? "Your monitor is now calibrated to industry standards. Color accuracy has been significantly improved."
                    let isError = description.contains("ERROR") || description.contains("Failed")
                    
                    Text(description)
                        .font(.system(size: 12))
                        .foregroundColor(isError ? .red : .gray)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 20)
                    
                    // Save Location Section
                    VStack(alignment: .leading, spacing: 12) {
                        Text("SAVE SETTINGS")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(.gray)
                        
                        VStack(spacing: 10) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Profile Name")
                                    .font(.system(size: 9, weight: .bold))
                                    .foregroundColor(.gray)
                                TextField("", text: $profileName)
                                    .textFieldStyle(.plain)
                                    .padding(8)
                                    .background(Color(white: 0.12))
                                    .cornerRadius(6)
                            }
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Location")
                                    .font(.system(size: 9, weight: .bold))
                                    .foregroundColor(.gray)
                                HStack {
                                    Text(saveDirectory.path)
                                        .font(.system(size: 9))
                                        .foregroundColor(.white.opacity(0.6))
                                        .lineLimit(1)
                                        .truncationMode(.middle)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                        .padding(8)
                                        .background(Color(white: 0.12))
                                        .cornerRadius(6)
                                    
                                    Button("Choose...") {
                                        selectFolder()
                                    }
                                    .font(.system(size: 10, weight: .bold))
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(Color(white: 0.15))
                                    .cornerRadius(6)
                                    .buttonStyle(.plain)
                                }
                            }
                        }
                        .padding(15)
                        .background(Color(white: 0.08))
                        .cornerRadius(10)
                    }
                    
                    // Action Buttons
                    VStack(spacing: 12) {
                        HStack(spacing: 12) {
                            ModernButton(title: "SAVE PROFILE (.ICC)", action: {
                                saveProfile()
                            }, backgroundColor: accentColor, foregroundColor: .black)
                            
                            ModernButton(title: "AUTO APPLY", action: {
                                installAndApply()
                            }, backgroundColor: Color.green, foregroundColor: .black)
                        }
                        
                        if let csv = metrics?["csv_log"] as? String {
                            Button("EXPORT RAW DATA (.CSV)") {
                                exportData(csv: csv)
                            }
                            .font(.system(size: 11, weight: .bold))
                            .padding(10)
                            .background(Color(white: 0.2))
                            .foregroundColor(.white)
                            .cornerRadius(8)
                            .buttonStyle(.plain)
                        }
                        
                        Button("BACK TO MAIN MENU (CLOSE)") {
                            dismiss()
                        }
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(.gray)
                        .padding(.top, 5)
                        .buttonStyle(.plain)
                    }
                }
                .padding(.top, 15)
                .padding(.horizontal, 35)
                .padding(.bottom, 35)
            }
        }

        .frame(width: 500, height: 750) // Fixed Frame
        .fixedSize()
        .background(Color(red: 0.03, green: 0.03, blue: 0.03))
        .preferredColorScheme(.dark)
        .alert(isPresented: $showSuccessAlert) {
            Alert(title: Text("Success"), message: Text(successMessage), dismissButton: .default(Text("OK")))
        }
    }
    
    private func selectFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        
        if panel.runModal() == .OK {
            if let url = panel.url {
                self.saveDirectory = url
            }
        }
    }
    
    private func saveProfile() {
        let fileName = "\(profileName).icc"
        let fileURL = saveDirectory.appendingPathComponent(fileName)
        
        // Ensure directory exists
        try? FileManager.default.createDirectory(at: saveDirectory, withIntermediateDirectories: true)
        
        let generator = SimpleICC(description: profileName)
        // Extract gamma value from string "2.2 (SDR)"
        if let gammaVal = Double(gammaTarget.split(separator: " ").first ?? "2.2") {
            generator.gamma = gammaVal
        }
        
        if generator.createProfile(url: fileURL) {
            successMessage = "ICC Pro Profile saved to:\n\(fileURL.path)"
            showSuccessAlert = true
        }
    }
    
    private func installAndApply() {
        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent("temp_monitor_profile.icc")
        let generator = SimpleICC(description: profileName)
        if let gammaVal = Double(gammaTarget.split(separator: " ").first ?? "2.2") {
            generator.gamma = gammaVal
        }
        
        if generator.createProfile(url: tempURL) {
            if let installedURL = ProfileManager.shared.installProfile(srcURL: tempURL, name: "\(profileName).icc") {
                _ = ProfileManager.shared.setDisplayProfile(profileURL: installedURL)
                successMessage = "Profile INSTALLED and APPLIED to your display!"
                showSuccessAlert = true
            }
        }
    }

    private func exportData(csv: String) {
        let fileName = "\(profileName)_Log.csv"
        let fileURL = saveDirectory.appendingPathComponent(fileName)
        
        do {
            try csv.write(to: fileURL, atomically: true, encoding: .utf8)
            successMessage = "CSV Log exported to:\n\(fileURL.path)"
            showSuccessAlert = true
            
            // Open folder
            NSWorkspace.shared.selectFile(fileURL.path, inFileViewerRootedAtPath: fileURL.deletingLastPathComponent().path)
        } catch {
            successMessage = "Failed to export CSV: \(error.localizedDescription)"
            showSuccessAlert = true
        }
    }
}
