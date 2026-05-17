# Cấu hình nguồn Video đa Camera
# Cấu hình máy chủ Stream
# "localhost:8554" hoặc "192.168.1.144:1935/TTS"
STREAM_SERVER = "localhost:8554" 
PROTOCOL = "rtsp" # "rtsp" hoặc "rtmp"

CAMERAS = {
    "CAM_1": {
        "url": f"{PROTOCOL}://{STREAM_SERVER}/cam1",
        "task": "POLYGON",
        "name": "Cam 1 (Đếm Vùng)"
    },
    "CAM_2": {
        "url": f"{PROTOCOL}://{STREAM_SERVER}/cam2",
        "task": "LINE_CROSSING",
        "name": "Cam 2 (Vượt Tuyến)"
    }
}


# Cấu hình Model YOLO
MODEL_PATH = 'resources/weights/yolov8n.pt'
CONFIDENCE_THRESHOLD = 0.15
IOU_THRESHOLD = 0.8
IMGSZ = 1280
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
