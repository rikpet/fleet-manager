# pylint: skip-file

import pytest
from datetime import datetime
from tests.mock.mock_requests_get import MockHttpGet
from server.docker_hub import Token

def test_token_can_be_retrieved():
    mock_http_get = MockHttpGet()
    token_object = Token(mock_http_get, "", "", "")
    
    # Checking first token creation
    token = token_object()
    assert token == "1"

    # Checking second token creation.
    # Should no change as token has not expired
    token = token_object()
    assert token == "1"

    # Checking token renewal
    token_object._expires = datetime(2020, 1, 1)
    token = token_object()
    assert token == "2"

def test_token_when_unauthorized():
    mock_http_get = MockHttpGet(respond_unauthorized=True)
    token_object = Token(mock_http_get, "", "", "")
    
    with pytest.raises(PermissionError) as e_info:
        token = token_object()
