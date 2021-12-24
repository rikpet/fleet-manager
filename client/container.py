"""Module to handle docker container instances"""

class Container():
    """Class that wrap a docker container"""
    def __init__(self, container) -> None:
        self.container = container

    @property
    def id(self) -> str:   # pylint: disable=invalid-name
        """Short ID for the container

        Returns:
            str: Container ID
        """
        return self.full_id[:10]

    @property
    def full_id(self) -> str:
        """Full ID for the container

        Returns:
            str: Container full ID
        """
        return self.attr["Id"]

    @property
    def attr(self):
        """All available container attributes

        Returns:
            dict: All available attributes for the container
        """
        return self.container.attrs

    @property
    def name(self) -> str:
        """Container name

        Returns:
            str: Container name
        """
        return self.attr["Name"][1:]

    @property
    def image_sha(self) -> str:
        """Image SHA which the container is based on

        Returns:
            str: Image SHA
        """
        return self.attr["Image"]

    @property
    def image_name(self) -> str:
        """Image name which the container is based on

        Returns:
            str: Container name
        """
        return self.attr["Config"]["Image"]

    @property
    def image_repo(self) -> str:
        """Image repository

        Returns:
            str: Image repository
        """
        return self.image_name.split(':')[0]

    @property
    def image_tag(self) -> str:
        """Image tag which the container is based on

        Returns:
            str: image tag
        """
        return self.image_name.split(':')[-1]

    @property
    def running(self) -> bool:
        """Running status of the container

        Returns:
            bool: Runninge status of the container
        """
        return self.attr["State"]["Running"]

    @property
    def status(self) -> str:
        """Status of the container

        Returns:
            str: Status of the container
        """
        return self.attr["State"]["Status"]

    @property
    def volumes(self):
        """List of mounted volumes for the container

        Returns:
            list(str): List of the mounted volumes
        """
        _volumes = []
        for volume in self.attr['Mounts']:
            _volumes.append(f'{volume["Source"]}:{volume["Destination"]}')
        return _volumes

    @property
    def environment(self):
        """Environment variables for the docker
        (Only includes added by user, removes environment variables added by docker)

        Returns:
            list(str): Environment variables in the container
        """
        _environment = []
        for env_var in self.attr['Config']['Env']:
            if env_var[:4] == "PATH":
                break
            _environment.append(env_var)
        return _environment

    @property
    def ports(self) -> dict:
        """Port bindings in effect between container and device

        Returns:
            dict: Port bindings
        """
        _port_settings = self.attr["NetworkSettings"]["Ports"]

        _ports = {}

        for key, value in _port_settings.items():
            try:
                _ports[key] = value[0]["HostPort"]
            except TypeError:
                continue
        return _ports

    @property
    def restart_policy(self) -> dict:
        """Restart policy for the container

        Returns:
            dict: Restart policy for container<
        """
        return self.attr["HostConfig"]["RestartPolicy"]

    def start(self) -> None:
        """Start the container"""
        self.container.start()

    def stop(self) -> None:
        """Stop the container"""
        self.container.stop()

    def remove(self) -> None:
        """Remove the container"""
        self.container.remove()
        self.container = None

    def information(self) -> dict:
        """Summerizes the important information about the container.
        Adapted after requirement of information flow to server.

        Returns:
            dict: Information about the container
        """
        self.container.reload()

        return \
        {
            "name": self.name,
            "id": self.id,
            "image_sha": self.image_sha,
            "image_name": self.image_name,
            "image_repo": self.image_repo,
            "image_tag": self.image_tag,
            "status": self.status
        }

    def settings(self) -> dict:
        """Extract settings from container to enable start of a new container with the
        same settings. Adapted for the Docker SDK for Python
        [https://docker-py.readthedocs.io/en/stable/]

        The following settings are supported:

        - name
        - environment variables
        - port bindings
        - restart policy
        - volume bindings

        Container settings outside the list below will not be included in the extracted settings

        Returns:
            dict: Settings adapted for the Docker SDK for Python module
        """
        return \
        {
            "name": self.name,
            "environment": self.environment,
            "ports": self.ports,
            "restart_policy": self.restart_policy,
            "volumes": self.volumes
        }

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self.container = None
