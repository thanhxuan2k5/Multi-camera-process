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
        with open('resources/config/camera.yml', encoding='utf-8') as f:
            self.cameras_config = yaml.load(f, Loader=yaml.FullLoader)
            if self.cameras_config is None:
                self.cameras_config = {}

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

    def save_camera_config(self):
        with open('resources/config/camera.yml', 'w', encoding='utf-8') as f:
            yaml.dump(self.cameras_config, f, default_flow_style=False, allow_unicode=True)

    def add_camera_stream(self, camera_id: int, camera_config: dict):
        self.cameras_config[camera_id] = camera_config
        self.save_camera_config()
        camera = CameraController(camera_id, camera_config)
        self.list_camera.append(camera)
        camera.start()
        return camera

    def delete_camera_stream(self, camera_id: int):
        for camera in list(self.list_camera):
            if camera.camera_id == camera_id:
                camera.stop()
                self.list_camera.remove(camera)
                break
        if camera_id in self.cameras_config:
            del self.cameras_config[camera_id]
        self.save_camera_config()

    def update_camera_stream(self, camera_id: int, camera_config: dict):
        # Stop and remove existing camera controller if any
        for camera in list(self.list_camera):
            if camera.camera_id == camera_id:
                camera.stop()
                self.list_camera.remove(camera)
                break

        self.cameras_config[camera_id] = camera_config
        self.save_camera_config()
        camera = CameraController(camera_id, camera_config)
        self.list_camera.append(camera)
        camera.start()
        return camera
