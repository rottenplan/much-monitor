import SwiftUI

@main
struct MuchMonitorProApp: App {
    @StateObject private var appState = AppState()
    
    var body: some Scene {
        // 1. Main Window (Dashboard)
        WindowGroup(id: "main") {
            ContentView()
                .environmentObject(appState)
                .background(Color(red: 0.03, green: 0.03, blue: 0.03))
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentSize)
        .defaultSize(width: 500, height: 800)
        
        // 2. Calibration Window
        WindowGroup(id: "calibration") {
            CalibrationOverlayView()
                .environmentObject(appState)
        }
        .windowStyle(.hiddenTitleBar) // Or .plain if we want full immersion
        // Calibration usually needs to be flexible/fullscreen
        
        // 3. Results Window
        WindowGroup(id: "results") {
            ResultsView()
                .environmentObject(appState)
        }
        .windowResizability(.contentMinSize) // Allow resizing
    }
}
