import ColorSync
import Quartz
from Foundation import NSURL
import os

def test_set_profile(profile_path):
    # 1. Get Main Display ID
    display_id = Quartz.CGMainDisplayID()
    
    # 2. Get the ColorSync Device UUID for this display
    # On macOS, display device IDs for ColorSync are often formatted as "display/0" or using the UUID
    display_uuid_ptr = Quartz.CGDisplayCreateUUIDFromDisplayID(display_id)
    if not display_uuid_ptr:
        print("Failed to get display UUID")
        return False
    
    display_uuid = str(Quartz.CFUUIDCreateString(None, display_uuid_ptr))
    # Actually, for displays, the device class is kColorSyncDisplayDeviceClass
    # and the device ID is often just a string.
    
    print(f"Main Display UUID: {display_uuid}")
    
    # 3. Create Profile URL
    profile_url = NSURL.fileURLWithPath_(profile_path)
    
    # 4. Set Profile
    # kColorSyncDisplayDeviceClass = "cmdisp"
    # kColorSyncDeviceDefaultProfileID = "default"
    
    device_id = {"DeviceClass": ColorSync.kColorSyncDisplayDeviceClass, "DeviceID": display_uuid}
    profile_info = {ColorSync.kColorSyncDeviceDefaultProfileID: profile_url}
    
    try:
        success = ColorSync.ColorSyncDeviceSetCustomProfiles(ColorSync.kColorSyncDisplayDeviceClass, display_uuid, profile_info)
        print(f"Success: {success}")
        return success
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    p = "/Users/muchdas/Library/ColorSync/Profiles/MuchCalibrated_Profile.icc"
    if os.path.exists(p):
        test_set_profile(p)
    else:
        print(f"Profile not found: {p}")
