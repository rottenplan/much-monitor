import cv2

def list_cameras():
    index = 0
    arr = []
    while index < 5:
        cap = cv2.VideoCapture(index)
        if cap.read()[0]:
            arr.append(index)
            cap.release()
        index += 1
    return arr

if __name__ == "__main__":
    print(f"Searching for cameras...")
    cameras = list_cameras()
    print(f"Available camera indices: {cameras}")
