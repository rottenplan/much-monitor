import ColorSync
import objc

def test_iterate():
    print(f"Device Class: {ColorSync.kColorSyncDisplayDeviceClass}")
    
    # Let's try to get info for device "display/0" which is common for main display
    info = ColorSync.ColorSyncDeviceCopyDeviceInfo(ColorSync.kColorSyncDisplayDeviceClass, "display/0")
    print(f"Info for display/0: {info}")
    
    # Try with index 0
    info = ColorSync.ColorSyncDeviceCopyDeviceInfo(ColorSync.kColorSyncDisplayDeviceClass, "0")
    print(f"Info for 0: {info}")

if __name__ == "__main__":
    test_iterate()
