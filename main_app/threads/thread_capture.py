import cv2
import threading
from queue import Queue
import time

class ThreadCapture(threading.Thread):
    def __init__(self, camera_url: str, capture_queue: Queue):
        super().__init__()
        self.thread_running = False
        self.camera_url = camera_url
        self.capture_queue = capture_queue

    def run(self):
        print("Bắt đầu ghi lại URL: ", self.camera_url)
        cap = cv2.VideoCapture(self.camera_url)
        # Giảm buffer của OpenCV để tránh trễ
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        
        self.thread_running = True
        while self.thread_running:
            ret, frame = cap.read()
            if not ret:
                print("Kết nối lại với camera: ", self.camera_url)
                cap.release()
                time.sleep(1)
                cap = cv2.VideoCapture(self.camera_url)
                continue
            

            if self.capture_queue.full():
                try:
                    self.capture_queue.get_nowait()
                except:
                    pass
            
            self.capture_queue.put(frame)
            

            time.sleep(0.01)

    def stop(self):
        self.thread_running = False
        print("Dừng ghi dữ liệu từ camera: ", self.camera_url)
