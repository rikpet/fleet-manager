"""Module to mock python standard library :module:`requests"""
from http import HTTPStatus
from tests.mock.mock_response import MockResponse

class MockHttpGet():
    """Object to mock :object:``requests.get``"""
    def __init__(self, respond_unauthorized = False, response = None) -> None:
        self.respond_unauthorized = respond_unauthorized
        self.response = response

        self.received_url = None
        self.header = None

        self.token_number = 0

    def __call__(self, url, headers=None):
        self.received_url = url
        self.header = headers

        if "auth.docker.io" in url:  # Token request
            return self.token_response(self.respond_unauthorized)

        return self.response()

    def token_response(self, unauthorized):
        if unauthorized:
            return MockResponse(
                response=None,
                status_code=HTTPStatus.UNAUTHORIZED
            )

        self.token_number += 1
        return MockResponse(
            response={
                "token": f"{self.token_number}",
                "expires_in": "30"
            },
            status_code=HTTPStatus.ACCEPTED
        )
