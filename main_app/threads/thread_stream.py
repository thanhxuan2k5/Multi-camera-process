import threading
from queue import Queue
import subprocess
import time
import cv2


class ThreadStream(threading.Thread):
    def __init__(self, stream_queue: Queue, stream_url: str, camera_id: int, stream_size: list = [640, 480]):
        super().__init__()
        self.thread_running = False
        self.stream_queue = stream_queue
        self.stream_size = stream_size
        self.camera_id = camera_id

        self.stream_args = (
            "ffmpeg -y -r 15 -f rawvideo -vcodec rawvideo -pix_fmt "
            f"rgb24 -s {stream_size[0]}x{stream_size[1]} -i pipe:0 -pix_fmt yuv420p -c:v libx264 -preset ultrafast "
            f"-f rtsp {stream_url}/{camera_id} ").split()
        

        try:
            self.pipe = subprocess.Popen(self.stream_args, stdin=subprocess.PIPE)
        except Exception as e:
            print(f"Không thể khởi tạo ffmpeg stream: {e}")
            self.pipe = None

        print(f"Stream target (RTSP): {stream_url}/{camera_id}")

    def run(self):
        print(f"Bắt đầu stream camera {self.camera_id}... ")
        self.thread_running = True
        window_name = f"Camera {self.camera_id} Output"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        while self.thread_running:
            if self.stream_queue.empty():
                time.sleep(0.001)
                continue
            

            frame, _ = self.stream_queue.get()
            

            cv2.imshow(window_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            if self.pipe:

                stream_frame = cv2.resize(frame, tuple(self.stream_size))
                stream_frame = cv2.cvtColor(stream_frame, cv2.COLOR_BGR2RGB)
                try:
                    self.pipe.stdin.write(stream_frame.tobytes())
                except Exception as e:
                    print("Lỗi ghi pipe ffmpeg: ", e)
                    self.pipe = None
            
        cv2.destroyWindow(window_name)
        print(f"Dừng streaming camera {self.camera_id}")

    def stop(self):
        self.thread_running = False
        if self.pipe:
            self.pipe.terminate()
