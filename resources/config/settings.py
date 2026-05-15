# Cấu hình nguồn Video đa Camera
CAMERAS = {
    "CAM_1": {
        "url": "rtsp://localhost:8554/cam1",
        "task": "POLYGON",
        "name": "Cam 1 (Đếm Vùng)"
    },
    "CAM_2": {
        "url": "rtsp://localhost:8554/cam2",
        "task": "LINE_CROSSING",
        "name": "Cam 2 (Vượt Tuyến)"
    }
}

# Cấu hình Model YOLO
MODEL_PATH = 'resources/weights/yolov8n.pt'
CONFIDENCE_THRESHOLD = 0.2
IOU_THRESHOLD = 0.8
IMGSZ = 960
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
