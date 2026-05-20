# Premium dark stylesheets for the Multi-Camera GUI application

VIDEO_LABEL_STYLE = """
    QLabel {
        background-color: #111115;
        color: #64748b;
        border: 2px solid #1e1e24;
        border-radius: 8px;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
    }
"""

MAIN_WINDOW_STYLE = """
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
"""

CAMERA_MANAGER_STYLE = """
    QDialog {
        background-color: #0b0b0e;
        color: #e2e8f0;
        font-family: 'Segoe UI', sans-serif;
    }
    QLabel {
        color: #e2e8f0;
        font-size: 13px;
        font-weight: 500;
    }
    QTableWidget {
        background-color: #121216;
        color: #e2e8f0;
        gridline-color: #1e1e24;
        border: 1px solid #1e1e24;
        border-radius: 8px;
        font-size: 13px;
    }
    QTableWidget::item:selected {
        background-color: #2563eb;
        color: #ffffff;
    }
    QHeaderView::section {
        background-color: #1a1a22;
        color: #94a3b8;
        padding: 6px;
        border: none;
        border-bottom: 1px solid #1e1e24;
        font-weight: bold;
    }
    QLineEdit, QSpinBox {
        background-color: #1e1e24;
        color: #ffffff;
        border: 1px solid #2d2d37;
        border-radius: 6px;
        padding: 8px;
        font-size: 13px;
    }
    QLineEdit:focus, QSpinBox:focus {
        border-color: #2563eb;
    }
    QPushButton {
        background-color: #1e1e24;
        color: #e2e8f0;
        border: 1px solid #2d2d37;
        border-radius: 6px;
        padding: 10px 18px;
        font-weight: 600;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #2b2b36;
        border-color: #3b82f6;
        color: #ffffff;
    }
    QPushButton#btn_add {
        background-color: #2563eb;
        color: #ffffff;
        border: none;
    }
    QPushButton#btn_add:hover {
        background-color: #1d4ed8;
    }
    QPushButton#btn_delete {
        background-color: #dc2626;
        color: #ffffff;
        border: none;
    }
    QPushButton#btn_delete:hover {
        background-color: #b91c1c;
    }
    QPushButton#btn_update {
        background-color: #16a34a;
        color: #ffffff;
        border: none;
    }
    QPushButton#btn_update:hover {
        background-color: #15803d;
    }
"""
