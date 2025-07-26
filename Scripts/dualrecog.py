import cv2
import numpy as np
from ultralytics import YOLO
import math
import time
from concurrent.futures import ThreadPoolExecutor

model = YOLO("yolov8n.pt")


with open('/Users/debayan/Documents/donkey/delays.txt', 'w') as f:
    f.write("start\n")

def write_delays(delay1, delay2):
    """Write both delays to file with timestamps"""
    with open('/Users/debayan/Documents/donkey/delays.txt', 'a') as f:
        f.write(f"{time.time()}:{delay1}:{delay2}\n")

def process_video(video_path, lane_id):
    classNames = [
        'ambulance', 'army vehicle', 'auto rickshaw', 'bicycle', 'bus',
        'car', 'garbagevan', 'human hauler', 'minibus', 'minivan',
        'motorbike', 'pickup', 'policecar', 'rickshaw', 'scooter',
        'suv', 'taxi', 'three wheelers -CNG-', 'truck', 'van', 'wheelbarrow'
    ]
    
    weights = {
        'ambulance': 1000, 'army vehicle': 6, 'bus': 5, 'truck': 4,
        'car': 2, 'van': 3, 'suv': 3, 'motorbike': 1, 'scooter': 1,
        'bicycle': 0.5, 'auto rickshaw': 1.5, 'rickshaw': 1.5
    }

    cap = cv2.VideoCapture(video_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        results = model(frame)[0]
        weighted = 0
        
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                name = classNames[cls]
                weighted += weights.get(name, 1)
        
        delay = math.ceil(weighted / 3.68)
        
        if lane_id == 1:
            write_delays(delay, max(3, 60-delay))
        else:
            write_delays(max(3, 60-delay), delay)
        
        time.sleep(0.1)  

    cap.release()

def main():
    with ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(process_video, "vecteezy_busy-traffic-on-the-highway_6434705.mp4", 1)
        executor.submit(process_video, "vecteezy_busy-traffic-on-the-highway_6434705.mp4", 2)

if __name__ == "__main__":
    main()