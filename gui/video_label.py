from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from resources.config.setting import TARGET_WIDTH, TARGET_HEIGHT
from gui.styles import VIDEO_LABEL_STYLE

class VideoLabel(QLabel):
    double_clicked = pyqtSignal(int)

    def __init__(self, camera_id: int, parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
        self.current_qimage = None
        self.zoom_factor = 1.0
        
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(240, 135)
        self.setStyleSheet(VIDEO_LABEL_STYLE)
        
        if self.camera_id >= 0:
            self.setText(f"Camera {self.camera_id}\nĐang kết nối...")
        else:
            self.setText("Không có tín hiệu")

    def set_qimage(self, q_image: QImage, zoom_factor: float = 1.0):
        self.current_qimage = q_image
        self.zoom_factor = zoom_factor
        self.update_display()

    def update_display(self):
        if not self.current_qimage:
            return
        
        pixmap = QPixmap.fromImage(self.current_qimage)
        w = self.width() if self.width() > 0 else TARGET_WIDTH
        h = self.height() if self.height() > 0 else TARGET_HEIGHT

        target_w = int(w * self.zoom_factor)
        target_h = int(h * self.zoom_factor)

        scaled_pixmap = pixmap.scaled(
            target_w, target_h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.camera_id)
