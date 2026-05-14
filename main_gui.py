import sys
import time
import cv2
import numpy as np
import queue
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame
)
import supervision as sv
from ultralytics import YOLO

# Hàng đợi để giao tiếp giữa các luồng
capture_queue = queue.Queue(maxsize=2)
process_queue = queue.Queue(maxsize=2)

# 1. Luồng Capture: Đọc frame từ video/camera
class CaptureThread(QThread):
    def __init__(self, src=0):
        super().__init__()
        self._run_flag = True
        self.src = src

    def run(self):
        # Tối ưu cho RTSP nếu dùng link
        import os
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
        cap = cv2.VideoCapture(self.src)
        
        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                # Đẩy frame vào queue, nếu đầy thì bỏ frame cũ lấy frame mới (tránh lag stream)
                if not capture_queue.full():
                    capture_queue.put(frame)
                else:
                    try:
                        capture_queue.get_nowait()
                        capture_queue.put(frame)
                    except queue.Empty:
                        pass
            else:
                time.sleep(0.01)
        
        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()


# 2. Luồng Process: Nhận frame, chạy YOLO, tracking, đếm người
class ProcessThread(QThread):
    def __init__(self, model_path='yolov8n.pt'):
        super().__init__()
        self._run_flag = True
        self.model_path = model_path

    def run(self):
        model = YOLO(self.model_path)
        tracker = sv.ByteTrack(track_activation_threshold=0.3, lost_track_buffer=120, minimum_matching_threshold=0.6)
        
        zone = None
        zone_annotator = None
        line_zone = None
        line_zone_annotator = None
        
        try:
            box_annotator = sv.BoundingBoxAnnotator(thickness=2)
        except AttributeError:
            box_annotator = sv.BoxAnnotator(thickness=2)
        
        label_annotator = sv.LabelAnnotator(text_scale=0.5, text_thickness=1)

        while self._run_flag:
            try:
                frame = capture_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            h, w = frame.shape[:2]

            # Cấu hình Vùng (Polygon) đếm số người Đang Ở Trong
            if zone is None:
                polygon = np.array([
                    [int(w * 0.30), int(h * 0.30)],
                    [int(w * 0.70), int(h * 0.30)],
                    [int(w * 0.80), int(h * 0.80)],
                    [int(w * 0.20), int(h * 0.80)]
                ])
                zone = sv.PolygonZone(polygon=polygon)
                zone_annotator = sv.PolygonZoneAnnotator(zone=zone, color=sv.Color.WHITE)

            # Cấu hình Đường Kẻ (Line) đếm số người Đi Qua
            if line_zone is None:
                start_point = sv.Point(int(w * 0.2), int(h * 0.5))
                end_point = sv.Point(int(w * 0.8), int(h * 0.5))
                line_zone = sv.LineZone(start=start_point, end=end_point, triggering_anchors=[sv.Position.BOTTOM_CENTER])
                line_zone_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=2, text_scale=0.8, display_in_count=True)

            # Detect
            results = model(frame, imgsz=640, classes=[0], conf=0.3, iou=0.5, verbose=False)[0]
            detections = sv.Detections.from_ultralytics(results)
            
            # Tracking
            detections = tracker.update_with_detections(detections)

            count_in_zone = 0
            count_crossed = 0

            annotated_frame = frame.copy()

            if len(detections) > 0 and detections.tracker_id is not None:
                # 1. Đếm người TRONG VÙNG (PolygonZone)
                mask = zone.trigger(detections=detections)
                in_zone_detections = detections[mask]
                count_in_zone = len(in_zone_detections)

                # 2. Đếm người ĐI QUA VÙNG (LineZone)
                line_zone.trigger(detections=detections)

                # Vẽ Box & Label
                labels = [f"ID:{tid}" for tid in detections.tracker_id]
                annotated_frame = box_annotator.annotate(scene=annotated_frame, detections=detections)
                annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)

            count_crossed = line_zone.out_count + line_zone.in_count

            # Vẽ Annotation vùng và đường
            annotated_frame = zone_annotator.annotate(scene=annotated_frame)
            annotated_frame = line_zone_annotator.annotate(annotated_frame, line_counter=line_zone)

            # Đẩy kết quả đã xử lý sang queue cho StreamThread
            if not process_queue.full():
                process_queue.put((annotated_frame, count_in_zone, count_crossed))
            else:
                try:
                    process_queue.get_nowait()
                    process_queue.put((annotated_frame, count_in_zone, count_crossed))
                except queue.Empty:
                    pass

    def stop(self):
        self._run_flag = False
        self.wait()


# 3. Luồng Stream: Nhận frame đã xử lý và hiển thị lên GUI
class StreamThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    update_stats_signal = pyqtSignal(int, int) # (trong vùng, đi qua)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        while self._run_flag:
            try:
                frame, count_in_zone, count_crossed = process_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # Convert BGR (OpenCV) -> RGB (PyQt)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)

            self.change_pixmap_signal.emit(p)
            self.update_stats_signal.emit(count_in_zone, count_crossed)

    def stop(self):
        self._run_flag = False
        self.wait()


# ---------------------------------------------------------
# Giao diện chính của ứng dụng
# ---------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Vision Dashboard - MultiThreaded")
        self.resize(1000, 600)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")

        # Biến lưu trữ Thread
        self.capture_thread = None
        self.process_thread = None
        self.stream_thread = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.setup_sidebar()
        self.setup_main_content()

    def setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #181825;
                border-right: 1px solid #313244;
            }
            QPushButton {
                background-color: transparent;
                color: #a6adc8;
                border: none;
                padding: 15px;
                text-align: left;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #313244;
                color: #cdd6f4;
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(10)

        title_label = QLabel("VISION APP")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #89b4fa; padding-bottom: 20px;")
        sidebar_layout.addWidget(title_label)

        self.btn_dashboard = QPushButton("📊 Dashboard")
        self.btn_settings = QPushButton("⚙️ Cài đặt")
        self.btn_exit = QPushButton("❌ Thoát")

        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_settings)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.btn_exit)

        self.btn_exit.clicked.connect(self.close)
        self.main_layout.addWidget(self.sidebar)

    def setup_main_content(self):
        self.content_area = QFrame()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.video_label = QLabel("Camera Feed Sẽ Hiển Thị Ở Đây")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #11111b;
                border: 2px dashed #45475a;
                border-radius: 10px;
                font-size: 16px;
                color: #7f849c;
            }
        """)
        content_layout.addWidget(self.video_label, stretch=3)

        control_layout = QHBoxLayout()
        
        self.status_label = QLabel("Trạng thái: Đang dừng")
        self.status_label.setFont(QFont("Arial", 12))
        
        # Thống kê
        self.stats_in_zone = QLabel("Trong vùng: 0")
        self.stats_in_zone.setFont(QFont("Arial", 12))
        self.stats_in_zone.setStyleSheet("color: #a6e3a1; font-weight: bold;")

        self.stats_crossed = QLabel("Đã đi qua: 0")
        self.stats_crossed.setFont(QFont("Arial", 12))
        self.stats_crossed.setStyleSheet("color: #f9e2af; font-weight: bold;")

        self.btn_start = QPushButton("▶ Bắt đầu")
        self.btn_stop = QPushButton("⏹ Dừng")
        
        button_style = """
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #74c7ec; }
            QPushButton:pressed { background-color: #89dceb; }
        """
        self.btn_start.setStyleSheet(button_style)
        self.btn_stop.setStyleSheet(button_style.replace("#89b4fa", "#f38ba8").replace("#74c7ec", "#eba0ac").replace("#89dceb", "#f5c2e7"))

        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.stats_in_zone)
        control_layout.addWidget(QLabel(" | "))
        control_layout.addWidget(self.stats_crossed)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)

        content_layout.addLayout(control_layout, stretch=1)

        self.btn_start.clicked.connect(self.start_processing)
        self.btn_stop.clicked.connect(self.stop_processing)

        self.main_layout.addWidget(self.content_area)

    def empty_queue(self, q):
        while not q.empty():
            try:
                q.get_nowait()
            except queue.Empty:
                break

    def start_processing(self):
        # Đảm bảo dọn dẹp các luồng cũ nếu có
        self.stop_processing()

        # Tạo và kết nối các luồng
        # Thay '0' bằng link RTSP hoặc đường dẫn file video nếu cần
        self.capture_thread = CaptureThread(src=0) 
        self.process_thread = ProcessThread(model_path='yolov8n.pt')
        self.stream_thread = StreamThread()

        self.stream_thread.change_pixmap_signal.connect(self.update_image)
        self.stream_thread.update_stats_signal.connect(self.update_stats)

        self.capture_thread.start()
        self.process_thread.start()
        self.stream_thread.start()

        self.status_label.setText("Trạng thái: Đang chạy...")
        self.status_label.setStyleSheet("color: #a6e3a1;")

    def stop_processing(self):
        if self.capture_thread and self.capture_thread.isRunning():
            self.capture_thread.stop()
        if self.process_thread and self.process_thread.isRunning():
            self.process_thread.stop()
        if self.stream_thread and self.stream_thread.isRunning():
            self.stream_thread.stop()

        # Xóa các queue tránh lưu frame cũ
        self.empty_queue(capture_queue)
        self.empty_queue(process_queue)

        self.status_label.setText("Trạng thái: Đã dừng")
        self.status_label.setStyleSheet("color: #f38ba8;")
        self.video_label.setText("Camera Feed Đã Đóng")
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #11111b;
                border: 2px dashed #45475a;
                border-radius: 10px;
                font-size: 16px;
                color: #7f849c;
            }
        """)

    def update_image(self, qt_img):
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))
        self.video_label.setStyleSheet("border: 2px solid #89b4fa; border-radius: 10px;")

    def update_stats(self, count_in, count_crossed):
        self.stats_in_zone.setText(f"Trong vùng: {count_in}")
        self.stats_crossed.setText(f"Đã đi qua: {count_crossed}")

    def closeEvent(self, event):
        self.stop_processing()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
