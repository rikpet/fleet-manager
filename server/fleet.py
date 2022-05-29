"""Module for handling the fleet data"""

from datetime import datetime, timedelta
from shared import Device
from docker_hub import DockerHub

DATETIME_STANDARD_FORMAT = "%Y/%m/%d %H:%M:%S"

class Fleet():
    def __init__(self, docker_hub: DockerHub, consumers: list, event_stream: object) -> None:
        self._fleet = {}
        self.docker_hub = docker_hub
        self.consumers = consumers

        self.docker_hub.list_images()

        self.event_stream = event_stream

    def remove_device(self, device_id):
        self._fleet.pop(device_id)

    def get_device_ip(self, device_id):
        return self._fleet[device_id].ip_addr

    def add_telemetry(self, telemetry):
        telemetry['last_updated'] = datetime.now().strftime(DATETIME_STANDARD_FORMAT)
        self._fleet[telemetry["id"]] = Device(**telemetry)
        if len(self.consumers) > 0:
            self.event_stream(self.get_fleet_information())

    def empty(self) -> bool:
        """Checks if fleet is empty (no device registered)

        Returns:
            bool: If fleet is empty
        """
        return len(self._fleet) == 0

    def get_fleet_information(self):
        for device in self._fleet.values():
            device['online'] = self.device_online(device['last_updated'], device['push_interval'])
            for container in device['containers']:
                container['update_available'] = self.update_available(  container['image_repo'],
                                                                        container['image_tag'],
                                                                        container['image_sha'])
        return self._fleet

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

    @staticmethod
    def device_online(time, interval):
        last_updated_post = datetime.strptime(time, DATETIME_STANDARD_FORMAT)
        return datetime.now() < last_updated_post + timedelta(seconds=interval*2)
