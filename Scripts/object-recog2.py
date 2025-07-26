import numpy as np
import supervision as sv
from ultralytics import YOLO
import math


model = YOLO("yolov8s.pt")
tracker = sv.ByteTrack()
box_annotator = sv.BoundingBoxAnnotator()
label_annotator = sv.LabelAnnotator()
trace_annotator = sv.TraceAnnotator()

with open('/Users/debayan/Documents/donkey/delays.txt', 'w') as f:
        f.write("start\n")

def w_read(x):
    print(x)
    with open('/Users/debayan/Documents/donkey/delays.txt', 'a') as f:
        f.write(str(x)+" ")


def callback(frame: np.ndarray, _: int) -> np.ndarray:

    classNames =[
    'ambulance',
    'army vehicle',
    'auto rickshaw',
    'bicycle',
    'bus',
    'car',
    'garbagevan',
    'human hauler',
    'minibus',
    'minivan',
    'motorbike',
    'pickup',
    'policecar',
    'rickshaw',
    'scooter',
    'suv',
    'taxi',
    'three wheelers -CNG-',
    'truck',
    'van',
    'wheelbarrow',]
    results = model(frame)[0]
    weighted=0
    for r in results:
        boxes = r.boxes

        for box in boxes:

            # class name
            cls = int(box.cls[0])
            name=classNames[cls]
            print("Class name -->", name)
            if(name=='car'):
                weighted+=2
            if(name=='truck'):
                weighted+=4
            if(name=='bus'):
                weighted+=5
            if(name=="motorbike"):
                weighted+=1
    time=math.ceil(weighted/3.68)
    print("Time set -->",time)
    w_read(time)
            
    detections = sv.Detections.from_ultralytics(results)
    detections = tracker.update_with_detections(detections)

    labels = [
        f"#{tracker_id} {results.names[class_id]}"
        for class_id, tracker_id
        in zip(detections.class_id, detections.tracker_id)
    ]

    annotated_frame = box_annotator.annotate(
        frame.copy(), detections=detections)
    annotated_frame = label_annotator.annotate(
        annotated_frame, detections=detections, labels=labels)
    return trace_annotator.annotate(
        annotated_frame, detections=detections)

sv.process_video(
    source_path="vecteezy_busy-traffic-on-the-highway_6434705.mp4",
    target_path="ff2_result.mp4",
    callback=callback
)