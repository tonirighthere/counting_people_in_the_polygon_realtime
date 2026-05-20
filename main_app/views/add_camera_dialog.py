from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox

class AddCameraDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm Camera Mới")
        self.setModal(True)
        self.setFixedSize(450, 380)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 10px;
            }
            QLabel {
                color: #bac2de;
                font-size: 13px;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #11111b;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 8px 12px;
                color: #cdd6f4;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #89b4fa;
            }
            QComboBox {
                background-color: #11111b;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 8px 12px;
                color: #cdd6f4;
                font-size: 13px;
            }
            QComboBox:focus {
                border: 1px solid #89b4fa;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QPushButton {
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(12)

        # Title
        title = QLabel("Thêm Camera Mới")
        title.setStyleSheet("color: #89b4fa; font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title)

        # Tên camera
        layout.addWidget(QLabel("Tên Camera:"))
        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("Ví dụ: Camera Cửa Ra Vào, Cam 3")
        layout.addWidget(self.edit_name)

        # URL camera
        layout.addWidget(QLabel("Nguồn Video (URL RTSP/RTMP, File video hoặc số 0):"))
        self.edit_url = QLineEdit()
        self.edit_url.setPlaceholderText("Ví dụ: rtsp://127.0.0.1:8554/cam3 hoặc 0")
        layout.addWidget(self.edit_url)

        # Task camera
        layout.addWidget(QLabel("Nhiệm vụ Phân tích:"))
        self.combo_task = QComboBox()
        self.combo_task.addItem("Đếm Vùng (POLYGON)", "POLYGON")
        self.combo_task.addItem("Vượt Tuyến (LINE_CROSSING)", "LINE_CROSSING")
        layout.addWidget(self.combo_task)

        layout.addSpacing(10)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
        """)
        self.btn_save = QPushButton("Thêm")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
        """)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.validate_and_accept)

    def validate_and_accept(self):
        if not self.edit_name.text().strip():
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập tên camera.")
            return
        if not self.edit_url.text().strip():
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập nguồn Video (RTSP/RTMP hoặc 0).")
            return
        self.accept()

    def get_data(self):
        url_text = self.edit_url.text().strip()
        # Chuyển số nguyên (ví dụ: 0) thành int để sử dụng Webcam làm nguồn stream
        if url_text.isdigit():
            url = int(url_text)
        else:
            url = url_text
        return {
            "name": self.edit_name.text().strip(),
            "url": url,
            "task": self.combo_task.currentData()
        }
