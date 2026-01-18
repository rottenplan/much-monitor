import cv2
import numpy as np
import random
import platform
import time

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
        
        # Optimize: On macOS with AVFoundation, trust the system list
        # This prevents opening every camera (which causes errors/delays)
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
                    devices = [d for d in AVFoundation.AVCaptureDevice.devicesWithMediaType_(AVFoundation.AVMediaTypeVideo)]

                # SORTING FIX:
                # OpenCV (driver) tends to put External cameras (Continuity/USB) at Index 0, and Built-in at Index 1+
                # AVFoundation (OS) puts Built-in at Index 0.
                # To match OpenCV, we sort the OS list so External cameras come first.
                # "AVCaptureDeviceTypeBuiltInWideAngleCamera" will be pushed to the end.
                devices = sorted(devices, key=lambda d: 1 if "BuiltIn" in d.deviceType() else 0)

                # Directly map index -> device name
                for i, dev in enumerate(devices):
                    try:
                        name = dev.localizedName()
                        cameras.append((i, name))
                    except:
                        cameras.append((i, f"Camera {i}"))
                    
                return cameras

            except Exception as e:
                print(f"Error fetching camera names: {e}")
                # Fall through to OpenCV scan if this fails

        # Fallback: OpenCV validity check (slower, aggressive)
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Try to read a frame to confirm it's real
                ret, _ = cap.read()
                if ret:
                    cameras.append((i, f"Camera {i}"))
                cap.release()
            
        return cameras

    def start(self):
        """Memulai capture kamera."""
        if self.mock_mode:
            return True
            
        if self.cap is not None:
            self.stop()
            
        print(f"Attempting to start camera index {self.camera_index}...")
        
        # Enforce AVFoundation on macOS for better compatibility with iPhone
        force_backend = cv2.CAP_ANY
        if platform.system() == "Darwin":
            print("MacOS detected: Forcing AVFoundation backend.")
            force_backend = cv2.CAP_AVFOUNDATION
            
        self.cap = cv2.VideoCapture(self.camera_index, force_backend)
        
        if not self.cap.isOpened():
            print(f"Failed to open camera {self.camera_index}")
            self.cap = None
            return False
            
        # Set resolution to HD to force camera wake-up/mode switch
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        # Try to disable Auto Exposure for accurate color/gamma readings
        # Note: many macOS cameras ignore this, but it's worth a try.
        try:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25) # 0.25 (1 in some versions) = Manual
            # self.cap.set(cv2.CAP_PROP_EXPOSURE, -5) # Adjust if needed
        except:
            pass
        
        print("Camera opened. Warming up...")
            
        # Warmup loop: Continuity Camera and some webcams take time to send the first frame.
        # Try for up to 3 seconds (30 attempts * 0.1s)
        for i in range(30):
            ret, frame = self.cap.read()
            if ret:
                print(f"Frame received on attempt {i+1}")
                return True
            time.sleep(0.1)
            
        # If we get here, we failed to get a frame after waiting
        print("Failed to get first frame after warmup.")
        self.stop()
        return False

    def get_frame(self):
        if self.mock_mode:
            # Generate a random noise frame with a gray circle in the middle
            frame = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
            cv2.circle(frame, (320, 240), 100, (128, 128, 128), -1)
            return frame
            
        if self.cap is None:
            # Attempt to restart if cap is missing but we are supposed to be running
            if not self.start():
                return None

        ret, frame = self.cap.read()
        
        # Auto-reconnect logic
        if not ret:
            print("Frame lost. Attempting to reconnect...")
            # Try to release and restart a few times
            for attempt in range(3):
                self.stop()
                time.sleep(0.5) # Wait a bit before reconnecting
                if self.start():
                    print(f"Reconnected on attempt {attempt+1}")
                    ret, frame = self.cap.read()
                    if ret:
                        return frame
            
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
