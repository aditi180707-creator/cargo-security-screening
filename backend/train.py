from ultralytics import YOLO

# load model
model = YOLO("yolov8n.pt")

# run detection
results = model("test.jpg", show=True)

print("Detection done")