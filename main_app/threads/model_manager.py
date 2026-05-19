import threading
import torch
from ultralytics import YOLO

class ModelManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ModelManager, cls).__new__(cls, *args, **kwargs)
                    cls._instance._models = {}
                    cls._instance._load_lock = threading.Lock()
        return cls._instance

    def get_model(self, model_path, camera_id=None):
        """
        Lấy instance của model YOLO. Nếu model chưa được tải cho camera tương ứng,
        thực hiện tải và lưu vào cache (VRAM) riêng cho camera đó.
        Đảm bảo mỗi camera có 1 thực thể model riêng để chạy song song trên GPU/CPU.
        """
        cache_key = (model_path, camera_id) if camera_id else model_path

        # Kiểm tra nhanh trước khi lock để tối ưu hiệu năng
        if cache_key in self._models:
            return self._models[cache_key]

        with self._load_lock:
            # Kiểm tra lại lần nữa sau khi có lock (Double-Checked Locking Pattern)
            if cache_key not in self._models:
                camera_info = f" cho camera {camera_id}" if camera_id else ""
                print(f"[ModelManager] Đang tải model mới vào GPU/CPU{camera_info}: {model_path} ...")
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                
                # Khởi tạo YOLO model
                if model_path.endswith('.pt') or model_path.endswith('.pth'):
                    model = YOLO(model_path, task='detect').to(device)
                else:
                    model = YOLO(model_path, task='detect')
                
                # Lưu vào cache
                self._models[cache_key] = model
                print(f"[ModelManager] Tải thành công và lưu cache model: {model_path} trên thiết bị: {device}")
            
            return self._models[cache_key]

