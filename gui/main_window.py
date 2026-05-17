import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QImage, QPixmap
from main_app.controllers.main_controller import MainController
from resources.config.setting import TARGET_WIDTH, TARGET_HEIGHT # Import TARGET_WIDTH and TARGET_HEIGHT

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-camera Video Viewer")
        self.showMaximized() # Maximize window on startup

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Video display area
        self.video_display_layout = QHBoxLayout() # Layout for displaying multiple videos
        self.main_layout.addLayout(self.video_display_layout)

        self.video_label_cam1 = QLabel("Cam1 Placeholder")
        self.video_label_cam1.setAlignment(Qt.AlignCenter)
        self.video_label_cam1.setStyleSheet("background-color: black; color: white; border: 2px solid gray;")
        self.video_label_cam1.setScaledContents(True) # Allow QLabel to scale its contents
        self.video_display_layout.addWidget(self.video_label_cam1)

        self.video_label_cam2 = QLabel("Cam2 Placeholder")
        self.video_label_cam2.setAlignment(Qt.AlignCenter)
        self.video_label_cam2.setStyleSheet("background-color: black; color: white; border: 2px solid gray;")
        self.video_label_cam2.setScaledContents(True) # Allow QLabel to scale its contents
        self.video_display_layout.addWidget(self.video_label_cam2)
        self.video_label_cam2.hide() # Initially hide Cam2

        # Controls layout
        self.controls_layout = QHBoxLayout()
        self.main_layout.addLayout(self.controls_layout)

        # Camera selection buttons
        self.cam1_button = QPushButton("Cam1")
        self.cam2_button = QPushButton("Cam2")
        self.all_cams_button = QPushButton("All")

        self.controls_layout.addWidget(self.cam1_button)
        self.controls_layout.addWidget(self.cam2_button)
        self.controls_layout.addWidget(self.all_cams_button)
        self.controls_layout.addStretch() # Push buttons to the left

        # Zoom buttons
        self.zoom_in_button = QPushButton("Zoom +")
        self.zoom_out_button = QPushButton("Zoom -")

        self.controls_layout.addWidget(self.zoom_in_button)
        self.controls_layout.addWidget(self.zoom_out_button)

        # Connect signals
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.cam1_button.clicked.connect(lambda: self.set_camera_mode("cam1"))
        self.cam2_button.clicked.connect(lambda: self.set_camera_mode("cam2"))
        self.all_cams_button.clicked.connect(lambda: self.set_camera_mode("all"))

        self.main_controller = MainController()

        # Connect signals from each CameraController
        if self.main_controller.list_camera:
            for camera_controller in self.main_controller.list_camera:
                camera_controller.change_pixmap_signal.connect(self.update_image)
        else:
            print("No cameras configured to display.")

        self.main_controller.start()

        self.current_zoom_factor = 1.0
        # Initialize original_image_size using TARGET_WIDTH and TARGET_HEIGHT
        self.original_image_size = QSize(TARGET_WIDTH, TARGET_HEIGHT) 
        self.last_qimages = {} # Store last QImage for each camera for zoom
        self.set_camera_mode("cam1") # Initialize display

    def set_camera_mode(self, mode):
        self.current_camera_mode = mode
        if mode == "cam1":
            self.video_label_cam1.show()
            self.video_label_cam2.hide()
            if 0 in self.last_qimages:
                self._display_image(self.video_label_cam1, self.last_qimages[0])
        elif mode == "cam2":
            self.video_label_cam1.hide()
            self.video_label_cam2.show()
            if 1 in self.last_qimages:
                self._display_image(self.video_label_cam2, self.last_qimages[1])
        elif mode == "all":
            self.video_label_cam1.show()
            self.video_label_cam2.show()
            if 0 in self.last_qimages:
                self._display_image(self.video_label_cam1, self.last_qimages[0])
            if 1 in self.last_qimages:
                self._display_image(self.video_label_cam2, self.last_qimages[1])

    def _display_image(self, label: QLabel, q_image: QImage):
        # Create QPixmap from QImage
        pixmap = QPixmap.fromImage(q_image)
        
        # Scale the QPixmap based on zoom factor
        scaled_pixmap = pixmap.scaled(
            int(self.original_image_size.width() * self.current_zoom_factor),
            int(self.original_image_size.height() * self.current_zoom_factor),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation # For better quality scaling
        )
        label.setPixmap(scaled_pixmap)
        # label.resize(pixmap.width(), pixmap.height()) # Removed: Let setScaledContents handle this

    def update_image(self, camera_id: int, q_image: QImage):
        self.last_qimages[camera_id] = q_image # Store the last received image

        if camera_id == 0 and (self.current_camera_mode == "cam1" or self.current_camera_mode == "all"):
            self._display_image(self.video_label_cam1, q_image)
        elif camera_id == 1 and (self.current_camera_mode == "cam2" or self.current_camera_mode == "all"):
            self._display_image(self.video_label_cam2, q_image)


    def zoom_in(self):
        self.current_zoom_factor *= 1.1 # Increase zoom by 10%
        if self.current_zoom_factor > 5.0: # Limit max zoom
            self.current_zoom_factor = 5.0
        print(f"Zoom In clicked. Current zoom: {self.current_zoom_factor:.2f}")
        self._reapply_zoom()

    def zoom_out(self):
        self.current_zoom_factor /= 1.1
        if self.current_zoom_factor < 0.1:
            self.current_zoom_factor = 0.1
        print(f"Zoom Out clicked. Current zoom: {self.current_zoom_factor:.2f}")
        self._reapply_zoom()

    def _reapply_zoom(self):
        # Re-display the last images with the new zoom factor
        if self.current_camera_mode == "cam1" and 0 in self.last_qimages:
            self._display_image(self.video_label_cam1, self.last_qimages[0])
        elif self.current_camera_mode == "cam2" and 1 in self.last_qimages:
            self._display_image(self.video_label_cam2, self.last_qimages[1])
        elif self.current_camera_mode == "all":
            if 0 in self.last_qimages:
                self._display_image(self.video_label_cam1, self.last_qimages[0])
            if 1 in self.last_qimages:
                self._display_image(self.video_label_cam2, self.last_qimages[1])


    def closeEvent(self, event):
        if self.main_controller:
            self.main_controller.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
