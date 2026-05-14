import cv2
import queue
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage

class StreamThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    update_stats_signal = pyqtSignal(int) # Chỉ đếm người trong polygon

    def __init__(self, process_queue):
        super().__init__()
        self.process_queue = process_queue
        self._run_flag = True

    def run(self):
        while self._run_flag:
            try:
                frame, count_in_zone = self.process_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # Convert BGR (OpenCV) -> RGB (PyQt)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)

            self.change_pixmap_signal.emit(p)
            self.update_stats_signal.emit(count_in_zone)

    def stop(self):
        self._run_flag = False
        self.wait()
