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
from main_app.utils.geometry import point_in_polygon, get_side_of_line, shrink_bbox
from boxmot.trackers.ocsort.ocsort import OcSort


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
        # Các biến để tính FPS ổn định
        self.fps_update_interval = 0.5  # Cập nhật FPS hiển thị mỗi 0.5 giây
        self.fps_frame_counter = 0      # Đếm số khung hình đã xử lý trong khoảng interval
        self.fps_start_time = time.time()
        self.displayed_fps = 0.0

        self.load_model()

    def load_model(self):
        self.model = YOLO(MODEL_PATH)
        self.tracker = OcSort(min_conf=CONFIDENCE)

    def run(self):
        print(f"Bắt đầu xử lý: Device={DEVICE}")
        self.thread_running = True

        try:
            while self.thread_running:
                # Lấy một frame từ queue. Phương thức .get() sẽ chờ nếu queue rỗng.
                raw_frame = self.capture_queue.get() 

                if raw_frame is None:
                    continue

                self.process_frame(raw_frame)
        except Exception as e:
            print(f"Lỗi trong luồng xử lý camera {self.camera_id}: {e}")
        finally:
            self.thread_running = False

    def process_frame(self, raw_frame):
        frame = cv2.resize(raw_frame, (TARGET_WIDTH, TARGET_HEIGHT))

        # 1. Thực hiện phát hiện và theo dõi đối tượng
        tracks = self.detect_and_track(frame)

        # 2. Xử lý logic đếm và vẽ bounding boxes
        current_now_in_zone = self.process_tracks(frame, tracks)

        # 3. Vẽ đè đa giác vùng, đường đếm và các số liệu
        self.draw_overlay(frame, current_now_in_zone)

        # 4. Chuyển đổi định dạng và gửi tín hiệu hiển thị
        self.emit_frame(frame)

    def detect_and_track(self, frame):
        # Dùng model.predict thay vì model.track để tự theo dõi bằng OcSort
        results = self.model.predict(frame, classes=[0],
                                     conf=CONFIDENCE, device=DEVICE,
                                     verbose=False)

        dets = []
        if results[0].boxes is not None and len(results[0].boxes) > 0:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = box.cls[0].cpu().numpy()
                dets.append([x1, y1, x2, y2, conf, cls])

        dets_array = np.array(dets) if dets else np.empty((0, 6))
        return self.tracker.update(dets_array, frame)

    def process_tracks(self, frame, tracks):
        current_now_in_zone = 0
        thickness = int(BBOX_THICKNESS)

        if len(tracks) > 0:
            for track in tracks:
                x1, y1, x2, y2, tid, conf, cls, ind = track
                tid = int(tid)
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                curr_center = (cx, cy)

                # Cập nhật trạng thái trong vùng (Zone)
                if tid not in self.zone_state:
                    self.zone_state[tid] = False
                    self.zone_counter[tid] = 0
                is_inside = point_in_polygon(curr_center, self.zone_pts)
                if is_inside != self.zone_state[tid]:
                    self.zone_counter[tid] += 1
                    if self.zone_counter[tid] >= CONFIRM_FRAMES:
                        if is_inside:
                            self.count_in_zone += 1
                        self.zone_state[tid] = is_inside
                        self.zone_counter[tid] = 0
                else:
                    self.zone_counter[tid] = 0
                if self.zone_state[tid]:
                    current_now_in_zone += 1

                # Cập nhật trạng thái cắt đường đếm (Line)
                current_side = get_side_of_line(curr_center, self.line_pts)
                if tid in self.line_side_history:
                    prev_side = self.line_side_history[tid]
                    if prev_side * current_side < 0:
                        if current_side > 0:
                            self.count_in += 1
                        else:
                            self.count_out += 1
                self.line_side_history[tid] = current_side

                # Vẽ bounding box và ID của đối tượng
                sx1, sy1, sx2, sy2 = shrink_bbox(x1, y1, x2, y2, BBOX_SHRINK_FACTOR)
                cv2.rectangle(frame, (sx1, sy1), (sx2, sy2), (0, 255, 0), thickness)
                cv2.putText(frame, f"ID:{tid}", (sx1, sy1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                            thickness)
        return current_now_in_zone

    def draw_overlay(self, frame, current_now_in_zone):
        thickness = int(BBOX_THICKNESS)

        # Vẽ đa giác vùng và đường kẻ đếm
        cv2.polylines(frame, [self.zone_pts], True, (0, 255, 255), thickness)
        cv2.line(frame, (self.line_pts[0], self.line_pts[1]), (self.line_pts[2], self.line_pts[3]), (0, 0, 255),
                 thickness + 1)

        # Cập nhật và tính toán FPS ổn định
        self.fps_frame_counter += 1
        current_time = time.time()
        elapsed_time = current_time - self.fps_start_time
        if elapsed_time >= self.fps_update_interval:
            self.displayed_fps = self.fps_frame_counter / elapsed_time
            self.fps_frame_counter = 0
            self.fps_start_time = current_time

        # Vẽ thông tin FPS và số đếm lên màn hình
        cv2.putText(frame, f"FPS: {int(self.displayed_fps)}", (TARGET_WIDTH - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 255, 0), 2)

        cv2.putText(frame, f"IN ZONE: {current_now_in_zone}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 255), 2)
        cv2.putText(frame, f"IN: {self.count_in}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"OUT: {self.count_out}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    def emit_frame(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        convert_to_qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        self.change_pixmap_signal.emit(self.camera_id, convert_to_qt_format)

    def stop(self):
        self.thread_running = False
        try:
            self.capture_queue.put_nowait(None)
        except Exception:
            pass
