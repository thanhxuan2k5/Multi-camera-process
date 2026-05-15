from queue import Queue
from ..threads import *
from threading import Thread
from typing import List
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QImage


class CameraController(QObject): # Inherit from QObject to use signals
    change_pixmap_signal = pyqtSignal(QImage) # Define signal to pass frames to GUI

    def __init__(self, camera_id: int, camera_url: str) -> None: # Removed stream_url
        super().__init__()
        self.camera_id = camera_id
        self.camera_url = camera_url
        # self.stream_url = stream_url # Removed

        self.list_thread: List[Thread] = []

        self.create_queue()
        self.create_thread()

    def create_queue(self):
        self.capture_queue = Queue(maxsize=30)
        # self.process_queue = Queue(maxsize=30) # Removed

    def create_thread(self):
        self.thread_capture = ThreadCapture(
            self.camera_url, self.capture_queue)
        self.thread_process = ThreadProcess(
            self.capture_queue) # Removed process_queue
        
        # Connect the signal from thread_process to this controller's signal
        self.thread_process.change_pixmap_signal.connect(self.change_pixmap_signal)

        # self.thread_stream = ThreadStream( # Removed
        #     self.process_queue, self.stream_url, self.camera_id) # Removed

        self.list_thread = [self.thread_capture,
                            self.thread_process] # Removed thread_stream

    def start(self):
        print("Start camera: ", self.camera_id)
        for thread in self.list_thread:
            thread.start()

    def stop(self):
        for thread in self.list_thread:
            thread.stop()
