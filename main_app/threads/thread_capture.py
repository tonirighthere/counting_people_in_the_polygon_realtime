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
        # Sử dụng FFMPEG làm backend để tối ưu luồng RTSP/RTMP realtime
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_FFMPEG)
        # Buffer = 1 để giảm độ trễ (realtime)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # Yêu cầu decoder bỏ qua lỗi B/P-frame bị mất thay vì spam console
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))

    def run(self):
        # Tắt toàn bộ log spam cảnh báo của FFmpeg (ví dụ: decode_slice_header, Missing reference picture)
        os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"
        
        # Kiểm tra nếu self.src là chuỗi (URL) trước khi dùng .startswith()
        if isinstance(self.src, str):
            if self.src.startswith("rtsp"):
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                    "rtsp_transport;tcp"
                    "|stimeout;5000000"
                    "|fflags;nobuffer+discardcorrupt"
                    "|err_detect;ignore_err"
                    "|flags2;+export_mvs"
                )
                print(f"[Capture] Đang dùng cấu hình tối ưu cho RTSP: {self.src}")
            elif self.src.startswith("rtmp"):
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                    "rtmp_buffer;0"
                    "|fflags;nobuffer+discardcorrupt"
                    "|err_detect;ignore_err"
                    "|flags2;+export_mvs"
                    "|stimeout;5000000"
                )
                print(f"[Capture] Đang dùng cấu hình tối ưu cho RTMP: {self.src}")
        
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
