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


class DockerHub(): # pylint: disable=too-many-instance-attributes
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
        self.cache = {}
        self.cache_time = 60

    def list_images(self) -> list:
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
            image_tag (str): image tag to acquire manifest for

        Returns:
            dict: Manifest
        """
        header = {
            'Authorization': f'Bearer {self.token()}',
            'Accept': 'application/vnd.docker.distribution.manifest.v2+json'
        }

        response = self.http_get(f'{self.base_url}/manifests/{image_tag}', headers=header)
        return response.json()

    def get_remote_image_sha(self, image_repo: str, image_tag: str) -> str:
        """Gets the image SHA from the remote repository image which
        corresponds to the defined image tag.

        Cache function enabled to minimize requests to docker hub

        Args:
            image_repo (str): Repository for the image
            image_tag (str): Image tag

        Returns:
            str: Remote image SHA. Returns None if image can't be found.
        """
        if image_repo != self.repository:
            self.log.debug(
                "Image %s:%s is not a part of %s. Information can't be returned",
                image_repo, image_tag, self.repository
            )
            return None

        self.log.debug('Checking if image SHA "%s" is in cache', image_tag)
        for cache_item_key, cache_item_value in self.cache.items():
            if cache_item_key == image_tag and datetime.now() < cache_item_value['timestamp'] + timedelta(seconds=self.cache_time): # pylint: disable=line-too-long
                self.log.debug('Valid cache found')
                return cache_item_value['remote_image_sha']
        self.log.debug('No valid cache found')

        manifest = self.get_manifest(image_tag)
        if 'errors' in manifest:
            self.log.debug('Error identified in manifest: %s', manifest)
            if manifest['errors'][0]['code'] == 'MANIFEST_UNKNOWN':
                self.log.error('Could not find image: %s:%s', image_repo, image_tag)
                self._add_to_cache(image_tag, None)

            self.log.error(
                'Error when trying to recieve manifest from docker hub. Error message: "%s"',
                manifest['errors']
            )
            return None

        try:
            remote_image_sha = manifest["config"]["digest"]
            self._add_to_cache(image_tag, remote_image_sha)

            # Cache time is based on the limitaitons for a free account at Docker hub
            # Limitations are 200 requests within 6 hours
            self.cache_time = (6 * 3600 * len(self.cache.keys())) / 200

            return remote_image_sha

        except KeyError:
            self.log.error(
                'Could not extract image SHA for %s from Manifest. Manifest content: %s',
                image_tag, manifest
            )
            return None

    def _add_to_cache(self, image_tag: str, remote_image_sha: str) -> None:
        self.cache[image_tag] = {
            "timestamp": datetime.now(),
            "remote_image_sha": remote_image_sha
        }
