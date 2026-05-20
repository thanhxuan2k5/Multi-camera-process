import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QWidget, QStackedWidget, QGridLayout, QComboBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from main_app.controllers.main_controller import MainController
from resources.config.setting import TARGET_WIDTH, TARGET_HEIGHT
from gui.video_label import VideoLabel
from gui.camera_manager import CameraManagerDialog
from gui.styles import MAIN_WINDOW_STYLE

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Giám sát Đa luồng Camera")
        self.showMaximized(); self.setStyleSheet(MAIN_WINDOW_STYLE)

        self.cameras_per_page = 4; self.current_zoom_factor = 1.0
        self.last_qimages = {}; self.camera_labels = {}; self.maximized_camera_id = None

        self.central_widget = QWidget(); self.central_widget.setObjectName("central_widget")
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(15, 15, 15, 15); self.main_layout.setSpacing(15)

        # Header Setup
        self.header_layout = QHBoxLayout()
        title_label = QLabel("MULTI-CAMERA")
        title_label.setStyleSheet("color: #f8fafc; font-size: 18px; font-weight: bold; letter-spacing: 1px;")
        self.header_layout.addWidget(title_label); self.header_layout.addStretch()
        
        self.camera_selector = QComboBox(); self.camera_selector.addItem("ALL", -1)
        self.camera_selector.currentIndexChanged.connect(self.on_selector_changed)
        self.header_layout.addWidget(self.camera_selector)
        
        manage_cameras_btn = QPushButton("⚙ Quản lý Camera")
        manage_cameras_btn.clicked.connect(self.open_camera_manager); self.header_layout.addWidget(manage_cameras_btn)
        self.main_layout.addLayout(self.header_layout)

        # Pages View (Grid & Single)
        self.main_stacked_widget = QStackedWidget(); self.grid_stacked_widget = QStackedWidget()
        self.main_stacked_widget.addWidget(self.grid_stacked_widget)

        self.single_view_container = QWidget()
        single_view_layout = QVBoxLayout(self.single_view_container); single_view_layout.setContentsMargins(0, 0, 0, 0)
        self.single_view_label = VideoLabel(-1, self); single_view_layout.addWidget(self.single_view_label)
        self.main_stacked_widget.addWidget(self.single_view_container); self.main_layout.addWidget(self.main_stacked_widget)

        # Controls Panel Setup
        self.control_panel = QFrame(); self.control_panel.setObjectName("control_panel")
        self.control_panel.setStyleSheet("border-radius: 8px;")
        self.control_panel_layout = QHBoxLayout(self.control_panel); self.control_panel_layout.setContentsMargins(12, 12, 12, 12)
        
        self.prev_button = QPushButton("◀ Trang trước"); self.prev_button.setObjectName("nav_btn")
        self.page_indicator = QLabel("Trang 1 / 1")
        self.page_indicator.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: bold; margin: 0 10px;")
        self.next_button = QPushButton("Trang sau ▶"); self.next_button.setObjectName("nav_btn")
        
        self.prev_button.clicked.connect(lambda: self.change_page(-1))
        self.next_button.clicked.connect(lambda: self.change_page(1))
        
        self.control_panel_layout.addWidget(self.prev_button); self.control_panel_layout.addWidget(self.page_indicator)
        self.control_panel_layout.addWidget(self.next_button); self.control_panel_layout.addStretch()

        # Zoom Button Setup
        zoom_in_btn = QPushButton("Phóng to +"); zoom_out_btn = QPushButton("Thu nhỏ -"); zoom_reset_btn = QPushButton("Đặt lại Zoom")
        zoom_in_btn.clicked.connect(lambda: self.change_zoom(1.15))
        zoom_out_btn.clicked.connect(lambda: self.change_zoom(1 / 1.15))
        zoom_reset_btn.clicked.connect(lambda: self.change_zoom(0))

        for btn in [zoom_in_btn, zoom_out_btn, zoom_reset_btn]: self.control_panel_layout.addWidget(btn)
        self.main_layout.addWidget(self.control_panel)

        self.main_controller = MainController()
        for camera_controller in self.main_controller.list_camera:
            self.register_camera(camera_controller.camera_id)
            camera_controller.thread_process.change_pixmap_signal.connect(self.update_image)

        self.rebuild_pages(); self.show_grid_view(); self.main_controller.start()

    def register_camera(self, camera_id: int):
        if camera_id in self.camera_labels: return
        label = VideoLabel(camera_id, self); label.double_clicked.connect(self.toggle_maximize_camera)
        self.camera_labels[camera_id] = label; self.camera_selector.addItem(f"Camera {camera_id}", camera_id)
        self.rebuild_pages()

    def rebuild_pages(self):
        old_page_idx = self.grid_stacked_widget.currentIndex()
        while self.grid_stacked_widget.count() > 0:
            w = self.grid_stacked_widget.widget(0); self.grid_stacked_widget.removeWidget(w); w.deleteLater()

        sorted_cam_ids = sorted(list(self.camera_labels.keys()))
        num_cams = len(sorted_cam_ids)
        if num_cams == 0:
            empty_w = QWidget(); empty_lay = QVBoxLayout(empty_w)
            placeholder = QLabel("Không tìm thấy luồng camera nào."); placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #64748b; font-size: 16px; font-weight: bold;"); empty_lay.addWidget(placeholder)
            self.grid_stacked_widget.addWidget(empty_w)
            self.prev_button.setDisabled(True); self.next_button.setDisabled(True); self.page_indicator.setText("Trang 1 / 1")
            return

        num_pages = max(1, (num_cams + self.cameras_per_page - 1) // self.cameras_per_page)
        for p in range(num_pages):
            page_w = QWidget(); grid_lay = QGridLayout(page_w); grid_lay.setContentsMargins(0, 0, 0, 0); grid_lay.setSpacing(12)
            start_idx = p * self.cameras_per_page
            end_idx = min(start_idx + self.cameras_per_page, num_cams)
            cams_on_page = end_idx - start_idx

            # Thiết lập stretch tỉ lệ đều nhau cho các hàng và cột trong grid
            if cams_on_page == 1:
                grid_lay.setRowStretch(0, 1)
                grid_lay.setColumnStretch(0, 1)
            elif cams_on_page == 2:
                grid_lay.setRowStretch(0, 1)
                grid_lay.setColumnStretch(0, 1)
                grid_lay.setColumnStretch(1, 1)
            else:  # 3 hoặc 4 camera
                grid_lay.setRowStretch(0, 1)
                grid_lay.setRowStretch(1, 1)
                grid_lay.setColumnStretch(0, 1)
                grid_lay.setColumnStretch(1, 1)

            for i in range(start_idx, end_idx):
                cam_id = sorted_cam_ids[i]; local_idx = i - start_idx
                grid_lay.addWidget(self.camera_labels[cam_id], local_idx // 2, local_idx % 2)
            self.grid_stacked_widget.addWidget(page_w)

        self.grid_stacked_widget.setCurrentIndex(old_page_idx if 0 <= old_page_idx < num_pages else 0)
        self.update_pagination_ui()

    def update_pagination_ui(self):
        if self.maximized_camera_id is not None:
            self.prev_button.setDisabled(True); self.next_button.setDisabled(True); self.page_indicator.setText("Chế độ xem đơn")
            return
        tot_pages = self.grid_stacked_widget.count(); curr_page = self.grid_stacked_widget.currentIndex() + 1
        self.page_indicator.setText(f"Trang {curr_page} / {tot_pages}")
        self.prev_button.setEnabled(curr_page > 1); self.next_button.setEnabled(curr_page < tot_pages)

    def change_page(self, step):
        curr = self.grid_stacked_widget.currentIndex()
        self.grid_stacked_widget.setCurrentIndex(max(0, min(self.grid_stacked_widget.count() - 1, curr + step)))
        self.update_pagination_ui()

    def show_grid_view(self):
        self.maximized_camera_id = None; self.main_stacked_widget.setCurrentIndex(0)
        self._set_selector_val(-1); self.update_pagination_ui()

    def show_single_view(self, camera_id: int):
        self.maximized_camera_id = camera_id
        if camera_id in self.last_qimages: self.single_view_label.set_qimage(self.last_qimages[camera_id], self.current_zoom_factor)
        else: self.single_view_label.setText(f"Camera {camera_id}\nĐang kết nối...")
        self.main_stacked_widget.setCurrentIndex(1); self._set_selector_val(camera_id); self.update_pagination_ui()

    def _set_selector_val(self, val):
        self.camera_selector.blockSignals(True)
        for i in range(self.camera_selector.count()):
            if self.camera_selector.itemData(i) == val:
                self.camera_selector.setCurrentIndex(i); break
        self.camera_selector.blockSignals(False)

    def toggle_maximize_camera(self, camera_id: int):
        self.show_grid_view() if self.maximized_camera_id is not None else self.show_single_view(camera_id)

    def on_selector_changed(self, index: int):
        camera_id = self.camera_selector.itemData(index)
        self.show_grid_view() if camera_id == -1 else self.show_single_view(camera_id)

    def update_image(self, camera_id: int, q_image: QImage):
        if camera_id not in self.camera_labels: return
        self.last_qimages[camera_id] = q_image
        self.camera_labels[camera_id].set_qimage(q_image, self.current_zoom_factor)
        if self.maximized_camera_id == camera_id: self.single_view_label.set_qimage(q_image, self.current_zoom_factor)

    def change_zoom(self, delta):
        self.current_zoom_factor = 1.0 if delta == 0 else max(0.2, min(5.0, self.current_zoom_factor * delta))
        for c_id, lbl in self.camera_labels.items():
            if c_id in self.last_qimages: lbl.set_qimage(self.last_qimages[c_id], self.current_zoom_factor)
        if self.maximized_camera_id in self.last_qimages:
            self.single_view_label.set_qimage(self.last_qimages[self.maximized_camera_id], self.current_zoom_factor)

    def open_camera_manager(self):
        dialog = CameraManagerDialog(self.main_controller.cameras_config, self)
        dialog.camera_added.connect(lambda cid, cfg: (self.register_camera(cid), self.main_controller.add_camera_stream(cid, cfg).thread_process.change_pixmap_signal.connect(self.update_image)))
        dialog.camera_updated.connect(lambda cid, cfg: self.main_controller.update_camera_stream(cid, cfg).thread_process.change_pixmap_signal.connect(self.update_image))
        dialog.camera_deleted.connect(self.on_camera_deleted); dialog.exec_()

    def on_camera_deleted(self, camera_id: int):
        self.main_controller.delete_camera_stream(camera_id)
        if camera_id in self.camera_labels:
            self.camera_labels[camera_id].deleteLater(); del self.camera_labels[camera_id]
        for i in range(self.camera_selector.count()):
            if self.camera_selector.itemData(i) == camera_id:
                self.camera_selector.removeItem(i); break
        self.last_qimages.pop(camera_id, None)
        if self.maximized_camera_id == camera_id: self.show_grid_view()
        self.rebuild_pages()

    def closeEvent(self, event):
        if self.main_controller: self.main_controller.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec_())
