# Cấu hình nguồn Video
RTSP_URL = 'rtsp://localhost:8554/cam2'

# Cấu hình Model YOLO
MODEL_PATH = 'resources/weights/yolov8n.pt'
CONFIDENCE_THRESHOLD = 0.3
IOU_THRESHOLD = 0.5
IMGSZ = 640
CLASSES = [0] # 0 là class 'person' trong bộ COCO

# Cấu hình Tracker (ByteTrack)
TRACK_THRESHOLD = 0.3
TRACK_BUFFER = 120
MATCH_THRESHOLD = 0.6

# Cấu hình Giao diện (UI)
WINDOW_TITLE = "AI Vision Dashboard - Polygon RTSP"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480
