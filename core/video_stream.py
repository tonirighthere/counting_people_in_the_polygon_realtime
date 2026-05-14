import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"

import cv2
import threading
import time

class VideoStream:
    def __init__(self, src):
        self.src = src
        self.cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.ret, self.frame = self.cap.read()
        self.stopped = False
        self.lock = threading.Lock()

    def start(self):
        t = threading.Thread(target=self.update, daemon=True)
        t.start()
        return self

    def _reconnect(self):
        try:
            if self.cap is not None:
                self.cap.release()
        except:
            pass
        time.sleep(2)
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def update(self):
        consecutive_failures = 0
        while not self.stopped:
            if not self.cap.isOpened():
                print("[VideoStream] Stream đóng, đang kết nối lại...")
                self._reconnect()
                consecutive_failures = 0
                continue
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    with self.lock:
                        self.frame = frame
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    if consecutive_failures > 30:
                        # Quá nhiều lần đọc thất bại → buộc reconnect
                        print("[VideoStream] Quá nhiều lỗi đọc frame, reconnect...")
                        self._reconnect()
                        consecutive_failures = 0
                    else:
                        time.sleep(0.05)
            except cv2.error as e:
                print(f"[VideoStream] cv2.error: {e} – reconnect...")
                self._reconnect()
                consecutive_failures = 0
            except Exception as e:
                print(f"[VideoStream] Lỗi không xác định: {e} – reconnect...")
                self._reconnect()
                consecutive_failures = 0
   
    # lấy ra khung hình mới nhất
    def read(self):
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None

    def stop(self):
        self.stopped = True
        self.cap.release()
