from .camera_controller import CameraController

class MainController:
    def __init__(self, view):
        self.view = view
        # Cấu hình FFmpeg và model mặc định
        self.camera_controller = CameraController(src='rtsp://localhost:8554/cam2', model_path='resources/weights/yolov8n.pt')
        
        # Kết nối sự kiện từ view (giao diện) tới controller
        self.view.btn_start.clicked.connect(self.start_processing)
        self.view.btn_stop.clicked.connect(self.stop_processing)
        
    def start_processing(self):
        # Dừng luồng cũ nếu đang chạy
        self.camera_controller.stop()
        
        # Khởi động các luồng
        self.camera_controller.start()
        
        # Kết nối signal từ stream_thread để cập nhật UI
        stream_thread = self.camera_controller.stream_thread
        stream_thread.change_pixmap_signal.connect(self.view.update_image)
        stream_thread.update_stats_signal.connect(self.view.update_stats)

        # Cập nhật trạng thái UI
        self.view.status_label.setText("Trạng thái: Đang chạy...")
        self.view.status_label.setStyleSheet("color: #a6e3a1;")

    def stop_processing(self):
        # Dừng các luồng
        self.camera_controller.stop()
        
        # Cập nhật trạng thái UI
        self.view.status_label.setText("Trạng thái: Đã dừng")
        self.view.status_label.setStyleSheet("color: #f38ba8;")
        self.view.video_label.setText("Camera Feed Đã Đóng")
        self.view.video_label.setStyleSheet("""
            QLabel {
                background-color: #11111b;
                border: 2px dashed #45475a;
                border-radius: 10px;
                font-size: 16px;
                color: #7f849c;
            }
        """)

    def close(self):
        self.stop_processing()
