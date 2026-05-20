import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QWidget, QStackedWidget, QGridLayout, 
                             QComboBox, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFont
from main_app.controllers.main_controller import MainController
from resources.config.setting import TARGET_WIDTH, TARGET_HEIGHT
from gui.camera_manager import CameraManagerDialog

class VideoLabel(QLabel):

    double_clicked = pyqtSignal(int)

    def __init__(self, camera_id: int, parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
        self.current_qimage = None
        self.zoom_factor = 1.0
        
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(240, 135)  # 16:9 safe minimum size
        
        # Premium dark styling for camera slot
        self.setStyleSheet("""
            QLabel {
                background-color: #111115;
                color: #64748b;
                border: 2px solid #1e1e24;
                border-radius: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
        """)
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
        
        # Calculate size based on current label bounds and zoom factor
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            w = TARGET_WIDTH
            h = TARGET_HEIGHT

        target_w = int(w * self.zoom_factor)
        target_h = int(h * self.zoom_factor)

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Giám sát Đa luồng Camera")
        self.showMaximized()

        # Configs
        self.cameras_per_page = 4  # 2x2 grid
        self.current_zoom_factor = 1.0
        self.last_qimages = {}
        self.camera_labels = {}
        self.maximized_camera_id = None

        # Main Setup Stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0b0e;
            }
            QWidget#central_widget {
                background-color: #0b0b0e;
            }
            QFrame#control_panel {
                background-color: #121216;
                border-top: 1px solid #1e1e24;
            }
            QPushButton {
                background-color: #1e1e24;
                color: #e2e8f0;
                border: 1px solid #2d2d37;
                border-radius: 6px;
                padding: 8px 16px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2b2b36;
                border-color: #3b82f6;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #141418;
            }
            QPushButton:disabled {
                background-color: #0d0d10;
                color: #475569;
                border-color: #18181b;
            }
            QPushButton#nav_btn {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
            }
            QPushButton#nav_btn:hover {
                background-color: #1d4ed8;
            }
            QPushButton#nav_btn:disabled {
                background-color: #1e293b;
                color: #64748b;
            }
            QComboBox {
                background-color: #1e1e24;
                color: #e2e8f0;
                border: 1px solid #2d2d37;
                border-radius: 6px;
                padding: 6px 12px;
                min-width: 150px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #121216;
                color: #e2e8f0;
                selection-background-color: #2563eb;
                border: 1px solid #2d2d37;
            }
            QLabel {
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        # Core layouts
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)

        # Header Title / Status bar
        self.header_layout = QHBoxLayout()
        self.title_label = QLabel("MULTI-CAMERA")
        self.title_label.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: bold; letter-spacing: 1px;")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        # Quick Camera Selector
        self.camera_selector = QComboBox()
        self.camera_selector.addItem("ALL", -1)
        self.camera_selector.currentIndexChanged.connect(self.on_selector_changed)
        self.header_layout.addWidget(self.camera_selector)
        
        # Camera Manager Button
        self.manage_cameras_btn = QPushButton("⚙ Quản lý Camera")
        self.manage_cameras_btn.clicked.connect(self.open_camera_manager)
        self.header_layout.addWidget(self.manage_cameras_btn)
        
        self.main_layout.addLayout(self.header_layout)

        # Main Stacked Layout (Page 0: Grid mode, Page 1: Single view mode)
        self.main_stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.main_stacked_widget)

        # Page 0: Grid mode (contains another stacked widget for paginated grid pages)
        self.grid_stacked_widget = QStackedWidget()
        self.main_stacked_widget.addWidget(self.grid_stacked_widget)

        # Page 1: Single camera view
        self.single_view_container = QWidget()
        self.single_view_layout = QVBoxLayout(self.single_view_container)
        self.single_view_layout.setContentsMargins(0, 0, 0, 0)
        self.single_view_label = VideoLabel(-1, self)
        self.single_view_layout.addWidget(self.single_view_label)
        self.main_stacked_widget.addWidget(self.single_view_container)

        # Controls panel bottom bar
        self.control_panel = QFrame()
        self.control_panel.setObjectName("control_panel")
        self.control_panel.setStyleSheet("border-radius: 8px;")
        self.control_panel_layout = QHBoxLayout(self.control_panel)
        self.control_panel_layout.setContentsMargins(12, 12, 12, 12)
        
        # Pagination buttons
        self.prev_button = QPushButton("◀ Trang trước")
        self.prev_button.setObjectName("nav_btn")
        self.page_indicator = QLabel("Trang 1 / 1")
        self.page_indicator.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: bold; margin: 0 10px;")
        self.next_button = QPushButton("Trang sau ▶")
        self.next_button.setObjectName("nav_btn")
        
        self.prev_button.clicked.connect(self.show_prev_page)
        self.next_button.clicked.connect(self.show_next_page)
        
        self.control_panel_layout.addWidget(self.prev_button)
        self.control_panel_layout.addWidget(self.page_indicator)
        self.control_panel_layout.addWidget(self.next_button)
        self.control_panel_layout.addStretch()

        # Zoom controls
        self.zoom_in_button = QPushButton("Phóng to +")
        self.zoom_out_button = QPushButton("Thu nhỏ -")
        self.zoom_reset_button = QPushButton("Đặt lại Zoom")
        
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_reset_button.clicked.connect(self.zoom_reset)

        self.control_panel_layout.addWidget(self.zoom_in_button)
        self.control_panel_layout.addWidget(self.zoom_out_button)
        self.control_panel_layout.addWidget(self.zoom_reset_button)

        self.main_layout.addWidget(self.control_panel)

        self.main_controller = MainController()

        if self.main_controller.list_camera:
            for camera_controller in self.main_controller.list_camera:
                self.register_camera(camera_controller.camera_id)
                camera_controller.change_pixmap_signal.connect(self.update_image)#...
        else:
            print("No cameras configured to display.")


        self.rebuild_pages()
        self.show_grid_view()


        self.main_controller.start()

    def register_camera(self, camera_id: int):
        if camera_id in self.camera_labels:
            return

        label = VideoLabel(camera_id, self)
        label.double_clicked.connect(self.toggle_maximize_camera)
        self.camera_labels[camera_id] = label

        self.camera_selector.addItem(f"Camera {camera_id}", camera_id)
        
        self.rebuild_pages()

    def rebuild_pages(self):
        old_page_index = self.grid_stacked_widget.currentIndex()


        while self.grid_stacked_widget.count() > 0:
            widget = self.grid_stacked_widget.widget(0)
            self.grid_stacked_widget.removeWidget(widget)
            widget.deleteLater()

        sorted_cam_ids = sorted(list(self.camera_labels.keys()))
        num_cams = len(sorted_cam_ids)
        
        if num_cams == 0:

            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            placeholder = QLabel("Không tìm thấy luồng camera nào.\nHãy kiểm tra file cấu hình camera.yml.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #64748b; font-size: 16px; font-weight: bold;")
            empty_layout.addWidget(placeholder)
            self.grid_stacked_widget.addWidget(empty_widget)
            self.prev_button.setDisabled(True)
            self.next_button.setDisabled(True)
            self.page_indicator.setText("Trang 1 / 1")
            return


        num_pages = max(1, (num_cams + self.cameras_per_page - 1) // self.cameras_per_page)

        for p in range(num_pages):
            page_widget = QWidget()
            grid_layout = QGridLayout(page_widget)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            grid_layout.setSpacing(12)

            start_idx = p * self.cameras_per_page
            end_idx = min(start_idx + self.cameras_per_page, num_cams)

            for i in range(start_idx, end_idx):
                cam_id = sorted_cam_ids[i]
                label = self.camera_labels[cam_id]
                

                local_idx = i - start_idx
                row = local_idx // 2
                col = local_idx % 2
                grid_layout.addWidget(label, row, col)

            self.grid_stacked_widget.addWidget(page_widget)


        if 0 <= old_page_index < num_pages:
            self.grid_stacked_widget.setCurrentIndex(old_page_index)
        else:
            self.grid_stacked_widget.setCurrentIndex(0)

        self.update_pagination_ui()

    def update_pagination_ui(self):
        if self.maximized_camera_id is not None:
            # In single camera view, hide pagination
            self.prev_button.setDisabled(True)
            self.next_button.setDisabled(True)
            self.page_indicator.setText("Chế độ xem đơn")
            return

        total_pages = self.grid_stacked_widget.count()
        current_page = self.grid_stacked_widget.currentIndex() + 1
        
        self.page_indicator.setText(f"Trang {current_page} / {total_pages}")
        self.prev_button.setEnabled(current_page > 1)
        self.next_button.setEnabled(current_page < total_pages)

    def show_prev_page(self):
        curr = self.grid_stacked_widget.currentIndex()
        if curr > 0:
            self.grid_stacked_widget.setCurrentIndex(curr - 1)
            self.update_pagination_ui()

    def show_next_page(self):
        curr = self.grid_stacked_widget.currentIndex()
        if curr < self.grid_stacked_widget.count() - 1:
            self.grid_stacked_widget.setCurrentIndex(curr + 1)
            self.update_pagination_ui()

    def show_grid_view(self):
        self.maximized_camera_id = None
        self.main_stacked_widget.setCurrentIndex(0)  # Show Grid mode page
        

        self.camera_selector.blockSignals(True)
        self.camera_selector.setCurrentIndex(0)
        self.camera_selector.blockSignals(False)
        
        self.update_pagination_ui()

    def show_single_view(self, camera_id: int):
        self.maximized_camera_id = camera_id
        
        # Load last image to avoid blank screen transition
        if camera_id in self.last_qimages:
            self.single_view_label.set_qimage(self.last_qimages[camera_id], self.current_zoom_factor)
        else:
            self.single_view_label.setText(f"Camera {camera_id}\nKhông có tín hiệu hoặc đang tải...")
            self.single_view_label.current_qimage = None

        self.main_stacked_widget.setCurrentIndex(1)  # Show Single View page
        

        self.camera_selector.blockSignals(True)
        for i in range(self.camera_selector.count()):
            if self.camera_selector.itemData(i) == camera_id:
                self.camera_selector.setCurrentIndex(i)
                break
        self.camera_selector.blockSignals(False)
        
        self.update_pagination_ui()

    def toggle_maximize_camera(self, camera_id: int):
        if self.maximized_camera_id is not None:
            self.show_grid_view()
        else:
            self.show_single_view(camera_id)

    def on_selector_changed(self, index: int):
        camera_id = self.camera_selector.itemData(index)
        if camera_id == -1:
            self.show_grid_view()
        else:
            self.show_single_view(camera_id)

    def update_image(self, camera_id: int, q_image: QImage):
        # Automatically register a camera if a new thread/id starts emitting at runtime
        if camera_id not in self.camera_labels:
            self.register_camera(camera_id)

        self.last_qimages[camera_id] = q_image


        self.camera_labels[camera_id].set_qimage(q_image, self.current_zoom_factor)


        if self.maximized_camera_id == camera_id:
            self.single_view_label.set_qimage(q_image, self.current_zoom_factor)

    def zoom_in(self):
        self.current_zoom_factor *= 1.15
        if self.current_zoom_factor > 5.0:
            self.current_zoom_factor = 5.0
        self._reapply_zoom()

    def zoom_out(self):
        self.current_zoom_factor /= 1.15
        if self.current_zoom_factor < 0.2:
            self.current_zoom_factor = 0.2
        self._reapply_zoom()

    def zoom_reset(self):
        self.current_zoom_factor = 1.0
        self._reapply_zoom()

    def _reapply_zoom(self):
        for cam_id, label in self.camera_labels.items():
            if cam_id in self.last_qimages:
                label.set_qimage(self.last_qimages[cam_id], self.current_zoom_factor)

        if self.maximized_camera_id is not None and self.maximized_camera_id in self.last_qimages:
            self.single_view_label.set_qimage(self.last_qimages[self.maximized_camera_id], self.current_zoom_factor)

    def open_camera_manager(self):
        dialog = CameraManagerDialog(self.main_controller.cameras_config, self)
        dialog.camera_added.connect(self.on_camera_added)
        dialog.camera_updated.connect(self.on_camera_updated)
        dialog.camera_deleted.connect(self.on_camera_deleted)
        dialog.exec_()

    def on_camera_added(self, camera_id: int, camera_config: dict):
        camera_controller = self.main_controller.add_camera_stream(camera_id, camera_config)
        self.register_camera(camera_id)
        camera_controller.change_pixmap_signal.connect(self.update_image)

    def on_camera_updated(self, camera_id: int, camera_config: dict):
        camera_controller = self.main_controller.update_camera_stream(camera_id, camera_config)
        camera_controller.change_pixmap_signal.connect(self.update_image)

    def on_camera_deleted(self, camera_id: int):
        self.main_controller.delete_camera_stream(camera_id)
        
        # Remove VideoLabel widget
        if camera_id in self.camera_labels:
            label = self.camera_labels[camera_id]
            label.deleteLater()
            del self.camera_labels[camera_id]

        # Remove from combobox
        for i in range(self.camera_selector.count()):
            if self.camera_selector.itemData(i) == camera_id:
                self.camera_selector.removeItem(i)
                break

        # Remove from cached images
        if camera_id in self.last_qimages:
            del self.last_qimages[camera_id]

        # Revert single view if the deleted camera was maximized
        if self.maximized_camera_id == camera_id:
            self.show_grid_view()

        self.rebuild_pages()

    def closeEvent(self, event):
        if self.main_controller:
            self.main_controller.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
