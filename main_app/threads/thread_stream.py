import os
# Tắt toàn bộ log spam cảnh báo của FFmpeg / OpenCV trước khi import cv2
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"
os.environ["OPENCV_LOG_LEVEL"] = "OFF"

import cv2
import queue
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage

class StreamThread(QThread):
    # Gửi khung hình video
    change_pixmap_signal = pyqtSignal(str, QImage)
    update_stats_signal = pyqtSignal(str, dict) # Truyền theo dict để linh hoạt { "in": 0, "out": 0 } hoặc { "count": 0 }

    def __init__(self, cam_id, process_queue):
        super().__init__()
        self.cam_id = cam_id
        self.process_queue = process_queue
        self._run_flag = True

    def run(self):
        while self._run_flag:
            try:
                frame, counts = self.process_queue.get(timeout=0.1)
                
            except queue.Empty:
                continue

            # Convert BGR (OpenCV) -> RGB (PyQt)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Gửi dữ liệu lên UI
            self.change_pixmap_signal.emit(self.cam_id, p)
            self.update_stats_signal.emit(self.cam_id, counts)

    def stop(self):
        self._run_flag = False
        self.wait()
