import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QFrame, QFormLayout, QSpinBox, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal
from gui.styles import CAMERA_MANAGER_STYLE

class CameraManagerDialog(QDialog):
    camera_added = pyqtSignal(int, dict)
    camera_updated = pyqtSignal(int, dict)
    camera_deleted = pyqtSignal(int)

    def __init__(self, cameras_config: dict, parent=None):
        super().__init__(parent)
        self.cameras_config = cameras_config
        self.setWindowTitle("Quản lý danh sách Camera")
        self.resize(1000, 600)
        self.setMinimumSize(850, 500)
        self.setup_ui()
        self.load_table_data()

    def setup_ui(self):
        self.setStyleSheet(CAMERA_MANAGER_STYLE)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Left Panel (Table)
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        table_title = QLabel("Danh sách camera hiện tại")
        table_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        left_layout.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Đường dẫn (URL / File)", "Vùng (Polygon)", "Đường kẻ (Line)"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        left_layout.addWidget(self.table)
        main_layout.addLayout(left_layout, stretch=3)

        # Right Panel (Form Editor)
        right_frame = QFrame()
        right_frame.setStyleSheet("background-color: #121216; border-radius: 8px; border: 1px solid #1e1e24;")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(15)

        form_title = QLabel("Thông tin chi tiết Camera")
        form_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc; border: none;")
        right_layout.addWidget(form_title)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.id_input = QSpinBox()
        self.id_input.setRange(0, 9999)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("rtsp://... hoặc file .mp4")
        self.polygon_input = QLineEdit()
        self.polygon_input.setPlaceholderText("[[x1, y1], [x2, y2], ...]")
        self.line_input = QLineEdit()
        self.line_input.setPlaceholderText("[x1, y1, x2, y2]")

        form_layout.addRow(QLabel("Camera ID:"), self.id_input)
        form_layout.addRow(QLabel("Link kết nối:"), self.url_input)
        form_layout.addRow(QLabel("Đa giác vùng:"), self.polygon_input)
        form_layout.addRow(QLabel("Đường đếm:"), self.line_input)
        right_layout.addLayout(form_layout)

        tips_label = QLabel("Mẹo: Nhấn nút 'Mặc định' để tự điền tọa độ mẫu.")
        tips_label.setStyleSheet("color: #64748b; font-size: 11px; border: none;")
        tips_label.setWordWrap(True)
        right_layout.addWidget(tips_label)

        btn_layout_1 = QHBoxLayout()
        self.btn_default_coords = QPushButton("Mặc định tọa độ")
        self.btn_clear = QPushButton("Làm mới")
        self.btn_default_coords.clicked.connect(self.fill_default_coordinates)
        self.btn_clear.clicked.connect(self.clear_form)
        btn_layout_1.addWidget(self.btn_default_coords)
        btn_layout_1.addWidget(self.btn_clear)
        right_layout.addLayout(btn_layout_1)

        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)
        
        self.btn_add = QPushButton("Thêm Camera")
        self.btn_add.setObjectName("btn_add")
        self.btn_add.clicked.connect(self.add_camera)
        self.btn_update = QPushButton("Sửa Camera")
        self.btn_update.setObjectName("btn_update")
        self.btn_update.clicked.connect(self.update_camera)
        self.btn_delete = QPushButton("Xóa Camera")
        self.btn_delete.setObjectName("btn_delete")
        self.btn_delete.clicked.connect(self.delete_camera)
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.close)

        for btn in [self.btn_add, self.btn_update, self.btn_delete, btn_close]:
            actions_layout.addWidget(btn)
        right_layout.addLayout(actions_layout)
        right_layout.addStretch()
        main_layout.addWidget(right_frame, stretch=2)

    def load_table_data(self):
        self.table.setRowCount(0)
        for key in sorted(self.cameras_config.keys()):
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            config = self.cameras_config[key]
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(key)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(config.get("url", "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(json.dumps(config.get("zone_polygon", []))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(json.dumps(config.get("counting_line", []))))
        for col in [0, 2, 3]:
            self.table.resizeColumnToContents(col)

    def on_table_selection_changed(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges: return
        row = selected_ranges[0].topRow()
        try:
            self.id_input.setValue(int(self.table.item(row, 0).text()))
            self.id_input.setEnabled(False)
            self.url_input.setText(self.table.item(row, 1).text())
            self.polygon_input.setText(self.table.item(row, 2).text())
            self.line_input.setText(self.table.item(row, 3).text())
        except Exception as e:
            print("Selection error:", e)

    def clear_form(self):
        next_id = max(self.cameras_config.keys()) + 1 if self.cameras_config else 0
        self.id_input.setValue(next_id)
        self.id_input.setEnabled(True)
        self.url_input.clear()
        self.polygon_input.clear()
        self.line_input.clear()
        self.table.clearSelection()

    def fill_default_coordinates(self):
        self.polygon_input.setText(json.dumps([[100, 100], [100, 620], [1180, 620], [1180, 100]]))
        self.line_input.setText(json.dumps([100, 360, 1180, 360]))

    def validate_inputs(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Lỗi nhập liệu", "Đường dẫn không được trống!")
            return None
        try:
            poly_str = self.polygon_input.text().strip()
            poly = json.loads(poly_str) if poly_str else [[100, 100], [100, 620], [1180, 620], [1180, 100]]
            if not isinstance(poly, list) or not all(isinstance(p, list) and len(p) == 2 for p in poly): raise ValueError
        except:
            QMessageBox.warning(self, "Lỗi nhập liệu", "Đa giác vùng không đúng định dạng!\nVí dụ: [[100, 100], [100, 620]]")
            return None
        try:
            line_str = self.line_input.text().strip()
            line = json.loads(line_str) if line_str else [100, 360, 1180, 360]
            if not isinstance(line, list) or len(line) != 4 or not all(isinstance(x, int) for x in line): raise ValueError
        except:
            QMessageBox.warning(self, "Lỗi nhập liệu", "Đường đếm không đúng định dạng!\nVí dụ: [100, 360, 1180, 360]")
            return None
        return {"url": url, "zone_polygon": poly, "counting_line": line}

    def add_camera(self):
        cam_id = self.id_input.value()
        if cam_id in self.cameras_config:
            QMessageBox.warning(self, "Lỗi", f"Camera ID {cam_id} đã tồn tại!")
            return
        config = self.validate_inputs()
        if config:
            self.cameras_config[cam_id] = config
            self.load_table_data()
            self.camera_added.emit(cam_id, config)
            self.clear_form()
            QMessageBox.information(self, "Thành công", f"Đã thêm Camera {cam_id} thành công!")

    def update_camera(self):
        cam_id = self.id_input.value()
        if cam_id not in self.cameras_config:
            QMessageBox.warning(self, "Lỗi", f"Không tìm thấy Camera ID {cam_id}!")
            return
        config = self.validate_inputs()
        if config:
            self.cameras_config[cam_id] = config
            self.load_table_data()
            self.camera_updated.emit(cam_id, config)
            QMessageBox.information(self, "Thành công", f"Đã cập nhật Camera {cam_id} thành công!")

    def delete_camera(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một camera trong danh sách!")
            return
        row = selected_ranges[0].topRow()
        cam_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(self, "Xác nhận xóa", f"Bạn có chắc muốn xóa Camera {cam_id}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if cam_id in self.cameras_config:
                del self.cameras_config[cam_id]
            self.load_table_data()
            self.camera_deleted.emit(cam_id)
            self.clear_form()
            QMessageBox.information(self, "Thành công", f"Đã xóa Camera {cam_id}!")
