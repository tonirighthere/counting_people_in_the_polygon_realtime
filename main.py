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

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal

from main_app.controllers.main_controller import MainController
from resources.config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, CAMERAS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.setup_sidebar()
        self.setup_main_content()
        
        # Initialize Controller
        self.controller = MainController(self)
        
        # Set initial page
        self.switch_page(0)

    def setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #181825;
                border-right: 1px solid #313244;
            }
            QPushButton {
                background-color: transparent;
                color: #a6adc8;
                border: none;
                padding: 15px;
                text-align: left;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #313244;
                color: #cdd6f4;
            }
            QPushButton#active {
                background-color: #313244;
                color: #89b4fa;
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(10)

        title_label = QLabel("VISION APP")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #89b4fa; padding-bottom: 20px;")
        sidebar_layout.addWidget(title_label)

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_settings = QPushButton("Cài đặt")
        self.btn_exit = QPushButton("Thoát")

        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_settings)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.btn_exit)

        self.btn_exit.clicked.connect(self.close)
        
        # Signals for page switching
        self.btn_dashboard.clicked.connect(lambda: self.switch_page(0))
        self.btn_settings.clicked.connect(lambda: self.switch_page(1))

        self.main_layout.addWidget(self.sidebar)

    def setup_main_content(self):
        self.stacked_widget = QStackedWidget()
        
        # Dashboard Page
        self.dashboard_page = QWidget()
        self.setup_dashboard_ui()
        self.stacked_widget.addWidget(self.dashboard_page)
        
        # Settings Page
        self.settings_page = QWidget()
        self.setup_settings_ui()
        self.stacked_widget.addWidget(self.settings_page)
        
        self.main_layout.addWidget(self.stacked_widget)

    def setup_dashboard_ui(self):
        layout = QVBoxLayout(self.dashboard_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Split screen area for cameras
        self.camera_container = QWidget()
        self.camera_layout = QGridLayout(self.camera_container)
        self.camera_layout.setSpacing(15)
        self.camera_layout.setColumnStretch(0, 1)
        self.camera_layout.setColumnStretch(1, 1)
        
        self.video_labels = {}
        self.stats_labels = {}
        
        # Add cameras to grid (parallel display)
        for i, (cam_id, config) in enumerate(CAMERAS.items()):
            cam_box = QFrame()
            cam_box.setStyleSheet("background-color: #11111b; border: 1px solid #313244; border-radius: 10px;")
            cam_vbox = QVBoxLayout(cam_box)
            
            title = QLabel(config["name"])
            title.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 14px;")
            title.setAlignment(Qt.AlignCenter)
            
            video_label = QLabel("Đang chờ tín hiệu...")
            video_label.setAlignment(Qt.AlignCenter)
            video_label.setStyleSheet("background-color: #000000; border-radius: 5px;")
            video_label.setMinimumSize(400, 300)
            video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            
            stats_label = QLabel("Thông số: --")
            stats_label.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 14px;")
            stats_label.setAlignment(Qt.AlignCenter)
            
            cam_vbox.addWidget(title)
            cam_vbox.addWidget(video_label, stretch=1)
            cam_vbox.addWidget(stats_label)
            
            # Grid placement (0,0) and (0,1) for 2 cameras side by side
            row = i // 2
            col = i % 2
            self.camera_layout.addWidget(cam_box, row, col)
            
            self.video_labels[cam_id] = video_label
            self.stats_labels[cam_id] = stats_label

        layout.addWidget(self.camera_container, stretch=1)

        # Bottom controls
        control_panel = QFrame()
        control_panel.setStyleSheet("background-color: #181825; border-radius: 10px; padding: 10px;")
        control_layout = QHBoxLayout(control_panel)
        
        self.status_label = QLabel("Trạng thái: Sẵn sàng")
        self.status_label.setStyleSheet("color: #bac2de; font-size: 14px;")
        
        self.btn_start = QPushButton("Bắt đầu")
        self.btn_stop = QPushButton("Dừng")
        
        button_style = """
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border-radius: 5px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #74c7ec; }
        """
        self.btn_start.setStyleSheet(button_style)
        self.btn_stop.setStyleSheet(button_style.replace("#89b4fa", "#f38ba8").replace("#74c7ec", "#eba0ac"))
        
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        
        layout.addWidget(control_panel)

    def setup_settings_ui(self):
        layout = QVBoxLayout(self.settings_page)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Cài đặt hệ thống")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #89b4fa;")
        
        desc = QLabel("Trang cấu hình camera và tham số AI")
        desc.setStyleSheet("color: #a6adc8; font-size: 16px;")
        
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addSpacing(50)
        
        # Placeholder for settings items
        placeholder = QFrame()
        placeholder.setFixedSize(400, 300)
        placeholder.setStyleSheet("background-color: #181825; border: 1px dashed #45475a; border-radius: 15px;")
        layout.addWidget(placeholder)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        # Update button styles
        self.btn_dashboard.setObjectName("active" if index == 0 else "")
        self.btn_settings.setObjectName("active" if index == 1 else "")
        self.sidebar.style().unpolish(self.btn_dashboard)
        self.sidebar.style().polish(self.btn_dashboard)
        self.sidebar.style().unpolish(self.btn_settings)
        self.sidebar.style().polish(self.btn_settings)

    def on_frame_received(self, cam_id, qt_img):
        if cam_id in self.video_labels:
            label = self.video_labels[cam_id]
            # Scale image to fit label while keeping aspect ratio
            scaled_img = qt_img.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(QPixmap.fromImage(scaled_img))

    def on_stats_received(self, cam_id, counts):
        if cam_id in self.stats_labels:
            label = self.stats_labels[cam_id]
            if "in" in counts and "out" in counts:
                label.setText(f"Vào: {counts['in']} | Ra: {counts['out']}")
            elif "count" in counts:
                label.setText(f"Hiện tại: {counts['count']} người")
            else:
                label.setText("Đang phân tích...")

    def closeEvent(self, event):
        if hasattr(self, 'controller'):
            self.controller.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

