import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QImage, QPixmap
from main_app.controllers.main_controller import MainController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-camera Video Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Video display area
        self.video_label = QLabel("Video Placeholder")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white; border: 2px solid gray;")
        self.main_layout.addWidget(self.video_label)

        # Controls layout
        self.controls_layout = QHBoxLayout()
        self.main_layout.addLayout(self.controls_layout)

        self.zoom_in_button = QPushButton("Zoom +")
        self.zoom_out_button = QPushButton("Zoom -")

        self.controls_layout.addWidget(self.zoom_in_button)
        self.controls_layout.addWidget(self.zoom_out_button)

        # Connect signals to slots
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)

        self.main_controller = MainController()
        # Assuming we want to display the first camera's feed
        if self.main_controller.list_camera:
            self.camera_controller = self.main_controller.list_camera[0]
            self.camera_controller.change_pixmap_signal.connect(self.update_image)
        else:
            print("No cameras configured to display.")
            self.camera_controller = None

        self.main_controller.start()

        self.current_zoom_factor = 1.0
        self.original_image_size = QSize(0, 0) # To store the size of the first frame

    def update_image(self, q_image: QImage):
        if self.original_image_size.width() == 0:
            self.original_image_size = q_image.size()

        # Scale the image based on current zoom factor
        scaled_image = q_image.scaled(
            int(self.original_image_size.width() * self.current_zoom_factor),
            int(self.original_image_size.height() * self.current_zoom_factor),
            Qt.KeepAspectRatio
        )
        pixmap = QPixmap.fromImage(scaled_image)
        self.video_label.setPixmap(pixmap)
        self.video_label.resize(pixmap.width(), pixmap.height()) # Adjust label size to pixmap

    def zoom_in(self):
        self.current_zoom_factor *= 1.1 # Increase zoom by 10%
        if self.current_zoom_factor > 5.0: # Limit max zoom
            self.current_zoom_factor = 5.0
        print(f"Zoom In clicked. Current zoom: {self.current_zoom_factor:.2f}")
        # Force update if an image is already displayed
        if self.video_label.pixmap():
            current_qimage = self.video_label.pixmap().toImage()
            self.update_image(current_qimage)


    def zoom_out(self):
        self.current_zoom_factor /= 1.1 # Decrease zoom by 10%
        if self.current_zoom_factor < 0.1: # Limit min zoom
            self.current_zoom_factor = 0.1
        print(f"Zoom Out clicked. Current zoom: {self.current_zoom_factor:.2f}")
        # Force update if an image is already displayed
        if self.video_label.pixmap():
            current_qimage = self.video_label.pixmap().toImage()
            self.update_image(current_qimage)

    def closeEvent(self, event):
        if self.main_controller:
            self.main_controller.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
