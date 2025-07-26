from ultralytics import YOLO
 
# Load the model.
def main():
   model = YOLO('yolov8m.pt')
   
   # Training.
   results = model.train(
      data='C:\\Users\\palar\\Documents\\yantra\\data.yaml',
      imgsz=640,
      epochs=20,
      batch=12,
      device='0',
      name='yolov8s_custom2'
   )
if __name__ == '__main__':
    main()