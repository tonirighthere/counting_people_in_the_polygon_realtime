from .camera_controller import CameraController
from resources.config import CAMERAS, MODEL_PATH, save_cameras

class MainController:
    def __init__(self, view):
        self.view = view
        self.cameras = {}
        self.is_running = False
        
        # Initialize CameraControllers for all configured cameras
        for cam_id, config in CAMERAS.items():
            cam = CameraController(
                cam_id=cam_id, 
                src=config["url"], 
                task=config["task"], 
                model_path=MODEL_PATH
            )
            # Default all cameras to active
            cam.set_active(True)
            self.cameras[cam_id] = cam
        
        # Connect UI signals
        self.view.btn_start.clicked.connect(self.start_processing)
        self.view.btn_stop.clicked.connect(self.stop_processing)

    def start_processing(self):
        # Stop existing threads if any
        self.stop_processing()
        self.is_running = True
        
        # Start all active camera threads
        for cam_id, cam in self.cameras.items():
            if cam.is_active:
                cam.start()
                # Connect signals to view for parallel updates
                cam.stream_thread.change_pixmap_signal.connect(self.view.on_frame_received)
                cam.stream_thread.update_stats_signal.connect(self.view.on_stats_received)
            else:
                if cam_id in self.view.video_labels:
                    self.view.video_labels[cam_id].clear()
                    self.view.video_labels[cam_id].setText("Camera Đang Tắt")
            
            # Update UI status indicators for each card
            self.view.update_camera_card_ui(cam_id)

        # Update UI status
        self.view.status_label.setText("Trạng thái: Đang chạy")
        self.view.status_label.setStyleSheet("color: #a6e3a1;")

    def stop_processing(self):
        self.is_running = False
        # Stop all threads
        for cam in self.cameras.values():
            cam.stop()
        
        # Update UI status and clear labels
        self.view.status_label.setText("Trạng thái: Đã dừng")
        self.view.status_label.setStyleSheet("color: #f38ba8;")
        
        for cam_id, cam in self.cameras.items():
            if cam_id in self.view.video_labels:
                self.view.video_labels[cam_id].clear()
                if cam.is_active:
                    self.view.video_labels[cam_id].setText("Camera Feed Đã Đóng")
                else:
                    self.view.video_labels[cam_id].setText("Camera Đang Tắt")
                self.view.stats_labels[cam_id].setText("Thông số: --")
            
            # Update card UI status indicator to reflect stopped status (with offline colors)
            self.view.update_camera_card_ui(cam_id)

    def toggle_camera_active(self, cam_id):
        """Bật/tắt trạng thái hoạt động của camera cụ thể"""
        if cam_id not in self.cameras:
            return
        
        cam = self.cameras[cam_id]
        new_state = not cam.is_active
        cam.set_active(new_state)
        
        # Nếu hệ thống chính đang chạy, tiến hành khởi động hoặc dừng các luồng camera tương ứng
        if self.is_running:
            if new_state:
                print(f"[Controller] Khởi động camera realtime: {cam_id}")
                cam.start()
                cam.stream_thread.change_pixmap_signal.connect(self.view.on_frame_received)
                cam.stream_thread.update_stats_signal.connect(self.view.on_stats_received)
            else:
                print(f"[Controller] Dừng camera realtime: {cam_id}")
                cam.stop()
                if cam_id in self.view.video_labels:
                    self.view.video_labels[cam_id].clear()
                    self.view.video_labels[cam_id].setText("Camera Đang Tắt")
                if cam_id in self.view.stats_labels:
                    self.view.stats_labels[cam_id].setText("Thông số: --")
        
        # Cập nhật giao diện card camera
        self.view.update_camera_card_ui(cam_id)

    def add_camera(self, name, url, task):
        """Thêm camera mới vào hệ thống"""
        # Tạo mã ID duy nhất cho camera
        idx = 1
        while f"CAM_{idx}" in self.cameras:
            idx += 1
        cam_id = f"CAM_{idx}"
        
        print(f"[Controller] Đang thêm camera mới: {cam_id} | Tên: {name} | Task: {task}")
        
        # Khởi tạo CameraController
        cam = CameraController(
            cam_id=cam_id, 
            src=url, 
            task=task, 
            model_path=MODEL_PATH
        )
        cam.set_active(True)
        self.cameras[cam_id] = cam
        
        # Lưu vào cấu hình config
        CAMERAS[cam_id] = {
            "name": name,
            "url": url,
            "task": task
        }
        save_cameras(CAMERAS)
        
        # Nếu hệ thống đang chạy thì kích hoạt chạy camera này luôn
        if self.is_running:
            cam.start()
            cam.stream_thread.change_pixmap_signal.connect(self.view.on_frame_received)
            cam.stream_thread.update_stats_signal.connect(self.view.on_stats_received)
            
        return cam_id

    def remove_camera(self, cam_id):
        """Xóa camera khỏi hệ thống"""
        if cam_id not in self.cameras:
            return False
            
        print(f"[Controller] Đang xóa camera: {cam_id}")
        
        # Dừng camera threads
        cam = self.cameras[cam_id]
        cam.stop()
        
        # Xóa khỏi danh sách cameras đang quản lý
        del self.cameras[cam_id]
        
        # Xóa khỏi cấu hình và lưu lại
        if cam_id in CAMERAS:
            del CAMERAS[cam_id]
        save_cameras(CAMERAS)
        
        return True

    def close(self):
        self.stop_processing()

