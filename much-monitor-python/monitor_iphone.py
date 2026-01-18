import AVFoundation
from Foundation import NSObject
import time

class CameraObserver(NSObject):
    def init(self):
        self = super().init()
        return self

def monitor_continuity_camera():
    print("="*50)
    print("   MONITORING CONTINUITY CAMERA (Kamera iPhone)")
    print("="*50)
    print("Mencari iPhone secara real-time...")
    print("Tips: Jika belum muncul, coba kunci & buka kunci iPhone Anda.")
    print("Tekan Ctrl+C untuk berhenti.\n")
    
    last_count = -1
    
    try:
        while True:
            # Re-discover devices
            discovery_session = AVFoundation.AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(
                ["AVCaptureDeviceTypeBuiltInWideAngleCamera", "AVCaptureDeviceTypeExternalUnknown", "AVCaptureDeviceTypeContinuityCamera"],
                AVFoundation.AVMediaTypeVideo,
                AVFoundation.AVCaptureDevicePositionUnspecified
            )
            devices = discovery_session.devices()
            
            if len(devices) != last_count:
                print(f"[{time.strftime('%H:%M:%S')}] Perubahan terdeteksi! (Jumlah: {len(devices)})")
                iphone_found = False
                for dev in devices:
                    is_iphone = "iPhone" in dev.localizedName()
                    prefix = "✅ SUCCESS:" if is_iphone else "  -"
                    print(f"  {prefix} {dev.localizedName()} [{dev.deviceType()}]")
                    if is_iphone: iphone_found = True
                
                if not iphone_found:
                    print("\n  ⚠️ iPhone BELUM TERDETEKSI.")
                    print("  Saran: Pastikan Intel Bluetooth di BIOS sudah OFF.")
                    print("  Saran: Cek Settings > General > AirPlay & Handoff di iPhone.")
                else:
                    print("\n  🎉 IPHONE TERDETEKSI! Anda bisa menjalankan main_gui.py sekarang.")
                
                print("-" * 30)
                last_count = len(devices)
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nMonitoring dihentikan.")

if __name__ == "__main__":
    monitor_continuity_camera()
