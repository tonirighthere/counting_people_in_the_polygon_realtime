from .camera_controller import CameraController
from resources.config import CAMERAS, MODEL_PATH

class MainController:
    def __init__(self, view):
        self.view = view
        self.cameras = {}
        
        # Initialize CameraControllers for all configured cameras
        for cam_id, config in CAMERAS.items():
            cam = CameraController(
                cam_id=cam_id, 
                src=config["url"], 
                task=config["task"], 
                model_path=MODEL_PATH
            )
            # Both cameras are active for parallel processing
            cam.set_active(True)
            self.cameras[cam_id] = cam
        
        # Connect UI signals
        self.view.btn_start.clicked.connect(self.start_processing)
        self.view.btn_stop.clicked.connect(self.stop_processing)

    def start_processing(self):
        # Stop existing threads if any
        self.stop_processing()
        
        # Start all camera threads
        for cam_id, cam in self.cameras.items():
            cam.start()
            # Connect signals to view for parallel updates
            cam.stream_thread.change_pixmap_signal.connect(self.view.on_frame_received)
            cam.stream_thread.update_stats_signal.connect(self.view.on_stats_received)

        # Update UI status
        self.view.status_label.setText("Trạng thái: Đang chạy song song")
        self.view.status_label.setStyleSheet("color: #a6e3a1;")

    def stop_processing(self):
        # Stop all threads
        for cam in self.cameras.values():
            cam.stop()
        
        # Update UI status and clear labels
        self.view.status_label.setText("Trạng thái: Đã dừng")
        self.view.status_label.setStyleSheet("color: #f38ba8;")
        
        for cam_id in self.cameras:
            if cam_id in self.view.video_labels:
                self.view.video_labels[cam_id].clear()
                self.view.video_labels[cam_id].setText("Camera Feed Đã Đóng")
                self.view.stats_labels[cam_id].setText("Thông số: --")

    def close(self):
        self.stop_processing()

