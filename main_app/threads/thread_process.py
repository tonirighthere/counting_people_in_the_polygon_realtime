import os
# Tắt toàn bộ log spam cảnh báo của FFmpeg / OpenCV trước khi import cv2
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"
os.environ["OPENCV_LOG_LEVEL"] = "OFF"

import queue
import time
import cv2
import numpy as np
import warnings
# Tắt cảnh báo FutureWarning từ thư viện supervision (về ByteTrack deprecation)
warnings.filterwarnings("ignore", category=FutureWarning, module="supervision")

from PyQt5.QtCore import QThread
import supervision as sv
from .model_manager import ModelManager
from resources.config import (
    TRACK_THRESHOLD, TRACK_BUFFER, MATCH_THRESHOLD,
    CONFIDENCE_THRESHOLD, IOU_THRESHOLD, IMGSZ, CLASSES
)
from resources.config import MODEL_PATH

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
        
        # Sử dụng ModelManager để lấy model độc lập cho từng camera nhằm hỗ trợ xử lý song song thực sự
        model = ModelManager().get_model(self.model_path, camera_id=self.cam_id)
        tracker = sv.ByteTrack(
            track_activation_threshold=TRACK_THRESHOLD, 
            lost_track_buffer=TRACK_BUFFER, 
            minimum_matching_threshold=MATCH_THRESHOLD
        )
        
        zone = None
        zone_annotator = None
        
        try:
            box_annotator = sv.BoundingBoxAnnotator(thickness=2)
        except AttributeError:
            box_annotator = sv.BoxAnnotator(thickness=2)
        
        label_annotator = sv.LabelAnnotator(text_scale=0.5, text_thickness=1)

        while self._run_flag:
            start_time = time.time()
            try:
                frame = self.capture_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            h, w = frame.shape[:2]

            # Cấu hình vùng tùy theo task
            if zone is None:
                if self.task_type == "POLYGON":
                    polygon = np.array([
                        [int(w * 0.50), int(h * 0.40)],
                        [int(w * 0.70), int(h * 0.30)],
                        [int(w * 0.85), int(h * 0.40)],
                        [int(w * 0.60), int(h * 0.60)]
                    ])
                    zone = sv.PolygonZone(polygon=polygon, triggering_anchors=[sv.Position.BOTTOM_CENTER])
                    zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.WHITE)
                elif self.task_type == "LINE_CROSSING":
                    start = sv.Point(int(w * 0.38), int(h * 0.4))
                    end = sv.Point(int(w * 0.51), int(h * 0.4))
                    zone = sv.LineZone(start=start, end=end, triggering_anchors=[sv.Position.BOTTOM_CENTER])
                    zone_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=1, text_scale=0.5)

            # Detect YOLOv8
            results = model(
                frame, 
                imgsz=IMGSZ, 
                classes=CLASSES, 
                conf=CONFIDENCE_THRESHOLD, 
                iou=IOU_THRESHOLD, 
                verbose=False,
                device=device
            )[0]
            detections = sv.Detections.from_ultralytics(results)
            
            # Tracking ByteTrack
            detections = tracker.update_with_detections(detections)

            counts = {}
            annotated_frame = frame.copy()

            if len(detections) > 0 and detections.tracker_id is not None:
                if self.task_type == "POLYGON":
                    mask = zone.trigger(detections=detections)
                    in_zone_detections = detections[mask]
                    counts = {"count": len(in_zone_detections)}
                    
                    labels = [f"ID:{tid}" for tid in in_zone_detections.tracker_id]
                    annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=in_zone_detections)
                    annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=in_zone_detections, labels=labels)
                
                elif self.task_type == "LINE_CROSSING":
                    zone.trigger(detections=detections)
                    counts = {"in": zone.in_count, "out": zone.out_count}
                    
                    labels = [f"ID:{tid}" for tid in detections.tracker_id]
                    annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections)
                    annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)

            # Vẽ Annotation
            if self.task_type == "LINE_CROSSING":
                # LineZoneAnnotator cần truyền kèm text (in/out counts)
                annotated_frame = zone_annotator.annotate(frame=annotated_frame, line_counter=zone)
            else:
                annotated_frame = zone_annotator.annotate(scene=annotated_frame)

            # Tính toán và hiển thị FPS sử dụng bộ lọc Exponential Moving Average (EMA) để làm mịn chỉ số hiển thị
            current_time = time.time()
            elapsed_time = current_time - start_time
            instantaneous_fps = 1.0 / (current_time - getattr(self, 'last_time', current_time - 0.033))
            self.last_time = current_time

            # Khởi tạo hoặc cập nhật fps_smooth bằng bộ lọc EMA (trọng số lịch sử 90%, tức thời 10%)
            if not hasattr(self, 'fps_smooth'):
                self.fps_smooth = instantaneous_fps
            else:
                self.fps_smooth = 0.9 * self.fps_smooth + 0.1 * instantaneous_fps

            # Vẽ FPS lên frame (Góc trên cùng bên trái)
            cv2.putText(annotated_frame, f"FPS: {self.fps_smooth:.0f}", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

            # Giới hạn FPS ở mức tối đa 30 (1/30 = 0.0333s)
            target_delay = 1.0 / 30
            if elapsed_time < target_delay:
                time.sleep(target_delay - elapsed_time)

            # Đẩy kết quả đã xử lý sang queue cho StreamThread
            if not self.process_queue.full():
                self.process_queue.put((annotated_frame, counts))
            else:
                try:
                    self.process_queue.get_nowait()
                    self.process_queue.put((annotated_frame, counts))
                except queue.Empty:
                    pass

    def stop(self):
        self._run_flag = False
        self.wait()
