import Quartz
import ctypes
import ctypes.util

# Load CoreGraphics and IOKit
cg = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreGraphics"))
iokit = ctypes.cdll.LoadLibrary(ctypes.util.find_library("IOKit"))

def get_display_uuid(display_id):
    # CGDisplayCreateUUIDFromDisplayID is a C function returning a CFUUIDRef
    # But we can try to get it from IOKit
    # Actually, let's try to get it from the display name or just use 'main'
    return None

def set_profile_with_colorsync(profile_path):
    import ColorSync
    from Foundation import NSURL
    
    # On some systems, the deviceID for displays in ColorSync is just "display/0" (for main)
    # or "display/1", etc.
    ids_to_try = ["display/0", "0", "1", "352964680", "MainDisplay"]
    
    profile_url = NSURL.fileURLWithPath_(profile_path)
    profile_info = {ColorSync.kColorSyncDeviceDefaultProfileID: profile_url}
    
    for device_id in ids_to_try:
        try:
            success = ColorSync.ColorSyncDeviceSetCustomProfiles(
                ColorSync.kColorSyncDisplayDeviceClass,
                device_id,
                profile_info
            )
            if success:
                print(f"SUCCESS with DeviceID: {device_id}")
                return True
        except:
            pass
    
    print("Failed with all common IDs")
    return False

if __name__ == "__main__":
    p = "/Users/muchdas/Library/ColorSync/Profiles/MuchCalibrated_Profile.icc"
    set_profile_with_colorsync(p)
