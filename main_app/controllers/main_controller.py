from .camera_controller import CameraController
from resources.config import CAMERAS, MODEL_PATH

class MainController:
    def __init__(self, view):
        self.view = view
        self.cameras = {}
        
        # Khởi tạo các CameraController từ settings
        for cam_id, config in CAMERAS.items():
            cam = CameraController(
                cam_id=cam_id, 
                src=config["url"], 
                task=config["task"], 
                model_path=MODEL_PATH
            )
            self.cameras[cam_id] = cam
            
        self.active_cam_id = list(CAMERAS.keys())[0] if CAMERAS else None
        if self.active_cam_id:
            self.cameras[self.active_cam_id].set_active(True)
        
        # Kết nối sự kiện từ view (giao diện) tới controller
        self.view.btn_start.clicked.connect(self.start_processing)
        self.view.btn_stop.clicked.connect(self.stop_processing)

    def set_active_camera(self, cam_id):
        if cam_id in self.cameras:
            if self.active_cam_id and self.active_cam_id in self.cameras:
                self.cameras[self.active_cam_id].set_active(False)
            self.active_cam_id = cam_id
            self.cameras[self.active_cam_id].set_active(True)
            self.view.update_active_cam_ui(cam_id)
        
    def start_processing(self):
        # Dừng luồng cũ nếu đang chạy
        self.stop_processing()
        
        # Khởi động tất cả các luồng
        for cam_id, cam in self.cameras.items():
            cam.start()
            # Kết nối signal từ stream_thread để cập nhật UI
            cam.stream_thread.change_pixmap_signal.connect(self.view.on_frame_received)
            cam.stream_thread.update_stats_signal.connect(self.view.on_stats_received)

        # Cập nhật trạng thái UI
        self.view.status_label.setText("Trạng thái: Đang chạy...")
        self.view.status_label.setStyleSheet("color: #a6e3a1;")

    def stop_processing(self):
        # Dừng các luồng
        for cam in self.cameras.values():
            cam.stop()
        
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
