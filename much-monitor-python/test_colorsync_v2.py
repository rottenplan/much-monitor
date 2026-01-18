import ColorSync
import Quartz

def list_devices():
    def callback(device_info, context):
        print(f"Device: {device_info}")
        return True
    
    # Iterate over display devices
    # ColorSyncDeviceIterate(callback, context)
    # Actually, in PyObjC, Iterate might not be implemented or different.
    # Let's try to get main display info.
    main_display = Quartz.CGMainDisplayID()
    print(f"Main Display ID (Quartz): {main_display}")
    
if __name__ == "__main__":
    list_devices()
