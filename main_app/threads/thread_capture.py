import time
import cv2
import queue
import os
from PyQt5.QtCore import QThread

class CaptureThread(QThread):
    def __init__(self, capture_queue, src=0):
        super().__init__()
        self.capture_queue = capture_queue
        self.src = src
        self._run_flag = True
        self.cap = None

    def _reconnect(self):
        if self.cap is not None:
            self.cap.release()
        time.sleep(1)
        # Sử dụng FFMPEG làm backend để tối ưu luồng RTSP realtime
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def run(self):
        # Tối ưu cho FFMPEG RTSP (Sử dụng TCP, timeout 5s)
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"
        self._reconnect()
        
        consecutive_fails = 0

        while self._run_flag:
            if not self.cap.isOpened():
                print("[Capture] Stream chưa mở, đang kết nối lại...")
                self._reconnect()
                continue
                
            ret, frame = self.cap.read()
            if ret:
                consecutive_fails = 0
                # Đẩy frame vào queue, nếu đầy thì bỏ frame cũ lấy frame mới (Giữ realtime)
                if not self.capture_queue.full():
                    self.capture_queue.put(frame)
                else:
                    try:
                        self.capture_queue.get_nowait()
                        self.capture_queue.put(frame)
                    except queue.Empty:
                        pass
            else:
                consecutive_fails += 1
                if consecutive_fails > 30: # Cấu hình số lần fail tối đa trước khi reconnect
                    print("[Capture] Mất luồng RTSP quá lâu, đang kết nối lại...")
                    self._reconnect()
                    consecutive_fails = 0
                else:
                    time.sleep(0.01)
        
        if self.cap:
            self.cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()
