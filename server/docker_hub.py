"""Module to handle Docker hub integration"""
from datetime import datetime, timedelta
from http import HTTPStatus
from logging import getLogger
import requests

class Token(): # pylint: disable=too-few-public-methods
    """Token handler for docker hub authentication token"""
    BASE_URL = "https://%s:%s@auth.docker.io/token?service=registry.docker.io&scope=repository:%s:pull" # pylint: disable=line-too-long

    def __init__(self, http_get: object, username: str, password: str, repository: str) -> None:
        self._token = ""
        self._expires = datetime(2020, 1, 1)

        self.http_get = http_get

        self._username = username
        self._password = password
        self._repository = repository

    def __call__(self):
        if datetime.now() > self._expires:
            self._get_new_token()
        return self._token

    def _get_new_token(self):
        response = self.http_get(self.BASE_URL % (self._username, self._password, self._repository))

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise PermissionError('Could not log in to docker hub')

        response_body = response.json()

        self._token = response_body["token"]
        self._expires = datetime.now() + timedelta(seconds=int(response_body["expires_in"]) - 5)


class DockerHub():
    """Wraps the integration towards Docker hub

    Args:
        http_get (requests.get): Get object from python standard library :module:`requests`
        username (str): Docker hub username
        password (str): Docker hub password
        password (str): Docker hub repository
    """

    BASE_URL = "https://index.docker.io/v2/%s"

    def __init__(   self, http_get: requests.get, username: str,
                    password: str, repository: str) -> None:

        self.repository = repository
        self.http_get = http_get

        self.base_url = self.BASE_URL % self.repository
        self.token = Token(http_get, username, password, repository)

        self.log = getLogger(self.__class__.__name__)

        self.images = []

    def list_images(self) -> list[str]:
        """List available images in repository"

        Returns:
            list[str]: Image tags
        """
        header = {'Authorization': f'Bearer {self.token()}'}
        response = self.http_get(f'{self.base_url}/tags/list', headers=header)

        response_body = response.json()
        self.images = response_body["tags"]
        return self.images

    def get_manifest(self, image_tag: str) -> dict:
        """Retrieves the manifest for the specified image from remote repository

        Args:
            image_tag (str): image to acquire manifest for

        Returns:
            dict: Manifest
        """
        header = {
            'Authorization': f'Bearer {self.token()}',
            'Accept': 'application/vnd.docker.distribution.manifest.v2+json'
        }
        response = self.http_get(f'{self.base_url}/manifests/{image_tag}', headers=header)
        return response.json()

    def get_image_id(self, image_tag: str) -> str:
        """Gets the image ID (SHA) from the remote repository image which
        corresponds to the defined image_tag

        Args:
            image_tag (str): Image tag

        Returns:
            str: Remote image ID (SHA). Returns None if image can't be found.
        """
        try:
            manifest = self.get_manifest(image_tag)
            return manifest["config"]["digest"]
        except KeyError:
            return None
