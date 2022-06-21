"""Module to handle the device."""

from logging import getLogger
from datetime import datetime
import psutil
from container import Container
import docker
import shared

class Device(): # pylint: disable=too-many-instance-attributes
    """Class to handle and bundle device information"""
    def __init__(self, device_name: str, device_id: str) -> None:
        self.device_name = device_name
        self.device_id = device_id

        self.client = docker.from_env()

        self.log = getLogger(f'{self.__class__.__name__}')
        self.log.info('Device ID: %s', self.device_id)

    def information(self) -> shared.DeviceTelemetry:
        """Compiles a dictionary with information about the fleet.

        Returns:
            dict: Information about the fleet
        """
        device_object = shared.DeviceTelemetry(
            name            = self.device_name,
            timestamp       = datetime.now(),
            device_id       = self.device_id,
            cpu_load        = self.cpu_load(),
            memory_usage    = self.memory_usage(),
        )

        for container in self.client.containers.list(all=True):
            container_obj = Container(container)
            device_object.containers.append(container_obj.information())

        return device_object

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

    def start_container(self, container_name: str) -> None:
        """Start a container

        Args:
            container_name (str): Name of the container to start
        """
        self.log.info('Starting container "%s"', container_name)
        with Container(self._get_container_obj(container_name)) as container_client:
            container_client.start()
        self.log.debug('Container "%s" started', container_name)

    def stop_container(self, container_name: str) -> None:
        """Stop a container

        Args:
            container_name (str): Name of the container to start
        """
        self.log.info('Stopping container "%s"', container_name)
        with Container(self._get_container_obj(container_name)) as container_client:
            container_client.stop()
        self.log.debug('Container "%s" stopped', container_name)

    def _get_container_obj(self, container_name: str):
        return self.client.containers.get(container_name)
