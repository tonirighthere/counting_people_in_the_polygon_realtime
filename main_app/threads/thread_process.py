import queue
import numpy as np
from PyQt5.QtCore import QThread
import supervision as sv
from ultralytics import YOLO
from resources.config import (
    TRACK_THRESHOLD, TRACK_BUFFER, MATCH_THRESHOLD,
    CONFIDENCE_THRESHOLD, IOU_THRESHOLD, IMGSZ, CLASSES
)

class ProcessThread(QThread):
    def __init__(self, capture_queue, process_queue, task_type="POLYGON", model_path='resources/weights/yolov8n.pt'):
        super().__init__()
        self.capture_queue = capture_queue
        self.process_queue = process_queue
        self.model_path = model_path
        self.task_type = task_type
        self._run_flag = True
        self.is_active = False

    def set_active(self, active):
        self.is_active = active

    def run(self):
        model = YOLO(self.model_path)
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
            try:
                frame = self.capture_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # Bỏ qua kiểm tra is_active để AI luôn chạy ngầm, đảm bảo luồng đếm người qua vạch (Line Crossing) có thể cộng dồn liên tục ngay cả khi không được hiển thị trên màn hình chính.

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
                    zone = sv.PolygonZone(polygon=polygon)
                    zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.WHITE)
                elif self.task_type == "LINE_CROSSING":
                    start = sv.Point(int(w * 0.2), int(h * 0.5))
                    end = sv.Point(int(w * 0.8), int(h * 0.5))
                    zone = sv.LineZone(start=start, end=end)
                    zone_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=1, text_scale=0.5)

            # Detect YOLOv8
            results = model(
                frame, 
                imgsz=IMGSZ, 
                classes=CLASSES, 
                conf=CONFIDENCE_THRESHOLD, 
                iou=IOU_THRESHOLD, 
                verbose=False
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
