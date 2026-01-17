import AVFoundation
from Foundation import NSArray

def list_av_devices():
    print("Listing all AVCaptureDevices...")
    # Use strings if attributes are missing in this PyObjC version
    device_types = [
        "AVCaptureDeviceTypeBuiltInWideAngleCamera",
        "AVCaptureDeviceTypeExternalUnknown",
        "AVCaptureDeviceTypeContinuityCamera"
    ]
    
    discovery_session = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(
        device_types,
        AVFoundation.AVMediaTypeVideo,
        AVFoundation.AVCaptureDevicePositionUnspecified
    )
    
    devices = discovery_session.devices()
    if not devices:
        print("No devices found via DiscoverySession.")
    else:
        for device in devices:
            print(f"Device: {device.localizedName()}")
            print(f"  ID: {device.uniqueID()}")
            print(f"  Model ID: {device.modelID()}")
            print(f"  Is Connected: {device.isConnected()}")
            print(f"  Is Suspended: {device.isSuspended()}")
            print("-" * 20)

if __name__ == "__main__":
    list_av_devices()
