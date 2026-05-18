import cv2
import numpy as np
from queue import Queue
import time
from ultralytics import YOLO
from resources.config.setting import (
    MODEL_PATH, CONFIDENCE, CONFIRM_FRAMES, 
    DEVICE, TARGET_WIDTH, TARGET_HEIGHT,
    BBOX_SHRINK_FACTOR, BBOX_THICKNESS, TRACKER_TYPE
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QImage

def point_in_polygon(pt, polygon):
    return cv2.pointPolygonTest(np.array(polygon, np.int32), pt, False) >= 0

def get_side_of_line(p, line):
    x1, y1, x2, y2 = line
    return (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1)

class ThreadProcess(QThread):
    change_pixmap_signal = pyqtSignal(int, QImage)

    def __init__(self, camera_id: int, capture_queue: Queue, zone_polygon: list, counting_line: list):
        super().__init__()
        self.camera_id = camera_id
        self.thread_running = False
        self.capture_queue = capture_queue
        self.zone_pts = np.array(zone_polygon, np.int32)
        self.line_pts = counting_line
        self.track_history = {}
        self.zone_state = {}
        self.zone_counter = {}
        self.line_side_history = {}
        self.count_in_zone = 0
        self.count_in = 0
        self.count_out = 0
        self.prev_frame_time = 0
        self.new_frame_time = 0
        self.load_model()

    def load_model(self):
        self.model = YOLO(MODEL_PATH)
        self.model.to(DEVICE)

    def shrink_bbox(self, x1, y1, x2, y2, factor):
        w = x2 - x1
        h = y2 - y1
        dw = int(w * factor)
        dh = int(h * factor)

        return int(x1 + dw), int(y1 + dh), int(x2 - dw), int(y2 - dh)

    def run(self):
        print(f"Bắt đầu xử lý: Device={DEVICE}")
        self.thread_running = True
        thickness = int(BBOX_THICKNESS)
        
        try: # Added try-except block
            while self.thread_running:
                self.new_frame_time = time.time()
                if self.capture_queue.empty():
                    time.sleep(0.001)
                    continue
                
                # Giải phóng toàn bộ khung hình cũ trong hàng đợi, chỉ giữ lại khung hình mới nhất (Zero Latency)
                raw_frame = None
                while not self.capture_queue.empty():
                    raw_frame = self.capture_queue.get()
                
                if raw_frame is None: 
                    continue
                
                # Resize frame for consistent processing dimensions
                frame = cv2.resize(raw_frame, (TARGET_WIDTH, TARGET_HEIGHT))
                
                results = self.model.track(frame, persist=True, classes=[0], 
                                         conf=CONFIDENCE, device=DEVICE, 
                                         tracker=TRACKER_TYPE, verbose=False)

                current_now_in_zone = 0
                if results[0].boxes is not None and results[0].boxes.id is not None:
                    boxes = results[0].boxes.xyxy.cpu().numpy()
                    ids = results[0].boxes.id.int().cpu().numpy()

                    for box, tid in zip(boxes, ids):
                        x1, y1, x2, y2 = box
                        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                        curr_center = (cx, cy)


                        if tid not in self.zone_state:
                            self.zone_state[tid] = False
                            self.zone_counter[tid] = 0
                        is_inside = point_in_polygon(curr_center, self.zone_pts)
                        if is_inside != self.zone_state[tid]:
                            self.zone_counter[tid] += 1
                            if self.zone_counter[tid] >= CONFIRM_FRAMES:
                                if is_inside: self.count_in_zone += 1
                                self.zone_state[tid] = is_inside
                                self.zone_counter[tid] = 0
                        else: self.zone_counter[tid] = 0
                        if self.zone_state[tid]: current_now_in_zone += 1


                        current_side = get_side_of_line(curr_center, self.line_pts)
                        if tid in self.line_side_history:
                            prev_side = self.line_side_history[tid]
                            if prev_side * current_side < 0:
                                if current_side > 0: self.count_in += 1
                                else: self.count_out += 1
                        self.line_side_history[tid] = current_side


                        sx1, sy1, sx2, sy2 = self.shrink_bbox(x1, y1, x2, y2, BBOX_SHRINK_FACTOR)
                        cv2.rectangle(frame, (sx1, sy1), (sx2, sy2), (0, 255, 0), thickness)
                        cv2.putText(frame, f"ID:{tid}", (sx1, sy1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), thickness)


                cv2.polylines(frame, [self.zone_pts], True, (0, 255, 255), thickness)
                cv2.line(frame, (self.line_pts[0], self.line_pts[1]), (self.line_pts[2], self.line_pts[3]), (0, 0, 255), thickness + 1)
                

                if (self.new_frame_time - self.prev_frame_time) > 0:
                    fps = 1 / (self.new_frame_time - self.prev_frame_time)
                    cv2.putText(frame, f"FPS: {int(fps)}", (TARGET_WIDTH - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                self.prev_frame_time = self.new_frame_time

                cv2.putText(frame, f"IN ZONE: {current_now_in_zone}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(frame, f"IN: {self.count_in}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"OUT: {self.count_out}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # Convert frame to QImage and emit signal
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                # Removed .scaled() here. Let MainWindow handle scaling for display.
                convert_to_qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                self.change_pixmap_signal.emit(self.camera_id, convert_to_qt_format)
        except Exception as e:
            print(f"Lỗi trong luồng xử lý camera {self.camera_id}: {e}")
        finally:
            self.thread_running = False # Ensure thread stops if an error occurs

    def stop(self):
        self.thread_running = False
