# pylint: skip-file

import json
import pytest
from client.container import Container

with open('tests/client_container_attribute_sample.json', encoding='utf-8') as stream:
    CONTAINER_ATTRIBUTE_SAMPLE = json.load(stream)

class MockContainer():
    def __init__(self, attributes) -> None:
        self.attrs = attributes

    @staticmethod
    def reload():
        return None

@pytest.fixture
def mock_container():
    mock_container_object = MockContainer(CONTAINER_ATTRIBUTE_SAMPLE)
    return Container(mock_container_object)

def test_name_is_extracted_correctly(mock_container):
    assert mock_container.name == "fm-server"

def test_id_is_extracted_correctly(mock_container):
    assert mock_container.id == "31a512bc7e"

def test_full_id_is_extracted_correctly(mock_container):
    assert mock_container.full_id == "31a512bc7e90a6046bfd9a08dca1eb8bda1f96671cb8052a263bd8c7496cf7d3"

def test_sha_is_extracted_correctly(mock_container):
    assert mock_container.image_sha == "sha256:25cc55b19c1d34f6911e366d840497cc80a9eb4808d80f03e86a1225acc730be"

def test_tag_is_extracted_correctly(mock_container):
    assert mock_container.image_tag == "fm-server-latest"

def test_running_is_extracted_correctly(mock_container):
    assert mock_container.running is True

def test_status_is_extracted_correctly(mock_container):
    assert mock_container.status == "running"

def test_volumes_is_extracted_correctly(mock_container):
    assert mock_container.volumes == ['/var/run/docker.sock:/var/run/docker.sock', '/test/source:/test/destination']

def test_environment_is_extracted_correctly(mock_container):
    assert len(mock_container.environment) == 4
    assert mock_container.environment == [
        'FLASK_ENV=development',
        'DOCKER_HUB_USERNAME=testusername',
        'DOCKER_HUB_PASSWORD=testpassword',
        'DOCKER_HUB_REPO=rikpet/easy-living'
    ]
    assert any(env[:4] == "PATH" for env in mock_container.environment) is False

def test_ports_are_extracted_correctly(mock_container):
    assert mock_container.ports == {"5000/tcp":"5010"}

def test_retry_policy_is_extracted_correctly(mock_container):
    assert mock_container.restart_policy == {"Name": "always", "MaximumRetryCount": 0}
