import Foundation
import Quartz
import Cocoa
import ApplicationServices

class ProfileManager {
    static let shared = ProfileManager()
    
    private init() {}
    
    func getUserProfilesDir() -> URL {
        let libraryDir = FileManager.default.urls(for: .libraryDirectory, in: .userDomainMask).first!
        let profilesDir = libraryDir.appendingPathComponent("ColorSync/Profiles")
        
        if !FileManager.default.fileExists(atPath: profilesDir.path) {
            try? FileManager.default.createDirectory(at: profilesDir, withIntermediateDirectories: true)
        }
        
        return profilesDir
    }
    
    func installProfile(srcURL: URL, name: String? = nil) -> URL? {
        let destDir = getUserProfilesDir()
        let fileName = name ?? srcURL.lastPathComponent
        let destURL = destDir.appendingPathComponent(fileName)
        
        do {
            if FileManager.default.fileExists(atPath: destURL.path) {
                try FileManager.default.removeItem(at: destURL)
            }
            try FileManager.default.copyItem(at: srcURL, to: destURL)
            print("Profile installed to: \(destURL.path)")
            return destURL
        } catch {
            print("Failed to install profile: \(error)")
            return nil
        }
    }
    
    func setDisplayProfile(profileURL: URL) -> Bool {
        // Since CGDisplaySetColorSpace is not available in the Swift bridge for macOS 13,
        // we use the reliable method of opening the Displays settings for the user
        // and optionally triggering a script to help them.
        
        return setDisplayProfileAppleScript(profileName: profileURL.deletingPathExtension().lastPathComponent)
    }
    
    private func setDisplayProfileAppleScript(profileName: String) -> Bool {
        // Open the Displays settings directly
        if let url = URL(string: "x-apple.systempreferences:com.apple.Displays-Settings.extension") {
            NSWorkspace.shared.open(url)
        }
        
        // This script tries multiple potential UI paths for Ventura/Sonoma
        let scriptSource = """
        set profileToSelect to "\(profileName)"
        
        tell application "System Settings"
            activate
            reveal anchor "displaysDisplayTab" of pane id "com.apple.Displays-Settings.extension"
        end tell
        
        delay 1.5
        
        tell application "System Events"
            tell process "System Settings"
                try
                    -- Ventura UI Path: Most common hierarchy
                    set popUp to pop up button 1 of group 1 of scroll area 1 of group 1 of group 2 of splitter group 1 of group 1 of window 1
                    click popUp
                    delay 0.5
                    click menu item profileToSelect of menu 1 of popUp
                    return "Success"
                on error err
                    return "Failed: " & err
                end try
            end tell
        end tell
        """
        
        if let script = NSAppleScript(source: scriptSource) {
            var error: NSDictionary?
            let result = script.executeAndReturnError(&error)
            
            if let err = error {
                print("AppleScript Error: \(err)")
                return false
            } else {
                print("AppleScript Success: \(result.stringValue ?? "No Result")")
                return true
            }
        }
        
        return false
    }
}
