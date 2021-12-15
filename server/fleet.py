"""Module for handling the fleet data"""

from datetime import datetime, timedelta

DATETIME_STANDARD_FORMAT = "%Y/%m/%d %H:%M:%S"

class Fleet():
    def __init__(self, docker_hub, event_stream) -> None:
        self._fleet = {}
        self.docker_hub = docker_hub

        self.event_stream = event_stream

    def add_telemetry(self, telemetry):
        telemetry['last_updated'] = datetime.now().strftime(DATETIME_STANDARD_FORMAT)
        self._fleet[telemetry["id"]] = telemetry
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
                container['update_available'] = self.update_available(  container['image_tag'],
                                                                        container['image_sha'])
        return self._fleet

    def update_available(self, image_tag: str, image_sha: str) -> bool:
        """Checks if there is a newer image available in remote repository

        Args:
            image_tag (str): The tag of the current image
            image_sha (str): The SHA of the current image

        Returns:
            bool: If there is a newer image available
        """
        return image_sha != self.docker_hub.get_image_id(image_tag)

    def device_online(self, time, interval):
        last_updated_post = datetime.strptime(time, DATETIME_STANDARD_FORMAT)
        return datetime.now() < last_updated_post + timedelta(seconds=interval*2)
