import torch

RTSP_URL = "rtsp://localhost:8554/live"
MODEL_PATH = "resources/weights/yolov8n.pt"
CONFIDENCE = 0.5
SHRINK_FACTOR = 0.2
CONFIRM_FRAMES = 5


TARGET_WIDTH = 1280
TARGET_HEIGHT = 720

DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"

# ZONE_POLYGON và COUNTING_LINE sẽ được định nghĩa riêng cho từng camera
# ZONE_POLYGON = [[255, 633], [381, 319], [847, 310], [993, 632]]
# COUNTING_LINE = [414, 211, 805, 204]


BBOX_SHRINK_FACTOR = 0.1 
BBOX_THICKNESS = 0.5
TRACKER_TYPE = "bytetrack.yaml"

# ZONES có thể cần được điều chỉnh hoặc loại bỏ nếu ZONE_POLYGON được định nghĩa riêng
ZONES = [
    {"name": "Vung_Trung_Tam", "points": [], "color": (0, 255, 255)} # Points will be set dynamically
]
