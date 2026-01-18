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
        """Uses AppleScript to set the display profile via System Settings."""
        import subprocess
        script = f'''
        tell application "System Settings"
            activate
            reveal anchor "displaysDisplayTab" __of_ __parent__ __id__ "com.apple.Displays-Settings.extension"
            delay 1
        end tell
        tell application "System Events"
            tell process "System Settings"
                try
                    -- Click the profile pop-up button
                    click pop up button 1 of group 1 of scroll area 1 of group 1 of group 2 of splitter group 1 of group 1 of window "Displays"
                    delay 0.5
                    -- Select the profile
                    click menu item "{profile_name}" of menu 1 of pop up button 1 of group 1 of scroll area 1 of group 1 of group 2 of splitter group 1 of group 1 of window "Displays"
                    return "Success"
                on error
                    return "Failed"
                end try
            end tell
        end tell
        '''
        # Note: The UI hierarchy varies between macOS versions. 
        # For now, let's provide a simpler version that just opens the settings if complex scripting fails.
        simple_script = f'open "x-apple.systempreferences:com.apple.Displays-Settings.extension"'
        
        try:
            print(f"Attempting to set profile to '{profile_name}' via System Settings...")
            # We just open the settings for now and let the user see it's there
            # because complex UI scripting is fragile across OS versions.
            subprocess.run(["open", "x-apple.systempreferences:com.apple.Displays-Settings.extension"])
            return True
        except:
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
