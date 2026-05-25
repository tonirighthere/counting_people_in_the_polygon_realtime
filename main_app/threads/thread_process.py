import os
# Tắt toàn bộ log spam cảnh báo của FFmpeg / OpenCV trước khi import cv2
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"
os.environ["OPENCV_LOG_LEVEL"] = "OFF"

import queue
import time
import cv2
import warnings
# Tắt cảnh báo FutureWarning từ thư viện supervision (về ByteTrack deprecation)
warnings.filterwarnings("ignore", category=FutureWarning, module="supervision")

from PyQt5.QtCore import QThread
import supervision as sv
from ..utils.thread_process_utils import (
    annotate_detections,
    annotate_zone_frame,
    create_box_annotator,
    create_zone,
    select_points_interactive,
    draw_fps,
    put_latest,
    update_fps_counter,
)
from ..utils.model_manager import ModelManager
from resources.config import (
    TRACK_THRESHOLD, TRACK_BUFFER, MATCH_THRESHOLD,
    CONFIDENCE_THRESHOLD, IOU_THRESHOLD, IMGSZ, CLASSES
)
from resources.config import MODEL_PATH
from ..utils.camera_config import load_cameras, save_cameras

class ProcessThread(QThread):
    def __init__(self, capture_queue, process_queue, task_type="POLYGON", model_path=MODEL_PATH, cam_id=None):
        super().__init__()
        self.capture_queue = capture_queue
        self.process_queue = process_queue
        self.model_path = model_path
        self.task_type = task_type
        self.cam_id = cam_id
        self._run_flag = True
        self.is_active = False

    def set_active(self, active):
        self.is_active = active

    def run(self):
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Sử dụng ModelManager để lấy model độc lập cho từng camera
        model = ModelManager().get_model(self.model_path, camera_id=self.cam_id)
        tracker = sv.ByteTrack(
            track_activation_threshold=TRACK_THRESHOLD, 
            lost_track_buffer=TRACK_BUFFER, 
            minimum_matching_threshold=MATCH_THRESHOLD
        )
        
        zone = None
        zone_annotator = None
        box_annotator = create_box_annotator()
        label_annotator = sv.LabelAnnotator(text_scale=0.5, text_thickness=1)

        # Khởi tạo các biến để đếm FPS trong khoảng thời gian 1 giây
        fps_counter = 0
        fps_start_time = time.time()
        fps_smooth = 0

        while self._run_flag:
            start_time = time.time()
            try:
                frame = self.capture_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if zone is None:
                cameras = load_cameras()
                cam_cfg = cameras.get(self.cam_id)
                
                if cam_cfg:
                    points = cam_cfg.get("points")
                    if not points:
                        window_name = f"Setup {self.cam_id}" if self.cam_id else "Setup Camera"
                        points = select_points_interactive(self.task_type, frame, window_name)
                        cam_cfg["points"] = points
                        cameras[self.cam_id] = cam_cfg
                        save_cameras(cameras)
                else:
                    window_name = f"Setup {self.cam_id}" if self.cam_id else "Setup Camera"
                    points = select_points_interactive(self.task_type, frame, window_name)
                    cameras[self.cam_id] = {
                        "url": "",
                        "task": self.task_type,
                        "name": "",
                        "points": points,
                    }
                    save_cameras(cameras)

                zone, zone_annotator = create_zone(self.task_type, points)

            # Detect YOLOv8
            results = model(
                frame, 
                imgsz=IMGSZ, 
                classes=CLASSES, 
                conf=CONFIDENCE_THRESHOLD, 
                iou=IOU_THRESHOLD, 
                verbose=False,
                device=device,
                rect=False  # padding ảnh thành hình vuông 640x640
            )[0]

            # chuyển từ output của YOLO sang Detections (chỉ có toạ độ hộp)
            detections = sv.Detections.from_ultralytics(results)
            
            # Tracking ByteTrack
            detections = tracker.update_with_detections(detections)

            # ko vẽ lên frame gốc => tránh ảnh hưởng detect và track
            annotated_frame = frame.copy()
            annotated_frame, counts = annotate_detections(
                self.task_type,
                zone,
                detections,
                annotated_frame,
                box_annotator,
                label_annotator,
            )

            # Vẽ Annotation
            annotated_frame = annotate_zone_frame(self.task_type, zone, zone_annotator, annotated_frame)

            # Tính toán FPS bằng cách đếm số khung hình được xử lý trong mỗi khoảng 1 giây
            current_time, fps_counter, fps_start_time, fps_smooth = update_fps_counter(
                fps_counter,
                fps_start_time,
                fps_smooth,
            )
            elapsed_time = current_time - start_time

            # Vẽ FPS lên frame
            draw_fps(annotated_frame, fps_smooth)

            # Giới hạn FPS ở mức tối đa 30 (1/30 = 0.0333s)
            target_delay = 1.0 / 30
            if elapsed_time < target_delay:
                time.sleep(target_delay - elapsed_time)

            # Đẩy kết quả đã xử lý sang queue cho StreamThread
            put_latest(self.process_queue, (annotated_frame, counts))

    def stop(self):
        self._run_flag = False
        self.wait()
