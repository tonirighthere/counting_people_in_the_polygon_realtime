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

# Tắt toàn bộ log spam cảnh báo của FFmpeg / OpenCV trước khi import bất kỳ thư viện nào khác
set_env_var("OPENCV_FFMPEG_LOGLEVEL", "-8")
set_env_var("OPENCV_LOG_LEVEL", "OFF")

from PyQt5.QtWidgets import QApplication
from main_app.views.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
