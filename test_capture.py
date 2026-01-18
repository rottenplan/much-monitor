import cv2
import time
import os

def test_iphone_capture():
    index = 1 # Based on diagnose_cameras.py
    print(f"Testing capture from index {index} (iPhone)...")
    
    cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Warmup
    print("Warming up...")
    for i in range(30):
        ret, frame = cap.read()
        if ret:
            print(f"Frame captured at iteration {i}")
            cv2.imwrite("debug_iphone_frame.jpg", frame)
            print("Successfully saved debug_iphone_frame.jpg")
            cap.release()
            return
        time.sleep(0.1)
    
    print("Failed to capture any frame after 30 attempts.")
    cap.release()

if __name__ == "__main__":
    test_iphone_capture()
