"""Module to handle the device."""

from logging import getLogger
import threading
import requests
import psutil
from container import Container
import docker

class Device(): # pylint: disable=too-many-instance-attributes
    """Class to handle and bundle device information"""
    def __init__(self, server_url: str, device_name: str, device_id: str) -> None:
        self.server_url = server_url
        self.device_name = device_name
        self.device_id = device_id

        self.client = docker.from_env()
        self.lock = threading.Lock()

        self.log = getLogger(f'{self.__class__.__name__}')

        self._cached_ip_address = None
        self.containers = []

    def update(self) -> None:
        """Updating list of containers"""
        with self.lock:
            container_list = self.client.containers.list(all=True)
            self.containers.clear()

            for container in container_list:
                self.containers.append(Container(container))

    def information(self) -> dict:
        """Compiles a dictionary with information about the fleet.

        Returns:
            dict: Information about the fleet
        """
        with self.lock:
            device_object = {
                "name": self.device_name,
                "id": self.device_id,
                "ip_address": self.ip_address(),
                "cpu_load": self.cpu_load(),
                "memory_usage": self.memory_usage(),
                "containers": []
            }

            for container in self.containers:
                device_object["containers"].append(container.information())

            return device_object

    def ip_address(self) -> str:
        """Getting device ip by sending a GET ressquest to fm server.
        IP is cached and is used as backup if server is not responding.

        Returns:
            str: device ip address
        """
        try:
            response = requests.get(url=f'{self.server_url}/myip')
            self._cached_ip_address = response.text
            return self._cached_ip_address
        except requests.exceptions.RequestException:
            return self._cached_ip_address

    @staticmethod
    def cpu_load(interval: int = 2) -> float:
        """Getting device CPU load.

        Args:
            interval (int, optional): CPU load measurement time. Defaults to 2.

        Returns:
            float: CPU load in percent
        """
        return psutil.cpu_percent(interval)

    @staticmethod
    def memory_usage() -> float:
        """Getting memory usage.

        Returns:
            float: Memory usage in percent
        """
        return psutil.virtual_memory()[2]

    def update_container(self, container_name: str) -> None:
        """Updating specified container.
        Reuses the settings from existing container, updates the image and
        starts a new container with the same settings.

        Be aware. All settings are not supported and will not be transferred.
        See :func:`container.Container.settings` for information about which settings
        are transferrable.

        Args:
            container_name (str): Name of the container that are being updated
        """
        #TODO: Add error handling
        self.log.info('Updating container "%s" with latest image from remote repository',
            container_name)

        with self.lock, Container(self._get_container_obj(container_name)) as container_client:
            container_settings = container_client.settings()
            image_name = container_client.image_name

            self.log.debug('Stopping container "%s"', container_name)
            container_client.stop()
            self.log.debug('Removing container "%s"', container_name)
            container_client.remove()

            self.log.debug('Pulling new image from remote repository')
            self.client.images.pull(image_name)
            self.log.debug('Starting the new image with name "%s"', container_name)
            self._start_new_container(image_name, container_settings)

        self.client.images.prune()
        self.log.info('Update of container "%s" complete', container_name)

    def start_container(self, container_name: str) -> None:
        """Start a container

        Args:
            container_name (str): Name of the container to start
        """
        self.log.info('Starting container "%s"', container_name)
        with self.lock, Container(self._get_container_obj(container_name)) as container_client:
            container_client.start()
        self.log.debug('Container "%s" started', container_name)

    def stop_container(self, container_name: str) -> None:
        """Stop a container

        Args:
            container_name (str): Name of the container to start
        """
        self.log.info('Stopping container "%s"', container_name)
        with self.lock, Container(self._get_container_obj(container_name)) as container_client:
            container_client.stop()
        self.log.debug('Container "%s" stopped', container_name)

    def _start_new_container(self, image_name, settings):
        self.client.containers.run(image=image_name, **settings)

    def _get_container_obj(self, container_name):
        return self.client.containers.get(container_name)
