import ColorSync
from AppKit import NSScreen
from Foundation import NSURL
import os

def set_profile_native(profile_path):
    # 1. Get Main Screen
    main_screen = NSScreen.mainScreen()
    if not main_screen:
        print("No main screen found")
        return False
    
    # 2. Get Display UUID (This is what ColorSync expects)
    device_desc = main_screen.deviceDescription()
    # "NSDeviceUUID" is often available in deviceDescription for displays
    display_uuid = str(device_desc.get("NSScreenNumber", ""))
    
    # Let's try to get the actual UUID string if available
    # In recent macOS, NSScreen doesn't directly expose the UUID easily with one key.
    # However, ColorSyncDeviceIterate is the "proper" way.
    
    print(f"Targeting Screen Number: {display_uuid}")
    
    profile_url = NSURL.fileURLWithPath_(profile_path)
    
    # Define the dictionary of profiles to set
    # Key should be kColorSyncDeviceDefaultProfileID
    # Value should be the profile URL
    profile_dict = {
        ColorSync.kColorSyncDeviceDefaultProfileID: profile_url
    }
    
    try:
        # deviceClass for displays is kColorSyncDisplayDeviceClass ("cmdisp")
        success = ColorSync.ColorSyncDeviceSetCustomProfiles(
            ColorSync.kColorSyncDisplayDeviceClass,
            display_uuid,
            profile_dict
        )
        print(f"Native Application Success: {success}")
        return success
    except Exception as e:
        print(f"ColorSync Error: {e}")
        return False

if __name__ == "__main__":
    p = "/Users/muchdas/Library/ColorSync/Profiles/MuchCalibrated_Profile.icc"
    if os.path.exists(p):
        set_profile_native(p)
    else:
        print(f"Profile not found: {p}")
