import cv2
import AVFoundation

def list_avfoundation_devices():
    print("--- AVFoundation Devices ---")
    # Comprehensive list of video device types
    device_types = [
        "AVCaptureDeviceTypeBuiltInWideAngleCamera",
        "AVCaptureDeviceTypeExternalUnknown", 
        "AVCaptureDeviceTypeContinuityCamera",
        "AVCaptureDeviceTypeBuiltInUltraWideCamera",
        "AVCaptureDeviceTypeDeskViewCamera",
        "AVCaptureDeviceTypeDiscoverySession"
    ]
    
    try:
        discovery_session = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(
            device_types,
            AVFoundation.AVMediaTypeVideo,
            AVFoundation.AVCaptureDevicePositionUnspecified
        )
        devices = discovery_session.devices()
        if not devices:
            print("No devices found via DiscoverySession. Trying legacy method...")
            devices = AVFoundation.AVCaptureDevice.devicesWithMediaType_(AVFoundation.AVMediaTypeVideo)
    except Exception as e:
        print(f"Error using DiscoverySession: {e}")
        devices = AVFoundation.AVCaptureDevice.devicesWithMediaType_(AVFoundation.AVMediaTypeVideo)

    for i, dev in enumerate(devices):
        print(f"Index {i}: {dev.localizedName()} (Type: {dev.deviceType()}, ID: {dev.uniqueID()})")
    return devices

def list_opencv_indices():
    print("\n--- OpenCV Valid Indices ---")
    for i in range(5):
        print(f"Checking Index {i}...")
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
             # Warmup
            frame_found = False
            for attempt in range(20):
                ret, _ = cap.read()
                if ret:
                    frame_found = True
                    break
                import time
                time.sleep(0.1)
                
            if frame_found:
                print(f"Index {i}: OPENED AND ACTIVE")
                # Try to get some property?
                w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                print(f"  Resolution: {w}x{h}")
            else:
                print(f"Index {i}: Opened but failed to capture frames (Timeout)")
            cap.release()
        else:
            print(f"Index {i}: Failed to open")

if __name__ == "__main__":
    list_avfoundation_devices()
    list_opencv_indices()
