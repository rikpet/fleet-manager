"""Module to handle Docker hub integration"""
from datetime import datetime, timedelta
from http import HTTPStatus
import requests

class Token(): # pylint: disable=too-few-public-methods
    """Token handler for docker hub authentication token"""
    BASE_URL = "https://%s:%s@auth.docker.io/token?service=registry.docker.io&scope=repository:%s:pull" # pylint: disable=line-too-long

    def __init__(self, username: str, password: str, repository: str) -> None:
        self._token = ""
        self._expires = datetime(2020, 1, 1)

        self._username = username
        self._password = password
        self._repository = repository

    def __call__(self):
        if datetime.now() > self._expires:
            self._get_new_token()
        return self._token

    def _get_new_token(self):
        # TODO: error handling
        response = requests.get(self.BASE_URL % (self._username, self._password, self._repository))
        response_body = response.json()

        self._token = response_body["token"]
        self._expires = datetime.now() + timedelta(seconds=int(response_body["expires_in"]) - 5)


class DockerHub():
    """Wraps the integration towards Docker hub"""

    BASE_URL = "https://index.docker.io/v2/%s"

    def __init__(self, username: str, password: str, repository: str) -> None:
        self.repository = repository

        self.base_url = self.BASE_URL % self.repository
        self.token = Token(username, password, repository)

        self.images = []
        self.list_images()

    def list_images(self):
        header = {'Authorization': f'Bearer {self.token()}'}
        response = requests.get(f'{self.base_url}/tags/list', headers=header)
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise PermissionError('Could not log in to docker hub')

        response_body = response.json()
        self.images = response_body["tags"]
        return self.images

    def get_manifest(self, image):
        header = {
            'Authorization': f'Bearer {self.token()}',
            'Accept': 'application/vnd.docker.distribution.manifest.v2+json'
        }
        response = requests.get(f'{self.base_url}/manifests/{image}', headers=header)
        return response.json()

    def get_image_id(self, image):
        manifest = self.get_manifest(image)
        return manifest["config"]["digest"]

    def get_all_image_ids(self, images=None):
        if images is None:
            self.list_images()
            images = self.images
        image_ids = {}
        for image in images:
            image_ids[image] = self.get_image_id(image)
        return image_ids
