from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy

class CameraCard(QFrame):
    # Signals for communication with parent
    toggle_clicked = pyqtSignal(str)  # Emits cam_id
    delete_clicked = pyqtSignal(str)  # Emits cam_id

    def __init__(self, cam_id, name, parent=None):
        super().__init__(parent)
        self.cam_id = cam_id
        self.name = name
        
        self.setStyleSheet("background-color: #11111b; border: 1px solid #313244; border-radius: 10px;")
        
        # Main layout
        card_vbox = QVBoxLayout(self)
        card_vbox.setContentsMargins(12, 12, 12, 12)
        card_vbox.setSpacing(10)
        
        # Header Layout (Title + Status Indicator)
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel(self.name)
        self.title_label.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 14px;")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Status Indicator: dot + text
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #a6adc8; font-size: 14px; padding-right: 2px;")
        self.status_text = QLabel("Đã dừng")
        self.status_text.setStyleSheet("color: #a6adc8; font-size: 12px; font-weight: bold;")
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_dot)
        header_layout.addWidget(self.status_text)
        
        card_vbox.addLayout(header_layout)
        
        # Video Display Label
        self.video_label = QLabel("Đang chờ tín hiệu...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000000; border-radius: 5px; color: #a6adc8; font-size: 14px;")
        self.video_label.setMinimumSize(400, 300)
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        card_vbox.addWidget(self.video_label, stretch=1)
        
        # Stats Label
        self.stats_label = QLabel("Thông số: --")
        self.stats_label.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 14px;")
        self.stats_label.setAlignment(Qt.AlignCenter)
        card_vbox.addWidget(self.stats_label)
        
        # Bottom Action Bar
        action_layout = QHBoxLayout()
        
        self.btn_toggle = QPushButton("Tắt Cam")
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #45475a; }
        """)
        
        self.btn_delete = QPushButton("Xóa Cam")
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8;
                color: #11111b;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #eba0ac; }
        """)
        
        action_layout.addWidget(self.btn_toggle, stretch=1)
        action_layout.addWidget(self.btn_delete, stretch=1)
        card_vbox.addLayout(action_layout)
        
        # Connect internal buttons to signals
        self.btn_toggle.clicked.connect(lambda: self.toggle_clicked.emit(self.cam_id))
        self.btn_delete.clicked.connect(lambda: self.delete_clicked.emit(self.cam_id))

    def update_ui(self, is_active, is_running):
        # Update styling based on active & running state
        if not is_active:
            self.status_dot.setStyleSheet("color: #f38ba8; font-size: 14px; padding-right: 2px;") # Red
            self.status_text.setText("Đã tắt")
            self.status_text.setStyleSheet("color: #f38ba8; font-size: 12px; font-weight: bold;")
            self.btn_toggle.setText("Bật Cam")
            self.btn_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #a6e3a1;
                    color: #11111b;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #94e2d5; }
            """)
            self.video_label.clear()
            self.video_label.setText("Camera Đang Tắt")
        else:
            if is_running:
                self.status_dot.setStyleSheet("color: #a6e3a1; font-size: 14px; padding-right: 2px;") # Green
                self.status_text.setText("Đang chạy")
                self.status_text.setStyleSheet("color: #a6e3a1; font-size: 12px; font-weight: bold;")
            else:
                self.status_dot.setStyleSheet("color: #f9e2af; font-size: 14px; padding-right: 2px;") # Yellow/orange
                self.status_text.setText("Sẵn sàng")
                self.status_text.setStyleSheet("color: #f9e2af; font-size: 12px; font-weight: bold;")
                
            self.btn_toggle.setText("Tắt Cam")
            self.btn_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #313244;
                    color: #cdd6f4;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #45475a; }
            """)

    def set_frame(self, qt_img):
        # Performance optimization: Scale image to fit label size using FastTransformation to preserve aspect ratio without lagging the GUI thread
        scaled_img = qt_img.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.FastTransformation)
        self.video_label.setPixmap(QPixmap.fromImage(scaled_img))

    def set_stats(self, counts):
        if "in" in counts and "out" in counts:
            self.stats_label.setText(f"Vào: {counts['in']} | Ra: {counts['out']}")
        elif "count" in counts:
            self.stats_label.setText(f"Hiện tại: {counts['count']} người")
        else:
            self.stats_label.setText("Đang phân tích...")

    def clear_video_feed(self, message):
        self.video_label.clear()
        self.video_label.setText(message)
        self.stats_label.setText("Thông số: --")
