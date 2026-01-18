import os
import shutil
import Quartz
from Foundation import NSURL

class ProfileManager:
    @staticmethod
    def get_user_profiles_dir():
        """Returns the user ColorSync profiles directory."""
        path = os.path.expanduser("~/Library/ColorSync/Profiles")
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @staticmethod
    def install_profile(src_path, profile_name=None):
        """Copies an ICC profile to the user profiles directory."""
        if not os.path.exists(src_path):
            print(f"Source profile not found: {src_path}")
            return None
        
        dest_dir = ProfileManager.get_user_profiles_dir()
        if not profile_name:
            profile_name = os.path.basename(src_path)
            
        dest_path = os.path.join(dest_dir, profile_name)
        
        try:
            shutil.copy2(src_path, dest_path)
            print(f"Profile installed to: {dest_path}")
            return dest_path
        except Exception as e:
            print(f"Failed to install profile: {e}")
            return None

    @staticmethod
    def set_display_profile(display_id, profile_path):
        """
        Sets the color profile for a specific display.
        Tries Quartz first, then falls back to AppleScript.
        """
        import Cocoa
        profile_name = os.path.basename(profile_path).replace(".icc", "").replace(".icm", "")
        
        try:
            # Step 1: Quartz Attempt (Fast, but sometimes blocked)
            data = Cocoa.NSData.dataWithContentsOfFile_(profile_path)
            if data:
                color_space = Quartz.CGColorSpaceCreateWithICCProfile(data)
                if color_space:
                    if display_id is None: display_id = Quartz.CGMainDisplayID()
                    status = Quartz.CGDisplaySetColorSpace(display_id, color_space)
                    if status == 0:
                        print(f"Quartz: Successfully applied {profile_name}")
                        # Even if Quartz works, we return True but might still need AppleScript for System Settings persistence
                        return True

            # Step 2: AppleScript Fallback (Reliable for System Settings)
            print("Quartz failed or was bypassed. Trying AppleScript fallback...")
            return ProfileManager.set_display_profile_applescript(profile_name)
                
        except Exception as e:
            print(f"Exception in set_display_profile: {e}")
            return ProfileManager.set_display_profile_applescript(profile_name)

    @staticmethod
    def set_display_profile_applescript(profile_name):
        """Uses AppleScript to set the display profile via System Settings (Ventura+)."""
        import subprocess
        
        # This script tries multiple potential UI paths for Ventura/Sonoma
        script = f'''
        set profileName to "{profile_name}"
        
        tell application "System Settings"
            activate
            -- Open Displays pane
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
                    click menu item profileName of menu 1 of popUp
                    return "Success"
                on error err
                    try
                        -- Fallback: Search for pop up button by description or name
                        set allPopUps to every pop up button of (every group of scroll area 1 of group 1 of group 2 of splitter group 1 of group 1 of window 1)
                        -- This is more complex, let's just try to click the one that looks like a profile picker
                        return "Alternative path needed: " & err
                    on error
                        return "Failed: " & err
                    end try
                end error
            end tell
        end tell
        '''
        
        try:
            print(f"Attempting to set profile to '{profile_name}' via System Settings (Ventura)...")
            # We first try to just open it to give user a chance
            subprocess.run(["open", "x-apple.systempreferences:com.apple.Displays-Settings.extension"])
            
            # Then we run the script to perform the click
            # We use osascript to run the above
            full_cmd = ["osascript", "-e", script]
            result = subprocess.run(full_cmd, capture_output=True, text=True)
            print(f"AppleScript Result: {result.stdout.strip()}")
            
            if "Success" in result.stdout:
                return True
                
            # If script failed, the settings window is at least open now.
            return False
        except Exception as e:
            print(f"Error in AppleScript execution: {e}")
            return False

    @staticmethod
    def get_main_display_id():
        """Returns the ID of the primary display."""
        return Quartz.CGMainDisplayID()

    @staticmethod
    def list_installed_profiles():
        """Lists all ICC profiles in the user's Profile directory."""
        profile_dir = ProfileManager.get_user_profiles_dir()
        profiles = []
        if os.path.exists(profile_dir):
            for f in os.listdir(profile_dir):
                if f.lower().endswith(('.icc', '.icm')):
                    profiles.append(os.path.join(profile_dir, f))
        return profiles
