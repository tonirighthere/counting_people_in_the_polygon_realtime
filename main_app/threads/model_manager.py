# Giúp tải model lên GPU đúng 1 lần đầu tiên, tất cả các luồng camera sau đó sẽ dùng chung chính thực thể (instance) model đó trong VRAM.
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

    def get_model(self, model_path):
        """
        Lấy instance của model YOLO. Nếu model chưa được tải, thực hiện tải và lưu vào cache (VRAM).
        Đảm bảo chỉ load duy nhất 1 lần cho mỗi đường dẫn model bất kể số lượng luồng camera.
        """
        # Kiểm tra nhanh trước khi lock để tối ưu hiệu năng
        if model_path in self._models:
            return self._models[model_path]

        with self._load_lock:
            # Kiểm tra lại lần nữa sau khi có lock (Double-Checked Locking Pattern)
            if model_path not in self._models:
                print(f"[ModelManager] Đang tải model mới vào GPU/CPU: {model_path} ...")
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                
                # Khởi tạo YOLO model
                if model_path.endswith('.pt') or model_path.endswith('.pth'):
                    model = YOLO(model_path, task='detect').to(device)
                else:
                    model = YOLO(model_path, task='detect')
                
                # Lưu vào cache
                self._models[model_path] = model
                print(f"[ModelManager] Tải thành công và lưu cache model: {model_path} trên thiết bị: {device}")
            
            return self._models[model_path]
