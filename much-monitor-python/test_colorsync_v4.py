import ColorSync
import objc

def list_all_colorsync_devices():
    devices = []
    
    # The callback for ColorSyncDeviceIterate
    def device_callback(device_info, context):
        devices.append(device_info)
        return True
    
    # We need to create a block or a C-style callback for PyObjC
    # ColorSyncDeviceIterate(ColorSyncDeviceIterateCallback callback, void* userInfo)
    try:
        # Note: In some PyObjC versions, Iterate might be difficult to call directly.
        # Let's try to get all devices using a different way if Iterate fails.
        print("Iterating devices...")
        # Since I don't have the exact signature for the callback in PyObjC handy,
        # I'll try to find the device ID by iterating NSScreens and checking their UUIDs from Quartz.
        pass
    except Exception as e:
        print(f"Iterate Error: {e}")
    
    import Quartz
    import AppKit
    
    for screen in AppKit.NSScreen.screens():
        desc = screen.deviceDescription()
        screen_number = desc["NSScreenNumber"]
        uuid_ptr = Quartz.CGDisplayCreateUUIDFromDisplayID(screen_number)
        if uuid_ptr:
            uuid_str = str(Quartz.CFUUIDCreateString(None, uuid_ptr))
            print(f"Screen {screen_number} -> UUID: {uuid_str}")
        else:
            print(f"Screen {screen_number} -> No UUID")

if __name__ == "__main__":
    list_all_colorsync_devices()
