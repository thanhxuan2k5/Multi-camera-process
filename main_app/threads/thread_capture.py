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
        self.cap = None # Initialize cap here

    def run(self):
        print("Bắt đầu ghi lại URL: ", self.camera_url)
        self.cap = cv2.VideoCapture(self.camera_url) # Assign to self.cap
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        
        self.thread_running = True
        while self.thread_running:
            ret, frame = self.cap.read()
            if not ret:
                print("Kết nối lại với camera: ", self.camera_url)
                self.cap.release() # Release current cap
                time.sleep(1)
                self.cap = cv2.VideoCapture(self.camera_url) # Re-initialize self.cap
                if not self.cap.isOpened(): # Check if re-initialization was successful
                    print(f"Không thể kết nối lại với camera: {self.camera_url}. Dừng luồng.")
                    self.thread_running = False
                    break
                continue
            

            if self.capture_queue.full():
                try:
                    self.capture_queue.get_nowait()
                except:
                    pass
            
            self.capture_queue.put(frame)
            

            time.sleep(0.01)
        
        # Ensure cap is released when the thread finishes its loop
        if self.cap and self.cap.isOpened():
            self.cap.release()
            print(f"Đã giải phóng tài nguyên camera: {self.camera_url} khi luồng kết thúc.")


    def stop(self):
        self.thread_running = False
        print("Dừng ghi dữ liệu từ camera: ", self.camera_url)

        if self.cap and self.cap.isOpened():
            self.cap.release()
            print(f"Đã giải phóng tài nguyên camera: {self.camera_url} từ phương thức stop().")
