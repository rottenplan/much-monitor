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
                    "AVCaptureDeviceTypeContinuityCamera",
                    "AVCaptureDeviceTypeBuiltInUltraWideCamera",
                    "AVCaptureDeviceTypeDeskViewCamera"
                ]
                
                # Check different API versions compatibility
                devices = []
                if hasattr(AVFoundation.AVCaptureDeviceDiscoverySession, 'discoverySessionWithDeviceTypes_mediaType_position_'):
                    discovery_session = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(
                        device_types,
                        AVFoundation.AVMediaTypeVideo,
                        AVFoundation.AVCaptureDevicePositionUnspecified
                    )
                    devices = list(discovery_session.devices())
                
                # Fallback to legacy if list is empty
                if not devices:
                    devices = list(AVFoundation.AVCaptureDevice.devicesWithMediaType_(AVFoundation.AVMediaTypeVideo))

                # PRIORITIZATION FIX:
                # We want iPhone/Continuity cameras to be at the very top (Index 0).
                # Priority: 0 (iPhone/Continuity), 1 (Other External), 2 (Built-in)
                def device_priority(d):
                    name = d.localizedName().lower()
                    dtype = d.deviceType().lower()
                    if "iphone" in name or "continuity" in dtype:
                        return 0
                    if "builtin" in dtype:
                        return 2
                    return 1
                
                devices = sorted(devices, key=device_priority)

                # Directly map index -> device name
                for i, dev in enumerate(devices):
                    try:
                        name = dev.localizedName()
                        dtype = str(dev.deviceType())
                        
                        # STRICT FILTER: Exclude Virtual/Digital Software Cameras
                        # We only want real physical lenses.
                        virtual_keywords = ["desk view", "virtual", "software", "obs", "snap", "logi plus", "zoom"]
                        if any(kw in name.lower() for kw in virtual_keywords):
                            print(f"DEBUG: Skipping Virtual Camera -> {name}")
                            continue
                            
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
            
        print(f"--- Memulai Kamera (Index: {self.camera_index}) ---")
        
        # Enforce AVFoundation on macOS for better compatibility with iPhone
        force_backend = cv2.CAP_ANY
        if platform.system() == "Darwin":
            print("MacOS: Menggunakan backend AVFoundation.")
            force_backend = cv2.CAP_AVFOUNDATION
            
        self.cap = cv2.VideoCapture(self.camera_index, force_backend)
        
        if not self.cap.isOpened():
            print(f"ERROR: Gagal membuka kamera pada index {self.camera_index}")
            self.cap = None
            return False
            
        # Tips: Beberapa kamera iPhone butuh waktu sebelum kita set resolusi
        print("Kamera terbuka. Menunggu frame awal sebelum set resolusi...")
        
        warmup_success = False
        for i in range(20):
            ret, frame = self.cap.read()
            if ret:
                print(f"Frame awal didapat pada percobaan ke-{i+1}")
                warmup_success = True
                break
            time.sleep(0.1)

        # Set resolusi ke HD (Opsional, jika gagal tetap lanjut)
        current_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        current_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Resolusi saat ini: {current_w}x{current_h}")
        
        if current_w != 1920 or current_h != 1080:
            print("Mencoba set resolusi ke HD (1920x1080)...")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            
            # Cek apakah resolusi berubah atau masih bisa baca frame
            ret, frame = self.cap.read()
            if not ret:
                print("Peringatan: Gagal baca frame setelah set HD. Menggunakan pengaturan default.")
                # Re-open if catastrophic failure on resolution change
                self.cap.release()
                self.cap = cv2.VideoCapture(self.camera_index, force_backend)
                warmup_success = self.cap.isOpened()
        
        print("Kamera siap.")
        return warmup_success

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
