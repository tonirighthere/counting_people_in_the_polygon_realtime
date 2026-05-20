import os
import sys
import ctypes

def set_env_var(name, value):
    os.environ[name] = str(value)
    if sys.platform == "win32":
        for dll_name in ["msvcrt.dll", "ucrtbase.dll"]:
            try:
                ctypes.CDLL(dll_name)._putenv(f"{name}={value}".encode("utf-8"))
            except Exception:
                pass

# Tắt log spam chỉ error của FFmpeg / OpenCV trước khi import cv2
set_env_var("OPENCV_FFMPEG_LOGLEVEL", "8")
set_env_var("OPENCV_LOG_LEVEL", "OFF")

import time
import cv2
import queue
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
        # Sử dụng FFMPEG làm backend để tối ưu luồng RTSP/RTMP realtime
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_FFMPEG)
        # Buffer = 1 để giảm độ trễ (realtime)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # Yêu cầu decoder bỏ qua lỗi B/P-frame bị mất thay vì spam console
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))

    def run(self):
        # Kiểm tra nếu self.src là chuỗi (URL) trước khi dùng .startswith()
        if isinstance(self.src, str):
            if self.src.startswith("rtsp"):
                set_env_var("OPENCV_FFMPEG_CAPTURE_OPTIONS", (
                    "rtsp_transport;tcp"
                    "|stimeout;5000000"
                    "|fflags;nobuffer+discardcorrupt"
                    "|err_detect;ignore_err"
                    "|flags2;+export_mvs"
                ))
                print(f"[Capture] Đang dùng cấu hình tối ưu cho RTSP: {self.src}")
            elif self.src.startswith("rtmp"):
                set_env_var("OPENCV_FFMPEG_CAPTURE_OPTIONS", (
                    "rtmp_buffer;0"
                    "|fflags;nobuffer+discardcorrupt"
                    "|err_detect;ignore_err"
                    "|flags2;+export_mvs"
                    "|stimeout;5000000"
                ))
                print(f"[Capture] Đang dùng cấu hình tối ưu cho RTMP: {self.src}")
        
        self._reconnect()
        
        # đếm số lần fail liên tiếp
        consecutive_fails = 0

        while self._run_flag:
            if not self.cap.isOpened():
                print("[Capture] Stream chưa mở, đang kết nối lại...")
                self._reconnect()
                continue
            
            # Đọc frame từ stream, return False nếu có lỗi (như mất kết nối), True nếu thành công,frame là ảnh đọc dạng numpy array ví dụ (720,1280,3)    
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
                if consecutive_fails > 30:
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


