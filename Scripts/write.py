import numpy as np
import supervision as sv
from ultralytics import YOLO
import math
import time

model = YOLO("yolov8s.pt")
tracker = sv.ByteTrack()
box_annotator = sv.BoundingBoxAnnotator()
label_annotator = sv.LabelAnnotator()
trace_annotator = sv.TraceAnnotator()

# Initialize delays file
with open('/Users/debayan/Documents/donkey/delays.txt', 'w') as f:
    f.write("start\n")

def write_delay(x):
    """Write delay value to file with timestamp"""
    with open('/Users/debayan/Documents/donkey/delays.txt', 'a') as f:
        f.write(f"{time.time()}:{x} ")  # Store with timestamp

def callback(frame: np.ndarray, _: int) -> np.ndarray:
    classNames = [
        'ambulance', 'army vehicle', 'auto rickshaw', 'bicycle', 'bus',
        'car', 'garbagevan', 'human hauler', 'minibus', 'minivan',
        'motorbike', 'pickup', 'policecar', 'rickshaw', 'scooter',
        'suv', 'taxi', 'three wheelers -CNG-', 'truck', 'van', 'wheelbarrow'
    ]
    
    weights = {
        'ambulance': 10, 'army vehicle': 6, 'bus': 5, 'truck': 4,
        'car': 2, 'van': 3, 'suv': 3, 'motorbike': 1, 'scooter': 1,
        'bicycle': 0.5, 'auto rickshaw': 1.5, 'rickshaw': 1.5
    }
    
    results = model(frame)[0]
    weighted = 0
    
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            name = classNames[cls]
            weighted += weights.get(name, 1)  # Default weight 1 for unlisted vehicles
    
    delay = math.ceil(weighted / 3.68)
    print(f"Detected traffic - setting delay: {delay}s")
    write_delay(delay)
    
    # Visualization (optional)
    detections = sv.Detections.from_ultralytics(results)
    detections = tracker.update_with_detections(detections)
    labels = [
        f"#{tracker_id} {classNames[class_id]}"
        for class_id, tracker_id in zip(detections.class_id, detections.tracker_id)
    ]
    frame = box_annotator.annotate(frame.copy(), detections=detections)
    frame = label_annotator.annotate(frame, detections=detections, labels=labels)
    return trace_annotator.annotate(frame, detections=detections)

sv.process_video(
    source_path="vecteezy_busy-traffic-on-the-highway_6434705.mp4",
    target_path="ff2_result.mp4",
    callback=callback
)