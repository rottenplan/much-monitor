import cv2
import numpy as np
import random
import platform

try:
    import AVFoundation
    from Foundation import NSArray
    HAS_AVFOUNDATION = True
except ImportError:
    HAS_AVFOUNDATION = False

class CameraHandler:
    def __init__(self, camera_index=0, mock_mode=False):
        self.camera_index = camera_index
        self.cap = None
        self.mock_mode = mock_mode

    @staticmethod
    def list_available_cameras(max_to_check=5):
        """DEPRECATED: Use get_available_cameras_with_names instead."""
        available = []
        for i in range(max_to_check):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append(i)
                cap.release()
        return available

    @staticmethod
    def get_available_cameras_with_names():
        """Returns a list of tuples (index, name) for available cameras."""
        cameras = []
        
        # 1. First, find which indices are actually valid using OpenCV
        valid_indices = []
        # Check standard indices 0-4
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Try to read a frame to confirm it's real
                ret, _ = cap.read()
                if ret:
                    valid_indices.append(i)
                cap.release()
        
        # 2. Try to match with AVFoundation names on macOS
        if HAS_AVFOUNDATION:
            try:
                device_types = [
                    "AVCaptureDeviceTypeBuiltInWideAngleCamera",
                    "AVCaptureDeviceTypeExternalUnknown", 
                    "AVCaptureDeviceTypeContinuityCamera"
                ]
                
                # Check different API versions compatibility
                if hasattr(AVFoundation.AVCaptureDeviceDiscoverySession, 'discoverySessionWithDeviceTypes_mediaType_position_'):
                    discovery_session = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(
                        device_types,
                        AVFoundation.AVMediaTypeVideo,
                        AVFoundation.AVCaptureDevicePositionUnspecified
                    )
                    devices = discovery_session.devices()
                else:
                    # Fallback for older PyObjC versions or slightly different bindings
                    devices = [d for d in AVFoundation.AVCaptureDevice.devicesWithMediaType_(AVFoundation.AVMediaTypeVideo)]

                # Map available valid indices to device names
                # logic: The order of devices from AVFoundation often matches valid_indices 
                # but might include devices OpenCV can't open (like virtual ones).
                # We need a robust way to match. simpler here: zip them.
                
                av_count = len(devices) if devices else 0
                
                for i, idx in enumerate(valid_indices):
                    name = f"Camera {idx}" # Default
                    if i < av_count:
                        try:
                            name = devices[i].localizedName()
                        except:
                            pass
                    cameras.append((idx, name))
                    
                return cameras

            except Exception as e:
                print(f"Error fetching camera names: {e}")
        
        # Fallback if no AVFoundation or error
        for idx in valid_indices:
            cameras.append((idx, f"Camera {idx}"))
            
        return cameras

    def start(self):
        """Memulai capture kamera."""
        if self.mock_mode:
            return True
            
        if self.cap is not None:
            self.stop()
            
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            self.cap = None
            return False
            
        ret, frame = self.cap.read()
        if not ret:
            self.stop()
            return False
            
        return True

    def get_frame(self):
        if self.mock_mode:
            # Generate a random noise frame with a gray circle in the middle
            frame = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
            cv2.circle(frame, (320, 240), 100, (128, 128, 128), -1)
            return frame
            
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def get_average_color(self, region_size=100):
        """Membaca rata-rata warna di tengah frame."""
        frame = self.get_frame()
        if frame is None:
            return None
        
        height, width, _ = frame.shape
        center_x, center_y = width // 2, height // 2
        
        half_size = region_size // 2
        y1 = max(0, center_y - half_size)
        y2 = min(height, center_y + half_size)
        x1 = max(0, center_x - half_size)
        x2 = min(width, center_x + half_size)
        
        roi = frame[y1:y2, x1:x2]
        
        if roi.size == 0:
            return None
            
        avg_color_bgr = cv2.mean(roi)[:3]
        
        # In mock mode, add some jitter to simulate real camera noise
        if self.mock_mode:
            jitter = lambda: random.randint(-5, 5)
            avg_color_bgr = [max(0, min(255, c + jitter())) for c in avg_color_bgr]
            
        return (int(avg_color_bgr[2]), int(avg_color_bgr[1]), int(avg_color_bgr[0]))

    def stop(self):
        if self.cap:
            self.cap.release()
            self.cap = None

if __name__ == "__main__":
    # Test script
    print("Searching for cameras...")
    available = CameraHandler.list_available_cameras()
    print(f"Available cameras: {available}")
    
    if available:
        handler = CameraHandler(camera_index=available[0])
        if handler.start():
            print(f"Camera {available[0]} started successfully.")
            color = handler.get_average_color()
            print(f"Average color in center (RGB): {color}")
            handler.stop()
        else:
            print(f"Failed to start camera {available[0]}. check permissions.")
    else:
        print("No cameras found.")
