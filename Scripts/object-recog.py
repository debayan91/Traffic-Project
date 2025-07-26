from ultralytics import YOLO
import cv2
import math 
# start webcam
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# model
model = YOLO("C:\\Users\\palar\\runs\\detect\\yolov8n_custom215\\weights\\best.pt")

# object classes
classNames = [
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
    'wheelbarrow',
              ]


while True:
    success, img = cap.read()
    results = model(img, stream=True)

    # coordinates
    for r in results:
        boxes = r.boxes

        for box in boxes:
            print(box)
            # bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2) # convert to int values

            # confidence
            confidence = math.ceil((box.conf[0]*100))/100
            print("Confidence --->",confidence)

            # class name
            cls = int(box.cls[0])
            name=classNames[cls]

            #check if it detects car, bus, truck etc.
                # put box in cam
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            print("Class name -->", classNames[cls])
            # object details
            org = [x1, y1]
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1
            color = (255, 0, 0)
            thickness = 2

            cv2.putText(img, classNames[cls], org, font, fontScale, color, thickness)

    cv2.imshow('Webcam', img)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()