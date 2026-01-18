import SwiftUI

@main
struct MuchMonitorProApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 550, minHeight: 700)
                .background(Color(red: 0.03, green: 0.03, blue: 0.03)) // Obsidian Black
        }
        .windowStyle(.hiddenTitleBar)
    }
}
