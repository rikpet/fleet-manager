# pylint: skip-file

from http import HTTPStatus
import time

from server.docker_hub import DockerHub
from tests.mock.mock_requests_get import MockHttpGet
from tests.mock.mock_response import MockResponse

def image_list_response():
    return MockResponse(
        response={
            "tags": [
                "mock-image-1",
                "mock-image-2",
                "mock-image-3"
            ]
        },
        status_code=HTTPStatus.ACCEPTED
    )

def manifest_response():
    return MockResponse(
        response={
            "config": {
                "digest": "ABCDE"
            }
        },
        status_code=HTTPStatus.ACCEPTED
    )

def manifest_response_2():
    return MockResponse(
        response={
            "config": {
                "digest": "BCDEF"
            }
        },
        status_code=HTTPStatus.ACCEPTED
    )

def manifest_error_response():
    return MockResponse(
        response={
            'errors': [
                {
                    'code': 'UNAUTHORIZED',
                    'message': 'authentication required',
                    'detail': [
                        {
                            'Type': 'repository',
                            'Class': '',
                            'Name': 'marthoc/deconz',
                            'Action': 'pull'
                        }
                    ]
                }
            ]
        },
        status_code=HTTPStatus.ACCEPTED
    )

def manifest_response_no_image():
    return MockResponse(response={}, status_code=HTTPStatus.ACCEPTED)

def test_returning_correct_image_list():
    mock_http_get = MockHttpGet(response=image_list_response)
    docker_hub_object = DockerHub(mock_http_get, "", "", "")

    image_list = docker_hub_object.list_images()
    assert image_list == [
        "mock-image-1",
        "mock-image-2",
        "mock-image-3"
    ]

    assert mock_http_get.header["Authorization"] == f"Bearer {mock_http_get.token_number}"

def test_returning_manifest():
    expected_response = {
        "config": {
            "digest": "ABCDE"
        }
    }

    mock_http_get = MockHttpGet(response=manifest_response)
    docker_hub_object = DockerHub(mock_http_get, "", "", "")

    manifest = docker_hub_object.get_manifest("fake_tag")
    assert manifest == expected_response

    assert "/manifests/fake_tag" in mock_http_get.received_url
    assert mock_http_get.header["Authorization"] == f"Bearer {mock_http_get.token_number}"
    assert mock_http_get.header["Accept"] == 'application/vnd.docker.distribution.manifest.v2+json'

def test_get_remote_image_sha_returns_correct():
    mock_http_get = MockHttpGet(response=manifest_response)
    docker_hub_object = DockerHub(mock_http_get, "", "", "fake_repo")

    image_sha = docker_hub_object.get_remote_image_sha("fake_repo", "fake_tag")
    assert image_sha == "ABCDE"

def test_get_image_returns_none_if_wrong_repo():
    mock_http_get = MockHttpGet(response=manifest_response)
    docker_hub_object = DockerHub(mock_http_get, "", "", "a_repo")

    image_sha = docker_hub_object.get_remote_image_sha("another_repo", "fake_tag")
    assert image_sha is None

def test_get_image_returns_none():
    mock_http_get = MockHttpGet(response=manifest_response_no_image)
    docker_hub_object = DockerHub(mock_http_get, "", "", "fake_repo")

    image_sha = docker_hub_object.get_remote_image_sha("fake_repo", "fake_tag")
    assert image_sha is None

def test_docker_hub_error_response_returns_none():
    mock_http_get = MockHttpGet(response=manifest_error_response)
    docker_hub_object = DockerHub(mock_http_get, "", "", "fake_repo")

    image_sha = docker_hub_object.get_remote_image_sha("fake_repo", "fake_tag")
    assert image_sha is None


def test_image_sha_cache_functions_correctly():
    mock_http_get = MockHttpGet(response=manifest_response)
    docker_hub_object = DockerHub(mock_http_get, "", "", "fake_repo")

    image_sha_1 = docker_hub_object.get_remote_image_sha("fake_repo", "fake_tag")
    mock_http_get.response = manifest_response_2
    image_sha_2 = docker_hub_object.get_remote_image_sha("fake_repo", "fake_tag")
    assert image_sha_1 == image_sha_2 == "ABCDE"

def test_image_sha_gets_new_sha_after_chache_timeout():
    mock_http_get = MockHttpGet(response=manifest_response)
    docker_hub_object = DockerHub(mock_http_get, "", "", "fake_repo")

    image_sha_1 = docker_hub_object.get_remote_image_sha("fake_repo", "fake_tag")
    
    mock_http_get.response = manifest_response_2
    docker_hub_object.cache_time = 1
    time.sleep(2)

    image_sha_2 = docker_hub_object.get_remote_image_sha("fake_repo", "fake_tag")
    assert image_sha_1 == "ABCDE"
    assert image_sha_2 == "BCDEF"
