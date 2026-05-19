import yaml
from .camera_controller import CameraController
from typing import List


class MainController(object):
    def __init__(self):
        super().__init__()

        self.cameras_config = {}
        self.load_camera()

        self.list_camera: List[CameraController] = []
        self.create_camera()

    def load_camera(self):
        with open('resources/config/camera.yml') as f:
            self.cameras_config = yaml.load(f, Loader=yaml.FullLoader)

    def create_camera(self):
        for key, value in self.cameras_config.items():
            camera_id = key
            camera = CameraController(camera_id, value)
            self.list_camera.append(camera)

    def start(self):
        print("Start all camera: ", len(self.list_camera))
        for camera in self.list_camera:
            camera.start()

    def stop(self):
        for camera in self.list_camera:
            camera.stop()
