import cv2
import time
import platform

def test_camera_backends():
    print(f"Sistem Operasi: {platform.system()}")
    print("Mencoba berbagai konfigurasi untuk membuka kamera...")
    
    # Kumpulkan daftar kamera dari AVFoundation jika di Mac
    devices = []
    try:
        import AVFoundation
        discovery_session = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(
            ["AVCaptureDeviceTypeBuiltInWideAngleCamera", "AVCaptureDeviceTypeExternalUnknown", "AVCaptureDeviceTypeContinuityCamera"],
            AVFoundation.AVMediaTypeVideo,
            AVFoundation.AVCaptureDevicePositionUnspecified
        )
        devices = discovery_session.devices()
    except:
        pass

    configs = [
        {"name": "AVFoundation - Auto Resolution", "backend": cv2.CAP_AVFOUNDATION, "width": None, "height": None},
        {"name": "AVFoundation - HD (1920x1080)", "backend": cv2.CAP_AVFOUNDATION, "width": 1920, "height": 1080},
        {"name": "AVFoundation - SD (640x480)", "backend": cv2.CAP_AVFOUNDATION, "width": 640, "height": 480},
        {"name": "Any Backend - Auto", "backend": cv2.CAP_ANY, "width": None, "height": None},
    ]

    for config in configs:
        print(f"\n--- Mengetes: {config['name']} ---")
        # Kita coba index 0 (biasanya eksternal/iPhone di Hackintosh jika Broadcom lancar)
        # Tapi mari coba index 0 sampai 1
        for idx in range(2):
            cap = cv2.VideoCapture(idx, config['backend'])
            if not cap.isOpened():
                print(f"  [Index {idx}] Gagal dibuka.")
                continue
            
            if config['width']:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['width'])
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['height'])
            
            print(f"  [Index {idx}] Kamera terbuka. Menunggu frame...")
            
            success = False
            for i in range(10): # Percobaan 10 kali (1 detik)
                ret, frame = cap.read()
                if ret and frame is not None:
                    h, w = frame.shape[:2]
                    print(f"  ✅ [Index {idx}] BERHASIL! Mendapatkan frame size: {w}x{h}")
                    success = True
                    break
                time.sleep(0.1)
            
            if not success:
                print(f"  ❌ [Index {idx}] Gagal mendapatkan frame (Layar Hitam).")
            
            cap.release()

if __name__ == "__main__":
    test_camera_backends()
