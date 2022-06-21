# pylint: disable=missing-class-docstring, missing-function-docstring
"""Module for handling the fleet data"""

from docker_hub import DockerHub
from device_information import DeviceInformation

class Fleet():
    def __init__(self, docker_hub: DockerHub, consumers: list, event_stream: object) -> None:
        self.devices = {}
        self.docker_hub = docker_hub
        self.consumers = consumers

        self.docker_hub.list_images()

        self.event_stream = event_stream

    def remove_device(self, device_id):
        self.devices.pop(device_id)

    def get_device_ip(self, device_id):
        return self.devices[device_id].ip_addr

    def add_telemetry(self, device_information: DeviceInformation):
        self.devices[device_information.telemetry.device_id] = device_information
        if len(self.consumers) > 0:
            self.event_stream(self.get_fleet_information())

    def empty(self) -> bool:
        """Checks if fleet is empty (no device registered)

        Returns:
            bool: If fleet is empty
        """
        return len(self.devices) == 0

    def get_fleet_information(self, jsonify: bool = True):
        for device in self.devices.values():
            for container in device.telemetry.containers:
                container['update_available'] = self.update_available(  container['image_repo'],
                                                                        container['image_tag'],
                                                                        container['image_sha'])
        if jsonify:
            _devices = {}
            for k, v in self.devices.items():
                _devices[k] = v.to_json()
            return _devices

        return self.devices

    def update_available(self, image_repo: str, image_tag: str, image_sha: str) -> bool:
        """Checks if there is a newer image available in remote repository

        Args:
            image_repo (str): The repository of the image
            image_tag (str): The tag of the current image
            image_sha (str): The SHA of the current image

        Returns:
            bool: If there is a newer image available
        """
        image_id = self.docker_hub.get_remote_image_sha(image_repo, image_tag)
        if image_id is None:
            return None
        return image_sha != image_id
