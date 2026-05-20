import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QGridLayout, QSizePolicy,
    QScrollArea, QDialog, QMessageBox
)

from main_app.controllers.main_controller import MainController
from resources.config import WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, CAMERAS
from .add_camera_dialog import AddCameraDialog
from .camera_card import CameraCard

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
        
        # Dynamically build camera grid now that controller is initialized
        self.rebuild_camera_grid()
        
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

        # ScrollArea to support dynamic multiple cameras
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        self.camera_container = QWidget()
        self.camera_container.setStyleSheet("background-color: transparent;")
        self.camera_layout = QGridLayout(self.camera_container)
        self.camera_layout.setSpacing(15)
        self.camera_layout.setContentsMargins(0, 0, 0, 0)
        self.camera_layout.setColumnStretch(0, 1)
        self.camera_layout.setColumnStretch(1, 1)
        
        scroll.setWidget(self.camera_container)
        layout.addWidget(scroll, stretch=1)
        
        # Dictionaries for backward compatibility with MainController
        self.camera_cards = {}
        self.video_labels = {}
        self.stats_labels = {}
        self.camera_status_dots = {}
        self.camera_status_texts = {}
        self.camera_toggle_buttons = {}

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

    def rebuild_camera_grid(self):
        # 1. Clear layout safely to prevent memory leaks and ghost widgets
        while self.camera_layout.count():
            child = self.camera_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        self.camera_cards = {}
        self.video_labels = {}
        self.stats_labels = {}
        self.camera_status_dots = {}
        self.camera_status_texts = {}
        self.camera_toggle_buttons = {}
        
        # 2. Add cameras to grid (parallel display)
        cameras_list = list(self.controller.cameras.items())
        for i, (cam_id, cam) in enumerate(cameras_list):
            cam_config = CAMERAS.get(cam_id, {
                "name": f"Camera {cam_id}",
                "url": cam.src,
                "task": cam.task
            })
            
            # Use modular CameraCard component
            card = CameraCard(cam_id, cam_config["name"], self)
            
            # Connect signals to MainWindow callbacks
            card.toggle_clicked.connect(self.controller.toggle_camera_active)
            card.delete_clicked.connect(self.confirm_and_remove_camera)
            
            # Add to Grid Layout
            row = i // 2
            col = i % 2
            self.camera_layout.addWidget(card, row, col)
            
            # Cache for direct operations and backward compatibility
            self.camera_cards[cam_id] = card
            self.video_labels[cam_id] = card.video_label
            self.stats_labels[cam_id] = card.stats_label
            self.camera_status_dots[cam_id] = card.status_dot
            self.camera_status_texts[cam_id] = card.status_text
            self.camera_toggle_buttons[cam_id] = card.btn_toggle
            
            # Initialize card UI state
            self.update_camera_card_ui(cam_id)
            
        # 3. Add the Plus "+" Card for adding camera
        plus_card = QFrame()
        plus_card.setMinimumSize(400, 380)
        plus_card.setStyleSheet("""
            QFrame {
                border: 2px dashed #45475a;
                border-radius: 10px;
                background-color: #11111b;
            }
            QFrame:hover {
                border-color: #89b4fa;
                background-color: #181825;
            }
        """)
        plus_card.setCursor(Qt.PointingHandCursor)
        plus_layout = QVBoxLayout(plus_card)
        plus_layout.setAlignment(Qt.AlignCenter)
        plus_layout.setSpacing(15)
        
        lbl_plus = QLabel("+")
        lbl_plus.setStyleSheet("color: #45475a; font-size: 56px; font-weight: bold; border: none; background-color: transparent;")
        lbl_plus.setAlignment(Qt.AlignCenter)
        
        lbl_add_text = QLabel("Thêm Camera Mới")
        lbl_add_text.setStyleSheet("color: #a6adc8; font-size: 16px; font-weight: bold; border: none; background-color: transparent;")
        lbl_add_text.setAlignment(Qt.AlignCenter)
        
        plus_layout.addWidget(lbl_plus)
        plus_layout.addWidget(lbl_add_text)
        
        plus_card.mousePressEvent = lambda event: self.show_add_camera_dialog()
        
        plus_index = len(cameras_list)
        row = plus_index // 2
        col = plus_index % 2
        self.camera_layout.addWidget(plus_card, row, col)

    def update_camera_card_ui(self, cam_id):
        if cam_id not in self.camera_cards or not hasattr(self, 'controller'):
            return
            
        cam = self.controller.cameras.get(cam_id)
        if not cam:
            return
            
        # Delegate UI update to the card component
        self.camera_cards[cam_id].update_ui(cam.is_active, self.controller.is_running)

    def confirm_and_remove_camera(self, cam_id):
        # Find camera name
        from resources.config import CAMERAS
        cam_name = CAMERAS.get(cam_id, {}).get("name", cam_id)
        
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa camera '{cam_name}' không?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.controller.remove_camera(cam_id)
            if success:
                # Rebuild grid to reflect the change
                self.rebuild_camera_grid()
                self.status_label.setText(f"Đã xóa camera: {cam_name}")
                self.status_label.setStyleSheet("color: #f38ba8;")

    def show_add_camera_dialog(self):
        dialog = AddCameraDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            cam_id = self.controller.add_camera(
                name=data["name"],
                url=data["url"],
                task=data["task"]
            )
            # Rebuild grid to show new camera card
            self.rebuild_camera_grid()
            self.status_label.setText(f"Đã thêm camera mới: {data['name']}")
            self.status_label.setStyleSheet("color: #a6e3a1;")

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
        if cam_id in self.camera_cards:
            self.camera_cards[cam_id].set_frame(qt_img)

    def on_stats_received(self, cam_id, counts):
        if cam_id in self.camera_cards:
            self.camera_cards[cam_id].set_stats(counts)

    def closeEvent(self, event):
        if hasattr(self, 'controller'):
            self.controller.close()
        event.accept()
