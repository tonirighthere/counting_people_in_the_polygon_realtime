import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame
)
from main_app.controllers.main_controller import MainController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Vision Dashboard - Polygon RTSP")
        self.resize(1000, 600)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.setup_sidebar()
        self.setup_main_content()
        
        # Khởi tạo Controller điều khiển logic
        self.controller = MainController(self)

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
        self.main_layout.addWidget(self.sidebar)

    def setup_main_content(self):
        self.content_area = QFrame()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.video_label = QLabel("Camera Feed Sẽ Hiển Thị Ở Đây")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #11111b;
                border: 2px dashed #45475a;
                border-radius: 10px;
                font-size: 16px;
                color: #7f849c;
            }
        """)
        content_layout.addWidget(self.video_label, stretch=3)

        control_layout = QHBoxLayout()
        
        self.status_label = QLabel("Trạng thái: Đang dừng")
        self.status_label.setFont(QFont("Arial", 12))
        
        self.stats_in_zone = QLabel("Trong Polygon: 0 người")
        self.stats_in_zone.setFont(QFont("Arial", 14, QFont.Bold))
        self.stats_in_zone.setStyleSheet("color: #a6e3a1; font-weight: bold; padding: 5px;")

        self.btn_start = QPushButton("▶ Bắt đầu")
        self.btn_stop = QPushButton("⏹ Dừng")
        
        button_style = """
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #74c7ec; }
            QPushButton:pressed { background-color: #89dceb; }
        """
        self.btn_start.setStyleSheet(button_style)
        self.btn_stop.setStyleSheet(button_style.replace("#89b4fa", "#f38ba8").replace("#74c7ec", "#eba0ac").replace("#89dceb", "#f5c2e7"))

        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.stats_in_zone)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)

        content_layout.addLayout(control_layout, stretch=1)
        self.main_layout.addWidget(self.content_area)

    def update_image(self, qt_img):
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))
        self.video_label.setStyleSheet("border: 2px solid #89b4fa; border-radius: 10px;")

    def update_stats(self, count_in):
        self.stats_in_zone.setText(f"Trong Polygon: {count_in} người")

    def closeEvent(self, event):
        if hasattr(self, 'controller'):
            self.controller.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
