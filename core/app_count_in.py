import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO
import time
from core.video_stream import VideoStream

class CountInApp:
    def __init__(self, rtsp_url, model_path='yolov8n.pt'):
        self.rtsp_url = rtsp_url
        self.model = YOLO(model_path)
        # Tracker ByteTrack 
        self.tracker = sv.ByteTrack()

    def get_polygon(self, w, h):
        return np.array([
            [int(w * 0.40), int(h * 0.40)],
            [int(w * 0.70), int(h * 0.25)],
            [int(w * 0.90), int(h * 0.30)],
            [int(w * 0.50), int(h * 0.80)]
        ])

    def run(self):
        # RTSP stream   
        vs = VideoStream(self.rtsp_url).start()
        time.sleep(2.0)

        # Chờ frame đầu tiên (tối đa 10 giây)
        frame = None
        for _ in range(50):
            frame = vs.read()
            if frame is not None:
                break
            time.sleep(0.2)

        if frame is None:
            print("Không thể đọc frame từ camera")
            vs.stop()
            return

        h, w = frame.shape[:2]
        # Định nghĩa vùng Polygon
        polygon = self.get_polygon(w, h)

        # Khởi tạo Zone & Annotators  
        zone = sv.PolygonZone(polygon=polygon)
        zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.WHITE)

        try:
            box_annotator = sv.BoundingBoxAnnotator(thickness=2)
        except AttributeError:
            box_annotator = sv.BoxAnnotator(thickness=2)

        label_annotator = sv.LabelAnnotator(
            text_scale=0.5,
            text_thickness=2,
            text_padding=6,
        )

        print(f"hiển thị luồng trực tiếp từ {self.rtsp_url}...")
        print("q để thoát.")

        cv2.namedWindow("RTSP Camera - Count In", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("RTSP Camera - Count In", 1280, 720)

        # Vòng lặp xử lý
        while True:
            frame = vs.read()
            if frame is None:
                time.sleep(0.01)
                continue

            # Detect người
            results = self.model(frame, imgsz=1280, classes=[0], conf=0.15, iou=0.8, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)

            # Gán tracker ID cho tất cả detections
            detections = self.tracker.update_with_detections(detections)

            # Lọc chỉ những người nằm trong polygon
            mask = zone.trigger(detections=detections)          # bool array
            in_zone_detections = detections[mask]               # chỉ người trong zone

            # Đếm số ID duy nhất đang ở trong zone
            count = len(in_zone_detections)

            # chỉ bounding box + label của người trong zone
            annotated_frame = frame.copy()

            # Vẽ polygon zone
            annotated_frame = zone_annotator.annotate(scene=annotated_frame)

            if count > 0:
                # Tạo label "ID: <tracker_id>" cho từng người trong zone
                labels = [f"ID:{tid}" for tid in in_zone_detections.tracker_id]

                annotated_frame = box_annotator.annotate(
                    scene=annotated_frame,
                    detections=in_zone_detections,
                )
                annotated_frame = label_annotator.annotate(
                    scene=annotated_frame,
                    detections=in_zone_detections,
                    labels=labels,
                )

            # hiển thị số người trong zone 
            hud_text = f"In Zone: {count}"
            (tw, th), _ = cv2.getTextSize(hud_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
            cv2.rectangle(annotated_frame, (10, 10), (20 + tw, 20 + th + 10), (0, 0, 0), -1)
            cv2.putText(
                annotated_frame, hud_text,
                (15, 15 + th),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                (0, 255, 0), 2, cv2.LINE_AA,
            )

            cv2.imshow("RTSP Camera - Count In", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        vs.stop()
        cv2.destroyAllWindows()
