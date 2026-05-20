from main_app.utils import CAMERAS, save_cameras


# Cấu hình Model YOLO
MODEL_PATH = 'resources/weights/yolov8n_best.engine'
CONFIDENCE_THRESHOLD = 0.15
# Thuật toán NMS dùng để loại bỏ các bounding box chồng lấn lên nhau
IOU_THRESHOLD = 0.8
IMGSZ = (640, 640)
CLASSES = [0]

# Cấu hình Tracker (ByteTrack)
TRACK_THRESHOLD = 0.3
TRACK_BUFFER = 120
MATCH_THRESHOLD = 0.6

# Cấu hình Giao diện (UI)
WINDOW_TITLE = "AI Vision Dashboard - RTMP"
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480
