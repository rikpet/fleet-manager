# pylint: skip-file

from http import HTTPStatus

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

def test_get_image_id_correct():
    mock_http_get = MockHttpGet(response=manifest_response)
    docker_hub_object = DockerHub(mock_http_get, "", "", "")

    image_id = docker_hub_object.get_image_id("fake_tag")
    assert image_id == "ABCDE"

def test_get_image_return_none():
    mock_http_get = MockHttpGet(response=manifest_response_no_image)
    docker_hub_object = DockerHub(mock_http_get, "", "", "")

    image_id = docker_hub_object.get_image_id("fake_tag")
    assert image_id is None